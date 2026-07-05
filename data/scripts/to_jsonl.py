"""
将 04_chunk 的 txt 文件转为中间层 JSONL。
每个文件一条记录，包含 YAML 元数据 + 正文 content。
对切片文件标注 id_chunk，通过交叉比对 03_processed 判断。
"""

import os
import re
import json
from pathlib import Path
from collections import Counter

CHUNK_DIR = Path(r"D:\Astro\Moss VMina\data\04_chunk")
SOURCE_DIR = Path(r"D:\Astro\Moss VMina\data\03_processed")
OUTPUT_DIR = Path(r"D:\Astro\Moss VMina\data\05_corpus_jsonl")
OUTPUT_FILE = OUTPUT_DIR / 'corpus.jsonl'

CHUNK_PATTERN = re.compile(r'^(.*)_(\d+)$')


def parse_yaml(content):
    """从 txt 中解析 YAML 字段和正文"""
    if not content.startswith('---'):
        return {}, content

    second = content.find('---', 3)
    if second == -1:
        return {}, content

    yaml_text = content[3:second].strip()
    body = content[second + 3:].strip()

    yaml_data = {}
    for line in yaml_text.split('\n'):
        line = line.strip()
        if ':' not in line:
            continue
        key, val = line.split(':', 1)
        key = key.strip()
        val = val.strip()

        # 处理 tags: [a, b, c]
        if key == 'tags' and val.startswith('[') and val.endswith(']'):
            val = [t.strip() for t in val[1:-1].split(',') if t.strip()]
        else:
            val = val.strip('"').strip("'")

        yaml_data[key] = val

    return yaml_data, body


def collect_original_stems():
    """收集 03_processed 中所有原始文件的相对路径（去掉 .txt）"""
    stems = set()
    for root, dirs, files in os.walk(SOURCE_DIR):
        for f in files:
            if not f.endswith('.txt'):
                continue
            rel = os.path.relpath(os.path.join(root, f), SOURCE_DIR)
            stems.add(rel[:-4])  # 去掉 .txt
    return stems


def detect_chunk(rel_stem, fname, original_stems):
    """判断文件是否是切片，返回 (id_chunk)"""
    m = CHUNK_PATTERN.match(fname)
    if not m:
        return 0

    base_name = m.group(1)
    chunk_num = int(m.group(2))

    rel_dir = os.path.dirname(rel_stem)
    base_stem = os.path.join(rel_dir, base_name) if rel_dir else base_name

    if base_stem in original_stems:
        return chunk_num
    return 0


def main():
    print("正在收集原始文件列表...")
    original_stems = collect_original_stems()
    print(f"  03_processed 原始文件: {len(original_stems)}")

    records = []
    stats = {'total': 0, 'chunks': 0, 'originals': 0}
    field_stats = Counter()

    print("\n正在转换 04_chunk 数据...")
    for root, dirs, files in os.walk(CHUNK_DIR):
        for f in sorted(files):
            if not f.endswith('.txt'):
                continue

            filepath = os.path.join(root, f)
            rel_path = os.path.relpath(filepath, CHUNK_DIR)
            rel_stem = rel_path[:-4]  # 去掉 .txt
            fname = f[:-4]

            content = open(filepath, encoding='utf-8').read()
            yaml_data, body = parse_yaml(content)

            # 判断切片
            id_chunk = detect_chunk(rel_stem, fname, original_stems)

            record = {
                'id': rel_stem,
                'id_chunk': id_chunk,
                **yaml_data,
                'content': body,
            }
            records.append(record)

            if id_chunk > 0:
                stats['chunks'] += 1
            else:
                stats['originals'] += 1
            stats['total'] += 1

            for k in yaml_data:
                field_stats[k] += 1

    # 写出 JSONL
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    # 统计
    print(f"\n{'='*50}")
    print(f"总记录数:    {stats['total']}")
    print(f"  原始文件:  {stats['originals']}")
    print(f"  切片文件:  {stats['chunks']}")
    print(f"\n字段统计:")
    for k, v in field_stats.most_common():
        print(f"  {k}: {v}/{stats['total']}")
    print(f"\n输出文件: {OUTPUT_FILE} ({OUTPUT_FILE.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == '__main__':
    main()