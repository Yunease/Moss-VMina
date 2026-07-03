"""
Script 2: 只保留 .md 文件，删除当前目录下所有其他后缀的文件
"""

import os
import sys
from pathlib import Path


def keep_only_md(root_dir: str = ".") -> None:
    root = Path(root_dir).resolve()
    if not root.is_dir():
        print(f"错误: 目录不存在 - {root}")
        sys.exit(1)

    deleted_count = 0
    skipped_dirs = 0

    for entry in root.iterdir():
        if entry.is_dir():
            skipped_dirs += 1
            continue
        if entry.suffix.lower() != ".md":
            entry.unlink()  # 删除文件
            deleted_count += 1
            print(f"  删除: {entry.name}")

    print(f"\n完成！删除 {deleted_count} 个非 md 文件", end="")
    if skipped_dirs:
        print(f"，跳过 {skipped_dirs} 个子目录（如需处理子目录请先运行 01_flatten_files.py）")
    else:
        print()


if __name__ == "__main__":
    # 用法: python 02_keep_only_md.py [目标目录]
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    keep_only_md(target)