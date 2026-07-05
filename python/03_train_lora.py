#!/usr/bin/env python3
"""
Gemma-3-4b LoRA SFT 训练脚本 (测试用)

使用 4-bit QLoRA 在 6GB 显存下进行轻量微调，验证数据管线和训练流程。
训练数据格式: JSONL (instruction + output)，自动转换为 Gemma 对话模板格式
（<start_of_turn>user / <start_of_turn>model）。

Usage:
    python python/train_lora.py
"""

import os

# 必须在 import torch 之前设置，减少显存碎片，
# 在显存紧张（6GB）时能多出一些可用空间，避免过早触发 OOM / 共享内存回退
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import json
import random
import torch
import numpy as np
from pathlib import Path
from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
    set_seed,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training


# ============ 路径配置 ============
MODEL_PATH = r"D:\Astro\Moss VMina\gemma\gemma-3-4b"
TRAIN_PATH = r"D:\Astro\Moss VMina\data\07_train_test_2_spilt\train.jsonl"
VAL_PATH = r"D:\Astro\Moss VMina\data\07_train_test_2_spilt\val.jsonl"
OUTPUT_DIR = r"D:\Astro\Moss VMina\output\lora_test"

# ============ 超参数 ============
SEED = 42

LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]
# 如果做完下面的调整显存还是紧张，可以先只打开注意力层，
# 去掉 gate/up/down_proj（MLP 层参数量大，可训练参数会明显变多）：
# TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj"]

# 6GB 显存下，attention 显存占用是 O(seq_len^2)，MAX_LENGTH 从 1024 降到 512
# 对显存的影响远大于调 batch size。先看你的数据实际长度分布，
# 如果大多数样本用不到 512，可以再降到 256~384。
MAX_LENGTH = 512
NUM_EPOCHS = 3
BATCH_SIZE = 1
GRADIENT_ACCUMULATION = 4
LEARNING_RATE = 2e-4
WEIGHT_DECAY = 0.01
LR_SCHEDULER_TYPE = "cosine"
WARMUP_RATIO = 0.03
EVAL_STEPS = 50
# LOG_STEPS = 10
LOG_STEPS = 1
SAVE_STEPS = 100

# 用于在数据集构建后打印前 N 条样本的 mask 结果，人工核对是否正确
# （详细日志只打印这么多条，避免刷屏；真正的边界校验见下面 FULL_SCAN_ON_LOAD）
NUM_SANITY_CHECK_SAMPLES = 3

# True: 数据集加载时对*全部*样本跑一遍 _build_ids_and_labels，
# 提前把所有"prompt 过长 / BPE 边界不一致"的坏样本暴露出来，
# 而不是训练跑到一半才在某个 batch 上炸掉。
# 对几千条以内的数据集，这个开销可以忽略不计。
FULL_SCAN_ON_LOAD = True


