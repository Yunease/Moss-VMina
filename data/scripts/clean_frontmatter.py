"""
二次清洗：遍历 03_processed 下所有 .txt 文件，
在 YAML frontmatter 内：
- 删除 description: 和 image: 字段行
- 将 tag: 修正为 tags:
直接覆盖原文件。
"""

import os
import re
import sys

DATA_DIR = r"D:\Astro\Moss VMina\data\03_processed"


def clean_frontmatter(text: str) -> str:
    """在 YAML frontmatter 区域内执行字段清理。"""
    # 查找 frontmatter 边界
    fm_start = text.find("---\n")
    if fm_start == -1:
        return text

    fm_end = text.find("\n---\n", fm_start + 4)
    if fm_end == -1:
        return text

    front = text[fm_start : fm_end + 5]  # 含结束 ---\n
    body = text[fm_end + 5 :]

    lines = front.split("\n")
    cleaned_lines = []
    for line in lines:
        # 删除 description 和 image 字段
        if re.match(r"^description\s*:", line):
            continue
        if re.match(r"^image\s*:", line):
            continue
        # tag: -> tags:
        if re.match(r"^tag\s*:", line):
            line = "tags:" + line[line.index(":") + 1 :]
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines) + body


def main():
    processed = 0
    for root, _dirs, files in os.walk(DATA_DIR):
        for fname in files:
            if not fname.endswith(".txt"):
                continue

            path = os.path.join(root, fname)

            try:
                with open(path, "r", encoding="utf-8") as f:
                    raw = f.read()
            except Exception as e:
                print(f"[skip] 读取出错: {path} — {e}", file=sys.stderr)
                continue

            cleaned = clean_frontmatter(raw)
            if cleaned == raw:
                continue  # 无变化则跳过写回

            with open(path, "w", encoding="utf-8") as f:
                f.write(cleaned)
            processed += 1

    print(f"完成：修改 {processed} 个文件。")


if __name__ == "__main__":
    main()