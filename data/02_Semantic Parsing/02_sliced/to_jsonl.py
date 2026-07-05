"""
将 output 目录下所有 .md 文件合并为一个 JSONL 文件。
"""
import os
import json

INPUT_DIR = "D:/Astro/Moss VMina/data/02_Semantic Parsing/02_sliced/output"
OUTPUT_JSONL = "D:/Astro/Moss VMina/data/02_Semantic Parsing/02_sliced/output.jsonl"

def main():
    md_files = []
    for root, dirs, files in os.walk(INPUT_DIR):
        for f in files:
            if f.endswith(".md"):
                md_files.append(os.path.join(root, f))

    md_files.sort()
    print(f"找到 {len(md_files)} 个 .md 文件")

    with open(OUTPUT_JSONL, "w", encoding="utf-8") as out:
        for idx, fpath in enumerate(md_files, 1):
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read().strip()

            record = {
                "id": f"novel_{idx}",
                "type": "text",
                "source": "小说",
                "content": content,
                "category": "小说",
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"已输出: {OUTPUT_JSONL}")


if __name__ == "__main__":
    main()