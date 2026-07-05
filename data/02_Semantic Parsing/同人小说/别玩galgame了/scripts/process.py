#!/usr/bin/env python3
"""
剧本处理工具：清除结构性文本 + 场景/分支切分
用于小模型训练微调数据准备

处理规则：
1. 删除结构性文本（get_input, <#>, ;注释, jump, menu, if/else, %%等）
2. 在 @场景切换 和 menu:分支 处切分文件
3. 游戏玩法标记（playerPrint/characterPrint/outPrint）映射为对应角色名
4. if/else 分支标记删除但内容保留（线性展平）
"""

import os
import re

INPUT_DIR = r"D:\Astro\Moss VMina\data\02_Semantic Parsing\同人小说\别玩galgame了"
OUTPUT_DIR = os.path.join(INPUT_DIR, "splits")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FILES = ["序章.md", "day2.md", "day3.md", "day4.md", "day5.md"]


def is_scene_header(stripped):
    return stripped.startswith('@') and not stripped.startswith('@@')


def is_structural_line(stripped):
    """检查是否是应整行删除的结构性文本"""
    if re.match(r'^<#>', stripped):
        return True
    if re.match(r'^<.*>', stripped):
        return True
    if re.match(r'^[;；]', stripped):
        return True
    if re.match(r'^menu[：:]?\s*$', stripped):
        return True
    if re.match(r'^if\s+.+[：:]?\s*$', stripped):
        return True
    if re.match(r'^else[：:]?\s*$', stripped):
        return True
    if re.match(r'^jump[：: \t]', stripped):
        return True
    if re.match(r'^temp_str\s*=', stripped):
        return True
    if re.match(r'^\|end\|\s*$', stripped):
        return True
    return False


def is_menu_option_line(stripped):
    """判断是否为菜单选项文本（在 menu: 和 jump: 之间的纯文本）"""
    if '：' in stripped or '："' in stripped or '（' in stripped:
        return False
    if stripped.startswith('@') or stripped.startswith('<') or stripped.startswith('#'):
        return False
    if re.match(r'^jump', stripped):
        return False
    if re.match(r'^if\s', stripped):
        return False
    if stripped in ('else',):
        return False
    # 纯文本行，不含对话标记 — 通常是菜单选项
    if re.match(r'^[ \t]*\S', stripped) and len(stripped) < 50:
        return True
    return False


def clean_line_text(line):
    """行内结构性文本清理"""
    # get_input 模式
    line = re.sub(r'`\s*playerName\s*=\s*get_input\(\)\s*`', 'playerName', line, flags=re.IGNORECASE)
    line = re.sub(r'`\s*player_input\s*=\s*get_input\(\)\s*`', '', line, flags=re.IGNORECASE)
    line = re.sub(r'`\s*playerPut\s*=\s*get_input\(\)\s*`', '', line, flags=re.IGNORECASE)
    line = re.sub(r'`\s*get_input\(\)\s*`', '', line, flags=re.IGNORECASE)
    # -temp = N
    line = re.sub(r'\s*-temp\s*=\s*\d+', '', line)
    # playerPrint → playerName
    line = re.sub(r'\bplayerPrint\b', 'playerName', line)
    # characterPrint → 乐乐
    line = re.sub(r'\bcharacterPrint\b', '乐乐', line)
    # outPrint → 删除
    line = re.sub(r'\boutPrint\b', '', line)
    # %% 删除
    line = line.replace('%', '')
    # 拼写纠正
    line = line.replace('playerNAme', 'playerName')
    # 删除 playerPut 变量值行（如 "playerName：playerPut"）
    if re.search(r'[：:]\s*playerPut\s*$', line):
        return ''
    return line


def collapse_blanks(text):
    """合并连续空行，去首尾空行"""
    lines = text.split('\n')
    result = []
    prev_blank = False
    for line in lines:
        if line.strip() == '':
            if not prev_blank:
                result.append('')
            prev_blank = True
        else:
            result.append(line)
            prev_blank = False
    while result and result[0].strip() == '':
        result.pop(0)
    while result and result[-1].strip() == '':
        result.pop()
    return '\n'.join(result)


