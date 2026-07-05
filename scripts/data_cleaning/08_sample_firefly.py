#!/usr/bin/env python3
"""从 firefly-train-1.1M.jsonl 中随机抽取 300 条保存到新文件。"""
import random
import argparse

INPUT = r"D:\Astro\Moss VMina\data\06_train_test_split\firefly-train-1.1M.jsonl"
OUTPUT = r"D:\Astro\Moss VMina\data\06_train_test_split\firefly-sample-300.jsonl"
N_SAMPLE = 300

def main():
    parser = argparse.ArgumentParser(description="随机采样 JSONL 文件")
    parser.add_argument("--input", default=INPUT)
    parser.add_argument("--output", default=OUTPUT)
    parser.add_argument("--n", type=int, default=N_SAMPLE, help="采样数量")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    args = parser.parse_args()

    random.seed(args.seed)

    # 先扫描总行数
    print("正在扫描文件行数...")
    with open(args.input, "r", encoding="utf-8") as f:
        total_lines = sum(1 for _ in f)
    print(f"总行数: {total_lines}")

    # 随机选 N 个行号
    sample_indices = set(random.sample(range(total_lines), min(args.n, total_lines)))

    # 读取对应行并写出
    print(f"正在抽取 {len(sample_indices)} 条...")
    count = 0
    with open(args.input, "r", encoding="utf-8") as f, \
         open(args.output, "w", encoding="utf-8") as out:
        for i, line in enumerate(f):
            if i in sample_indices:
                out.write(line)
                count += 1

    print(f"完成！已保存 {count} 条到: {args.output}")

if __name__ == "__main__":
    main()