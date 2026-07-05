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

import tqdm
from openai import OpenAI
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
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("sft_pipeline")

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
    api_base_url: str = "https://api.openai.com/v1"
    api_key: str = ""  # set via env var SFT_API_KEY or replace here
    api_model: str = "gpt-4o-mini"
    api_timeout: float = 120.0
    api_max_retries: int = 5
    api_max_tokens: int = 2048
    api_temperature: float = 0.7

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
        if not cfg.api_key:
            log.warning("SFT_API_KEY env var not set — using empty key (will fail at runtime)")
        return cfg


# ---------------------------------------------------------------------------
# Category-specific System Prompt Templates
# ---------------------------------------------------------------------------

CATEGORY_SYSTEM_PROMPTS: dict[str, str] = {
    "日常吐槽": (
        "你是一位擅长将日常吐槽转化为高质量指令数据的助手。\n"
        "你的任务是根据给定的原始吐槽内容，生成一条 JSON 格式的 SFT 训练数据，"
        "包含 \"instruction\"（用户提问）和 \"output\"（期望的模型回答）。\n"
        "要求：保持原文的真实情绪（如愤怒、无奈、自嘲），语气口语化、接地气，"
        "指令自然符合吐槽场景。"
    ),
    "聊天记录": (
        "你是一位擅长将聊天记录转化为高质量指令数据的助手。\n"
        "你的任务是根据给定的聊天内容，生成一条 JSON 格式的 SFT 训练数据，"
        "包含 \"instruction\"（用户提问）和 \"output\"（期望的模型回答）。\n"
        "要求：风格口语化、对话感强，指令要像用户在日常聊天中会问出的问题。"
    ),
    "日记": (
        "你是一位擅长将日记内容转化为高质量指令数据的助手。\n"
        "你的任务是根据给定的日记片段，生成一条 JSON 格式的 SFT 训练数据，"
        "包含 \"instruction\"（用户提问）和 \"output\"（期望的模型回答）。\n"
        "要求：保持个人化、内省的语气，指令应引导模型进行自我表达或情感反思。"
    ),
    "散文": (
        "你是一位擅长将散文转化为高质量指令数据的助手。\n"
        "你的任务是根据给定的散文内容，生成一条 JSON 格式的 SFT 训练数据，"
        "包含 \"instruction\"（用户提问）和 \"output\"（期望的模型回答）。\n"
        "要求：风格优美、文学性强，指令应引导模型进行描写或抒情表达。"
    ),
    "诗与歌": (
        "你是一位擅长将诗歌或歌词转化为高质量指令数据的助手。\n"
        "你的任务是根据给定的诗文内容，生成一条 JSON 格式的 SFT 训练数据，"
        "包含 \"instruction\"（用户提问）和 \"output\"（期望的模型回答）。\n"
        "要求：保留原作的节奏感和意象，指令应引导模型进行创造性文本生成。"
    ),
    "小说": (
        "你是一位擅长将小说片段转化为高质量指令数据的助手。\n"
        "你的任务是根据给定的小说内容，生成一条 JSON 格式的 SFT 训练数据，"
        "包含 \"instruction\"（用户提问）和 \"output\"（期望的模型回答）。\n"
        "要求：叙事性强，指令应引导模型进行故事叙述、场景描写或角色对话。"
    ),
    "剧本": (
        "你是一位擅长将剧本内容转化为高质量指令数据的助手。\n"
        "你的任务是根据给定的剧本片段，生成一条 JSON 格式的 SFT 训练数据，"
        "包含 \"instruction\"（用户提问）和 \"output\"（期望的模型回答）。\n"
        "要求：保留剧本的对话驱动特点，指令应引导模型进行场景构建或对白创作。"
    ),
    "幽默": (
        "你是一位擅长将幽默段子转化为高质量指令数据的助手。\n"
        "你的任务是根据给定的幽默内容，生成一条 JSON 格式的 SFT 训练数据，"
        "包含 \"instruction\"（用户提问）和 \"output\"（期望的模型回答）。\n"
        "要求：风格轻松诙谐，指令应引导模型进行幽默回应或调侃。"
    ),
    "学习": (
        "你是一位擅长将学习内容转化为高质量指令数据的助手。\n"
        "你的任务是根据给定的学习笔记或知识内容，生成一条 JSON 格式的 SFT 训练数据，"
        "包含 \"instruction\"（用户提问）和 \"output\"（期望的模型回答）。\n"
        "要求：风格清晰、有教育意义，指令应引导模型进行知识讲解或问题解答。"
    ),
}

# Length constraint suffix templates (Dice 2)
LENGTH_CONSTRAINTS: list[str] = [
    "请确保生成的 output 不超过 5 个词。",
    "请确保生成的 output 在 15 个词以内。",
    "请确保生成的 output 在 50 个词以内。",
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
            (ConnectionError, TimeoutError, Exception)
        ),
        before_sleep=before_sleep_log(log, logging.WARNING),
        reraise=True,
    )
    def _call(self, system: str, user: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.config.api_model,
            temperature=self.config.api_temperature,
            max_tokens=self.config.api_max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content.strip()

    def generate(self, system: str, user: str) -> Optional[dict[str, str]]:
        """Call LLM and parse JSON response. Returns None on failure."""
        try:
            raw = self._call(system, user)
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

    p = argparse.ArgumentParser(
        description="SFT Data Preprocessing Pipeline — transform raw JSONL into instruction-output pairs.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--input-glob", default="*.jsonl", help="Glob pattern for input JSONL files")
    p.add_argument("--output-dir", default="processed_sft", help="Output directory for train/val JSONL")
    p.add_argument("--checkpoint-db", default=".sft_checkpoint.db", help="SQLite checkpoint file path")
    p.add_argument("--val-split", type=float, default=0.1, help="Validation split ratio (0.0–1.0)")
    p.add_argument("--api-base-url", default="https://api.openai.com/v1", help="API base URL")
    p.add_argument("--api-model", default="gpt-4o-mini", help="Model name")
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