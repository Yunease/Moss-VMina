"""
schemas.py

OpenAI Compatible API Schemas
"""

from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field


# ============================================================
# Message
# ============================================================

RoleType = Literal[
    "system",
    "user",
    "assistant",
    "tool"
]


from typing import Union, List
from pydantic import BaseModel


class ContentPart(BaseModel):
    type: str
    text: str


class ChatMessage(BaseModel):
    role: str

    content: Union[
        str,
        List[ContentPart]
    ]


# ============================================================
# Chat Request
# ============================================================

class ChatCompletionRequest(BaseModel):

    model: str

    messages: List[ChatMessage]

    temperature: Optional[float] = 0.8

    top_p: Optional[float] = 0.95

    max_tokens: Optional[int] = 512

    stream: Optional[bool] = False

    stop: Optional[Union[str, List[str]]] = None

    presence_penalty: Optional[float] = 0.0

    frequency_penalty: Optional[float] = 0.0

    repetition_penalty: Optional[float] = 1.05


# ============================================================
# Response
# ============================================================

from typing import Union, List, Dict, Any

class ChatResponseMessage(BaseModel):

    role: str = "assistant"

    content: Union[str, List[Dict[str, Any]]]


class Choice(BaseModel):

    index: int = 0

    message: ChatResponseMessage

    finish_reason: str = "stop"


class Usage(BaseModel):

    prompt_tokens: int

    completion_tokens: int

    total_tokens: int


class ChatCompletionResponse(BaseModel):

    id: str

    object: str = "chat.completion"

    created: int

    model: str

    choices: List[Choice]

    usage: Usage


# ============================================================
# /v1/models
# ============================================================

class ModelCard(BaseModel):

    id: str

    object: str = "model"

    owned_by: str = "local"


class ModelList(BaseModel):

    object: str = "list"

    data: List[ModelCard]