#!/usr/bin/env python3
"""
加载训练好的 LoRA adapter 并与模型对话。

Usage:
    python python/chat_lora.py
"""

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TextStreamer,
)
from peft import PeftModel


# ============ 路径配置 ============

BASE_MODEL_PATH = r"D:\Astro\Moss VMina\qwen\Qwen--Qwen3.5-2B"
# LORA_ADAPTER_PATH = r"D:\Astro\Moss VMina\output\lora_test"
LORA_ADAPTER_PATH = r"D:\Astro\Moss VMina\output\lora_qwen3.5_2b"


def main():

    print("=" * 55)
    print("  Qwen3.5-0.8B + LoRA — 对话")
    print("=" * 55)


    # ============ GPU ============
    if not torch.cuda.is_available():

        print("[WARN] CUDA 不可用，使用 CPU")
        device = "cpu"
        bnb_config = None

    else:

        device = "cuda"

        name = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory / 1024**3

        print(
            f"\n GPU: {name} ({vram:.1f} GB)"
        )


        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )


    # ============ tokenizer ============

    print("\n[1/3] 加载 Tokenizer...")


    # 优先使用 LoRA 保存的 tokenizer
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            LORA_ADAPTER_PATH,
            trust_remote_code=True
        )

        print("  使用 LoRA tokenizer")

    except Exception:

        tokenizer = AutoTokenizer.from_pretrained(
            BASE_MODEL_PATH,
            trust_remote_code=True
        )

        print("  使用 base tokenizer")


    # 确保 pad 正确

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token


    print(
        f"  EOS token id: {tokenizer.eos_token_id}"
    )

    print(
        f"  PAD token id: {tokenizer.pad_token_id}"
    )


    # ============ model ============

    print("\n[2/3] 加载基座模型...")


    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_PATH,
        quantization_config=bnb_config,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True,
        torch_dtype=(
            torch.bfloat16
            if device == "cuda"
            else torch.float32
        ),
    )


    print("\n[3/3] 加载 LoRA...")


    model = PeftModel.from_pretrained(
        model,
        LORA_ADAPTER_PATH
    )


    model.eval()


    print("\n模型加载完成\n")


    # ============ chat ============

    print(
        "输入消息开始对话"
    )
    print(
        "输入 /reset 重置历史，/exit退出\n"
    )


    history = []


    while True:


        try:
            user = input("你: ").strip()

        except KeyboardInterrupt:
            print()
            break


        if not user:
            continue


        if user == "/exit":
            break


        if user == "/reset":

            history = []

            print(
                "历史已清空\n"
            )

            continue



        history.append(
            {
                "role": "user",
                "content": user
            }
        )


        messages = [
            {
                "role": "system",
                "content":
                """
                你是Moss VMina，琴泠的好朋友。
                你拥有独立人格和表达习惯。
                """
            }
        ] + history



        # Qwen3.5关闭thinking

        try:

            text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )

        except TypeError:

            # 老版本 transformers 不支持
            text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )


        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=4096,
        )


        if device == "cuda":

            inputs = {
                k:v.cuda()
                for k,v in inputs.items()
            }



        print(
            "模型: ",
            end="",
            flush=True
        )


        streamer = TextStreamer(
            tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
        )


        with torch.no_grad():

            outputs = model.generate(

                **inputs,

                max_new_tokens=256,

                temperature=0.7,

                top_p=0.9,

                top_k=50,

                repetition_penalty=1.1,

                do_sample=True,

                streamer=streamer,


                # 关键修复
                eos_token_id=tokenizer.eos_token_id,

                pad_token_id=tokenizer.pad_token_id,
            )



        response = tokenizer.decode(

            outputs[0][
                inputs["input_ids"].shape[1]:
            ],

            skip_special_tokens=True

        ).strip()



        history.append(
            {
                "role":"assistant",
                "content":response
            }
        )


        print("\n")



if __name__ == "__main__":
    main()