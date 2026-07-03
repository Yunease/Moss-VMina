"""
Script 3: 清洗 Markdown 数据
- 删除 YAML front matter
- 删除 markdown 图片引用 (![]() 和参考式图片)
- 删除 HTML 标签及 HTML 转义字符
- 删除空行中的残留图片引用标记
- 清洗后保存至 D:\\Astro\\Moss VMina\\data\\processed\\{key}
"""

import os
import re
import sys
from pathlib import Path


def remove_yaml(text: str) -> str:
    """删除开头的 YAML front matter（--- 包裹的部分）"""
    pattern = r"^---\s*\n.*?\n---\s*\n"
    result = re.sub(pattern, "", text, count=1, flags=re.DOTALL)
    return result


def remove_markdown_images(text: str) -> str:
    """删除 Markdown 图片引用：
       - 标准图片: ![alt](url)
       - 参考式图片: ![alt][ref] 和 ![alt][ref] 定义行 [ref]: url
    """
    # 删除标准图片语法 ![alt](url)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)

    # 删除参考式图片 ![alt][ref]
    text = re.sub(r"!\[.*?\]\[.*?\]", "", text)

    # 删除参考式链接定义的图片行 [ref]: url  （只删明显是图片的引用行）
    text = re.sub(r"^\[.*?\]:\s*\S+\.(png|jpg|jpeg|gif|svg|webp|bmp|ico)(\s+.*)?$", "", text, flags=re.MULTILINE | re.IGNORECASE)

    return text


def remove_html(text: str) -> str:
    """删除 HTML 标签和 HTML 转义字符"""
    # 删除 HTML 标签（包括跨行标签）
    text = re.sub(r"<[^>]*>", "", text)

    # 替换 HTML 转义字符为对应字符或空格
    html_escapes = {
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&#39;": "'",
        "&#x27;": "'",
        "&#x2F;": "/",
        "&#x60;": "`",
        "&#x3D;": "=",
        "&nbsp;": " ",
        "&ensp;": " ",
        "&emsp;": " ",
        "&mdash;": "—",
        "&ndash;": "–",
        "&hellip;": "…",
        "&laquo;": "«",
        "&raquo;": "»",
        "&ldquo;": "“",
        "&rdquo;": "”",
        "&lsquo;": "‘",
        "&rsquo;": "’",
    }
    for escaped, char in html_escapes.items():
        text = text.replace(escaped, char)

    # 捕获剩余的通用 &#数字; 和 &#x十六进制; 直接删除
    text = re.sub(r"&#\d+;", "", text)
    text = re.sub(r"&#x[0-9a-fA-F]+;", "", text)

    return text


def remove_image_ref_lines(text: str) -> str:
    """删除仅包含图片引用标记的残留行"""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # 跳过空行或只有图片引用标记的行
        if not stripped or re.match(r"^\[.*?\]:\s*$", stripped):
            continue
        # 如果去掉图片引用后啥也不剩，也跳过
        without_img_ref = re.sub(r"\[.*?\]", "", stripped).strip()
        if without_img_ref and without_img_ref != stripped:
            # 还有实际内容，保留
            cleaned.append(line)
        elif without_img_ref:
            # 只剩空内容，跳过
            continue
        else:
            cleaned.append(line)

    return "\n".join(cleaned)


def clean_markdown(text: str) -> str:
    """执行所有清洗步骤"""
    text = remove_yaml(text)
    text = remove_markdown_images(text)
    text = remove_html(text)
    # 清理多余空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    return text


def process_directory(input_dir: str, output_key: str = "mine") -> None:
    input_path = Path(input_dir).resolve()
    output_dir = Path(r"D:\Astro\Moss VMina\data\processed") / output_key

    if not input_path.is_dir():
        print(f"错误: 输入目录不存在 - {input_path}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    md_files = sorted(input_path.glob("*.md"))
    if not md_files:
        print("警告: 未找到任何 .md 文件")
        return

    success = 0
    failed = 0

    for md_file in md_files:
        try:
            raw_text = md_file.read_text(encoding="utf-8")
            cleaned = clean_markdown(raw_text)

            # 保留原文件名
            output_path = output_dir / md_file.name
            output_path.write_text(cleaned, encoding="utf-8")
            success += 1
            print(f"  ✓ {md_file.name}")

        except Exception as e:
            print(f"  ✗ {md_file.name} — 处理失败: {e}")
            failed += 1

    print(f"\n完成！成功: {success} 个，失败: {failed} 个")
    print(f"输出目录: {output_dir}")


if __name__ == "__main__":
    # 用法: python 03_clean_markdown.py [输入目录] [key]
    #  - 输入目录: 默认为当前目录
    #  - key: 默认为 "mine"
    input_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    output_key = sys.argv[2] if len(sys.argv) > 2 else "mine"
    process_directory(input_dir, output_key)