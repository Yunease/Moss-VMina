#!/usr/bin/env python3
"""
Moss VMina — SFT Data Preprocessing Pipeline (Enterprise Edition)

Transforms raw JSONL corpora into instruction-output JSONL files for LLM fine-tuning,
with stateful resume, exponential-backoff retries, rate limiting, and automatic
train/validation splitting.

Usage:
    python sft_pipeline.py                          # use defaults (./*.jsonl)
    python sft_pipeline.py --input-dir /path/to/data
    python sft_pipeline.py --val-split 0.15 --max-rpm 30

Requirements:
    pip install openai tenacity tqdm
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
import random
import textwrap
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from dotenv import find_dotenv, load_dotenv

import tqdm
from openai import (
    OpenAI,
    APIConnectionError,
    RateLimitError,
    BadRequestError,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)
import logging

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
log = logging.getLogger("sft_pipeline")
log.setLevel(logging.INFO)

_fh = logging.FileHandler("sft_pipeline.log", mode="a", encoding="utf-8")
_fh.setLevel(logging.INFO)
_fh.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))
log.addHandler(_fh)

_sh = logging.StreamHandler()
_sh.setLevel(logging.INFO)
_sh.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))
log.addHandler(_sh)

# 防止日志重复传播到 root logger
log.propagate = False

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class PipelineConfig:
    """Central configuration — tweak weights, paths, and API settings here."""

    # ---------- Paths ----------
    input_glob: str = "*.jsonl"
    output_dir: str = "processed_sft"
    checkpoint_db: str = ".sft_checkpoint.db"

    # ---------- Data split ----------
    val_split: float = 0.1  # fraction of items routed to val.jsonl

    # ---------- API ----------
    # DeepSeek 官方 API（OpenAI 兼容端点）
    # 通过环境变量 SFT_API_KEY / SFT_API_BASE_URL / SFT_API_MODEL 可覆盖以下默认值
    api_base_url: str = "https://api.deepseek.com"
    api_key: str = ""  # 必须通过环境变量 SFT_API_KEY 或 --api-key 设置
    api_model: str = "deepseek-chat"
    api_timeout: float = 120.0
    api_max_retries: int = 5
    api_max_tokens: int = 6144
    api_temperature: float = 0.7
    # deepseek-chat 不需要 thinking 参数；如果用 deepseek-reasoner 可开启
    api_extra_body: dict[str, Any] | None = None

    # ---------- Rate limiting ----------
    max_rpm: int = 30  # requests per minute ceiling

    # ---------- Dice 1 — Context Condition weights ----------
    # Conversational categories → 20 % metadata, 80 % blind
    conversational_categories: tuple[str, ...] = ("日常吐槽", "聊天记录")
    conv_metadata_weight: float = 0.20
    # Long-text / creative categories → 75 % metadata, 25 % blind
    creative_metadata_weight: float = 0.75

    # ---------- Dice 2 — Length constraint weights ----------
    # Conversational: 60 % (1-5), 30 % (within 15), 10 % (within 50)
    conv_length_weights: tuple[float, ...] = (0.60, 0.30, 0.10)
    # Creative: 33 % / 33 % / 34 %
    creative_length_weights: tuple[float, ...] = (0.33, 0.33, 0.34)

    # ---------- Runtime flags ----------
    dry_run: bool = False  # if True, discover + exit without API calls
    skip_schema: bool = False

    @classmethod
    def from_env(cls) -> PipelineConfig:
        cfg = cls()
        cfg.api_key = os.environ.get("SFT_API_KEY", cfg.api_key)
        cfg.api_base_url = os.environ.get("SFT_API_BASE_URL", cfg.api_base_url)
        cfg.api_model = os.environ.get("SFT_API_MODEL", cfg.api_model)
        if not cfg.api_key:
            log.warning("SFT_API_KEY env var not set — using empty key (will fail at runtime)")
        return cfg


# ---------------------------------------------------------------------------
# Category-specific System Prompt Templates
# ---------------------------------------------------------------------------

COMMON_PROMPT_RULES = textwrap.dedent(
    """\
    你是一位专业的 SFT 训练数据构造师。你会收到一段真实的原始文本（可能附带元数据），
    任务是基于它产出一条 JSON 格式的"指令-回答"训练样本：
    {"instruction": "用户可能提出的指令/问题", "output": "对应的理想回答"}

    请始终遵守以下规则：
    1.【output 的定位】output 应当以给定的原始内容为基础，只做必要的整理（修正明显错别字、
       去掉格式噪声），但必须完整保留原文的情绪、观点、具体细节和语气，不要淡化负面情绪、
       不要加入说教或免责声明、不要暴露"这是AI生成/训练数据"的痕迹。output 不是对原文的
       评论或分析，而是原文本身（经轻度整理后）的呈现。
    2.【instruction 的定位】instruction 是"反推"出来的指令：设想一个真实用户在什么情境下，
       会提出一个请求或问题，而上面的 output 恰好是对这个请求最自然、最贴切的回答。
       instruction 不能是原文的复述，而应该是能够合理引出该 output 的提问/指令。
    3.【多样性】instruction 的句式、人称、角度要富于变化，禁止每条都使用相同的固定模板
       （如总是"请你谈谈…"），可以是请求、疑问句、命令句、口语化开场白等不同形式。
    4.【元数据使用】如果[元数据]中包含 title/mood/mood_level/tags 等字段，可参考它们理解
       原文的情绪基调或主题背景，但不要把字段名或原始取值直接写进 instruction 或 output 里。
       如果没有提供元数据，就只凭正文内容自行判断。
    5.【格式】只输出合法的单行 JSON，不要用 markdown 代码块包裹，不要输出 JSON 以外的任何
       文字；原文中的换行请转义为 \\n，双引号需要正确转义为 \\"。"""
)


