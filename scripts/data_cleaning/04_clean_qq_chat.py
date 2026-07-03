import json
import re

# ===== 敏感词配置（请根据实际聊天对象修改） =====
# 以下是在聊天中出现的对方称呼，微调语料中应脱敏处理。
# 如果你们的聊天中对方有其他称呼，请追加到列表中。
FILTER_NAMES = [
    "123", "123",       # QQ昵称/英文名
    "123", "123",          # 中文简称
    "123",               # 昵称/戏称
]

input_path = "friend_u_dDklELKgUB5eywvJafMJkQ_20260703_184341.json"
output_path = "cleaned_chat.json"

with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

messages = data.get("messages", [])
cleaned = []
auto_id = 1
url_pattern = re.compile(r"https?://[^\s\]）)+]+")

for msg in messages:
    content_obj = msg.get("content", {})
    text = content_obj.get("text", "")

    if not text:
        continue

    # 1. 跳过图片、视频、文件、卡片、合并转发等非纯文本消息
    if (
        text.startswith("[图片:")
        or text.startswith("[视频:")
        or text.startswith("[文件:")
        or text.startswith("[卡片消息:")
        or text.startswith("[合并转发:")
    ):
        continue

    # 2. 检查是否有图片资源
    resources = content_obj.get("resources", [])
    if any(r.get("type") == "image" for r in resources):
        continue

    # 3. 去掉回复前缀，只保留 \n 后面的实际回复内容
    if text.startswith("[回复"):
        parts = text.split("\n", 1)
        if len(parts) > 1:
            text = parts[1]
        else:
            continue

    # 4. 再次检查剩余文本是否为图片/视频/文件
    if (
        text.startswith("[图片:")
        or text.startswith("[视频:")
        or text.startswith("[文件:")
    ):
        continue

    # 5. 删除含链接的项
    if url_pattern.search(text):
        continue

    # 6. 删除含代码/路径/命令行的
    if re.search(r"home/|select |FROM |nohover|\.py|npm |git |/bin|/etc|localhost", text):
        continue

    # 7. 删除重复字过多的（同一字符重复5次以上）
    if re.search(r"(.)\1{4,}", text):
        continue
    # 句号占比超过一半
    if text.count("。") > len(text) // 2:
        continue

    # 8. 删除明显的小说/故事创作（超过300字且含换行）
    if len(text) > 300 and "\n" in text:
        continue

    # 9. 删除旧版QQ表情标记
    if "[em]" in text or "[/em]" in text:
        continue

    # 10. 删除以逗号/冒号/分号结尾的不完整句子
    if text.endswith(("，", "、", "：", "；")):
        continue

    # 11. 删除含账号密码等敏感信息的
    if re.search(r"帐号|密码", text):
        continue

    # 12. 删除含对方名字/称呼的（使用 FILTER_NAMES 配置，避免过拟合到特定人名）
    name_pattern = re.compile("|".join(re.escape(n) for n in FILTER_NAMES))
    if name_pattern.search(text):
        continue

    # 13. 只保留字数超过25的
    if len(text) > 25:
        cleaned.append({"id": auto_id, "content": text})
        auto_id += 1

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(cleaned, f, ensure_ascii=False, indent=2)

print(f"原始消息数: {len(messages)}")
print(f"清洗后: {len(cleaned)} 条")
print(f"输出: {output_path}")