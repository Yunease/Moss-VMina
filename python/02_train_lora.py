#!/usr/bin/env python3
"""
Qwen3.5-0.8B LoRA SFT 训练脚本 (测试用)

使用 4-bit QLoRA 在 6GB 显存下进行轻量微调，验证数据管线和训练流程。
训练数据格式: JSONL (instruction + output)，自动转换为 Qwen 对话模板格式。

Usage:
    python python/train_lora.py
"""

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
MODEL_PATH = r"D:\Astro\Moss VMina\qwen\Qwen3.5-0.8B"
TRAIN_PATH = r"D:\Astro\Moss VMina\data\07_train_test_2_spilt\merged_train.jsonl"
VAL_PATH = r"D:\Astro\Moss VMina\data\06_train_test_split\val.jsonl"
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

MAX_LENGTH = 2048
NUM_EPOCHS = 3
BATCH_SIZE = 1
GRADIENT_ACCUMULATION = 4
LEARNING_RATE = 2e-4
WEIGHT_DECAY = 0.01
LR_SCHEDULER_TYPE = "cosine"
WARMUP_RATIO = 0.03
EVAL_STEPS = 50
LOG_STEPS = 10
SAVE_STEPS = 100

# 用于在数据集构建后打印前 N 条样本的 mask 结果，人工核对是否正确
NUM_SANITY_CHECK_SAMPLES = 3


# ============ 数据集 ============
class SFTDataset(Dataset):
    """将 instruction-output JSONL 转为 Qwen 对话格式并 tokenize。

    Assistant-mask 实现说明（重点修复点）：
    原实现是对完整对话文本一次性 tokenize，然后在 token 序列中用
    `tokenizer.encode("<|im_start|>assistant")` 的结果去做子串匹配，
    以此定位 assistant 回复的起始位置。这个方法本质上不可靠，原因：
      1. BPE/BBPE 分词是上下文相关的。单独对
         "<|im_start|>assistant" 编码得到的 token id 序列，
         和它出现在完整对话文本中间时被切分出的 token id 序列，
         在边界处可能并不相同（合并方式不同），导致子串匹配不到。
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

    messages = [
        {
            "role": "user",
            "content": instruction
        },
        {
            "role": "assistant",
            "content": output
        }
    ]

    # 完整对话
    full_ids = self.tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=False,
        truncation=True,
        max_length=self.max_length,
    )

    # 只到 assistant 内容开始之前
    prompt_messages = [
        {
            "role": "user",
            "content": instruction
        }
    ]

    prompt_ids = self.tokenizer.apply_chat_template(
        prompt_messages,
        tokenize=True,
        add_generation_prompt=True,
    )


    prompt_len = len(prompt_ids)


    # 安全检查
    if full_ids[:prompt_len] != prompt_ids:
        print("WARNING: chat template boundary mismatch")

        # fallback:
        # 找 assistant content 的真实token位置
        assistant_ids = self.tokenizer(
            output,
            add_special_tokens=False
        )["input_ids"]

        prompt_len = len(full_ids) - len(assistant_ids)



    labels = [-100] * prompt_len + full_ids[prompt_len:]


    # 防止 assistant header 泄露
    for i in range(prompt_len):
        labels[i] = -100


    return full_ids, labels, prompt_len

    def _sanity_check(self):
        """构建后立即抽样人工核对 mask 是否落在正确位置。"""
        n = min(NUM_SANITY_CHECK_SAMPLES, len(self.data))
        if n == 0:
            return
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
    print("  Qwen3.5-0.8B LoRA SFT — 测试训练")
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
    if tokenizer.chat_template is None:
        raise ValueError(
            "该 tokenizer 没有 chat_template，无法用 apply_chat_template 构造对话格式。"
        )
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
        device_map="auto",
        trust_remote_code=True,
        dtype=compute_dtype,
    )
    model.config.use_cache = False  # 与 gradient checkpointing 同时开启会冲突/报警告，必须关闭
    model = prepare_model_for_kbit_training(model)
    model.gradient_checkpointing_enable()

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
        optim="adamw_8bit",
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