def _make_system_prompt(style_note: str, example_content: str, example_json: str) -> str:
    """Assemble a category system prompt from shared rules + category style + one few-shot example."""
    return (
        f"{COMMON_PROMPT_RULES}\n\n"
        f"【本类别风格要求】\n{style_note}\n\n"
        f"【示例】\n"
        f"原始内容：\n{example_content}\n\n"
        f"期望输出：\n{example_json}"
    )


CATEGORY_SYSTEM_PROMPTS: dict[str, str] = {
    "日常吐槽": _make_system_prompt(
        style_note=(
            "保留原文真实、直接、略带情绪化的口语表达（如愤怒、无奈、自嘲），不要把吐槽内容"
            "改写得过于礼貌或官方。instruction 应体现用户想找人倾诉/吐槽的情境。"
        ),
        example_content="我的claude马上就过期哩，接下来只有codex的额度可以用了，要不然。。还是老老实实认真学一下吧？",
        example_json=(
            '{"instruction": "我的Claude额度马上就要过期了，之后大概只能靠codex的额度撑一阵，'
            '你说是不是该老老实实学点东西了，帮我把这种又纠结又自嘲的心情吐槽出来", '
            '"output": "我的claude马上就过期哩，接下来只有codex的额度可以用了，要不然。。还是'
            '老老实实认真学一下吧？"}'
        ),
    ),
    "聊天记录": _make_system_prompt(
        style_note=(
            "保留对话体的口语感和来回节奏，instruction 应像用户在请求'模拟/续写'一段符合特定"
            "情境的聊天，而不是复述聊天内容本身。"
        ),
        example_content="因为跨平台做账号管理也比较麻烦，所以我就干脆懒得搞了",
        example_json=(
            '{"instruction": "朋友问我为什么不把各个平台的账号都同步管理起来，帮我回一句，'
            '就说太麻烦所以干脆懒得弄了", '
            '"output": "因为跨平台做账号管理也比较麻烦，所以我就干脆懒得搞了"}'
        ),
    ),
    "日记": _make_system_prompt(
        style_note="保持第一人称、内省、私人化的语气，instruction 应体现用户想记录/整理当天心情或经历的意图。",
        example_content=(
            "耳机中在播放什么音乐呢？今天又是阴雨的一天，但雨水比昨天要小很多了，直到下午的时候，"
            "只剩下像雾气一般细碎的雨纹，把我的外衣弄潮，扰乱我的眼镜——就好像我近视加重了一样。"
            "这样说起来，我似乎一直没有戴新的眼镜，尽管假期配上了，直至今日也没有用上，"
            "自己到底是因为什么才刻意忽视了呢？"
        ),
        example_json=(
            '{"instruction": "帮我写一段今天的日记，主题是阴雨天听着耳机音乐时，忽然想起自己'
            '配了新眼镜却一直没戴、说不清为什么会一直拖延的那种恍惚感", '
            '"output": "耳机中在播放什么音乐呢？今天又是阴雨的一天，但雨水比昨天要小很多了，'
            '直到下午的时候，只剩下像雾气一般细碎的雨纹，把我的外衣弄潮，扰乱我的眼镜——就好像'
            '我近视加重了一样。这样说起来，我似乎一直没有戴新的眼镜，尽管假期配上了，直至今日也'
            '没有用上，自己到底是因为什么才刻意忽视了呢？"}'
        ),
    ),
    "散文": _make_system_prompt(
        style_note="保留原文优美、富有画面感和文学性的语言风格，instruction 应引导一段描写性或抒情性的文字创作。",
        example_content=(
            "像蘑菇，像残垣。雨水促长淘金者的狂热，鱼群的飘摇避无可避。发散的空想得以准许，"
            "路牌指向阶梯，且不计较透明星烁的轨道，游思牵引爪的前驱，滑动到夜鹰星座的苍白火焰上。"
        ),
        example_json=(
            '{"instruction": "写一段意象超现实、发散跳跃的散文，融合雨水、鱼群、星轨这些意象，'
            '风格要空灵、不追求逻辑连贯，读起来像一段游离的意识流", '
            '"output": "像蘑菇，像残垣。雨水促长淘金者的狂热，鱼群的飘摇避无可避。发散的空想得'
            '以准许，路牌指向阶梯，且不计较透明星烁的轨道，游思牵引爪的前驱，滑动到夜鹰星座的'
            '苍白火焰上。"}'
        ),
    ),
    "诗与歌": _make_system_prompt(
        style_note=(
            "保留原文的节奏感、意象和韵律，不必逐字押韵但要保留诗意；instruction 应引导一段"
            "主题相符的诗歌/歌词创作。"
        ),
        example_content=(
            "我所钟爱的昨日已经生锈，变得单调、毫无生气，像泛黄的枫叶，像垂死的鹰；然而，"
            "西风不会降临，没有一样东西能够驱使慵懒的过去，让它变得清晰。我叹出的气化为白霜，"
            "静静驻留在谁人的窗前，可那窗，永远覆着看不清的霜，就像我看不清曾经一般，满心挂念，"
            "却始终难以窥见。"
        ),
        example_json=(
            '{"instruction": "写一段带诗意的文字，主题是怀念已经模糊、无法看清的过去，意象上用'
            '生锈的枫叶、垂死的鹰、化不开的白霜这类萧瑟的画面", '
            '"output": "我所钟爱的昨日已经生锈，变得单调、毫无生气，像泛黄的枫叶，像垂死的鹰；'
            '然而，西风不会降临，没有一样东西能够驱使慵懒的过去，让它变得清晰。我叹出的气化为'
            '白霜，静静驻留在谁人的窗前，可那窗，永远覆着看不清的霜，就像我看不清曾经一般，'
            '满心挂念，却始终难以窥见。"}'
        ),
    ),
    "小说": _make_system_prompt(
        style_note="保留叙事性和场景细节，instruction 应引导一段带有具体人物/场景/情绪的小说片段创作。",
        example_content=(
            "在兴奋和吵闹的环境中我完全没听进去毕业典礼里那些感人的演讲，看着那些平日里绝不掉眼泪的"
            "同学在此刻哭成泪人，我缄默地在角落里用另一种方式参与这场离别。从阴影中退场，我留给他们"
            "金辉色的时光。在这一刻，我是迷惘的。当听起同学好不容易鼓起勇气说出的梦想时，我的心中"
            "毫无波澜。我既不想独自去遥远的地区旅行，也没有留在家乡的意愿。"
        ),
        example_json=(
            '{"instruction": "写一段第一人称视角的小说片段，主角在热闹的毕业典礼上却感到麻木和'
            '迷惘，听着同学畅谈梦想时心里毫无波澜，也说不清自己到底想要什么", '
            '"output": "在兴奋和吵闹的环境中我完全没听进去毕业典礼里那些感人的演讲，看着那些'
            '平日里绝不掉眼泪的同学在此刻哭成泪人，我缄默地在角落里用另一种方式参与这场离别。'
            '从阴影中退场，我留给他们金辉色的时光。在这一刻，我是迷惘的。当听起同学好不容易鼓起'
            '勇气说出的梦想时，我的心中毫无波澜。我既不想独自去遥远的地区旅行，也没有留在家乡的'
            '意愿。"}'
        ),
    ),
    "剧本": _make_system_prompt(
        style_note="保留对白驱动、场景提示的剧本格式，instruction 应引导一段带有具体人物关系和情绪冲突的场景创作。",
        example_content=(
            "诗怜（微笑）：“谢谢你愿意跟我说这些。”\n诗怜：“也没有太难熬，在医院也结识了朋友。”\n"
            "诗怜：“有时也会怀念，一点点。”\n诗怜（微笑）：“到家了！”\n诗怜（微笑）：“那个......谢谢。”"
        ),
        example_json=(
            '{"instruction": "写一段剧本对白，一个刚经历住院、现在准备回家的角色跟陪同的朋友道别，'
            '语气温柔、带点释然和感激", '
            '"output": "诗怜（微笑）：“谢谢你愿意跟我说这些。”\\n诗怜：“也没有太难熬，在医院也'
            '结识了朋友。”\\n诗怜：“有时也会怀念，一点点。”\\n诗怜（微笑）：“到家了！”\\n'
            '诗怜（微笑）：“那个......谢谢。”"}'
        ),
    ),
    "幽默": _make_system_prompt(
        style_note="保留原文轻松诙谐、包袱感强的语言风格，instruction 应引导一段特定主题的幽默/调侃创作。",
        example_content=(
            "我一看这出题的，哎，一拍大腿，他肯定是玩apex的，没错，也只有我们apex玩家能想出这么"
            "扫码的作文题目，也是耄耋在哈气——欠爱了。但毕竟是考场作文，我们还是按照教条板正的来"
            "写吧。\n何为专，何为转，何为传？\n我认为专就是专注轻机枪。每个游戏都有最扫码的武器，"
            "在瓦叫奥丁，到我们apex则是专注。古人云：专注狗，专注狗，按住左键不松手。假如你好不"
            "容易打了1000多来到决赛圈，最后一对全红甲金专注，那你不就炸了？就算我们艾许大人来了，"
            "面对红甲老头也手无缚坤之力。"
        ),
        example_json=(
            '{"instruction": "帮我用apex玩家的视角调侃一下这次的考场作文题目（专/转/传），然后'
            '煞有介事地写一段带游戏黑话、自嘲又中二的\'范文\'开头", '
            '"output": "我一看这出题的，哎，一拍大腿，他肯定是玩apex的，没错，也只有我们apex'
            '玩家能想出这么扫码的作文题目，也是耄耋在哈气——欠爱了。但毕竟是考场作文，我们还是'
            '按照教条板正的来写吧。\\n何为专，何为转，何为传？\\n我认为专就是专注轻机枪。每个'
            '游戏都有最扫码的武器，在瓦叫奥丁，到我们apex则是专注。古人云：专注狗，专注狗，按住'
            '左键不松手。假如你好不容易打了1000多来到决赛圈，最后一对全红甲金专注，那你不就炸了？'
            '就算我们艾许大人来了，面对红甲老头也手无缚坤之力。"}'
        ),
    ),
    "学习": _make_system_prompt(
        style_note="保留清晰、有条理的讲解风格，instruction 应像一个学习者提出的具体知识性问题。",
        example_content=(
            "严格来说，哈希并不是计算机网络的内容。但是后面讲BT协议需要用到，这里也就简单说明一下"
            "好啦！\n哈希算法是把乱七八糟的各种文件，变成一串字符串序列的算法。文件和哈希序列在"
            "一个表中是唯一对应的（忽略发生可能性极低的哈希碰撞的话），文件只要被修改过，生成出的"
            "字符串就不一样，一旦检测就会暴露。\n哈希算法从原理上就不可逆，只能单向计算，无法逆向"
            "还原。就像水果和果汁的关系，你不可能把果汁还原成水果，但可以通过喝一口果汁感觉一下"
            "味道变了没有，从而确定这个水果没有混淆。"
        ),
        example_json=(
            '{"instruction": "帮我讲一下哈希算法是什么、为什么说它不可逆，最好用一个通俗的类比'
            '讲清楚", '
            '"output": "严格来说，哈希并不是计算机网络的内容。但是后面讲BT协议需要用到，这里也'
            '就简单说明一下好啦！\\n哈希算法是把乱七八糟的各种文件，变成一串字符串序列的算法。'
            '文件和哈希序列在一个表中是唯一对应的（忽略发生可能性极低的哈希碰撞的话），文件只要'
            '被修改过，生成出的字符串就不一样，一旦检测就会暴露。\\n哈希算法从原理上就不可逆，'
            '只能单向计算，无法逆向还原。就像水果和果汁的关系，你不可能把果汁还原成水果，但可以'
            '通过喝一口果汁感觉一下味道变了没有，从而确定这个水果没有混淆。"}'
        ),
    ),
}

