#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复Markdown文件换行问题：将单个换行(\n)替换为两个换行(\n\n)
适用场景：网页端MD渲染时，通过双换行区分段落/内容块
"""
import os

def fix_md_line_breaks_double_newline(input_md_path, output_md_path):
    """
    核心功能：把MD文件中的单个换行替换为两个换行，实现段落/内容的清晰分隔
    :param input_md_path: 待处理的MD文件路径
    :param output_md_path: 处理后保存的MD文件路径
    """
    # 1. 校验输入文件是否存在
    if not os.path.isfile(input_md_path):
        print(f"❌ 错误：输入文件 {input_md_path} 不存在，请检查路径！")
        return

    # 2. 读取并处理文件内容
    try:
        # 读取原始内容（保留所有换行符）
        with open(input_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 核心逻辑：将单个换行符替换为两个换行符
        # 注：使用replace('\n', '\n\n')会把连续换行也加倍，这里做优化：
        # 先把连续换行临时标记，处理完单换行后恢复，避免多余空行
        # 步骤1：替换连续换行（≥2个）为临时标记
        import re
        content_temp = re.sub(r'\n{2,}', '###MULTI_NEWLINE###', content)
        # 步骤2：把单个换行替换为两个换行
        content_fixed = content_temp.replace('\n', '\n\n')
        # 步骤3：恢复连续换行为原始状态（避免空行过多）
        content_final = content_fixed.replace('###MULTI_NEWLINE###', '\n\n')

        # 3. 写入处理后的文件
        with open(output_md_path, 'w', encoding='utf-8') as f:
            f.write(content_final)

        print(f"✅ 处理成功！")
        print(f"📄 原始文件：{input_md_path}")
        print(f"📄 输出文件：{output_md_path}")
        print(f"🔧 处理规则：单个换行→两个换行 | 原有连续换行保持不变")

    # 异常处理（覆盖常见问题）
    except UnicodeDecodeError:
        print(f"❌ 错误：文件编码非UTF-8，请确认文件格式！")
    except PermissionError:
        print(f"❌ 错误：无文件读写权限，请检查文件是否被占用！")
    except Exception as e:
        print(f"❌ 处理失败！未知错误：{str(e)}")

# ====================== 快速使用入口 ======================
if __name__ == "__main__":
    # --------------------------
    # 【请修改这两个路径！】
    # --------------------------
    INPUT_FILE = "1.md"    # 你的原始MD文件路径（例：C:/Desktop/笔记.md）
    OUTPUT_FILE = "水伊布姐姐.md"  # 处理后保存的路径（例：C:/Desktop/笔记_修复换行.md）
    
    # 执行修复
    fix_md_line_breaks_double_newline(INPUT_FILE, OUTPUT_FILE)