#!/usr/bin/env python3
"""
Poems → SFT Training Data Generator

Reads poems.jsonl, sends each poem to DeepSeek API to generate an instruction
that makes the poem a natural AI response in a human chat scenario.
Outputs a combined SFT training JSONL file.
"""

import json
import os
import sys
import time
from pathlib import Path

from openai import OpenAI
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Configuration — edit these or set env vars
# ---------------------------------------------------------------------------
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")

POEMS_FILE = Path(__file__).parent.parent / "data" / "04_chunk" / "poems.jsonl"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "04_chunk" / "poems_sft_train.jsonl"
MAX_RPM = 15  # conservative rate limit for DeepSeek

SYSTEM_PROMPT = """你是一名文学编辑，正在帮助训练一个具有文学气质的中文 AI。

我提供一首诗歌，请你反向设计一个真实的人类聊天场景，使这首诗能够自然成为 AI 的回复。

要求：

1. instruction 必须像日常聊天中的用户表达，而不是写作命令。

可以是：
- 分享情绪；
- 提出人生困惑；
- 讨论某个现象；
- 表达某种感受；
- 寻求安慰或思考。

不要使用：
- 请写一首诗；
- 请创作；
- 模仿某某风格。

2. instruction 应该让诗歌作为回答显得自然。

3. 不要直接提及诗中的特殊词语或句子。

4. 目标是训练 AI 在普通对话中展现诗意，而不是只在写作任务中输出文学文本。

输出：

{
"instruction":"用户的话",
"output":"原诗"
}

保持 output 原文不变。"""


def load_poems(path: Path) -> list[dict]:
    poems = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                poems.append(json.loads(line))
    return poems


def call_api(client: OpenAI, poem_text: str) -> dict | None:
    """Call DeepSeek API and return parsed {"instruction": ..., "output": ...} or None."""
    try:
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            temperature=0.8,
            max_tokens=4096,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"诗歌内容：\n{poem_text}"},
            ],
        )
        raw = resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [API Error] {e}", file=sys.stderr)
        return None

    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.splitlines()
        start = next((i + 1 for i, ln in enumerate(lines) if ln.strip().startswith("```")), 0)
        end = next((i for i in range(len(lines) - 1, start - 1, -1) if lines[i].strip().startswith("```")), len(lines))
        raw = "\n".join(lines[start:end]).strip()

    if not raw:
        return None

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        print(f"  [JSON Parse Error] {raw[:200]}", file=sys.stderr)
        return None

    instruction = parsed.get("instruction", "").strip()
    output = parsed.get("output", "").strip()
    if not instruction or not output:
        print(f"  [Missing fields] instruction={bool(instruction)} output={bool(output)}", file=sys.stderr)
        return None

    return {"instruction": instruction, "output": output}


def main():
    if not DEEPSEEK_API_KEY:
        print("Error: DEEPSEEK_API_KEY not set. Set it as an environment variable or edit the script.")
        sys.exit(1)

    if not POEMS_FILE.exists():
        print(f"Error: poems file not found at {POEMS_FILE}")
        sys.exit(1)

    poems = load_poems(POEMS_FILE)
    print(f"Loaded {len(poems)} poems from {POEMS_FILE}")

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

    # Resume support: skip already processed
    existing_ids = set()
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    existing_ids.add(json.loads(line).get("_poem_idx"))
        print(f"Found {len(existing_ids)} already processed entries in {OUTPUT_FILE}")

    results = []
    errors = 0
    last_call = 0.0
    min_interval = 60.0 / MAX_RPM

    for idx, poem in enumerate(tqdm(poems, desc="Generating", unit="poem")):
        if idx in existing_ids:
            continue

        # Rate limiting
        elapsed = time.monotonic() - last_call
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

        result = call_api(client, poem["text"])
        last_call = time.monotonic()

        if result is None:
            errors += 1
            tqdm.write(f"  Failed on poem #{idx}, skipping...")
            continue

        result["_poem_idx"] = idx
        results.append(result)

        # Append immediately to output file
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

    print(f"\nDone. Success: {len(results)}, Errors: {errors}")
    print(f"Output saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()