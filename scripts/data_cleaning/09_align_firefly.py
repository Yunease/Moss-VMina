#!/usr/bin/env python3
"""将 firefly-sample 的字段对齐 train.jsonl 格式: input→instruction, target→output"""
import json

INPUT = r"D:\Astro\Moss VMina\data\06_train_test_split\firefly-sample-300.jsonl"
OUTPUT = r"D:\Astro\Moss VMina\data\06_train_test_split\firefly-sample-300-aligned.jsonl"

count = 0
with open(INPUT, "r", encoding="utf-8") as f, \
     open(OUTPUT, "w", encoding="utf-8") as out:
    for line in f:
        d = json.loads(line)
        new_d = {
            "instruction": d["input"],
            "output": d["target"]
        }
        out.write(json.dumps(new_d, ensure_ascii=False) + "\n")
        count += 1

print(f"完成！已转换 {count} 条，保存到: {OUTPUT}")