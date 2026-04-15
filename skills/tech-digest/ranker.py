from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, List

from models import FeedItem


def freshness_score(item: FeedItem, decay_hours: float = 48.0) -> float:
    """1.0 for items <= 24h old, 0.0 at decay_hours, linear in between."""
    now = datetime.now(timezone.utc)
    pub = item.published
    if pub.tzinfo is None:
        pub = pub.replace(tzinfo=timezone.utc)
    age_hours = (now - pub).total_seconds() / 3600
    if age_hours <= 24:
        return 1.0
    if age_hours >= decay_hours:
        return 0.0
    return 1.0 - (age_hours - 24) / (decay_hours - 24)


def keyword_bonus(item: FeedItem, tech_keywords: List[str]) -> float:
    """0.1 per unique matched keyword in title+summary, capped at 1.0."""
    text = (item.title + " " + item.summary).lower()
    unique_hits = sum(1 for kw in set(kw.lower() for kw in tech_keywords) if kw in text)
    return min(unique_hits * 0.1, 1.0)


def _score_items(items: List[FeedItem], config: dict) -> None:
    """Score all items in-place."""
    scoring = config["scoring"]
    fw = scoring["freshness_weight"]
    kw = scoring["keyword_weight"]
    decay = scoring["freshness_decay_hours"]
    tech_kws = config.get("tech_keywords", [])
    for item in items:
        item.score = (
            freshness_score(item, decay) * fw
            + keyword_bonus(item, tech_kws) * kw
        )


def rank_by_category(items: List[FeedItem], config: dict) -> Dict[str, List[FeedItem]]:
    """Score all items globally, then return top_n per category."""
    top_n = config["scoring"]["top_n"]
    _score_items(items, config)
    by_cat: Dict[str, List[FeedItem]] = {}
    for item in items:
        by_cat.setdefault(item.category, []).append(item)
    return {
        cat: sorted(cat_items, key=lambda i: i.score, reverse=True)[:top_n]
        for cat, cat_items in by_cat.items()
    }
