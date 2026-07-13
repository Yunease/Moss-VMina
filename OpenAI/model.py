"""
model.py

负责加载：
- HuggingFace Base Model
- PEFT LoRA
- Tokenizer

整个程序生命周期内只加载一次
"""

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
)

from peft import PeftModel

from config import (
    BASE_MODEL_PATH,
    LORA_MODEL_PATH,
    BNB_CONFIG,
    DTYPE,
)

import torch

# ============================================================
# 全局变量
# ============================================================

_model = None
_tokenizer = None


# ============================================================
# Load Model
# ============================================================

def load_model():

    global _model
    global _tokenizer

    if _model is not None:
        return

    print("=" * 60)
    print("Loading tokenizer...")
    print("=" * 60)

    _tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL_PATH,
        trust_remote_code=True,
    )

    print("=" * 60)
    print("Loading base model...")
    print("=" * 60)

    model_kwargs = {
        "trust_remote_code": True,
        "device_map": "auto",
    }

    if BNB_CONFIG is not None:

        model_kwargs["quantization_config"] = BNB_CONFIG

    else:

        model_kwargs["torch_dtype"] = DTYPE

    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_PATH,
        **model_kwargs
    )

    print("=" * 60)
    print("Loading LoRA...")
    print("=" * 60)

    _model = PeftModel.from_pretrained(
        base_model,
        LORA_MODEL_PATH,
    )

    _model.eval()

    print("=" * 60)
    print("Model Loaded")
    print("=" * 60)

    try:
        print(f"Model Device: {_model.device}")
    except:
        pass


# ============================================================
# Getter
# ============================================================

def get_model():

    if _model is None:
        load_model()

    return _model


def get_tokenizer():

    if _tokenizer is None:
        load_model()

    return _tokenizer


# ============================================================
# Utils
# ============================================================

def get_device():

    model = get_model()

    try:
        return model.device
    except:
        return torch.device(
            "cuda" if torch.cuda.is_available()
            else "cpu"
        )


def warmup():

    """
    可选预热
    """

    model = get_model()
    tokenizer = get_tokenizer()

    text = "你好"

    inputs = tokenizer(
        text,
        return_tensors="pt"
    )

    try:
        inputs = inputs.to(get_device())
    except:
        pass

    with torch.no_grad():

        _ = model.generate(
            **inputs,
            max_new_tokens=8
        )

    print("Warmup Finished")


# ============================================================
# Debug
# ============================================================

if __name__ == "__main__":

    load_model()

    warmup()

    print("Everything OK")