# Length constraint suffix templates (Dice 2) — unit changed from ambiguous "词" to 汉字字符数
LENGTH_CONSTRAINTS: list[str] = [
    "请确保生成的 output 在 15 个汉字以内（不含标点）。",
    "请确保生成的 output 在 40 个汉字以内。",
    "请确保生成的 output 在 120 个汉字以内。",
]


# ---------------------------------------------------------------------------
# Stage 1 — Schema Discovery
# ---------------------------------------------------------------------------

@dataclass
class SchemaReport:
    files: list[Path]
    categories: dict[str, set[str]]  # category → set of field names
    totals: dict[str, int]  # file → line count


def discover_schema(input_glob: str = "*.jsonl") -> SchemaReport:
    """Scan all matching JSONL files and aggregate category → field mappings."""
    files = sorted(Path.cwd().glob(input_glob))
    if not files:
        log.error("No JSONL files matching %r found in %s", input_glob, Path.cwd())
        sys.exit(1)

    categories: dict[str, set[str]] = {}
    totals: dict[str, int] = {}
    raw_examples: dict[str, dict[str, Any]] = {}

    for fp in files:
        count = 0
        with open(fp, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                count += 1
                obj = json.loads(line)
                cat = obj.get("category", "__unknown__")
                if cat not in categories:
                    categories[cat] = set(obj.keys())
                    raw_examples[cat] = obj
                else:
                    categories[cat] |= set(obj.keys())
        totals[str(fp.name)] = count

    # Print clean report
    header = "=" * 62
    print(f"\n{header}")
    print("  📋  STAGE 1 — SCHEMA DISCOVERY REPORT")
    print(f"{header}")
    for fp in files:
        print(f"  📄 {fp.name}: {totals[str(fp.name)]} lines")
    print(f"{header}")
    print(f"  Found {len(categories)} unique categories:\n")
    for cat in sorted(categories.keys()):
        fields = sorted(categories[cat])
        print(f"  │  [{cat}]")
        print(f"  │   fields ({len(fields)}): {', '.join(fields)}")
        print()
    print(f"{header}\n")

    return SchemaReport(files=files, categories=categories, totals=totals)


# ---------------------------------------------------------------------------
# Checkpoint Manager (SQLite)
# ---------------------------------------------------------------------------

class CheckpointManager:
    """Persistent tracking of processed items using SQLite."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, timeout=10)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS checkpoint (
                item_id   TEXT NOT NULL,
                chunk     INTEGER NOT NULL DEFAULT 0,
                source    TEXT NOT NULL DEFAULT '',
                status    TEXT NOT NULL DEFAULT 'done',
                created   TEXT NOT NULL,
                PRIMARY KEY (item_id, chunk, source)
            )
            """
        )
        self.conn.commit()

    def is_processed(self, item_id: str, chunk: int = 0, source: str = "") -> bool:
        cur = self.conn.execute(
            "SELECT 1 FROM checkpoint WHERE item_id=? AND chunk=? AND source=?",
            (item_id, chunk, source),
        )
        return cur.fetchone() is not None

    def mark_done(self, item_id: str, chunk: int = 0, source: str = ""):
        self.conn.execute(
            "INSERT OR IGNORE INTO checkpoint (item_id, chunk, source, created) VALUES (?, ?, ?, ?)",
            (item_id, chunk, source, datetime.now(timezone.utc).isoformat()),
        )
        self.conn.commit()

    def count_processed(self) -> int:
        cur = self.conn.execute("SELECT COUNT(*) FROM checkpoint")
        return cur.fetchone()[0]

    def close(self):
        self.conn.close()


