import json
import hashlib

INPUT_PATH = r"D:\Astro\Moss VMina\data\sensitive data\data\processed\train_data.json"
OUTPUT_PATH = r"D:\Astro\Moss VMina\data\sensitive data\data\processed\qq_corpus.jsonl"

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    records = json.load(f)

with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
    for item in records:
        content = item["content"]
        h = hashlib.md5(content.encode("utf-8")).hexdigest()[:6]
        new_id = f"qq_20260703_essay_{h}"
        line = json.dumps({
            "id": new_id,
            "type": "text",
            "source": "essay",
            "text": content
        }, ensure_ascii=False)
        out.write(line + "\n")

print(f"Done. {len(records)} records written to {OUTPUT_PATH}")