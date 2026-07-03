"""
清洗脚本：
1. 去除 YAML frontmatter（文件开头的 --- ... ---）
2. 去除 HTML 标签（保留标签内文本）
3. 去除 markdown 图片引用 ![alt](url)
4. 去除纯空白/占位的 div 行（如 <div>&nbsp</div>）
5. HTML 实体 &nbsp; 转为空格
6. 去除多余的空白行
"""

import os
import re
import shutil

RAW_DIR = r"D:\Astro\Moss VMina\data\raw\mine"
OUT_DIR = r"D:\Astro\Moss VMina\data\processed\mine"


def strip_yaml(text: str) -> str:
    """移除开头的 YAML frontmatter (--- ... ---)"""
    return re.sub(r'^---\s*\n.*?\n---\s*\n', '', text, count=1, flags=re.DOTALL)


def strip_html_tags(text: str) -> str:
    """去除 HTML 标签，保留标签内的文本内容"""
    # 移除 <style>...</style> 及其内容
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    # 移除 HTML 标签（保留内容）
    text = re.sub(r'<[^>]+>', '', text)
    return text


def strip_md_images(text: str) -> str:
    """移除 markdown 图片引用 ![alt](url)"""
    return re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)


def clean_whitespace(text: str) -> str:
    """清理多余的空白"""
    # 将 &nbsp; 转成空格
    text = text.replace('&nbsp;', ' ').replace('&nbsp', ' ')
    # 将连续空行压缩为单个空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 去掉首尾空白
    text = text.strip()
    return text


def process_file(filepath: str) -> str | None:
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    original_text = text

    text = strip_yaml(text)
    text = strip_md_images(text)
    text = strip_html_tags(text)
    text = clean_whitespace(text)

    if not text:
        return None

    return text


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    md_files = [f for f in os.listdir(RAW_DIR) if f.endswith('.md') and f != 'clean_data.py']
    md_files.sort()

    success = 0
    skipped = 0
    failed = 0

    for filename in md_files:
        src_path = os.path.join(RAW_DIR, filename)
        try:
            cleaned = process_file(src_path)
            if cleaned is None or len(cleaned.strip()) == 0:
                print(f"  [跳过] {filename} — 清洗后内容为空")
                skipped += 1
                continue

            out_path = os.path.join(OUT_DIR, filename)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(cleaned)
            success += 1
        except Exception as e:
            print(f"  [失败] {filename}: {e}")
            failed += 1

    print(f"\n完成！成功: {success}, 跳过: {skipped}, 失败: {failed}")


if __name__ == '__main__':
    main()