# ---------------------------------------------------------------------------
# Rate Limiter (token-bucket style)
# ---------------------------------------------------------------------------

class RateLimiter:
    """Simple token-bucket rate limiter for RPM control."""

    def __init__(self, max_rpm: int):
        self.max_rpm = max_rpm
        self.min_interval = 60.0 / max_rpm if max_rpm > 0 else 0.0
        self._last_call: float = 0.0

    def wait(self):
        if self.min_interval <= 0:
            return
        elapsed = time.monotonic() - self._last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_call = time.monotonic()


# ---------------------------------------------------------------------------
# Dice Router
# ---------------------------------------------------------------------------

class DiceRouter:
    """Dual-dice random routing engine."""

    def __init__(self, config: PipelineConfig):
        self.config = config

    def is_conversational(self, category: str) -> bool:
        return category in self.config.conversational_categories

    def roll_context(self, category: str) -> bool:
        """Return True = use metadata, False = blind guess."""
        weight = (
            self.config.conv_metadata_weight
            if self.is_conversational(category)
            else self.config.creative_metadata_weight
        )
        return random.random() < weight

    def roll_length(self, category: str) -> str:
        """Return a length-constraint prompt suffix."""
        weights = (
            self.config.conv_length_weights
            if self.is_conversational(category)
            else self.config.creative_length_weights
        )
        idx = random.choices(range(len(LENGTH_CONSTRAINTS)), weights=weights, k=1)[0]
        return LENGTH_CONSTRAINTS[idx]


