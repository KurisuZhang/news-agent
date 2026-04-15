from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FeedItem:
    title: str
    url: str
    summary: str
    published: datetime
    source: str
    score: float = field(default=0.0)
    category: str = field(default="")
