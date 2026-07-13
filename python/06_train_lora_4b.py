#!/usr/bin/env python3
"""
Qwen3.5-4B QLoRA SFT Training (Fixed v4)
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


MODEL_PATH = r"D:\Astro\Moss VMina\qwen\Qwen--Qwen3.5-4B"
TRAIN_PATH = r"D:\Astro\Moss VMina\data\07_train_test_3_spilt\train.jsonl"
VAL_PATH = r"D:\Astro\Moss VMina\data\07_train_test_3_spilt\val.jsonl"
OUTPUT_DIR = r"D:\Astro\Moss VMina\output\lora_qwen3.5_4b"


SEED = 42

MAX_LENGTH = 512  # 如果加载时打印的 prompt 长度分布显示大量样本接近/超过这个值，调大它

NUM_EPOCHS = 1.5
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
你是Moss VMina，琴泠的好朋友。
你拥有独立人格和表达习惯。
""".strip()

# Qwen 系列 chat template 里 assistant 轮次开始的固定 marker。
# 如果你的 tokenizer 的模板不是 ChatML 格式（<|im_start|>...），改这里。
ASSISTANT_MARKER_TEXT = "<|im_start|>assistant\n"


def find_subsequence(haystack, needle):
    """在 haystack 里找 needle 这段 token id 序列最后一次出现的位置，返回起始 index，找不到返回 None。"""
    if not needle:
        return None
    n, m = len(haystack), len(needle)
    for start in range(n - m, -1, -1):
        if haystack[start:start + m] == needle:
            return start
    return None


class SFTDataset(Dataset):
    def __init__(self, path, tokenizer, max_length=MAX_LENGTH):
        self.tokenizer = tokenizer
        self.max_length = max_length

        assistant_marker_ids = tokenizer.encode(
            ASSISTANT_MARKER_TEXT, add_special_tokens=False
        )

        raw_items = []
        with open(path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                if "instruction" not in item or "output" not in item:
                    raise ValueError(f"{path}:{line_no} 缺少 instruction/output")
                raw_items.append(item)

        self.examples = []
        prompt_lens = []
        n_truncated = 0
        n_dropped_no_marker = 0
        n_dropped_prompt_too_long = 0

        for item in raw_items:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": item["instruction"]},
                {"role": "assistant", "content": item["output"]},
            ]

            full_ids = tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=False,
            )
            if hasattr(full_ids, "input_ids"):
                full_ids = full_ids["input_ids"]
            full_ids = list(full_ids)

            marker_pos = find_subsequence(full_ids, assistant_marker_ids)
            if marker_pos is None:
                n_dropped_no_marker += 1
                continue

            prefix_len = marker_pos + len(assistant_marker_ids)
            prompt_lens.append(prefix_len)

            # 显式判断：prompt 本身就顶到/超过 max_length，截断后不可能留下任何
            # answer token，这条样本没救，直接跳过（而不是让 answer_len 被动
            # clamp 成 0 再悄悄生成全 -100 的 labels）。
            if prefix_len >= self.max_length:
                n_dropped_prompt_too_long += 1
                continue

            if len(full_ids) > self.max_length:
                # 保留完整 prompt，只截短 answer 部分，尽量保留训练信号
                full_ids = full_ids[: self.max_length]
                n_truncated += 1

            answer_len = len(full_ids) - prefix_len
            labels = [-100] * prefix_len + full_ids[prefix_len:]

            self.examples.append(
                {
                    "input_ids": full_ids,
                    "attention_mask": [1] * len(full_ids),
                    "labels": labels,
                }
            )

        print(f"Loaded {len(self.examples)} usable samples from {path} "
              f"(raw={len(raw_items)})")
        print(f"  truncated (answer shortened, prompt kept intact): {n_truncated}")
        print(f"  dropped (no assistant marker found): {n_dropped_no_marker}")
        print(f"  dropped (prompt alone >= max_length={self.max_length}): {n_dropped_prompt_too_long}")

        if prompt_lens:
            arr = np.array(prompt_lens)
            print(f"  prompt length stats: p50={int(np.percentile(arr, 50))} "
                  f"p90={int(np.percentile(arr, 90))} "
                  f"p99={int(np.percentile(arr, 99))} "
                  f"max={int(arr.max())} (MAX_LENGTH={self.max_length})")

        if n_dropped_no_marker > 0:
            print(f"  [警告] 有 {n_dropped_no_marker} 条样本没找到 assistant marker，"
                  f"检查 tokenizer 的 chat_template 是否真的是 ChatML 格式")

        if n_dropped_prompt_too_long > 0:
            print(f"  [警告] 有 {n_dropped_prompt_too_long} 条样本 prompt 本身就 >= "
                  f"{self.max_length} token，被整条丢弃。如果这个数字不小，"
                  f"说明 MAX_LENGTH 对你的数据来说太小，考虑调大（比如 768/1024）")

        if len(self.examples) == 0:
            raise RuntimeError(f"{path} 里没有任何可用样本，全部被过滤掉了，检查数据/MAX_LENGTH")

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, index):
        ex = self.examples[index]
        return {
            "input_ids": list(ex["input_ids"]),
            "attention_mask": list(ex["attention_mask"]),
            "labels": list(ex["labels"]),
        }


def check_for_bad_samples(dataset, name):
    """训练前扫描一遍：确认没有 labels 全为 -100 的"哑"样本混进去。
    正常情况下 SFTDataset 在加载阶段已经过滤掉了这类样本，这里是双重保险。
    """
    bad_indices = []
    for i in range(len(dataset)):
        x = dataset[i]
        if all(t == -100 for t in x["labels"]):
            bad_indices.append(i)

    if bad_indices:
        print(f"[坏样本扫描] {name} 中发现 {len(bad_indices)} 条全 -100 样本: "
              f"{bad_indices[:20]}{'...' if len(bad_indices) > 20 else ''}")
        raise RuntimeError(
            f"{name} 存在 {len(bad_indices)} 条没有监督信号的样本，"
            f"训练/评估时会产生 nan loss，请先检查数据或截断逻辑"
        )
    else:
        print(f"[坏样本扫描] {name}: 未发现异常样本，共检查 {len(dataset)} 条")


def collate_fn(features, pad_id):
    max_len = max(len(x["input_ids"]) for x in features)

    input_ids = []
    attention_mask = []
    labels = []

    for x in features:
        pad_len = max_len - len(x["input_ids"])

        input_ids.append(x["input_ids"] + [pad_id] * pad_len)
        attention_mask.append(x["attention_mask"] + [0] * pad_len)
        labels.append(x["labels"] + [-100] * pad_len)

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

    train_dataset = SFTDataset(TRAIN_PATH, tokenizer)
    val_dataset = SFTDataset(VAL_PATH, tokenizer)

    # 训练前的双重保险检查
    check_for_bad_samples(train_dataset, "train_dataset")
    check_for_bad_samples(val_dataset, "val_dataset")

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
        data_collator=lambda features: collate_fn(
            features,
            tokenizer.pad_token_id
        ),
    )

    trainer.train()

    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)


if __name__ == "__main__":
    main()