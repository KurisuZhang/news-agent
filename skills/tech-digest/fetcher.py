from __future__ import annotations
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Dict, List

import feedparser

from models import FeedItem


def fetch_source(name: str, url: str, timeout: int = 10) -> List[FeedItem]:
    """Fetch a single RSS source. Returns [] on any error."""
    try:
        feed = feedparser.parse(url, request_headers={"User-Agent": "TechDigestAgent/1.0"})
        items = []
        for entry in feed.get("entries", []):
            published = _parse_time(entry.get("published_parsed"))
            items.append(
                FeedItem(
                    title=entry.get("title", "").strip(),
                    url=entry.get("link", ""),
                    summary=entry.get("summary", "").strip(),
                    published=published,
                    source=name,
                )
            )
        return items
    except Exception as exc:
        print(f"[WARN] Failed to fetch {name} ({url}): {exc}")
        return []


def fetch_all(sources: List[dict]) -> Dict[str, List[FeedItem]]:
    """Concurrently fetch all sources. Returns dict keyed by source name."""
    result: Dict[str, List[FeedItem]] = {}
    with ThreadPoolExecutor(max_workers=len(sources)) as executor:
        future_to_name = {
            executor.submit(fetch_source, s["name"], s["url"]): s["name"]
            for s in sources
        }
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            result[name] = future.result()
    return result


def _parse_time(time_struct) -> datetime:
    if time_struct is None:
        return datetime.now(timezone.utc)
    try:
        return datetime(*time_struct[:6], tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)
