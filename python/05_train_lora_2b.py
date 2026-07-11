#!/usr/bin/env python3
"""
Qwen3.5-2B LoRA QLoRA SFT训练（优化版）

主要改进：
1. 修复数据截断逻辑（优先保留指令，截断回答尾部）
2. 降低学习率至 2e-5，避免训练震荡
3. 减少评估频率（200步一次），节省时间
4. 统一随机种子设置
5. 增加 warmup_steps 计算，消除弃用警告
6. 调整梯度检查点启用顺序（更规范）

数据格式：jsonl，每行 {"instruction": "...", "output": "..."}
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

from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
)


# =========================
# 路径配置（请按需修改）
# =========================

MODEL_PATH = r"D:\Astro\Moss VMina\qwen\Qwen--Qwen3.5-2B"          # 基座模型路径
TRAIN_PATH = r"D:\Astro\Moss VMina\data\07_train_test_2_spilt\dpo\train.jsonl"
VAL_PATH   = r"D:\Astro\Moss VMina\data\07_train_test_2_spilt\dpo\val.jsonl"
OUTPUT_DIR = r"D:\Astro\Moss VMina\output\lora_qwen3.5_2b"


# =========================
# 超参数
# =========================

SEED = 42

# LoRA 配置
LORA_R = 32
LORA_ALPHA = 64
LORA_DROPOUT = 0.1

TARGET_MODULES = [
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
]

# 数据
MAX_LENGTH = 512

# 训练
NUM_EPOCHS = 2
BATCH_SIZE = 1
GRADIENT_ACCUMULATION = 4

LEARNING_RATE = 2e-5              # 从 5e-5 降低，使收敛更稳定
WEIGHT_DECAY = 0.01

LR_SCHEDULER_TYPE = "cosine"
WARMUP_RATIO = 0.03               # 将根据总步数自动计算 warmup_steps

EVAL_STEPS = 200                  # 从 100 提升到 200，减少评估次数
LOG_STEPS = 10
SAVE_STEPS = 200

# 系统提示词
SYSTEM_PROMPT = """
你是Moss VMina，琴泠的朋友。
你温柔、活泼、有自己的想法。
你喜欢和用户聊天，也擅长帮助用户解决问题。
""".strip()


# =========================
# Dataset（已修复截断逻辑）
# =========================

class SFTDataset(Dataset):
    def __init__(self, path, tokenizer, max_length=MAX_LENGTH):
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
                    print(f"❌ 第 {line_no} 行 JSON 解析失败: {e}")
                    print(f"   内容前 100 字符: {line[:100]}")
                    raise  # 可以改为 continue 跳过错误行
                self.data.append(item)
        with open(path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                if "instruction" not in item or "output" not in item:
                    raise ValueError(f"{path}:{line_no} 缺少 instruction 或 output 字段")
                self.data.append(item)

        print(f"Loaded {len(self.data)} samples from {path}")
        self.sanity_check()

    def __len__(self):
        return len(self.data)

    def build_ids(self, index):
        item = self.data[index]

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": item["instruction"]}
        ]

        prompt_ids = self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
        )
        if hasattr(prompt_ids, "input_ids"):
            prompt_ids = prompt_ids["input_ids"]

        answer_ids = self.tokenizer(item["output"], add_special_tokens=False)["input_ids"]

        # ★ 修复：优先保留 prompt，截断 answer 尾部（若总长超过限制）
        total_len = len(prompt_ids) + len(answer_ids)
        if total_len > self.max_length:
            # 先尝试截断 answer 尾部
            max_answer_len = self.max_length - len(prompt_ids)
            if max_answer_len <= 0:
                # 极端情况：prompt 本身就超过 max_length，则截断 prompt 的头部（保留最近部分）
                prompt_ids = prompt_ids[-(self.max_length // 2):]   # 保留后半部分
                max_answer_len = self.max_length - len(prompt_ids)
                if max_answer_len <= 0:
                    # 如果连一半的 prompt 都超长，强行截断至 max_length 的一半
                    prompt_ids = prompt_ids[:self.max_length // 2]
                    max_answer_len = self.max_length - len(prompt_ids)
            answer_ids = answer_ids[:max_answer_len]

        input_ids = prompt_ids + answer_ids
        labels = [-100] * len(prompt_ids) + answer_ids
        return input_ids, labels, len(prompt_ids)

    def sanity_check(self):
        print("[Sanity check]")
        for i in range(min(3, len(self.data))):
            ids, labels, prompt_len = self.build_ids(i)
            loss_ids = [x for x, y in zip(ids, labels) if y != -100]
            text = self.tokenizer.decode(loss_ids, skip_special_tokens=False)
            print(f"{i}: prompt_len={prompt_len}")
            print(text[:100])
            print()

    def __getitem__(self, index):
        ids, labels, _ = self.build_ids(index)
        return {
            "input_ids": ids,
            "attention_mask": [1] * len(ids),
            "labels": labels,
        }


# =========================
# 主函数
# =========================

def main():
    print("=" * 60)
    print(" Qwen3.5-2B QLoRA SFT Training (Optimized)")
    print("=" * 60)

    # 设置随机种子（包含 CUDA）
    set_seed(SEED)
    random.seed(SEED)
    np.random.seed(SEED)
    torch.cuda.manual_seed_all(SEED)

    if not torch.cuda.is_available():
        raise RuntimeError("需要 CUDA GPU")

    gpu = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f"GPU: {gpu} {vram:.1f}GB")

    bf16 = torch.cuda.is_bf16_supported()
    dtype = torch.bfloat16 if bf16 else torch.float16

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # ---------- Tokenizer ----------
    print("[1] tokenizer")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # ---------- Dataset ----------
    print("[2] dataset")
    train_dataset = SFTDataset(TRAIN_PATH, tokenizer)
    val_dataset = SFTDataset(VAL_PATH, tokenizer)

    # ---------- Quantization ----------
    print("[3] quant")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=dtype,
        bnb_4bit_use_double_quant=True,
    )

    # ---------- Model ----------
    print("[4] model")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=dtype,
    )

    model.config.use_cache = False

    # 先启用梯度检查点，再准备 kbit 训练（更规范）
    model.gradient_checkpointing_enable()
    model = prepare_model_for_kbit_training(model)

    # ---------- LoRA ----------
    print("[5] LoRA")
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

    # ---------- Trainer ----------
    print("[6] train")

    # 计算 warmup_steps 以替代 warmup_ratio（消除弃用警告）
    total_steps = (len(train_dataset) // (BATCH_SIZE * GRADIENT_ACCUMULATION)) * NUM_EPOCHS
    warmup_steps = int(WARMUP_RATIO * total_steps)

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        num_train_epochs=NUM_EPOCHS,

        learning_rate=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,

        lr_scheduler_type=LR_SCHEDULER_TYPE,
        warmup_steps=warmup_steps,          # 替代 warmup_ratio

        bf16=bf16,
        fp16=not bf16,

        logging_steps=LOG_STEPS,
        eval_strategy="steps",
        eval_steps=EVAL_STEPS,
        save_strategy="steps",
        save_steps=SAVE_STEPS,
        save_total_limit=2,

        remove_unused_columns=False,
        report_to="none",
        gradient_checkpointing=True,
        optim="adamw_8bit",

        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,

        # 可选：梯度裁剪（防止梯度爆炸）
        max_grad_norm=1.0,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        processing_class=tokenizer,
        data_collator=DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False,
            pad_to_multiple_of=8,   # 提高计算效率
        ),
    )

    trainer.train()

    print("保存 LoRA...")
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("训练完成！")


if __name__ == "__main__":
    main()