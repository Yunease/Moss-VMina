import json
import os
from pathlib import Path
from collections import Counter

corpus_file = Path(r"D:\Astro\Moss VMina\data\05_corpus_jsonl\corpus.jsonl")
backup_file = Path(r"D:\Astro\Moss VMina\data\05_corpus_jsonl\corpus.jsonl.bak")

# ID 前缀 → category 映射
PREFIX_MAP = {
    "message": "日常吐槽",
    "poetry": "诗与歌",
    "同人小说": "小说",
    "技术文章": "学习",
    "杂文": "散文",
}

# 先备份（如果已有备份则跳过）
if not backup_file.exists():
    corpus_file.rename(backup_file)
    print(f"已备份原文件 → {backup_file}")
else:
    print(f"备份已存在，跳过备份")

filled = Counter()
skipped = 0
total = 0

with open(backup_file, "r", encoding="utf-8") as fin, \
     open(corpus_file, "w", encoding="utf-8") as fout:
    for line in fin:
        line = line.strip()
        if not line:
            continue
        total += 1
        obj = json.loads(line)
        prefix = obj["id"].split(os.sep)[0]

        # 已有非空 category → 跳过
        if "category" in obj and obj["category"]:
            skipped += 1
            fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
            continue

        # 缺 category 或为空 → 按前缀填充
        if prefix in PREFIX_MAP:
            obj["category"] = PREFIX_MAP[prefix]
            filled[prefix] += 1
        else:
            # 未知前缀，留空待处理
            obj["category"] = ""
            filled["<未知>"] += 1

        fout.write(json.dumps(obj, ensure_ascii=False) + "\n")

print(f"总数: {total}")
print(f"已有 category 跳过: {skipped}")
print("\n=== 本次填充统计 ===")
for p, c in sorted(filled.items(), key=lambda x: -x[1]):
    print(f"  {p}: {c}条")

# 最终 category 分布验证
cat_dist = Counter()
with open(corpus_file, "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        cat_dist[obj.get("category", "")] += 1

print("\n=== 最终 category 分布 ===")
for cat, cnt in sorted(cat_dist.items(), key=lambda x: -x[1]):
    print(f"  '{cat}': {cnt}条")

print(f"\n备份文件: {backup_file}")
print(f"输出文件: {corpus_file}")