# ============ 数据集 ============
class SFTDataset(Dataset):
    """将 instruction-output JSONL 转为 Gemma 对话格式并 tokenize。

    Assistant-mask 实现说明（重点修复点）：
    原实现是对完整对话文本一次性 tokenize，然后在 token 序列中用
    「单独 encode 模型的 assistant 起始标记（比如 Gemma 的
    `<start_of_turn>model`，或 Qwen 的 `<|im_start|>assistant`）」
    的结果去做子串匹配，以此定位 assistant 回复的起始位置。
    这个方法本质上不可靠，原因：
      1. BPE/BBPE 分词是上下文相关的。单独对起始标记编码得到的
         token id 序列，和它出现在完整对话文本中间时被切分出的
         token id 序列，在边界处可能并不相同（合并方式不同），
         导致子串匹配不到。
      2. 匹配不到时代码会静默地把整条样本的 labels 全部设为 -100，
         也就是这条样本完全不参与 loss 计算，但训练不会报错或警告，
         非常隐蔽，容易在跑了很久之后才发现某些样本根本没训练到。

    修复方案：不做"先拼全文再找位置"的反向工程，而是分别对
    "只到 assistant 起始标记为止的 prompt" 和 "完整对话" 各自
    调用 apply_chat_template + tokenizer 一次，用 prompt 部分的
    token 长度直接作为 mask 边界。并加入一致性校验：如果
    full_ids 的前 prompt_len 个 token 与 prompt_ids 不完全一致
    （说明边界处分词发生了变化），直接抛出异常而不是静默产生
    错误的 mask，方便第一时间发现问题。
    """

    def __init__(self, path: str, tokenizer, max_length: int = MAX_LENGTH):
        self.tokenizer = tokenizer
        self.max_length = max_length

        self.data = []
        with open(path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError as e:
                    raise ValueError(f"{path} 第 {line_no} 行 JSON 解析失败: {e}")
                if "instruction" not in item or "output" not in item:
                    raise ValueError(
                        f"{path} 第 {line_no} 行缺少 instruction/output 字段: {item}"
                    )
                self.data.append(item)
        print(f"  Loaded {len(self.data)} samples from {path}")

        self._sanity_check()

    def __len__(self):
        return len(self.data)

    def _build_ids_and_labels(self, idx):
        item = self.data[idx]
        instruction = item["instruction"]
        output = item["output"]

        user_only = [{"role": "user", "content": instruction}]
        full_conv = user_only + [{"role": "assistant", "content": output}]

        # prompt_text: 到 "<|im_start|>assistant\n" 为止（不含 assistant 的实际内容）
        prompt_text = self.tokenizer.apply_chat_template(
            user_only, tokenize=False, add_generation_prompt=True
        )
        # full_text: 完整的一问一答
        full_text = self.tokenizer.apply_chat_template(
            full_conv, tokenize=False, add_generation_prompt=False
        )

        prompt_ids = self.tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
        full_ids = self.tokenizer(
            full_text,
            add_special_tokens=False,
            truncation=True,
            max_length=self.max_length,
        )["input_ids"]

        prompt_len = len(prompt_ids)

        # 检查顺序很重要：必须先排除"prompt 本身就超长"这种情况，
        # 否则下面的前缀比对会因为 full_ids 被截断而失败，
        # 报出"BPE 边界不一致"这种文不对题的错误信息，
        # 让人误以为是分词器问题，实际上只是 instruction 太长。
        if prompt_len >= self.max_length:
            raise RuntimeError(
                f"[样本 idx={idx}] prompt（仅 instruction 部分）本身长度"
                f"({prompt_len}) 已达到或超过 max_length({self.max_length})，"
                "说明这条样本的指令本身就过长，与 assistant 回复无关。"
                "请检查该样本内容，或考虑调大 max_length / 过滤掉超长样本。\n"
                f"  instruction 前80字符: {instruction[:80]!r}"
            )

        if full_ids[:prompt_len] != prompt_ids:
            raise RuntimeError(
                f"[样本 idx={idx}] prompt 的 token 前缀与完整对话不一致，"
                "说明 tokenizer 在 prompt/response 边界处发生了不同的 BPE 合并，"
                "无法用长度直接切分 mask。请检查 chat_template 或联系模型作者确认"
                "assistant 起始标记附近是否有特殊分词行为。\n"
                f"  prompt_ids tail = {prompt_ids[-8:]}\n"
                f"  full_ids  same pos = {full_ids[max(0, prompt_len - 8):prompt_len]}"
            )

        if prompt_len >= len(full_ids):
            raise RuntimeError(
                f"[样本 idx={idx}] prompt 长度({prompt_len}) >= 截断后总长度"
                f"({len(full_ids)})，assistant 回复被 max_length={self.max_length} "
                "完全截断（instruction 本身没超长，是 output 太长导致整体被截掉了）。"
                "请检查该样本长度或调大 max_length。"
            )

        labels = [-100] * prompt_len + full_ids[prompt_len:]
        return full_ids, labels, prompt_len

    def _sanity_check(self):
        """构建后核对 mask 是否落在正确位置。

        两步：
          1) 对前 NUM_SANITY_CHECK_SAMPLES 条样本打印详细的人工核对信息
             （prompt_len / total_len / 解码内容是否匹配 output），方便肉眼确认。
          2) 如果 FULL_SCAN_ON_LOAD=True，再对*全部*样本跑一遍
             _build_ids_and_labels（不打印，只校验），把所有"指令过长"
             或"BPE 边界不一致"的坏样本在训练开始前就一次性找出来，
             而不是等训练跑到某个 batch 才崩溃。
        """
        n = min(NUM_SANITY_CHECK_SAMPLES, len(self.data))
        if n > 0:
            print(f"  [sanity check] 核对前 {n} 条样本的 assistant mask...")
            for i in range(n):
                full_ids, labels, prompt_len = self._build_ids_and_labels(i)
                unmasked_ids = [t for t in full_ids[prompt_len:]]
                decoded_span = self.tokenizer.decode(
                    unmasked_ids, skip_special_tokens=True
                ).strip()
                expected = self.data[i]["output"].strip()
                match = decoded_span[: min(60, len(decoded_span))] == expected[: min(60, len(expected))]
                print(
                    f"    - idx={i} prompt_len={prompt_len} total_len={len(full_ids)} "
                    f"前60字符匹配: {match}"
                )
                if not match:
                    print(f"      [WARNING] 解码得到: {decoded_span[:80]!r}")
                    print(f"      [WARNING] 期望内容: {expected[:80]!r}")

        if FULL_SCAN_ON_LOAD:
            total = len(self.data)
            print(f"  [full scan] 对全部 {total} 条样本做 mask 边界校验...")
            bad = []
            for i in range(total):
                try:
                    self._build_ids_and_labels(i)
                except RuntimeError as e:
                    bad.append((i, str(e)))
            if bad:
                preview = "\n".join(
                    f"  --- idx={i} ---\n{msg}" for i, msg in bad[:10]
                )
                more = f"\n  ...(还有 {len(bad) - 10} 条未展示)" if len(bad) > 10 else ""
                raise RuntimeError(
                    f"[full scan] 发现 {len(bad)}/{total} 条样本存在问题，"
                    f"训练前必须先修复或过滤这些样本：\n{preview}{more}"
                )
            print(f"  [full scan] 全部通过，未发现坏样本。")

    def __getitem__(self, idx):
        full_ids, labels, _ = self._build_ids_and_labels(idx)
        return {
            "input_ids": full_ids,
            "attention_mask": [1] * len(full_ids),
            "labels": labels,
        }


# ============ 主流程 ============
def main():
    print("=" * 55)
    print("  Gemma-3-4B LoRA SFT — 测试训练")
    print("=" * 55)

    set_seed(SEED)
    random.seed(SEED)
    np.random.seed(SEED)

    if not torch.cuda.is_available():
        print("[ERROR] CUDA 不可用！训练需要 GPU。")
        return

    device_name = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f"\n  GPU: {device_name}  ({vram:.1f} GB)")
    use_bf16 = torch.cuda.is_bf16_supported()
    print(f"  BF16 support: {use_bf16}")

    # ---- 0. 路径检查 ----
    for name, p in [
        ("MODEL_PATH", MODEL_PATH),
        ("TRAIN_PATH", TRAIN_PATH),
        ("VAL_PATH", VAL_PATH),
    ]:
        if not Path(p).exists():
            raise FileNotFoundError(f"{name} 不存在: {p}")
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # ---- 1. Tokenizer ----
    print("\n[1/6] 加载 Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 重要：先记录"模型是否自带 chat_template"，
    # 因为如果自带了，下面的 fallback 模板根本不会被使用——
    # 这里明确打印出来，避免误以为训练用的是你手写的那份模板。
    has_builtin_template = tokenizer.chat_template is not None
    if has_builtin_template:
        print("  chat_template 来源: 模型自带（tokenizer_config 中的 chat_template）")
    else:
        print("  [WARNING] tokenizer 无内建 chat_template，使用手写的 Gemma 默认模板")
        tokenizer.chat_template = (
            "{{ bos_token }}"
            "{% for message in messages %}"
            "{% if message['role'] == 'user' %}"
            "{{ '<start_of_turn>user\\n' + message['content'] + '<end_of_turn>\\n' }}"
            "{% elif message['role'] == 'assistant' %}"
            "{{ '<start_of_turn>model\\n' + message['content'] + '<end_of_turn>\\n' }}"
            "{% endif %}"
            "{% endfor %}"
            "{% if add_generation_prompt %}{{ '<start_of_turn>model\\n' }}{% endif %}"
        )
        print("  chat_template 来源: 手写 fallback（Gemma <start_of_turn> 格式）")

    # 打印一个真实样例，直观确认 prompt 边界到底切在哪里
    _demo_prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": "示例问题"}],
        tokenize=False,
        add_generation_prompt=True,
    )
    print(f"  chat_template 渲染示例 (add_generation_prompt=True):\n{_demo_prompt!r}")

    # 训练阶段用右侧 padding（生成/推理阶段再改回 left）
    tokenizer.padding_side = "right"

    # ---- 2. Dataset ----
    print("\n[2/6] 加载数据集...")
    train_dataset = SFTDataset(TRAIN_PATH, tokenizer)
    val_dataset = SFTDataset(VAL_PATH, tokenizer)

    # ---- 3. 量化配置 ----
    print("\n[3/6] 配置 4-bit 量化...")
    compute_dtype = torch.bfloat16 if use_bf16 else torch.float16
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=True,
    )

    # ---- 4. 加载模型 ----
    print("\n[4/6] 加载模型 (4-bit)...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        quantization_config=bnb_config,
        # device_map="auto" 在显存不够时可能会把部分层悄悄 offload 到 CPU，
        # 这本身也会导致训练速度断崖式下跌（现象和"共享内存"一样，都是
        # GPU 在等 CPU/RAM 搬数据）。单卡场景下明确指定到 cuda:0，
        # 这样一旦真的放不下会直接报 OOM，而不是偷偷变慢让你难以排查。
        device_map={"": 0},
        trust_remote_code=True,
        dtype=compute_dtype,
        # Gemma3 不再需要 attention softcap 强制 eager，用 sdpa 可以显著降低
        # attention 的显存峰值（不用手动 materialize 完整的 seq_len x seq_len 矩阵）。
        # 如果装了 flash-attn，可以改成 "flash_attention_2" 进一步省显存。
        attn_implementation="sdpa",
    )
    model.config.use_cache = False  # 与 gradient checkpointing 同时开启会冲突/报警告，必须关闭
    model = prepare_model_for_kbit_training(model)
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})

    # ---- 5. LoRA ----
    print("\n[5/6] 应用 LoRA...")
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        target_modules=TARGET_MODULES,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # ---- 6. 训练 ----
    print("\n[6/6] 开始训练...")
    steps_per_epoch = max(1, len(train_dataset) // (BATCH_SIZE * GRADIENT_ACCUMULATION))
    total_steps = steps_per_epoch * NUM_EPOCHS
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        num_train_epochs=NUM_EPOCHS,
        learning_rate=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
        lr_scheduler_type=LR_SCHEDULER_TYPE,
        warmup_steps=max(1, int(total_steps * WARMUP_RATIO)),
        fp16=not use_bf16,
        bf16=use_bf16,
        logging_steps=LOG_STEPS,
        eval_strategy="steps",
        eval_steps=EVAL_STEPS,
        save_strategy="steps",
        save_steps=SAVE_STEPS,
        save_total_limit=2,
        remove_unused_columns=False,
        report_to="none",
        dataloader_num_workers=0,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        # paged_adamw_8bit 在优化器状态可能瞬间增大时会自动 page 到 CPU 内存，
        # 相比普通 adamw_8bit 更不容易在显存边缘触发 OOM / 共享内存回退。
        # 注意：paged 系列优化器依赖 bitsandbytes 的 CUDA 分页机制，在 Windows 上
        # （bitsandbytes 官方主要支持 Linux，Windows 版是社区/非官方编译）
        # 稳定性不如 Linux。如果实际运行时在 optimizer.step() 报错或功能异常，
        # 先退回下面这行普通版本排查：
        # optim="adamw_8bit",
        optim="paged_adamw_8bit",
        seed=SEED,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        processing_class=tokenizer,
        data_collator=DataCollatorForSeq2Seq(
            tokenizer, pad_to_multiple_of=8, padding=True, label_pad_token_id=-100
        ),
    )

    trainer.train()

    # ---- 保存 ----
    print(f"\n保存 LoRA adapter 到 {OUTPUT_DIR}...")
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("\nDone!")


if __name__ == "__main__":
    main()
