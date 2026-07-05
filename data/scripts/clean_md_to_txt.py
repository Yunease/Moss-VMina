"""
清洗脚本：递归遍历 02_Semantic Parsing 下的所有 .md 文件，
保留 YAML frontmatter 原样不动（含 --- 分隔符），
仅对正文部分去除 markdown 格式转为纯文本。
输出到 03_processed，保留目录结构。
"""

import os
import re
import sys

import markdown
from bs4 import BeautifulSoup

SRC_DIR = r"D:\Astro\Moss VMina\data\02_Semantic Parsing"
OUT_DIR = r"D:\Astro\Moss VMina\data\03_processed"

MD_EXTENSIONS = ["extra", "tables", "codehilite"]


def md_to_plain(text: str) -> str:
    """将 Markdown 文本转为纯文本。"""
    html = markdown.markdown(text, extensions=MD_EXTENSIONS)
    soup = BeautifulSoup(html, "html.parser")
    plain = soup.get_text()
    plain = re.sub(r"\n{3,}", "\n\n", plain)
    plain = "\n".join(line.strip() for line in plain.split("\n"))
    return plain.strip()


def split_frontmatter(text: str):
    """分离 YAML frontmatter 与正文。

    如果文件以 ---\\n 开头则尝试提取 frontmatter，
    返回 (frontmatter_str, body_str)。
    """
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            front = text[: end + 5]  # 包含结束的 ---\n
            body = text[end + 5 :]
            return front, body
    return None, text


def main():
    converted = 0
    skipped = 0
    for root, _dirs, files in os.walk(SRC_DIR):
        for fname in files:
            if not fname.endswith(".md"):
                continue

            src_path = os.path.join(root, fname)

            try:
                with open(src_path, "r", encoding="utf-8") as f:
                    raw = f.read()
            except Exception as e:
                print(f"[skip] 读取出错: {src_path} — {e}", file=sys.stderr)
                skipped += 1
                continue

            if not raw.strip():
                print(f"[skip] 空文件: {src_path}")
                skipped += 1
                continue

            front, body = split_frontmatter(raw)

            # 只对正文做 md 转换
            cleaned_body = md_to_plain(body) if body.strip() else ""

            if front:
                cleaned = front + cleaned_body
            else:
                cleaned = cleaned_body

            if not cleaned.strip():
                print(f"[skip] 处理后为空: {src_path}")
                skipped += 1
                continue

            rel = os.path.relpath(root, SRC_DIR)
            out_dir = os.path.join(OUT_DIR, rel)
            os.makedirs(out_dir, exist_ok=True)

            out_name = fname.rsplit(".", 1)[0] + ".txt"
            out_path = os.path.join(out_dir, out_name)

            with open(out_path, "w", encoding="utf-8") as f:
                f.write(cleaned)

            converted += 1

    print(f"完成：转换 {converted} 个文件，跳过 {skipped} 个文件。")


if __name__ == "__main__":
    main()