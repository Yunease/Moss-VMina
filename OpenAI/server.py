"""
server.py
OpenAI-compatible FastAPI server.

依赖已有模块（按实际接口对接）：
    - config.py      : 配置
    - model.py       : load_model() -> None（内部 global 持有 _model / _tokenizer，无返回值）
    - inference.py   : generate(messages, temperature, top_p, max_tokens, repetition_penalty, stop)
                        -> (answer: str, prompt_tokens: int, completion_tokens: int)
                        不支持 stream。
    - schemas.py     : ChatCompletionRequest, ChatCompletionResponse

支持：
    GET  /
    GET  /health
    GET  /v1/models
    POST /v1/chat/completions   （不支持 stream，收到 stream=True 会返回 400）

可直接被 AstrBot 等 OpenAI 兼容客户端调用（base_url 指向本服务 + /v1）。
"""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import config
from model import load_model
from inference import generate
from schemas import ChatCompletionRequest, ChatCompletionResponse


# --------------------------------------------------------------------------- #
# 日志配置
# --------------------------------------------------------------------------- #
logging.basicConfig(
    level=getattr(config, "LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("server")


# --------------------------------------------------------------------------- #
# 一些从 config.py 里尽量兼容取值的配置项（config.py 没有的字段就用默认值）
# --------------------------------------------------------------------------- #
MODEL_NAME: str = getattr(config, "MODEL_NAME", "local-model")
HOST: str = getattr(config, "HOST", "0.0.0.0")
PORT: int = getattr(config, "PORT", 8000)
API_KEY: Optional[str] = getattr(config, "API_KEY", None)  # 若配置了则需要 Bearer 校验
SERVICE_NAME: str = getattr(config, "SERVICE_NAME", "openai-compatible-server")

# generate() 的默认可选参数（req 中没有这些字段时使用）
DEFAULT_REPETITION_PENALTY: float = getattr(config, "REPETITION_PENALTY", 1.1)
DEFAULT_STOP = getattr(config, "STOP", None)


# --------------------------------------------------------------------------- #
# 启动时加载模型。load_model() 无返回值，内部通过 global 持有权重，
# 这里只需要调用一次并记录是否加载成功即可。
# --------------------------------------------------------------------------- #
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("正在加载模型：%s ...", MODEL_NAME)
    try:
        load_model()
        app.state.model_ready = True
        logger.info("模型加载完成。")
    except Exception:
        app.state.model_ready = False
        logger.exception("模型加载失败！服务将以不可用状态启动。")
    yield
    logger.info("服务正在关闭。")


app = FastAPI(
    title=SERVICE_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

# 允许跨域，方便本地/内网工具（如 AstrBot、WebUI）调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# 工具函数
# --------------------------------------------------------------------------- #
def openai_error(message: str, err_type: str = "invalid_request_error",
                  code: Optional[str] = None, status_code: int = 400) -> JSONResponse:
    """构造与 OpenAI 一致的错误响应体。"""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "message": message,
                "type": err_type,
                "param": None,
                "code": code,
            }
        },
    )


def check_api_key(authorization: Optional[str]) -> None:
    """若 config 中设置了 API_KEY，则校验请求头 Authorization: Bearer <key>。"""
    if not API_KEY:
        return  # 未配置 API_KEY 则不校验，方便本地调试
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    if token != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


def make_chat_completion_id() -> str:
    return f"chatcmpl-{uuid.uuid4().hex}"


# --------------------------------------------------------------------------- #
# 路由
# --------------------------------------------------------------------------- #
@app.get("/")
async def root():
    return {
        "service": SERVICE_NAME,
        "status": "ok",
        "model": MODEL_NAME,
        "docs": "/docs",
        "openai_compatible_endpoint": "/v1/chat/completions",
    }


@app.get("/health")
async def health(request: Request):
    ready = getattr(request.app.state, "model_ready", False)
    if not ready:
        return JSONResponse(status_code=503, content={"status": "unavailable", "model_ready": False})
    return {"status": "ok", "model_ready": True, "model": MODEL_NAME}


@app.get("/v1/models")
async def list_models():
    now = int(time.time())
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_NAME,
                "object": "model",
                "created": now,
                "owned_by": "local",
            }
        ],
    }


@app.post("/v1/chat/completions")
async def chat_completions(
    req: ChatCompletionRequest,
    request: Request,
    authorization: Optional[str] = Header(default=None),
):
    check_api_key(authorization)

    if not getattr(request.app.state, "model_ready", False):
        return openai_error("Model is not ready.", err_type="server_error", status_code=503)

    if not req.messages:
        return openai_error("`messages` field is required and cannot be empty.")

    # 当前 inference.py 不支持流式，显式拒绝，避免客户端以为在流式却拿不到分片
    if getattr(req, "stream", False):
        return openai_error(
            "Streaming is not supported by this server yet. Please call with stream=false.",
            err_type="invalid_request_error",
            status_code=400,
        )

    request_id = make_chat_completion_id()
    model_name = req.model or MODEL_NAME

    logger.info("收到 chat completion 请求 id=%s model=%s messages=%d",
                request_id, model_name, len(req.messages))

    # 可选参数，req 上没有的字段就用默认值，不强行假设 schemas.py 一定包含它们
    repetition_penalty = getattr(req, "repetition_penalty", None)
    if repetition_penalty is None:
        repetition_penalty = DEFAULT_REPETITION_PENALTY
    stop = getattr(req, "stop", None)
    if stop is None:
        stop = DEFAULT_STOP

    try:
        # messages 直接原样传给 inference.py，保持 ChatMessage 对象，
        # 不在 server.py 里转换成 dict（转换逻辑由 inference.py 自己的
        # build_prompt 负责，与其 apply_chat_template 的期望保持一致）。
        answer, prompt_tokens, completion_tokens = generate(
            messages=req.messages,
            temperature=req.temperature if req.temperature is not None else 0.7,
            top_p=req.top_p if req.top_p is not None else 1.0,
            max_tokens=req.max_tokens if req.max_tokens is not None else 512,
            repetition_penalty=repetition_penalty,
            stop=stop,
        )
    except Exception as e:
        logger.exception("生成过程中发生异常 request_id=%s", request_id)
        return openai_error(f"Inference failed: {e}", err_type="server_error", status_code=500)

    response_payload = {
        "id": request_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model_name,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": answer},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }

    # 直接返回构造好的 dict，交给 FastAPI 序列化即可，
    # 不再借 ChatCompletionResponse(**payload) 做二次校验，避免字段不一致导致的隐性报错。
    return response_payload


# --------------------------------------------------------------------------- #
# 全局异常处理
# --------------------------------------------------------------------------- #
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return openai_error(str(exc.detail), err_type="invalid_request_error", status_code=exc.status_code)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("未处理的异常：%s", exc)
    return openai_error("Internal server error.", err_type="server_error", status_code=500)


# --------------------------------------------------------------------------- #
# 本地直接运行
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host=HOST, port=PORT, reload=False)