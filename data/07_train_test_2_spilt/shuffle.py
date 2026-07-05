import json
import random
import os

base_dir = r"D:\Astro\Moss VMina\data\07_train_test_2_spilt"
random.seed(42)

for name in ["train.jsonl", "val.jsonl"]:
    path = os.path.join(base_dir, name)
    with open(path, encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]

    random.shuffle(lines)

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"{name}: {len(lines)} 条，已打乱")