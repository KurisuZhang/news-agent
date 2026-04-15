from __future__ import annotations
from typing import Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from models import FeedItem


def deduplicate(
    feeds: Dict[str, List[FeedItem]],
    similarity_threshold: float = 0.85,
) -> Dict[str, List[FeedItem]]:
    """URL exact dedup + title cosine similarity dedup, per source."""
    return {
        source: _dedup_items(items, similarity_threshold)
        for source, items in feeds.items()
    }


def filter_clickbait(items: List[FeedItem], filter_keywords: List[str]) -> List[FeedItem]:
    """Remove items whose title contains any filter keyword."""
    lowered = [kw.lower() for kw in filter_keywords]
    return [
        item for item in items
        if not any(kw in item.title.lower() for kw in lowered)
    ]


def _dedup_items(items: List[FeedItem], threshold: float) -> List[FeedItem]:
    # Stage 1: URL exact dedup
    seen_urls: set[str] = set()
    unique: List[FeedItem] = []
    for item in items:
        if item.url not in seen_urls:
            seen_urls.add(item.url)
            unique.append(item)

    # Stage 2: title similarity dedup
    if len(unique) < 2:
        return unique

    titles = [item.title for item in unique]
    try:
        tfidf = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b").fit_transform(titles)
        sim_matrix = cosine_similarity(tfidf)
    except ValueError:
        # e.g. all empty titles
        return unique

    keep = [True] * len(unique)
    for i in range(len(unique)):
        if not keep[i]:
            continue
        for j in range(i + 1, len(unique)):
            if keep[j] and sim_matrix[i, j] >= threshold:
                keep[j] = False  # drop the later duplicate

    return [item for item, k in zip(unique, keep) if k]
