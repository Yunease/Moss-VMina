#!/usr/bin/env python3
"""
Qwen3.5-2B QLoRA SFT Training (Fixed)

修复:
1. 修复 Dataset 重复加载 bug
2. 正确使用 Qwen chat template，保留 assistant 结束标记
3. 修复 SFT labels mask
4. 使用自定义 collator，避免 DataCollatorForLanguageModeling 覆盖 labels
5. 保留原有 QLoRA 配置
"""

import json
import random
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    set_seed,
)

from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
)


MODEL_PATH = r"D:\Astro\Moss VMina\qwen\Qwen--Qwen3.5-2B"
TRAIN_PATH = r"D:\Astro\Moss VMina\data\07_train_test_2_spilt\dpo\train.jsonl"
VAL_PATH = r"D:\Astro\Moss VMina\data\07_train_test_2_spilt\dpo\val.jsonl"
OUTPUT_DIR = r"D:\Astro\Moss VMina\output\lora_qwen3.5_2b_fixed"


SEED = 42

MAX_LENGTH = 512

NUM_EPOCHS = 2
BATCH_SIZE = 1
GRADIENT_ACCUMULATION = 4

LEARNING_RATE = 2e-5
WEIGHT_DECAY = 0.01

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


SYSTEM_PROMPT = """
你是Moss VMina。
你拥有独立人格和表达习惯。
你会认真回答用户问题。
你的表达自然、有温度，但避免刻意卖萌。
""".strip()


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

                item = json.loads(line)

                if "instruction" not in item or "output" not in item:
                    raise ValueError(
                        f"{path}:{line_no} 缺少 instruction/output"
                    )

                self.data.append(item)

        print(f"Loaded {len(self.data)} samples from {path}")

    def __len__(self):
        return len(self.data)

    def build_ids(self, index):
        item = self.data[index]

        prompt_messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": item["instruction"]
            }
        ]

        answer_messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": item["instruction"]
            },
            {
                "role": "assistant",
                "content": item["output"]
            }
        ]

        prompt_ids = self.tokenizer.apply_chat_template(
            prompt_messages,
            tokenize=True,
            add_generation_prompt=True,
        )

        full_ids = self.tokenizer.apply_chat_template(
            answer_messages,
            tokenize=True,
            add_generation_prompt=False,
        )

        answer_len = len(full_ids) - len(prompt_ids)

        if len(full_ids) > self.max_length:
            full_ids = full_ids[:self.max_length]
            answer_len = max(0, len(full_ids) - len(prompt_ids))

        labels = (
            [-100] * (len(full_ids) - answer_len)
            + full_ids[-answer_len:] if answer_len > 0
            else [-100] * len(full_ids)
        )

        return full_ids, labels

    def __getitem__(self, index):
        ids, labels = self.build_ids(index)

        return {
            "input_ids": ids,
            "attention_mask": [1] * len(ids),
            "labels": labels,
        }


def collate_fn(features):
    max_len = max(len(x["input_ids"]) for x in features)

    input_ids = []
    attention_mask = []
    labels = []

    pad_id = features[0]["input_ids"][0]

    for x in features:
        pad_len = max_len - len(x["input_ids"])

        input_ids.append(
            x["input_ids"] + [pad_id] * pad_len
        )

        attention_mask.append(
            x["attention_mask"] + [0] * pad_len
        )

        labels.append(
            x["labels"] + [-100] * pad_len
        )

    return {
        "input_ids": torch.tensor(input_ids, dtype=torch.long),
        "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
        "labels": torch.tensor(labels, dtype=torch.long),
    }


def main():

    set_seed(SEED)
    random.seed(SEED)
    np.random.seed(SEED)

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_PATH,
        trust_remote_code=True
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("EOS:", tokenizer.eos_token, tokenizer.eos_token_id)
    print("PAD:", tokenizer.pad_token, tokenizer.pad_token_id)

    train_dataset = SFTDataset(
        TRAIN_PATH,
        tokenizer
    )

    val_dataset = SFTDataset(
        VAL_PATH,
        tokenizer
    )

    bf16 = torch.cuda.is_bf16_supported()
    dtype = torch.bfloat16 if bf16 else torch.float16

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=dtype,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=dtype,
    )

    model.config.use_cache = False

    model.gradient_checkpointing_enable()
    model = prepare_model_for_kbit_training(model)

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

    total_steps = (
        len(train_dataset)
        // (BATCH_SIZE * GRADIENT_ACCUMULATION)
        * NUM_EPOCHS
    )

    args = TrainingArguments(
        output_dir=OUTPUT_DIR,

        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=1,

        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        num_train_epochs=NUM_EPOCHS,

        learning_rate=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,

        warmup_steps=max(1, int(total_steps * 0.03)),
        lr_scheduler_type="cosine",

        bf16=bf16,
        fp16=not bf16,

        logging_steps=10,

        eval_strategy="steps",
        eval_steps=200,

        save_strategy="steps",
        save_steps=200,
        save_total_limit=2,

        remove_unused_columns=False,

        report_to="none",

        gradient_checkpointing=True,
        optim="adamw_8bit",

        max_grad_norm=1.0,

        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
    )


    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=collate_fn,
    )

    trainer.train()

    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)


if __name__ == "__main__":
    main()
