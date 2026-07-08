import json
import os
import re
import time
from googletrans import Translator

CHUNK_DIR = r"D:\Astro\Moss VMina\data\01_raw\sp"
FILES = [f"train_chunk_{i}.jsonl" for i in range(12)]

# Tokens that should NOT be translated
PRESERVE_TOKENS = {
    "<extra_id_1>", "Assistant", "User", "System", "Human",
}

def preserve_special_tokens(text, translator, src="en", dest="zh-cn"):
    """Translate text while preserving special tokens."""
    # Replace special tokens with placeholders
    placeholders = {}
    pattern = r'(<[^>]+>|\b(?:Assistant|User|System|Human)\b)'

    def replacer(match):
        token = match.group(0)
        ph = f"__TOKEN_{len(placeholders)}__"
        placeholders[ph] = token
        return ph

    protected_text = re.sub(pattern, replacer, text)

    # Translate the protected text
    try:
        translated = translator.translate(protected_text, src=src, dest=dest).text
    except Exception as e:
        print(f"  Translation error: {e}")
        return text

    # Restore placeholders
    for ph, token in placeholders.items():
        translated = translated.replace(ph, token)

    return translated


def process_file(filepath, translator):
    print(f"Processing: {filepath}")
    lines = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(line)

    translated_lines = []
    for i, line in enumerate(lines):
        try:
            obj = json.loads(line)
            # Translate prompt
            if "prompt" in obj and obj["prompt"]:
                obj["prompt"] = preserve_special_tokens(obj["prompt"], translator)
                time.sleep(0.3)  # Rate limit
            # Translate response
            if "response" in obj and obj["response"]:
                obj["response"] = preserve_special_tokens(obj["response"], translator)
                time.sleep(0.3)  # Rate limit
            translated_lines.append(json.dumps(obj, ensure_ascii=False))
        except json.JSONDecodeError as e:
            print(f"  JSON error line {i+1}: {e}")
            translated_lines.append(line)
        except Exception as e:
            print(f"  Error line {i+1}: {e}")
            translated_lines.append(line)

        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(lines)}")

    # Write back
    with open(filepath, "w", encoding="utf-8") as f:
        for line in translated_lines:
            f.write(line + "\n")

    print(f"  Done: {len(lines)} lines translated")
    return len(lines)


def main():
    translator = Translator()
    total = 0
    for fname in FILES:
        fpath = os.path.join(CHUNK_DIR, fname)
        if os.path.exists(fpath):
            total += process_file(fpath, translator)
        else:
            print(f"File not found: {fpath}")
    print(f"\nAll done! Total lines translated: {total}")


if __name__ == "__main__":
    main()