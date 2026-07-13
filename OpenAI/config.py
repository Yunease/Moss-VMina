"""
config.py

Moss OpenAI Server 配置文件
"""

import torch
from transformers import BitsAndBytesConfig

# ============================================================
# 模型路径
# ============================================================

# HuggingFace 基座模型
BASE_MODEL_PATH = r"D:\Astro\Moss VMina\qwen\Qwen--Qwen3.5-2B"

# LoRA 权重
LORA_MODEL_PATH = r"D:\Astro\Moss VMina\output\lora_qwen3.5_2b"

# ============================================================
# OpenAI Server
# ============================================================

HOST = "0.0.0.0"
PORT = 8000

MODEL_NAME = "moss-vmina"

# API Key（目前不校验）
API_KEY = "sk-local"

# ============================================================
# 推理参数
# ============================================================

DEFAULT_MAX_NEW_TOKENS = 512

DEFAULT_TEMPERATURE = 0.8

DEFAULT_TOP_P = 0.95

DEFAULT_REPETITION_PENALTY = 1.05

DEFAULT_DO_SAMPLE = True

DEFAULT_STOP = None

# ============================================================
# Device
# ============================================================

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

DTYPE = torch.float16 if torch.cuda.is_available() else torch.float32

# ============================================================
# 是否使用4bit量化
# ============================================================

USE_4BIT = True

USE_8BIT = False

if USE_4BIT:

    BNB_CONFIG = BitsAndBytesConfig(

        load_in_4bit=True,

        bnb_4bit_quant_type="nf4",

        bnb_4bit_use_double_quant=True,

        bnb_4bit_compute_dtype=torch.float16,

    )

elif USE_8BIT:

    BNB_CONFIG = BitsAndBytesConfig(

        load_in_8bit=True,

    )

else:

    BNB_CONFIG = None

# ============================================================
# Generate 默认参数
# ============================================================

GENERATION_CONFIG = {

    "temperature": DEFAULT_TEMPERATURE,

    "top_p": DEFAULT_TOP_P,

    "max_new_tokens": DEFAULT_MAX_NEW_TOKENS,

    "do_sample": DEFAULT_DO_SAMPLE,

    "repetition_penalty": DEFAULT_REPETITION_PENALTY,

}

# ============================================================
# Logging
# ============================================================

LOG_LEVEL = "INFO"

# ============================================================
# Chat Template
# ============================================================

ADD_GENERATION_PROMPT = True

# ============================================================
# OpenAI
# ============================================================

OPENAI_OBJECT = "chat.completion"

# ============================================================
# 以后可扩展
# ============================================================

ENABLE_STREAM = False

ENABLE_FUNCTION_CALL = False

ENABLE_VISION = False

ENABLE_TTS = False

ENABLE_RAG = False

ENABLE_MEMORY = False