# ---------------------------------------------------------------------------
# Prompt Builder
# ---------------------------------------------------------------------------

class PromptBuilder:
    """Build system + user prompts from raw data and dice rolls."""

    def __init__(self, dice: DiceRouter):
        self.dice = dice

    def build(
        self,
        obj: dict[str, Any],
        category: str,
        use_metadata: bool,
        length_hint: str,
    ) -> tuple[str, str]:
        """Return (system_prompt, user_prompt)."""
        # System prompt
        system_prompt = CATEGORY_SYSTEM_PROMPTS.get(
            category,
            CATEGORY_SYSTEM_PROMPTS["学习"],  # fallback
        )

        # Build user prompt with optional metadata
        content = obj.get("content") or obj.get("text", "")
        if use_metadata:
            meta_parts = []
            for key in ("title", "mood", "mood_level", "published", "tags", "collection", "source", "type"):
                val = obj.get(key)
                if val is not None:
                    meta_parts.append(f"{key}: {val}")
            meta_str = " | ".join(meta_parts) if meta_parts else ""
            if meta_str:
                user_prompt = f"[元数据] {meta_str}\n\n[内容]\n{content}\n\n{length_hint}"
            else:
                user_prompt = f"[内容]\n{content}\n\n{length_hint}"
        else:
            user_prompt = f"[内容]\n{content}\n\n{length_hint}"

        # Append output format instruction
        user_prompt += (
            '\n\n请严格按照以下 JSON 格式回复（不要加多余文本）：\n'
            '{"instruction": "用户指令", "output": "模型回答"}'
        )

        return system_prompt, user_prompt


