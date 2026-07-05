"""
将 data/01_raw 下的 .md 文件按中文标点切片，
每段约 400 字，最长不超过 480 字，
输出到 data/02_sliced/output/ 目录。
"""

import os
import re

INPUT_DIRS = [
    "D:/Astro/Moss VMina/data/01_raw/external",
]
OUTPUT_DIR = "D:/Astro/Moss VMina/data/02_sliced/output"

# 切片参数
TARGET = 400      # 目标字数，达到此值后寻找结束标点
HARD_LIMIT = 480  # 硬限制，超过此值直接截断

# 结束标点 pattern：单个结束符或复合结束符（如 。" 」）
# 注意：…… 是两个字符，需要特殊处理
SENTENCE_END = re.compile(
    r'(?:[。？！…]|\.{3,}|……)[」"”\']?|'
    r'[」"”\'](?=[\s\n\r]|$)'
)

def find_split_pos(text, start, target, hard_limit):
    """
    在 text[start:start+hard_limit] 范围内寻找合适的切分位置。
    返回相对于 text 的绝对位置，或 -1 表示无法切分。
    """
    end = min(start + hard_limit, len(text))
    search_zone = text[start:end]

    # 从 target 位置开始往前找结束标点
    search_start = min(target, len(search_zone))

    # 在 search_zone[:search_start] 中找最后一个结束标点
    for m in reversed(list(SENTENCE_END.finditer(search_zone[:search_start]))):
        pos = m.end()
        # 确保切在至少 target*0.5 位置之后，避免切出太短的段
        if pos >= target * 0.5:
            return start + pos

    # 没找到合适的结束标点，在 target 附近找任意标点
    fallback = re.compile(r'[，、；：\s\n]')
    for m in reversed(list(fallback.finditer(search_zone[:search_start]))):
        pos = m.end()
        if pos >= target * 0.5:
            return start + pos

    # 还找不到，就用硬限制
    return start + hard_limit if end < len(text) else -1


def split_text(text):
    """将文本切片，返回切片列表。"""
    if not text or len(text) <= TARGET:
        return [text] if text else []

    chunks = []
    start = 0

    # 跳过开头的空行
    text = text.strip()

    while start < len(text):
        remaining = len(text) - start

        if remaining <= TARGET:
            chunks.append(text[start:])
            break

        split_at = find_split_pos(text, start, TARGET, HARD_LIMIT)

        if split_at == -1 or split_at >= len(text):
            chunks.append(text[start:])
            break

        chunk = text[start:split_at].strip()
        if chunk:
            chunks.append(chunk)
        start = split_at

    return chunks


def process_files():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total_input = 0
    total_output = 0

    for input_dir in INPUT_DIRS:
        if not os.path.isdir(input_dir):
            print(f"  [跳过] 目录不存在: {input_dir}")
            continue

        for root, dirs, files in os.walk(input_dir):
            for fname in sorted(files):
                if not fname.endswith(".md"):
                    continue

                fpath = os.path.join(root, fname)
                total_input += 1

                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read()

                chunks = split_text(text)

                if len(chunks) <= 1:
                    continue  # 无需切片

                # 构造输出文件名：保留相对路径结构，用 _1, _2 后缀
                rel_path = os.path.relpath(fpath, input_dir)
                base, _ = os.path.splitext(rel_path)

                for i, chunk in enumerate(chunks, 1):
                    # 保持目录结构
                    out_name = f"{base}_{i}.md"
                    out_path = os.path.join(OUTPUT_DIR, out_name)
                    os.makedirs(os.path.dirname(out_path), exist_ok=True)

                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(chunk)

                    total_output += 1

                print(f"  {fname} -> {len(chunks)} 段")

    print(f"\n完成！处理 {total_input} 个文件，输出 {total_output} 个切片文件")
    print(f"输出目录: {OUTPUT_DIR}")


if __name__ == "__main__":
    process_files()