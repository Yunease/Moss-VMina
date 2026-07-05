import json
import sys
from pathlib import Path

corpus_file = Path(r"D:\Astro\Moss VMina\data\05_corpus_jsonl\corpus.jsonl")
output_file = Path(r"D:\Astro\Moss VMina\data\05_corpus_jsonl\ids_without_category.txt")

ids = []
total = 0

with open(corpus_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        total += 1
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}", file=sys.stderr)
            continue

        if "category" not in obj:
            ids.append(obj["id"])

with open(output_file, "w", encoding="utf-8") as f:
    for id_ in ids:
        f.write(id_ + "\n")

print(f"Total entries: {total}")
print(f"Entries without 'category' field: {len(ids)}")
print(f"IDs written to: {output_file}")