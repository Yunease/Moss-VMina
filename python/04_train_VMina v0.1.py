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
    DataCollatorForLanguageModeling,
    set_seed,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training


# ============ 路径配置 ============
MODEL_PATH = r"D:\Astro\Moss VMina\qwen\Qwen3.5-0.8B"
TRAIN_PATH = r"D:\Astro\Moss VMina\data\07_train_test_2_spilt\merged_train.jsonl"
VAL_PATH = r"D:\Astro\Moss VMina\data\06_train_test_split\val.jsonl"
OUTPUT_DIR = r"D:\Astro\Moss VMina\output\lora_test"

# ============ System Prompt ============
# 必须与推理时使用的 system prompt 完全一致，否则训练/推理分布不一致
SYSTEM_PROMPT = "你是 Moss VMina，琴泠的朋友。"

# ============ 超参数 ============
SEED = 42
 
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.1
TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]

MAX_LENGTH = 512
NUM_EPOCHS = 1.5
BATCH_SIZE = 1
GRADIENT_ACCUMULATION = 4
LEARNING_RATE = 1e-4
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

    def __init__(self, path: str, tokenizer, max_length=MAX_LENGTH):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.data = []

        with open(path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                item = json.loads(line)

                if "instruction" not in item or "output" not in item:
                    raise ValueError(
                        f"{path} 第 {line_no} 行缺少 instruction/output"
                    )

                self.data.append(item)

        print(f"  Loaded {len(self.data)} samples from {path}")
        self._sanity_check()


    def __len__(self):
        return len(self.data)


    def _build_ids_and_labels(self, idx):

        item = self.data[idx]

        # ---- 用 system + user + assistant 构造完整对话 ----
        # 训练和推理必须使用同一个 system prompt，否则会分布漂移
        full_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": item["instruction"]},
            {"role": "assistant", "content": item["output"]},
        ]

        # 只有 system + user，用于定位 "assistant 回答开始之前" 的边界
        prompt_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": item["instruction"]},
        ]

        full_ids = self.tokenizer.apply_chat_template(
            full_messages,
            tokenize=True,
            add_generation_prompt=False,
        )
        if hasattr(full_ids, "input_ids"):
            full_ids = full_ids["input_ids"]

        prompt_ids = self.tokenizer.apply_chat_template(
            prompt_messages,
            tokenize=True,
            add_generation_prompt=True,
        )
        if hasattr(prompt_ids, "input_ids"):
            prompt_ids = prompt_ids["input_ids"]

        prompt_len = len(prompt_ids)

        # 保险起见：如果模板本身没有在结尾加上 eos/im_end，手动补上
        # （大多数 Qwen 模板会自动加 <|im_end|>，这里做兜底，避免模型学不会何时停止）
        eos_id = self.tokenizer.eos_token_id
        if eos_id is not None and (len(full_ids) == 0 or full_ids[-1] != eos_id):
            full_ids = full_ids + [eos_id]

        input_ids = full_ids
        labels = [-100] * prompt_len + input_ids[prompt_len:]

        # ---- 截断处理：优先保留完整回答（labels 非 -100 的部分）----
        if len(input_ids) > self.max_length:
            answer_part_len = len(input_ids) - prompt_len
            if answer_part_len >= self.max_length:
                # 回答本身就超长，只能截断回答，prompt 全部丢弃
                input_ids = input_ids[prompt_len:][:self.max_length]
                labels = input_ids[:]  # 全部计算 loss（已不含 prompt）
                prompt_len = 0
            else:
                # 从左侧裁掉多余的 prompt，保留回答完整
                keep_prompt = self.max_length - answer_part_len
                input_ids = input_ids[prompt_len - keep_prompt:]
                labels = [-100] * keep_prompt + labels[prompt_len:]
                prompt_len = keep_prompt

        return input_ids, labels, prompt_len


    def _sanity_check(self):

        n = min(NUM_SANITY_CHECK_SAMPLES, len(self.data))

        print(f"[sanity check] 检查 {n} 条样本")

        for i in range(n):

            ids, labels, prompt_len = self._build_ids_and_labels(i)

            # 打印完整序列（prompt + answer），而不是只 decode label
            # 这样才能看到 <think> / role token 之类的内容是否符合预期
            full_text = self.tokenizer.decode(
                ids,
                skip_special_tokens=False
            )

            target_ids = [
                x for x, y in zip(ids, labels)
                if y != -100
            ]
            loss_text = self.tokenizer.decode(
                target_ids,
                skip_special_tokens=False
            )

            print(f"idx={i}, prompt_len={prompt_len}")
            print(f"  完整序列={full_text!r}")
            print(f"  loss文本={loss_text[:80]!r}")

            # 检查 loss 文本（真正参与训练 loss 的部分）里是否泄露了 role token
            # 如果这里出现 <think>/assistant 等，说明 mask 边界算错了
            for bad in [
                "<|im_start|>",
                "<|im_end|>",
                "<think>",
                "</think>",
                "assistant",
                "user",
                "system",
            ]:
                if bad in loss_text:
                    print(f"[WARNING] loss文本中检测到 role/think token: {bad}")

            # eos 检查：确认每条样本真的以 eos/im_end 结尾
            if ids[-1] != self.tokenizer.eos_token_id:
                print(f"[WARNING] idx={i} 样本末尾不是 eos_token_id，结束符可能没生效")


    def __getitem__(self, idx):

        input_ids, labels, _ = self._build_ids_and_labels(idx)

        return {
            "input_ids": input_ids,
            "attention_mask": [1] * len(input_ids),
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
        data_collator=DataCollatorForLanguageModeling(
            tokenizer,
            mlm=False,
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