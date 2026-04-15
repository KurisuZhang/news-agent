from __future__ import annotations
from typing import Dict, List

from models import FeedItem


def classify_item(
    item: FeedItem,
    categories: Dict[str, List[str]],
    default_category: str = "",
) -> str:
    """Assign the category with the most keyword hits. Tie-break: first category wins.
    Falls back to default_category (or the first category) when nothing matches."""
    text = (item.title + " " + item.summary).lower()
    scores = {
        cat: sum(1 for kw in keywords if kw.lower() in text)
        for cat, keywords in categories.items()
    }
    max_score = max(scores.values())
    if max_score == 0:
        return default_category if default_category in categories else next(iter(categories))
    return max(scores, key=lambda c: scores[c])


def classify_all(
    items: List[FeedItem],
    categories: Dict[str, List[str]],
    default_category: str = "",
) -> List[FeedItem]:
    """Classify all items in-place and return them."""
    for item in items:
        item.category = classify_item(item, categories, default_category)
    return items
