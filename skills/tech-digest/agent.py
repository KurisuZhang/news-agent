#!/usr/bin/env python3
"""Tech Digest Agent — 每日科技信息收集与摘要"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

import yaml

from classifier import classify_all
from deduplicator import deduplicate, filter_clickbait
from fetcher import fetch_all
from models import FeedItem
from ranker import rank_by_category
from summarizer import print_prompt
from writer import render_markdown, write_output


def load_config(path: str = "config.yaml") -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main(output_dir: str = "output", config_path: str = "config.yaml") -> None:
    config = load_config(config_path)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 1. Fetch
    print("[Agent] 正在抓取 RSS 源...")
    raw_feeds = fetch_all(config["sources"])
    total = sum(len(v) for v in raw_feeds.values())
    print(f"[Agent] 共抓取 {total} 条原始条目")

    # 2. Deduplicate + filter clickbait
    print("[Agent] 去重与过滤中...")
    deduped = deduplicate(raw_feeds)
    filter_kws = config.get("filter_keywords", [])
    all_items: list[FeedItem] = []
    for src, items in deduped.items():
        all_items.extend(filter_clickbait(items, filter_kws))

    # 3. Classify ALL items first
    print("[Agent] 分类中...")
    categories_config: dict = config.get("categories", {})
    category_names = list(categories_config.keys())
    default_category = config.get("default_category", category_names[0] if category_names else "")
    classify_all(all_items, categories_config, default_category)

    # 4. Global score + rank per category
    print("[Agent] 评分排序中...")
    ranked = rank_by_category(all_items, config)

    # 5. Flatten ranked items for prompt
    ranked_items: list[FeedItem] = [item for cat in category_names for item in ranked.get(cat, [])]

    # 6. Summarize — print prompt for AI in the running environment
    print("[Agent] 构造摘要 Prompt...")
    print_prompt(ranked_items, category_names)

    # 7. Build AI summary placeholder (running env AI reads prompt above and provides summary)
    ai_summary = (
        "<!-- AI 摘要：请将上方 Prompt 的输出粘贴至此处，或由运行环境 AI 自动填充 -->\n"
        "_[摘要待生成 — 请将终端输出的 Prompt 交给 AI 生成后填入]_"
    )

    # 8. Write output
    md = render_markdown(ranked, ai_summary, category_names, date_str)
    write_output(md, date_str, output_dir=output_dir)
    print(f"[Agent] 完成！输出目录：{output_dir}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="每日科技信息收集与摘要 Agent")
    parser.add_argument("--output-dir", default="output", help="输出目录（默认：output）")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    args = parser.parse_args()
    main(output_dir=args.output_dir, config_path=args.config)
