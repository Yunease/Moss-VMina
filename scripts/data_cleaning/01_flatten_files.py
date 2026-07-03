"""
Script 1: 展平文件 — 遍历当前目录下所有子代/后代文件夹，将所有文件移至当前目录
处理文件名冲突：同名文件自动添加数字后缀
"""

import os
import shutil
import sys
from pathlib import Path


def flatten_files(root_dir: str = ".") -> None:
    root = Path(root_dir).resolve()
    if not root.is_dir():
        print(f"错误: 目录不存在 - {root}")
        sys.exit(1)

    moved_count = 0
    conflict_count = 0

    # walk 会递归遍历所有子目录
    for dirpath, dirnames, filenames in os.walk(root):
        current_dir = Path(dirpath).resolve()

        # 跳过根目录本身
        if current_dir == root:
            continue

        for filename in filenames:
            src = current_dir / filename
            dst = root / filename

            # 如果目标已存在，添加数字后缀避免覆盖
            if dst.exists():
                stem = dst.stem          # 文件名（不含后缀）
                suffix = dst.suffix      # 后缀（如 .md）
                counter = 1
                while True:
                    new_name = f"{stem}_{counter}{suffix}"
                    candidate = root / new_name
                    if not candidate.exists():
                        dst = candidate
                        break
                    counter += 1
                conflict_count += 1

            shutil.move(str(src), str(dst))
            moved_count += 1
            print(f"  移动: {src.name} -> {dst.name}")

        # 尝试删除空目录（如果调用了 rmdir，目录非空会静默失败）
        try:
            current_dir.rmdir()
        except OSError:
            pass

    print(f"\n完成！共移动 {moved_count} 个文件", end="")
    if conflict_count:
        print(f"（其中 {conflict_count} 个存在重名，已自动重命名）")
    else:
        print()


if __name__ == "__main__":
    # 用法: python 01_flatten_files.py [目标目录]
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    flatten_files(target)