def process_file(filename):
    filepath = os.path.join(INPUT_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_lines = f.read().split('\n')

    segments = []          # 输出片段列表
    current = []           # 当前片段积累
    in_menu_zone = False   # 是否在 menu: 后的分支区域
    menu_accum = []        # menu 后积累的内容（将被丢弃）

    i = 0
    n = len(raw_lines)

    while i < n:
        raw = raw_lines[i]
        stripped = raw.strip()

        # ---- 空行 ----
        if not stripped:
            current.append('')
            i += 1
            continue

        # ---- 场景切换：分割 ----
        if is_scene_header(stripped):
            if current:
                segments.append('\n'.join(current))
            current = [stripped]
            in_menu_zone = False
            menu_accum = []
            i += 1
            continue

        # ---- menu: 标记：开始分支区域 ----
        if re.match(r'^menu[：:]?\s*$', stripped):
            # 保存当前积累的内容作为一个片段
            if current:
                segments.append('\n'.join(current))
            current = []
            in_menu_zone = True
            menu_accum = []
            i += 1
            continue

        # ---- 在 menu 分支区域 ----
        if in_menu_zone:
            if is_structural_line(stripped):
                # 跳过结构性行（jump: 等）
                i += 1
                continue
            # 菜单选项文本也跳过
            if is_menu_option_line(stripped):
                i += 1
                continue
            # 普通文本行（不太可能在menu区域出现）
            cleaned = clean_line_text(raw)
            if cleaned.strip():
                current.append(cleaned)
            i += 1
            continue

        # ---- 结构性行（删除） ----
        if is_structural_line(stripped):
            i += 1
            continue

        # ---- 普通文本行 ----
        cleaned = clean_line_text(raw)
        if cleaned.strip():
            current.append(cleaned)
        i += 1

    # 最后一段
    if current:
        segments.append('\n'.join(current))

    # 后处理：合并连续空行，过滤过短片段（<5有效行）
    merged = []
    buffer = None  # 用于暂存过短片段

    for seg_text in segments:
        collapsed = collapse_blanks(seg_text)
        lines = collapsed.split('\n')
        non_empty = sum(1 for l in lines if l.strip())

        if non_empty >= 5:
            # 有效片段，如有缓冲则先合并
            if buffer:
                # 将缓冲合并到当前片段
                merged.append(collapse_blanks(buffer + '\n\n' + collapsed))
                buffer = None
            else:
                merged.append(collapsed)
        else:
            # 过短片段，暂存或合并到缓冲
            if buffer:
                buffer = buffer + '\n\n' + collapsed
            else:
                buffer = collapsed

    # 处理尾部缓冲
    if buffer and merged:
        merged[-1] = collapse_blanks(merged[-1] + '\n\n' + buffer)
    elif buffer:
        merged.append(buffer)

    return merged


def main():
    print(f"输入: {INPUT_DIR}")
    print(f"输出: {OUTPUT_DIR}")
    print()

    for filename in FILES:
        filepath = os.path.join(INPUT_DIR, filename)
        if not os.path.exists(filepath):
            print(f"[跳过] {filename}")
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            original_lines = len(f.read().split('\n'))

        segments = process_file(filename)
        base = os.path.splitext(filename)[0]

        print(f"{filename}（原{original_lines}行）:")
        if not segments:
            print("  ⚠ 未生成有效片段")
            continue

        for idx, text in enumerate(segments, 1):
            out_name = f"{base}_{idx}.md" if len(segments) > 1 else filename
            out_path = os.path.join(OUTPUT_DIR, out_name)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(text)
            line_count = len(text.split('\n'))
            print(f"  → {out_name}（{line_count}行）")

        print()


if __name__ == '__main__':
    main()