# ---------------------------------------------------------------------------
# API Client (with tenacity retry)
# ---------------------------------------------------------------------------

class APIClient:
    """Thread-safe OpenAI-compatible API client with exponential-backoff retry."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.client = OpenAI(
            base_url=config.api_base_url,
            api_key=config.api_key,
            timeout=config.api_timeout,
            max_retries=0,  # handled by tenacity below
        )

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=2, max=120),
        retry=retry_if_exception_type(
            (APIConnectionError, RateLimitError, TimeoutError, ConnectionError)
        ),
        before_sleep=before_sleep_log(log, logging.WARNING),
        reraise=True,
    )
    def _call(self, system: str, user: str) -> str:
        kwargs: dict[str, Any] = dict(
            model=self.config.api_model,
            temperature=self.config.api_temperature,
            max_tokens=self.config.api_max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        if self.config.api_extra_body:
            kwargs["extra_body"] = self.config.api_extra_body
        resp = self.client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content.strip()

    def generate(self, system: str, user: str) -> Optional[dict[str, str]]:
        """Call LLM and parse JSON response. Returns None on failure."""
        try:
            raw = self._call(system, user)
        except BadRequestError as exc:
            log.warning("Content moderation blocked item: %s", exc)
            return None
        except Exception as exc:
            log.error("API call failed after retries: %s", exc)
            return None

        # Attempt to extract JSON from the response (handle markdown fences)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            # Strip markdown code fences
            lines = cleaned.splitlines()
            start = 0
            end = len(lines)
            for i, ln in enumerate(lines):
                if ln.strip().startswith("```"):
                    start = i + 1
                    break
            for i in range(len(lines) - 1, start - 1, -1):
                if lines[i].strip().startswith("```") or lines[i].strip() == "":
                    end = i
                    break
            cleaned = "\n".join(lines[start:end]).strip()

        if not cleaned:
            log.warning("Empty response from API")
            return None

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            log.warning("Failed to parse JSON from response: %.150s", cleaned)
            return None

        instruction = parsed.get("instruction") or parsed.get("Instruction", "")
        output = parsed.get("output") or parsed.get("Output", "")
        if not instruction or not output:
            log.warning("Response missing instruction or output: keys=%s", list(parsed.keys()))
            return None

        return {"instruction": instruction.strip(), "output": output.strip()}


# ---------------------------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(config: Optional[PipelineConfig] = None):
    """Orchestrate the three-stage preprocessing pipeline."""
    if config is None:
        config = PipelineConfig.from_env()

    # ---- Stage 1: Schema Discovery ----
    log.info("Stage 1: Schema discovery — scanning input files...")
    schema = discover_schema(config.input_glob)

    if config.skip_schema:
        log.info("Schema discovery skipped (--skip-schema)")

    if config.dry_run:
        log.info("Dry-run mode — exiting after schema discovery.")
        return

    # ---- Init services ----
    checkpoint = CheckpointManager(config.checkpoint_db)
    ratelimit = RateLimiter(config.max_rpm)
    dice = DiceRouter(config)
    prompt_builder = PromptBuilder(dice)
    api = APIClient(config)

    # Prepare output directory and files
    out_dir = Path(config.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    train_fp = out_dir / "train.jsonl"
    val_fp = out_dir / "val.jsonl"

    # Collect all items with their source files
    all_items: list[tuple[Path, dict[str, Any]]] = []
    for fp in schema.files:
        with open(fp, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                all_items.append((fp, obj))

    random.shuffle(all_items)  # deterministic shuffle for split

    # Determine val split threshold per item
    val_threshold = config.val_split

    # Pre-filter: count already processed
    skipped = 0
    items_to_process: list[tuple[Path, dict[str, Any], bool]] = []  # (file, obj, is_val)
    for fp, obj in all_items:
        item_id = obj.get("id", "")
        id_chunk = obj.get("id_chunk", 0)
        source_name = fp.name
        if checkpoint.is_processed(item_id, id_chunk, source_name):
            skipped += 1
            continue
        is_val = random.random() < val_threshold
        items_to_process.append((fp, obj, is_val))

    already_done = checkpoint.count_processed()
    log.info(
        "Checkpoint: %d already processed, %d new items to process (of %d total)",
        already_done, len(items_to_process), len(all_items),
    )

    if not items_to_process:
        log.info("All items already processed. Nothing to do.")
        checkpoint.close()
        return

    # ---- Stage 2 & 3: Process with progress bar ----
    log.info("Stage 2/3: Processing items with dual-dice routing + production guardrails...")
    progress = tqdm.tqdm(
        total=len(items_to_process),
        unit="item",
        desc="SFT Pipeline",
        ncols=100,
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
    )

    success_count = 0
    error_count = 0
    train_count = 0
    val_count = 0

    for fp, obj, is_val in items_to_process:
        category = obj.get("category", "__unknown__")
        item_id = obj.get("id", "")
        id_chunk = obj.get("id_chunk", 0)
        source_name = fp.name

        # Dice roll 1: context condition
        use_metadata = dice.roll_context(category)

        # Dice roll 2: length constraint
        length_hint = dice.roll_length(category)

        # Build prompts
        system_prompt, user_prompt = prompt_builder.build(
            obj, category, use_metadata, length_hint,
        )

        # Call API
        result = api.generate(system_prompt, user_prompt)

        if result is None:
            error_count += 1
            progress.set_postfix(errors=error_count, refresh=False)
            progress.update(1)
            continue

        # Write to train or val
        line = json.dumps(result, ensure_ascii=False)
        target = val_fp if is_val else train_fp
        with open(target, "a", encoding="utf-8") as fout:
            fout.write(line + "\n")

        # Mark checkpoint
        checkpoint.mark_done(item_id, id_chunk, source_name)

        success_count += 1
        if is_val:
            val_count += 1
        else:
            train_count += 1

        progress.set_postfix(
            ok=success_count,
            err=error_count,
            train=train_count,
            val=val_count,
            refresh=False,
        )
        progress.update(1)

        # Rate-limit **after** each request
        ratelimit.wait()

    progress.close()
    checkpoint.close()

    # ---- Final summary ----
    print()
    print("=" * 62)
    print("  ✅  PIPELINE COMPLETE")
    print("=" * 62)
    print(f"  Total items in corpus:     {len(all_items)}")
    print(f"  Skipped (already done):    {skipped}")
    print(f"  Successfully processed:    {success_count}")
    print(f"  Errors:                    {error_count}")
    print(f"  ──────────────────────────────────")
    print(f"  Train samples written:     {train_count}  →  {train_fp}")
    print(f"  Val samples written:       {val_count}  →  {val_fp}")
    if error_count:
        print(f"  ⚠  {error_count} item(s) failed — check logs above.")
    print(f"  Checkpoint DB:             {config.checkpoint_db}")
    print("=" * 62)
    print()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> PipelineConfig:
    """Minimal CLI arg parser (no external dependency)."""
    import argparse

    load_dotenv(find_dotenv())  # load .env from project root

    p = argparse.ArgumentParser(
        description="SFT Data Preprocessing Pipeline — transform raw JSONL into instruction-output pairs.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--input-glob", default="*.jsonl", help="Glob pattern for input JSONL files")
    p.add_argument("--output-dir", default="processed_sft", help="Output directory for train/val JSONL")
    p.add_argument("--checkpoint-db", default=".sft_checkpoint.db", help="SQLite checkpoint file path")
    p.add_argument("--val-split", type=float, default=0.1, help="Validation split ratio (0.0–1.0)")
    p.add_argument("--api-base-url", default="https://api.deepseek.com", help="API base URL")
    p.add_argument("--api-model", default="deepseek-chat", help="Model name (e.g. deepseek-chat, deepseek-reasoner)")
    p.add_argument("--api-key", default="", help="API key (fallback; prefer SFT_API_KEY env var)")
    p.add_argument("--api-max-tokens", type=int, default=2048, help="Max generated tokens")
    p.add_argument("--api-temperature", type=float, default=0.7, help="Generation temperature")
    p.add_argument("--max-rpm", type=int, default=30, help="Max requests per minute")
    p.add_argument("--dry-run", action="store_true", help="Discover schema and exit without API calls")
    p.add_argument("--skip-schema", action="store_true", help="Skip schema discovery phase")
    p.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")

    args = p.parse_args(argv)

    cfg = PipelineConfig(
        input_glob=args.input_glob,
        output_dir=args.output_dir,
        checkpoint_db=args.checkpoint_db,
        val_split=args.val_split,
        api_base_url=args.api_base_url,
        api_model=args.api_model,
        api_key=args.api_key or os.environ.get("SFT_API_KEY", ""),
        api_max_tokens=args.api_max_tokens,
        api_temperature=args.api_temperature,
        max_rpm=args.max_rpm,
        dry_run=args.dry_run,
        skip_schema=args.skip_schema,
    )

    if args.seed is not None:
        random.seed(args.seed)

    return cfg


def main():
    cfg = parse_args()
    run_pipeline(cfg)


if __name__ == "__main__":
    main()