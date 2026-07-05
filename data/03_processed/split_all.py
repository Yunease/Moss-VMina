"""
通用语料拆分脚本：对 03_processed 下所有 .txt 文件执行拆分。
规则：
1. 统计字数跳过YAML头
2. <1500字 → 原样复制
3. >=1500字 → 在结束符号（！？。）处截断拆分，输出为 xxx_1.txt, xxx_2.txt ...
4. 超过1800字未遇到结束符号 → 强制截断

特例：同人小说/别玩galgame了 无YAML头 → 自动添加 剧本 类YAML头
"""

import os
import re
import shutil
from pathlib import Path

SOURCE_DIR = Path(r"D:\Astro\Moss VMina\data\03_processed")
OUTPUT_DIR = Path(r"D:\Astro\Moss VMina\data\04_chunk")
MAX_CHARS = 1500
HARD_LIMIT = 1800
SENTENCE_END_PATTERN = re.compile(r'[！？。]')

# 无YAML文件的collection推断映射
COLLECTION_MAP = {
    '别玩galgame了': ('剧本', '剧本', '别玩galgame了'),
}


def parse_yaml_frontmatter(content):
    """解析YAML头，返回 (raw_lines, title, body, has_yaml)"""
    if not content.startswith('---'):
        return None, None, content, False

    second_idx = content.find('---', 3)
    if second_idx == -1:
        return None, None, content, False

    yaml_text = content[3:second_idx].strip()
    body = content[second_idx + 3:]
    raw_lines = yaml_text.split('\n')

    title = None
    for line in raw_lines:
        if line.startswith('title:'):
            title_val = line[6:].strip().strip('"').strip("'")
            if title_val:
                title = title_val
            break

    return raw_lines, title, body, True


def build_yaml_text(raw_lines, new_title):
    """基于原始YAML行，只替换title，保持其他字段原始格式"""
    lines = ['---']
    title_replaced = False
    for line in raw_lines:
        if line.startswith('title:'):
            stripped = line[6:].strip()
            if stripped.startswith('"'):
                lines.append(f'title: "{new_title}"')
            elif stripped.startswith("'"):
                lines.append(f"title: '{new_title}'")
            else:
                lines.append(f'title: {new_title}')
            title_replaced = True
        else:
            lines.append(line)
    if not title_replaced:
        lines.append(f'title: {new_title}')
    lines.append('---')
    return '\n'.join(lines)


def build_default_yaml(title, tags, category, collection):
    """为无YAML文件构建全新的YAML文本"""
    tags_str = '[' + ', '.join(tags) + ']'
    return f"""---
title: {title}
tags: {tags_str}
category: {category}
collection: {collection}
---"""


def split_body(body):
    """将正文按句子边界拆分为段落列表"""
    segments = []
    start = 0
    body_len = len(body)

    while start < body_len:
        search_start = start + MAX_CHARS

        if search_start >= body_len:
            segments.append(body[start:])
            break

        search_end = min(start + HARD_LIMIT, body_len)
        chunk = body[search_start:search_end]

        match = SENTENCE_END_PATTERN.search(chunk)
        if match:
            split_pos = search_start + match.end()
            segments.append(body[start:split_pos])
            start = split_pos
        else:
            split_pos = search_end
            segments.append(body[start:split_pos])
            start = split_pos

    return segments


def get_infer_collection(rel_path):
    """从相对路径推断无YAML文件的collection信息"""
    parts = rel_path.parts
    if len(parts) >= 2:
        dir_name = parts[0]
        if dir_name == '同人小说' and len(parts) >= 3:
            dir_name = parts[1]

        if dir_name in COLLECTION_MAP:
            return COLLECTION_MAP[dir_name]

        # 默认用上级目录名
        return (dir_name, dir_name, dir_name)

    return ('未分类', '未分类', '未分类')


def get_output_path(rel_path, segment_idx, total_segments):
    """计算输出文件路径"""
    stem = rel_path.stem
    suffix = rel_path.suffix

    if segment_idx == 0 and total_segments == 1:
        filename = rel_path.name
    else:
        filename = f"{stem}_{segment_idx + 1}{suffix}"

    return OUTPUT_DIR / rel_path.parent / filename


def get_body_char_count(body):
    return len(body)


def process_file(filepath):
    """处理单个文件，返回状态描述"""
    rel_path = filepath.relative_to(SOURCE_DIR)
    content = filepath.read_text(encoding='utf-8')

    # 1. 解析YAML
    raw_lines, original_title, body, has_yaml = parse_yaml_frontmatter(content)

    # 2. 无YAML文件处理（别玩galgame了等）
    if not has_yaml:
        tags, category, collection = get_infer_collection(rel_path)
        title = rel_path.stem
        raw_lines = None
        original_title = title
        yaml_info = ('default', tags, category, collection)
    else:
        yaml_info = ('raw', raw_lines)

    # 3. 统计正文字数
    body_chars = get_body_char_count(body)

    # 4. 不足阈值直接复制
    if body_chars < MAX_CHARS:
        out_path = OUTPUT_DIR / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(filepath, out_path)
        return f"  复制 ({body_chars}字)"

    # 5. 拆分
    segments = split_body(body)

    # 6. 写出各分段
    for i, segment in enumerate(segments):
        new_title = original_title if len(segments) == 1 else f"{original_title}_{i + 1}"

        if yaml_info[0] == 'raw':
            out_content = build_yaml_text(yaml_info[1], new_title) + '\n' + segment
        else:
            _, tags, category, collection = yaml_info
            out_content = build_default_yaml(new_title, tags, category, collection) + '\n' + segment

        out_path = get_output_path(rel_path, i, len(segments))
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(out_content, encoding='utf-8')

    detail = ' + '.join(f"s{i+1}={len(segments[i])}" for i in range(len(segments)))
    return f"  拆分 {len(segments)}个 ({detail})"


def main():
    txt_files = sorted(SOURCE_DIR.rglob('*.txt'))
    print(f"找到 {len(txt_files)} 个 .txt 文件\n")

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    stats = {'copied': 0, 'split': 0, 'files_in': 0, 'files_out': 0}

    for fp in txt_files:
        rel = fp.relative_to(SOURCE_DIR)
        try:
            result = process_file(fp)
            if '拆分' in result:
                stats['split'] += 1
            else:
                stats['copied'] += 1
            stats['files_in'] += 1
            print(f"{rel}{result}")
        except Exception as e:
            print(f"{rel}  ERROR: {e}")

    # 统计输出文件数
    for root, dirs, files in os.walk(str(OUTPUT_DIR)):
        for f in files:
            if f.endswith('.txt'):
                stats['files_out'] += 1

    print(f"\n{'='*50}")
    print(f"原文件: {stats['files_in']}")
    print(f"未拆分(复制): {stats['copied']}")
    print(f"已拆分: {stats['split']}")
    print(f"输出文件总数: {stats['files_out']}")
    print(f"输出目录: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()