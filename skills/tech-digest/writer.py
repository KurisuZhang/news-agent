from __future__ import annotations
import os
import re
from datetime import datetime, timezone
from typing import Dict, List

from models import FeedItem
from translator import translate_to_zh


def _extract_description(summary: str, max_len: int = 100) -> str:
    """Strip HTML tags and return a clean one-line description."""
    text = re.sub(r"<[^>]+>", " ", summary)   # remove tags
    text = re.sub(r"\s+", " ", text).strip()   # collapse whitespace
    if not text:
        return ""
    return text[:max_len].rstrip() + ("…" if len(text) > max_len else "")

SOURCE_LABELS = {
    "zhihu": "知乎",
    "github": "GitHub",
    "v2ex": "V2EX",
    "hackernews": "HN",
    "cnblogs": "博客园",
    "solidot": "Solidot",
    "infoq": "InfoQ",
}

CATEGORY_LABELS = {
    "科技技术": "🔬 科技技术",
    "实时新闻": "📰 实时新闻",
}


def render_markdown(
    by_category: Dict[str, List[FeedItem]],
    ai_summary: str,
    categories: List[str],
    date_str: str,
) -> str:
    top_n = max((len(v) for v in by_category.values()), default=5)
    lines = [
        f"# 每日科技信息摘要 · {date_str}",
        "",
        "> 数据来源：知乎 / GitHub Trending / V2EX / Hacker News / 博客园 / Solidot / InfoQ",
        "",
        "---",
        "",
        f"## 📋 按维度 Top {top_n}",
        "",
    ]

    for cat in categories:
        label = CATEGORY_LABELS.get(cat, cat)
        lines.append(f"### {label}")
        items = by_category.get(cat, [])
        if not items:
            lines.append("_（本维度暂无条目）_")
        else:
            for item in items:
                src_label = SOURCE_LABELS.get(item.source, item.source)
                lines.append(f"- [{item.title}]({item.url}) `{src_label}`")
                if item.source == "github":
                    desc = _extract_description(item.summary)
                    if desc:
                        lines.append(f"  {translate_to_zh(desc)}")
        lines.append("")

    lines += [
        "---",
        "",
        "## 🧠 AI 维度总结",
        "",
        ai_summary,
        "",
        "---",
        f"_生成时间：{date_str} | Agent 版本：1.0_",
    ]

    return "\n".join(lines)


def write_output(content: str, date_str: str, output_dir: str = "output") -> None:
    os.makedirs(output_dir, exist_ok=True)
    dated_path = os.path.join(output_dir, f"{date_str}-tech-digest.md")
    latest_path = os.path.join(output_dir, "latest-digest.md")
    for path in (dated_path, latest_path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    print(f"[Writer] 已输出：{dated_path}")
    print(f"[Writer] 已更新：{latest_path}")
