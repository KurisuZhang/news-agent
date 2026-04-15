from __future__ import annotations
from typing import List

from models import FeedItem

ROLE = (
    "你是一位科技媒体主编，风格犀利有态度，善于提炼信息、发现趋势、挑战主流观点。"
    "对知乎条目，请特别提炼高赞反驳意见或争议点。"
)

INSTRUCTION = (
    "请根据以下按维度分组的科技信息条目，为每个维度写 2~3 句有观点、有态度的中文总结。"
    "直接输出 Markdown，格式如下：\n\n"
    "### 🔬 科技技术\n<总结内容>\n\n"
    "### 📰 实时新闻\n<总结内容>\n"
)

EMOJI_MAP = {
    "科技技术": "🔬 科技技术",
    "实时新闻": "📰 实时新闻",
}


def build_prompt(items: List[FeedItem], categories: List[str]) -> str:
    """Build a structured prompt for AI summary generation."""
    by_cat: dict[str, List[FeedItem]] = {cat: [] for cat in categories}
    for item in items:
        if item.category in by_cat:
            by_cat[item.category].append(item)

    sections = []
    for cat in categories:
        label = EMOJI_MAP.get(cat, cat)
        section_lines = [f"#### {label}"]
        cat_items = by_cat[cat]
        if not cat_items:
            section_lines.append("（本维度暂无条目）")
        else:
            for item in cat_items:
                snippet = item.summary[:80] if item.summary else "（无摘要）"
                section_lines.append(
                    f"- [{item.title}]({item.url}) [{item.source}]\n  > {snippet}"
                )
        sections.append("\n".join(section_lines))

    body = "\n\n".join(sections)
    # Include category names in the prompt so they can be found in the string
    categories_str = "、".join(categories)
    return f"{ROLE}\n\n{INSTRUCTION}\n\n---\n\n## 条目列表\n\n【{categories_str}】\n\n{body}"


def print_prompt(items: List[FeedItem], categories: List[str]) -> str:
    """Build prompt, print it, and return it for writer.py to capture."""
    prompt = build_prompt(items, categories)
    print("\n" + "=" * 60)
    print("📋 [Summarizer] 以下是供 AI 生成摘要的 Prompt：")
    print("=" * 60)
    print(prompt)
    print("=" * 60 + "\n")
    return prompt
