#!/usr/bin/env python3
"""
过滤训练集中 instruction 超过 max_length 以及 BPE 边界不一致的坏样本。
"""
import json, sys
from pathlib import Path
from transformers import AutoTokenizer

MODEL_PATH = r"D:\Astro\Moss VMina\gemma\gemma-3-4b"
TRAIN_PATH = r"D:\Astro\Moss VMina\data\07_train_test_2_spilt\train.jsonl"
VAL_PATH = r"D:\Astro\Moss VMina\data\07_train_test_2_spilt\val.jsonl"
MAX_LENGTH = 512

# Gemma 默认对话模板（与训练脚本一致）
GEMMA_CHAT_TEMPLATE = (
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

def filter_jsonl(in_path, out_path, tokenizer):
    kept, removed_inst, removed_bpe = 0, 0, 0
    bad_indices = []

    with open(in_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        item = json.loads(line)
        instruction = item["instruction"]

        # 构建 prompt_ids
        user_only = [{"role": "user", "content": instruction}]
        prompt_text = tokenizer.apply_chat_template(
            user_only, tokenize=False, add_generation_prompt=True
        )
        prompt_ids = tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
        prompt_len = len(prompt_ids)

        # 检查1: instruction 本身太长
        if prompt_len >= MAX_LENGTH:
            print(f"  [DROP idx={idx}] instruction 长度 {prompt_len} >= {MAX_LENGTH}, 前50字: {instruction[:50]!r}")
            removed_inst += 1
            bad_indices.append(idx)
            continue

        # 检查2: BPE 边界不一致
        output = item["output"]
        full_conv = user_only + [{"role": "assistant", "content": output}]
        full_text = tokenizer.apply_chat_template(
            full_conv, tokenize=False, add_generation_prompt=False
        )
        full_ids = tokenizer(
            full_text, add_special_tokens=False,
            truncation=True, max_length=MAX_LENGTH,
        )["input_ids"]

        if full_ids[:prompt_len] != prompt_ids:
            print(f"  [DROP idx={idx}] BPE 边界不一致 (prompt_len={prompt_len}), 前50字: {instruction[:50]!r}")
            removed_bpe += 1
            bad_indices.append(idx)
            continue

        kept += 1

    # 重新写入干净样本
    kept_lines = [lines[i] for i in range(len(lines)) if i not in bad_indices]
    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(kept_lines)

    print(f"\n完成: 保留 {kept}, 删除 instruction超长 {removed_inst}, BPE边界问题 {removed_bpe}, 共移除 {len(bad_indices)} 条")
    print(f"输出: {out_path}")
    return bad_indices

def main():
    print("加载 tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    # 确保 chat_template 存在（与训练脚本逻辑一致）
    if tokenizer.chat_template is None:
        tokenizer.chat_template = GEMMA_CHAT_TEMPLATE

    # 处理训练集
    train_path = Path(TRAIN_PATH)
    out_train = train_path.parent / "train_filtered.jsonl"
    print(f"\n=== 过滤训练集: {train_path} ===")
    filter_jsonl(str(train_path), str(out_train), tokenizer)

    # 也检查验证集
    val_path = Path(VAL_PATH)
    out_val = val_path.parent / "val_filtered.jsonl"
    print(f"\n=== 检查验证集: {val_path} ===")
    filter_jsonl(str(val_path), str(out_val), tokenizer)

    print("\n提示: 将 train_filtered.jsonl / val_filtered.jsonl 重命名或修改训练脚本中的 TRAIN_PATH 指向新文件即可使用。")

if __name__ == "__main__":
    main()