#!/usr/bin/env python3
"""
Qwen3.5-0.8B LoRA SFT 训练脚本 (测试用)

使用 4-bit QLoRA 在 6GB 显存下进行轻量微调，验证数据管线和训练流程。
训练数据格式: JSONL (instruction + output)，自动转换为 Qwen 对话模板格式。

Usage:
    python python/train_lora.py
"""

import json
import torch
from pathlib import Path
from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training


# ============ 路径配置 ============
MODEL_PATH = r"D:\Astro\Moss VMina\qwen\Qwen3.5-0.8B"
TRAIN_PATH = r"D:\Astro\Moss VMina\data\06_train_test_split\train.jsonl"
VAL_PATH = r"D:\Astro\Moss VMina\data\06_train_test_split\val.jsonl"
OUTPUT_DIR = r"D:\Astro\Moss VMina\output\lora_test"

# ============ 超参数 ============
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
WARMUP_RATIO = 0.03
EVAL_STEPS = 50
LOG_STEPS = 10
SAVE_STEPS = 100


# ============ 数据集 ============
class SFTDataset(Dataset):
    """将 instruction-output JSONL 转为 Qwen 对话格式并 tokenize。

    自动对 labels 做 mask：只保留 assistant 回答部分参与 loss 计算，
    用户指令部分被 mask 掉 (设为 -100)。
    """

    def __init__(self, path: str, tokenizer, max_length: int = MAX_LENGTH):
        self.tokenizer = tokenizer
        self.max_length = max_length

        self.response_ids = tokenizer.encode(
            "<|im_start|>assistant", add_special_tokens=False
        )
        self.rlen = len(self.response_ids)

        self.data = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    self.data.append(json.loads(line))
        print(f"  Loaded {len(self.data)} samples from {path}")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        messages = [
            {"role": "user", "content": item["instruction"]},
            {"role": "assistant", "content": item["output"]},
        ]
        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=False
        )

        encoded = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding=False,
        )
        input_ids = encoded["input_ids"]

        # 只对 assistant 回复部分计算 loss，用户指令部分 mask 掉
        labels = [-100] * len(input_ids)
        for i in range(len(input_ids) - self.rlen, -1, -1):
            if input_ids[i:i + self.rlen] == self.response_ids:
                labels[i:] = input_ids[i:]
                break

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

    if not torch.cuda.is_available():
        print("[ERROR] CUDA 不可用！训练需要 GPU。")
        return

    device_name = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f"\n  GPU: {device_name}  ({vram:.1f} GB)")
    use_bf16 = torch.cuda.is_bf16_supported()
    print(f"  BF16 support: {use_bf16}")

    # ---- 1. Tokenizer ----
    print("\n[1/6] 加载 Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

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
    total_steps = len(train_dataset) // (BATCH_SIZE * GRADIENT_ACCUMULATION) * NUM_EPOCHS
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        num_train_epochs=NUM_EPOCHS,
        learning_rate=LEARNING_RATE,
        warmup_steps=int(total_steps * WARMUP_RATIO),
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