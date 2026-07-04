import os

def merge_all_md_recursive():
    current_dir = os.getcwd()
    output_file = "all_combined.md"
    all_content = []

    # 遍历所有子文件夹
    for root, dirs, files in os.walk(current_dir):
        for file in files:
            # 只处理 md，跳过输出文件本身
            if file.lower().endswith(".md") and file != output_file:
                md_path = os.path.join(root, file)
                print(f"合并：{md_path}")

                try:
                    with open(md_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception as e:
                    print(f"读取失败：{md_path}，错误：{e}")
                    continue

                # 加上文件路径作为标题
                rel_path = os.path.relpath(md_path, current_dir)
                all_content.append(f"\n# ====== {rel_path} ======\n")
                all_content.append(content)
                all_content.append("\n\n")

    # 写入合并结果
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("".join(all_content))

    print(f"\n✅ 合并完成！文件保存在：{os.path.abspath(output_file)}")

if __name__ == "__main__":
    merge_all_md_recursive()