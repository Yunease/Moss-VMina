"""
inference.py

负责：
- messages -> Chat Template
- generate()
- 返回回答

本版本相较原始代码修复：
1. temperature / top_p 传入时会强制 do_sample=True，否则 HF generate()
   在 do_sample=False（贪心解码）下会静默忽略这两个参数。
2. tokenizer 编码时加上 truncation，避免长对话超出模型最大长度时报错或输出退化。
3. 显式传 pad_token_id（缺失时回退到 eos_token_id），避免多轮/边界场景下的
   padding 警告或异常。
4. stop 截断后，同步重新计算 completion_tokens，避免 usage 统计比实际返回
   文本偏大。
5. messages 为空时提前抛出明确异常，避免传空列表给 apply_chat_template
   产生奇怪的 prompt。
"""

import torch

from model import (
    get_model,
    get_tokenizer,
)

from config import (
    GENERATION_CONFIG,
    ADD_GENERATION_PROMPT,
)


# def build_prompt(messages):
#     """
#     OpenAI messages
#             ↓
#     Qwen Chat Template
#     """
#     if not messages:
#         raise ValueError("messages 不能为空")

#     tokenizer = get_tokenizer()

#     prompt = tokenizer.apply_chat_template(
#         [m.model_dump() for m in messages],
#         tokenize=False,
#         add_generation_prompt=True,
#         enable_thinking=False,
#     )

#     return prompt

def build_prompt(messages):

    if not messages:
        raise ValueError("messages不能为空")

    formatted_messages = []

    for m in messages:
        data = m.model_dump()

        # 兼容 OpenAI content 数组格式
        if isinstance(data.get("content"), list):
            text_parts = []

            for item in data["content"]:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                else:
                    text_parts.append(str(item))

            data["content"] = "".join(text_parts)

        formatted_messages.append(data)


    system_prompt = (
        "你是Moss VMina，琴泠的好朋友。"
        "你拥有独立人格和表达习惯。"
    )


    # 检查是否已有system
    if formatted_messages and formatted_messages[0]["role"] == "system":

        formatted_messages[0]["content"] = (
            system_prompt
            + "\n\n"
            + formatted_messages[0]["content"]
        )

    else:

        formatted_messages.insert(
            0,
            {
                "role": "system",
                "content": system_prompt
            }
        )


    tokenizer = get_tokenizer()

    prompt = tokenizer.apply_chat_template(
        formatted_messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )

    return prompt


def generate(
    messages,
    temperature=None,
    top_p=None,
    max_tokens=None,
    repetition_penalty=None,
    stop=None,
):
    """
    返回：
    answer,
    prompt_tokens,
    completion_tokens
    """

    model = get_model()
    tokenizer = get_tokenizer()

    prompt = build_prompt(messages)

    # 加上 truncation，避免长对话超出模型最大长度时直接报错或输出退化
    max_length = getattr(tokenizer, "model_max_length", None)
    tokenize_kwargs = {"return_tensors": "pt", "truncation": True}
    # 部分 tokenizer 的 model_max_length 是一个巨大的哨兵值（如 1e30），
    # 这种情况下不传 max_length，交给 tokenizer 自行处理，避免报错。
    if max_length and max_length < 1_000_000:
        tokenize_kwargs["max_length"] = max_length

    inputs = tokenizer(prompt, **tokenize_kwargs)

    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    generation_args = GENERATION_CONFIG.copy()

    # temperature / top_p 只有在 do_sample=True 时才会生效，
    # 一旦客户端传了这两个参数，就说明期望采样式生成，强制打开 do_sample。
    if temperature is not None:
        generation_args["temperature"] = temperature
        generation_args["do_sample"] = True

    if top_p is not None:
        generation_args["top_p"] = top_p
        generation_args["do_sample"] = True

    if max_tokens is not None:
        generation_args["max_new_tokens"] = max_tokens

    if repetition_penalty is not None:
        generation_args["repetition_penalty"] = repetition_penalty

    # 显式传 pad_token_id，缺失时回退到 eos_token_id，
    # 避免单条/多条场景下的 padding 警告或异常。
    generation_args.setdefault(
        "pad_token_id",
        tokenizer.pad_token_id
        if tokenizer.pad_token_id is not None
        else tokenizer.eos_token_id,
    )

    with torch.no_grad():

        outputs = model.generate(
            **inputs,
            **generation_args,
        )

    input_length = inputs["input_ids"].shape[1]

    generated = outputs[0][input_length:]

    answer = tokenizer.decode(
        generated,
        skip_special_tokens=True,
    ).strip()

    # OpenAI usage
    prompt_tokens = input_length
    completion_tokens = len(generated)

    # stop处理（简单版本）
    if stop:

        if isinstance(stop, str):
            stop = [stop]

        for s in stop:

            idx = answer.find(s)

            if idx != -1:
                answer = answer[:idx]

        # 文本被 stop 截断后，重新计算真实的 completion_tokens，
        # 避免 usage 里报出的 token 数比实际返回文本偏大。
        completion_tokens = len(
            tokenizer(answer, add_special_tokens=False)["input_ids"]
        )

    return (
        answer,
        prompt_tokens,
        completion_tokens,
    )


if __name__ == "__main__":

    from schemas import ChatMessage

    msgs = [
        ChatMessage(
            role="user",
            content="你好，请介绍一下自己。"
        )
    ]

    answer, pt, ct = generate(msgs)

    print(answer)
    print(pt, ct)