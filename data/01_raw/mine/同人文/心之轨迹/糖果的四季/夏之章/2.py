#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理当前文件夹下所有.md文件：将单个换行(\n)替换为两个换行(\n\n)
输出文件名格式：原文件名(1).md
"""
import os
import re
import glob


def fix_md_line_breaks_double_newline(input_md_path, output_md_path):
    """
    把MD文件中的单个换行替换为两个换行，原有连续换行保持不变
    """
    if not os.path.isfile(input_md_path):
        print(f"❌ 错误：输入文件 {input_md_path} 不存在！")
        return False

    try:
        with open(input_md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 连续换行(≥2)临时标记
        content_temp = re.sub(r'\n{2,}', '###MULTI_NEWLINE###', content)
        # 单换行→双换行
        content_fixed = content_temp.replace('\n', '\n\n')
        # 恢复连续换行
        content_final = content_fixed.replace('###MULTI_NEWLINE###', '\n\n')

        with open(output_md_path, 'w', encoding='utf-8') as f:
            f.write(content_final)

        print(f"✅ {os.path.basename(input_md_path)} → {os.path.basename(output_md_path)}")
        return True

    except UnicodeDecodeError:
        print(f"❌ 错误：{input_md_path} 编码非UTF-8！")
    except PermissionError:
        print(f"❌ 错误：无读写权限，文件可能被占用！")
    except Exception as e:
        print(f"❌ 处理 {input_md_path} 失败：{str(e)}")
    return False


if __name__ == "__main__":
    # 获取当前脚本所在目录下所有.md文件（排除自身）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    md_files = glob.glob(os.path.join(script_dir, "*.md"))

    if not md_files:
        print("⚠️ 当前文件夹未找到.md文件")
    else:
        success = 0
        for md_path in md_files:
            basename = os.path.basename(md_path)
            name, ext = os.path.splitext(basename)
            output_path = os.path.join(script_dir, f"{name}(1){ext}")
            if fix_md_line_breaks_double_newline(md_path, output_path):
                success += 1
        print(f"\n🎉 处理完成！共 {success}/{len(md_files)} 个文件")
