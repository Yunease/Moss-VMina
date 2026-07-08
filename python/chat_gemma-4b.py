#!/usr/bin/env python3
"""
加载 Gemma-3-4B LoRA checkpoint 并对话测试。

Usage:
    python chat_gemma-4b.py
"""

import torch
from pathlib import Path
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TextStreamer,
)
from peft import PeftModel

# ============ 路径配置 ============
BASE_MODEL_PATH = Path(r"D:\Astro\Moss VMina\gemma\gemma-3-4b")
LORA_ADAPTER_PATH = Path(r"D:\Astro\Moss VMina\output\lora_test_gemma_1\checkpoint-100")


def main():
    print("=" * 55)
    print("  Gemma-3-4B + LoRA — 对话测试")
    print("=" * 55)

    if not torch.cuda.is_available():
        print("[WARN] CUDA 不可用，使用 CPU（极慢）")
        device = "cpu"
        bnb_config = None
    else:
        device = "cuda"
        device_name = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory / 1024 ** 3
        print(f"\n  GPU: {device_name}  ({vram:.1f} GB)")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )

    print("\n[1/3] 加载 Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_PATH, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    # Gemma 原版 tokenizer 没有 chat_template，手动设置
    tokenizer.chat_template = (
        "{{ bos_token }}"
        "{% for message in messages %}"
        "{% if message['role'] == 'user' %}"
        "{{ '<start_of_turn>user\\n' + message['content'] + '<end_of_turn>\\n' }}"
        "{% elif message['role'] == 'assistant' %}"
        "{{ '<start_of_turn>model\\n' + message['content'] + '<end_of_turn>\\n' }}"
        "{% endif %}"
        "{% endfor %}"
        "{% if add_generation_prompt %}{{ '<start_of_turn>model\\n' }}{% endif %}"
    )

    print("[2/3] 加载基座模型...")
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_PATH,
        quantization_config=bnb_config,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True,
        torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
    )

    print("[3/3] 加载 LoRA Adapter...")
    model = PeftModel.from_pretrained(model, LORA_ADAPTER_PATH)
    model.eval()
    print("  Done!\n")

    # ============ 对话循环 ============
    print("输入消息开始对话（输入 /reset 重置历史，/exit 退出）\n")

    history = []
    while True:
        try:
            user = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if user == "/exit":
            break
        if user == "/reset":
            history = []
            print("  已重置对话历史\n")
            continue
        if not user:
            continue

        history.append({"role": "user", "content": user})

        messages = [
            {"role": "system", "content": "你是VMina，你喜欢杀戮。"}
        ] + history

        text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=4096)
        if device == "cuda":
            inputs = {k: v.cuda() for k, v in inputs.items()}

        print("模型: ", end="", flush=True)
        streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=1024,
                temperature=0.7,
                top_p=0.9,
                top_k=50,
                repetition_penalty=1.05,
                do_sample=True,
                streamer=streamer,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
            )

        response = tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
        ).strip()
        history.append({"role": "assistant", "content": response})
        print()


if __name__ == "__main__":
    main()