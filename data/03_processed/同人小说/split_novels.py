"""
拆分长篇小说语料文件。
规则：
1. 统计字数跳过YAML头
2. <1500字 → 原样复制
3. >=1500字 → 在结束符号（！？。）处截断拆分，输出为 xxx_1.txt, xxx_2.txt ...
4. 超过1800字未遇到结束符号 → 强制截断
"""

import os
import re
import shutil
from pathlib import Path

CURRENT_DIR = Path(r"D:\Astro\Moss VMina\data\03_processed\同人小说")
OUTPUT_DIR = Path(r"D:\Astro\Moss VMina\data\03_processed\同人小说_split")
MAX_CHARS = 1500
HARD_LIMIT = 1800
SENTENCE_END_PATTERN = re.compile(r'[！？。]')

# 无YAML文件的默认字段（针对"别玩galgame了"）
DEFAULT_YAML = {
    'tags': ['剧本'],
    'category': '剧本',
    'collection': '别玩galgame了',
}


def parse_yaml_frontmatter(content):
    """解析YAML头，返回 (yaml_raw_lines, title, body_text, has_yaml)
    yaml_raw_lines 是原始YAML的每一行（不含---），用于保持原始格式。
    """
    if not content.startswith('---'):
        return None, None, content, False

    second_idx = content.find('---', 3)
    if second_idx == -1:
        return None, None, content, False

    yaml_text = content[3:second_idx].strip()
    body = content[second_idx + 3:]

    # 逐行保存原始YAML，同时提取title
    raw_lines = yaml_text.split('\n')
    title = None
    for line in raw_lines:
        if line.startswith('title:'):
            # 支持 title: xxx 和 title: "xxx" 两种格式
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
            # 判断原格式是否带引号
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
        # 万一没有title字段，追加一个
        lines.append(f'title: {new_title}')

    lines.append('---')
    return '\n'.join(lines)


def build_default_yaml_text(title, tags, category, collection):
    """为无YAML文件构建YAML文本"""
    tags_str = '[' + ', '.join(tags) + ']'
    return f"""---
title: {title}
tags: {tags_str}
category: {category}
collection: {collection}
---"""


def count_body_chars(body):
    """统计正文字数"""
    return len(body)


def split_body(body):
    """将正文按句子边界拆分为段落列表"""
    segments = []
    start = 0
    body_len = len(body)

    while start < body_len:
        # 从 start + MAX_CHARS 开始寻找第一个句子结束符
        search_start = start + MAX_CHARS

        if search_start >= body_len:
            # 剩余部分不足 MAX_CHARS，直接作为最后一段
            segments.append(body[start:])
            break

        # 在 [search_start, start + HARD_LIMIT] 范围内查找结束符
        search_end = min(start + HARD_LIMIT, body_len)
        chunk_to_search = body[search_start:search_end]

        match = SENTENCE_END_PATTERN.search(chunk_to_search)
        if match:
            # 在结束符处截断（包含结束符）
            split_pos = search_start + match.end()
            segments.append(body[start:split_pos])
            start = split_pos
        else:
            # 未找到结束符，强制截断
            split_pos = search_end
            segments.append(body[start:split_pos])
            start = split_pos

    return segments


def get_output_path(rel_path, segment_idx, total_segments):
    """计算输出文件路径"""
    stem = rel_path.stem  # 不含扩展名的文件名
    suffix = rel_path.suffix  # .txt

    if segment_idx == 0 and total_segments == 1:
        # 无需拆分，保持原名
        filename = rel_path.name
    else:
        # 拆分文件，加 _1, _2 后缀
        filename = f"{stem}_{segment_idx + 1}{suffix}"

    return OUTPUT_DIR / rel_path.parent / filename


def process_file(filepath):
    """处理单个文件，返回处理状态"""
    rel_path = filepath.relative_to(CURRENT_DIR)
    content = filepath.read_text(encoding='utf-8')

    # 1. 解析YAML
    raw_lines, original_title, body, has_yaml = parse_yaml_frontmatter(content)

    # 2. 为无YAML文件创建默认YAML（别玩galgame了）
    if not has_yaml:
        title = rel_path.stem
        parts = rel_path.parts
        if len(parts) >= 2:
            collection = parts[0]
        else:
            collection = '同人小说'

        raw_lines = None
        original_title = title
        # 暂存默认YAML字段，用于后续构建
        default_tags = ['剧本']
        default_category = '剧本'
        default_collection = collection

    # 3. 统计正文字数
    body_chars = count_body_chars(body)

    # 4. 如果正文 < 1500字，直接复制
    if body_chars < MAX_CHARS:
        out_path = OUTPUT_DIR / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(filepath, out_path)
        return f" 复制 (共{body_chars}字，未达拆分阈值)"

    # 5. 拆分正文
    segments = split_body(body)

    # 6. 写出各分段
    for i, segment in enumerate(segments):
        new_title = original_title if len(segments) == 1 else f"{original_title}_{i + 1}"

        if has_yaml:
            out_content = build_yaml_text(raw_lines, new_title) + '\n' + segment
        else:
            out_content = build_default_yaml_text(new_title, default_tags, default_category, default_collection) + '\n' + segment
            if len(segments) == 1:
                out_content = segment

        out_path = get_output_path(rel_path, i, len(segments))
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(out_content, encoding='utf-8')

    total_out = len(segments)
    details = ' + '.join([f"seg{_+1}={len(segments[_])}字" for _ in range(len(segments))])
    return f" 拆分为 {total_out} 个文件 ({details})"


def main():
    # 收集所有txt文件
    txt_files = sorted(CURRENT_DIR.rglob('*.txt'))
    print(f"找到 {len(txt_files)} 个 txt 文件\n")

    # 清空并重建输出目录
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    summary = {'copied': 0, 'split': 0, 'total_original': 0, 'total_output': 0}

    for filepath in txt_files:
        rel_path = filepath.relative_to(CURRENT_DIR)
        try:
            result = process_file(filepath)
            if result.startswith(' 复制'):
                summary['copied'] += 1
                summary['total_original'] += 1
                summary['total_output'] += 1
            else:
                summary['split'] += 1
                summary['total_original'] += 1
                # 计算输出文件数
                out_parent = OUTPUT_DIR / rel_path.parent
                stem = rel_path.stem
                out_files = list(out_parent.glob(f"{stem}*.txt"))
                summary['total_output'] += len(out_files)

            print(f"{rel_path}{result}")
        except Exception as e:
            print(f"{rel_path}  ERROR: {e}")

    print(f"\n=== 完成 ===")
    print(f"原文件总数: {summary['total_original']}")
    print(f"未拆分(直接复制): {summary['copied']}")
    print(f"已拆分: {summary['split']}")
    print(f"输出文件总数: {summary['total_output']}")
    print(f"输出目录: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()