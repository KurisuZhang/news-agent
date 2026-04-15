# 每日科技信息收集与摘要 Agent — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个可一条命令运行的 Python Agent，自动抓取4个RSS源、去重过滤评分分类，生成每日科技摘要 Markdown 文档。

**Architecture:** 单入口 `agent.py` 串联6个职责单一的模块（fetcher / deduplicator / ranker / classifier / summarizer / writer），通过 `config.yaml` 驱动所有可变配置，输出双份 MD 文档。

**Tech Stack:** Python 3.9+, feedparser, requests, scikit-learn (TF-IDF), pyyaml, concurrent.futures (stdlib)

---

## 文件清单

| 文件 | 职责 |
|------|------|
| `tech-digest-agent/config.yaml` | RSS源列表、分类关键词、过滤词、评分权重 |
| `tech-digest-agent/agent.py` | 主入口，串联所有模块，CLI 参数解析 |
| `tech-digest-agent/fetcher.py` | 并发抓取RSS，返回 Dict[str, List[FeedItem]] |
| `tech-digest-agent/deduplicator.py` | URL去重 + 标题相似度去重 + 标题党过滤 |
| `tech-digest-agent/ranker.py` | 每源 freshness+keyword 评分，取 Top5 |
| `tech-digest-agent/classifier.py` | 关键词规则四维度分类 |
| `tech-digest-agent/summarizer.py` | 构造 Prompt，打印到终端 |
| `tech-digest-agent/writer.py` | 渲染 Markdown，写入 output/ 双份文件 |
| `tech-digest-agent/requirements.txt` | 依赖列表 |
| `tech-digest-agent/output/` | 输出目录（.gitkeep） |

---

## Task 1: 项目骨架 + config.yaml + requirements.txt

**Files:**
- Create: `tech-digest-agent/config.yaml`
- Create: `tech-digest-agent/requirements.txt`
- Create: `tech-digest-agent/output/.gitkeep`

- [ ] **Step 1: 创建项目目录结构**

```bash
mkdir -p tech-digest-agent/output
touch tech-digest-agent/output/.gitkeep
```

- [ ] **Step 2: 创建 requirements.txt**

内容如下（写入 `tech-digest-agent/requirements.txt`）：

```
feedparser>=6.0.11
requests>=2.28.0
scikit-learn>=1.3.0
pyyaml>=6.0
```

- [ ] **Step 3: 创建 config.yaml**

内容如下（写入 `tech-digest-agent/config.yaml`）：

```yaml
# RSS 数据源配置（新增源只需在此添加一项）
sources:
  - name: zhihu
    display_name: "知乎热榜"
    url: "https://decemberpei.cyou/rssbox/zhihu.xml"
    language: zh
  - name: github
    display_name: "GitHub Trending"
    url: "https://mshibanami.github.io/GitHubTrendingRSS/daily/all.xml"
    language: en
  - name: v2ex
    display_name: "V2EX 技术"
    url: "https://rsshub.liumingye.cn/v2ex/tab/tech"
    language: zh
  - name: hackernews
    display_name: "Hacker News Best"
    url: "https://rsshub.liumingye.cn/hackernews/best"
    language: en

# 每源取 Top N 条
top_n_per_source: 5

# 标题党过滤关键词（命中则丢弃该条目）
filter_keywords:
  - 震惊
  - 不敢相信
  - 颠覆认知
  - 看完沉默
  - 求扩散
  - 广告
  - 推广
  - 转发
  - 速看

# 去重相似度阈值（0~1，越高越严格）
dedup_threshold: 0.85

# 四维度分类关键词
categories:
  AI与大模型:
    emoji: "🤖"
    keywords:
      - GPT
      - Claude
      - LLM
      - 大模型
      - 推理
      - fine-tune
      - RAG
      - embedding
      - Ollama
      - Gemini
      - 智谱
      - 通义
      - 文心
      - transformer
      - diffusion
      - 人工智能
      - AI
      - 机器学习
      - 深度学习
      - neural
      - model
  前端与全栈:
    emoji: "💻"
    keywords:
      - React
      - Vue
      - Next.js
      - TypeScript
      - CSS
      - Tailwind
      - Vite
      - Node.js
      - Bun
      - Deno
      - WebAssembly
      - 前端
      - 全栈
      - web
      - JavaScript
      - HTML
      - webpack
      - rollup
      - svelte
      - nuxt
  开源新锐:
    emoji: "🌟"
    keywords:
      - GitHub
      - open source
      - 开源
      - star
      - release
      - fork
      - CLI
      - rust
      - Rust
      - golang
      - Go
      - python
      - library
      - framework
      - repo
      - repository
      - v2
      - v3
      - MIT
      - Apache
  行业吃瓜:
    emoji: "🍿"
    keywords:
      - 裁员
      - 融资
      - 收购
      - 上市
      - 争议
      - 维权
      - 倒闭
      - lawsuit
      - fired
      - layoff
      - drama
      - controversy
      - 大厂
      - 诉讼
      - 罚款
      - 封禁
      - 下架
      - 抄袭

# 评分权重
scoring:
  freshness_weight: 0.6   # 新鲜度权重
  keyword_weight: 0.4     # 关键词加分权重
  keyword_bonus_per_hit: 0.1  # 每命中一个核心词加分
  freshness_max_hours: 48     # 超过此小时数新鲜度为0

# 核心科技关键词（用于 keyword_bonus 加分）
tech_keywords:
  - AI
  - 开源
  - GitHub
  - Python
  - Rust
  - Go
  - React
  - TypeScript
  - LLM
  - GPU
  - 大模型
  - cloud
  - API
  - framework
  - performance
  - security
  - database
  - kubernetes
  - docker
  - linux
```

- [ ] **Step 4: 提交骨架**

```bash
cd tech-digest-agent
git add config.yaml requirements.txt output/.gitkeep
git commit -m "feat: add project scaffold, config.yaml and requirements.txt"
```

---

## Task 2: FeedItem 数据模型 + fetcher.py

**Files:**
- Create: `tech-digest-agent/fetcher.py`

- [ ] **Step 1: 安装依赖**

```bash
cd tech-digest-agent
pip install -r requirements.txt
```

- [ ] **Step 2: 创建 fetcher.py**

写入 `tech-digest-agent/fetcher.py`：

```python
"""
fetcher.py — 并发抓取 RSS 数据源，返回按源分组的 FeedItem 列表
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
import time

import feedparser
import requests

logger = logging.getLogger(__name__)


@dataclass
class FeedItem:
    title: str
    url: str
    summary: str
    published: datetime
    source: str          # 源的 name（如 zhihu / github）
    score: float = 0.0   # 由 ranker 填充
    category: str = ""   # 由 classifier 填充


def _parse_published(entry: feedparser.FeedParserDict) -> datetime:
    """将 feedparser 的时间结构转为 timezone-aware datetime（UTC）"""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        t = entry.published_parsed
        return datetime(*t[:6], tzinfo=timezone.utc)
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        t = entry.updated_parsed
        return datetime(*t[:6], tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


def _fetch_one(source: dict, timeout: int = 10) -> tuple[str, List[FeedItem]]:
    """抓取单个 RSS 源，返回 (source_name, items)"""
    name = source["name"]
    url = source["url"]
    items: List[FeedItem] = []

    try:
        # feedparser 内部使用 urllib，这里手动用 requests 获取内容以支持超时
        resp = requests.get(url, timeout=timeout, headers={
            "User-Agent": "TechDigestAgent/1.0 (+https://github.com/digest-agent)"
        })
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)

        for entry in feed.entries:
            title = getattr(entry, "title", "").strip()
            link = getattr(entry, "link", "").strip()
            summary = getattr(entry, "summary", "").strip()

            if not title or not link:
                continue

            items.append(FeedItem(
                title=title,
                url=link,
                summary=summary[:500],  # 截断过长摘要
                published=_parse_published(entry),
                source=name,
            ))

        logger.info(f"[{name}] 抓取成功，共 {len(items)} 条")
    except Exception as e:
        logger.warning(f"[{name}] 抓取失败：{e}")

    return name, items


def fetch_all(sources: list, timeout: int = 10, max_workers: int = 4) -> Dict[str, List[FeedItem]]:
    """
    并发抓取所有 RSS 源。

    Args:
        sources: config.yaml 中的 sources 列表
        timeout: 单个请求超时秒数
        max_workers: 并发线程数

    Returns:
        Dict[str, List[FeedItem]]，key 为 source.name
    """
    results: Dict[str, List[FeedItem]] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(_fetch_one, src, timeout): src["name"]
            for src in sources
        }
        for future in as_completed(future_map):
            name, items = future.result()
            results[name] = items

    return results
```

- [ ] **Step 3: 快速验证抓取（直接运行）**

```bash
cd tech-digest-agent
python -c "
import yaml, logging, json
from fetcher import fetch_all
logging.basicConfig(level=logging.INFO)
with open('config.yaml') as f:
    cfg = yaml.safe_load(f)
results = fetch_all(cfg['sources'])
for src, items in results.items():
    print(f'{src}: {len(items)} 条')
    if items:
        print(f'  第一条: {items[0].title[:60]}')
"
```

预期输出（各源条目数大于0）：
```
INFO:fetcher:[zhihu] 抓取成功，共 N 条
INFO:fetcher:[github] 抓取成功，共 N 条
...
zhihu: N 条
github: N 条
```

- [ ] **Step 4: 提交**

```bash
git add fetcher.py
git commit -m "feat: add fetcher with concurrent RSS fetch and FeedItem dataclass"
```

---

## Task 3: deduplicator.py（去重 + 标题党过滤）

**Files:**
- Create: `tech-digest-agent/deduplicator.py`

- [ ] **Step 1: 创建 deduplicator.py**

写入 `tech-digest-agent/deduplicator.py`：

```python
"""
deduplicator.py — 去重与过滤
1. URL 精确去重（同源内）
2. 标题余弦相似度去重（TF-IDF，阈值可配）
3. 标题党关键词过滤
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from fetcher import FeedItem

logger = logging.getLogger(__name__)


def _url_deduplicate(items: List[FeedItem]) -> List[FeedItem]:
    """URL 精确去重，保留第一次出现的条目"""
    seen_urls: set = set()
    result = []
    for item in items:
        normalized = item.url.rstrip("/").split("?")[0]  # 去掉 query string
        if normalized not in seen_urls:
            seen_urls.add(normalized)
            result.append(item)
    return result


def _title_deduplicate(items: List[FeedItem], threshold: float = 0.85) -> List[FeedItem]:
    """
    标题余弦相似度去重。
    threshold: 相似度超过此值认为是重复，保留评分较高的一条（默认保留第一条）。
    """
    if len(items) <= 1:
        return items

    titles = [item.title for item in items]

    try:
        vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 3))
        tfidf_matrix = vectorizer.fit_transform(titles)
        sim_matrix = cosine_similarity(tfidf_matrix)
    except ValueError:
        # 标题全空等极端情况
        return items

    keep = [True] * len(items)
    for i in range(len(items)):
        if not keep[i]:
            continue
        for j in range(i + 1, len(items)):
            if keep[j] and sim_matrix[i][j] >= threshold:
                keep[j] = False  # 保留 i，丢弃 j

    result = [item for item, k in zip(items, keep) if k]
    removed = len(items) - len(result)
    if removed:
        logger.debug(f"标题相似度去重：移除 {removed} 条")
    return result


def _filter_clickbait(items: List[FeedItem], filter_keywords: List[str]) -> List[FeedItem]:
    """过滤标题包含标题党关键词的条目"""
    if not filter_keywords:
        return items

    pattern = re.compile("|".join(re.escape(kw) for kw in filter_keywords), re.IGNORECASE)
    result = []
    for item in items:
        if pattern.search(item.title):
            logger.debug(f"过滤标题党：{item.title[:50]}")
        else:
            result.append(item)
    return result


def deduplicate_and_filter(
    source_items: Dict[str, List[FeedItem]],
    filter_keywords: List[str],
    threshold: float = 0.85,
) -> Dict[str, List[FeedItem]]:
    """
    对每个源独立执行：URL去重 → 标题去重 → 标题党过滤

    Args:
        source_items: fetch_all 返回的按源分组数据
        filter_keywords: 标题党黑名单关键词
        threshold: 标题相似度去重阈值

    Returns:
        同结构，每源去重过滤后的 FeedItem 列表
    """
    result: Dict[str, List[FeedItem]] = {}
    for source, items in source_items.items():
        before = len(items)
        items = _url_deduplicate(items)
        items = _title_deduplicate(items, threshold)
        items = _filter_clickbait(items, filter_keywords)
        after = len(items)
        logger.info(f"[{source}] 去重过滤：{before} → {after} 条")
        result[source] = items
    return result
```

- [ ] **Step 2: 验证去重逻辑**

```bash
cd tech-digest-agent
python -c "
from fetcher import FeedItem
from deduplicator import deduplicate_and_filter
from datetime import datetime, timezone

now = datetime.now(timezone.utc)
items = [
    FeedItem('GPT-5 发布了', 'https://a.com/1', '', now, 'test'),
    FeedItem('GPT-5 发布了', 'https://a.com/1', '', now, 'test'),  # 完全重复
    FeedItem('GPT-5 正式发布', 'https://a.com/2', '', now, 'test'),  # 高相似
    FeedItem('震惊！GPT-5发布', 'https://a.com/3', '', now, 'test'),  # 标题党
    FeedItem('React 19 新特性介绍', 'https://b.com/1', '', now, 'test'),
]
result = deduplicate_and_filter(
    {'test': items},
    filter_keywords=['震惊'],
    threshold=0.85
)
print(f'去重后剩余: {len(result[\"test\"])} 条')
for i in result['test']:
    print(f'  - {i.title}')
"
```

预期输出：
```
去重后剩余: 2 条
  - GPT-5 发布了
  - React 19 新特性介绍
```

- [ ] **Step 3: 提交**

```bash
git add deduplicator.py
git commit -m "feat: add deduplicator with URL dedup, TF-IDF title dedup, clickbait filter"
```

---

## Task 4: ranker.py（每源 Top5 评分）

**Files:**
- Create: `tech-digest-agent/ranker.py`

- [ ] **Step 1: 创建 ranker.py**

写入 `tech-digest-agent/ranker.py`：

```python
"""
ranker.py — 对每源条目评分，取 Top N
评分 = freshness_score * freshness_weight + keyword_bonus * keyword_weight
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Dict, List

from fetcher import FeedItem

logger = logging.getLogger(__name__)


def _freshness_score(published: datetime, max_hours: float = 48.0) -> float:
    """
    新鲜度分：0h内=1.0，max_hours外=0.0，线性衰减。
    """
    now = datetime.now(timezone.utc)
    # 确保 published 有时区信息
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    age_hours = (now - published).total_seconds() / 3600
    if age_hours <= 0:
        return 1.0
    if age_hours >= max_hours:
        return 0.0
    return 1.0 - (age_hours / max_hours)


def _keyword_bonus(text: str, tech_keywords: List[str], bonus_per_hit: float = 0.1) -> float:
    """命中科技关键词每个加 bonus_per_hit，上限 1.0"""
    hits = sum(1 for kw in tech_keywords if kw.lower() in text.lower())
    return min(hits * bonus_per_hit, 1.0)


def rank_and_select(
    source_items: Dict[str, List[FeedItem]],
    tech_keywords: List[str],
    top_n: int = 5,
    freshness_weight: float = 0.6,
    keyword_weight: float = 0.4,
    keyword_bonus_per_hit: float = 0.1,
    freshness_max_hours: float = 48.0,
) -> Dict[str, List[FeedItem]]:
    """
    对每源独立评分，返回每源 Top N 条目（score 已填充）。

    Args:
        source_items: 去重过滤后的按源条目
        tech_keywords: config.yaml 中的 tech_keywords 列表
        top_n: 每源取多少条
        freshness_weight: 新鲜度权重
        keyword_weight: 关键词加分权重
        keyword_bonus_per_hit: 每命中一个关键词的加分
        freshness_max_hours: 超过此小时数新鲜度为0

    Returns:
        每源 Top N 的 FeedItem 列表（score 已填充）
    """
    result: Dict[str, List[FeedItem]] = {}

    for source, items in source_items.items():
        for item in items:
            text = item.title + " " + item.summary
            fs = _freshness_score(item.published, freshness_max_hours)
            kb = _keyword_bonus(text, tech_keywords, keyword_bonus_per_hit)
            item.score = freshness_weight * fs + keyword_weight * kb

        ranked = sorted(items, key=lambda x: x.score, reverse=True)
        selected = ranked[:top_n]
        logger.info(f"[{source}] 评分完成，Top{top_n} 最高分: "
                    f"{selected[0].score:.2f} 最低分: {selected[-1].score:.2f}"
                    if selected else f"[{source}] 无条目")
        result[source] = selected

    return result
```

- [ ] **Step 2: 验证评分逻辑**

```bash
cd tech-digest-agent
python -c "
from fetcher import FeedItem
from ranker import rank_and_select
from datetime import datetime, timezone, timedelta

now = datetime.now(timezone.utc)
items = [
    FeedItem('GPT-5 发布', 'https://a.com/1', 'AI LLM', now - timedelta(hours=1), 'test'),
    FeedItem('老新闻', 'https://a.com/2', '', now - timedelta(hours=50), 'test'),
    FeedItem('React 19 新特性', 'https://a.com/3', 'web frontend', now - timedelta(hours=5), 'test'),
    FeedItem('Rust 2024', 'https://a.com/4', 'GitHub open source', now - timedelta(hours=2), 'test'),
    FeedItem('普通文章', 'https://a.com/5', '', now - timedelta(hours=10), 'test'),
    FeedItem('另一文章', 'https://a.com/6', '', now - timedelta(hours=12), 'test'),
]
result = rank_and_select(
    {'test': items},
    tech_keywords=['AI', 'LLM', 'React', 'Rust', 'GitHub', 'open source'],
    top_n=3
)
for item in result['test']:
    print(f'score={item.score:.2f} | {item.title}')
"
```

预期输出（GPT-5 和 Rust 2024 应排前列，老新闻垫底被截断）：
```
score=... | GPT-5 发布
score=... | Rust 2024
score=... | React 19 新特性
```

- [ ] **Step 3: 提交**

```bash
git add ranker.py
git commit -m "feat: add ranker with freshness + keyword scoring, top-N selection per source"
```

---

## Task 5: classifier.py（四维度关键词分类）

**Files:**
- Create: `tech-digest-agent/classifier.py`

- [ ] **Step 1: 创建 classifier.py**

写入 `tech-digest-agent/classifier.py`：

```python
"""
classifier.py — 将 FeedItem 按四维度关键词规则分类
每条目的 title + summary 与各维度关键词匹配，取命中最多的维度
"""

from __future__ import annotations

import logging
from typing import Dict, List

from fetcher import FeedItem

logger = logging.getLogger(__name__)


def classify_items(
    source_items: Dict[str, List[FeedItem]],
    categories: Dict[str, dict],
) -> Dict[str, List[FeedItem]]:
    """
    为每个 FeedItem 填充 category 字段。

    Args:
        source_items: rank_and_select 返回的按源条目
        categories: config.yaml 中的 categories 字典，结构为：
            { "AI与大模型": { "emoji": "🤖", "keywords": [...] }, ... }

    Returns:
        同结构，每条目的 category 已填充
    """
    category_names = list(categories.keys())

    for source, items in source_items.items():
        for item in items:
            text = (item.title + " " + item.summary).lower()
            scores = {}
            for cat_name, cat_cfg in categories.items():
                hits = sum(
                    1 for kw in cat_cfg.get("keywords", [])
                    if kw.lower() in text
                )
                scores[cat_name] = hits

            # 取命中最多的维度；全部为0时取第一个作为兜底
            best_cat = max(scores, key=lambda k: scores[k])
            if scores[best_cat] == 0:
                best_cat = category_names[0]

            item.category = best_cat
            logger.debug(f"[{item.source}] '{item.title[:40]}' → {item.category}")

    return source_items


def group_by_category(
    source_items: Dict[str, List[FeedItem]],
) -> Dict[str, List[FeedItem]]:
    """
    将按源分组的条目重新按 category 分组，用于摘要和输出。

    Returns:
        Dict[category_name, List[FeedItem]]
    """
    result: Dict[str, List[FeedItem]] = {}
    for items in source_items.values():
        for item in items:
            result.setdefault(item.category, []).append(item)
    return result
```

- [ ] **Step 2: 验证分类逻辑**

```bash
cd tech-digest-agent
python -c "
import yaml
from fetcher import FeedItem
from classifier import classify_items, group_by_category
from datetime import datetime, timezone

with open('config.yaml') as f:
    cfg = yaml.safe_load(f)

now = datetime.now(timezone.utc)
items = {
    'test': [
        FeedItem('GPT-5 大模型推理加速', 'https://a.com/1', 'LLM AI', now, 'test'),
        FeedItem('React 19 Compiler 详解', 'https://a.com/2', 'frontend web', now, 'test'),
        FeedItem('Rust 开源新项目 star 暴增', 'https://a.com/3', 'GitHub open source', now, 'test'),
        FeedItem('某大厂裁员 1000 人', 'https://a.com/4', 'layoff drama', now, 'test'),
    ]
}
result = classify_items(items, cfg['categories'])
by_cat = group_by_category(result)
for cat, cat_items in by_cat.items():
    print(f'{cat}: {[i.title[:30] for i in cat_items]}')
"
```

预期输出：
```
AI与大模型: ['GPT-5 大模型推理加速']
前端与全栈: ['React 19 Compiler 详解']
开源新锐: ['Rust 开源新项目 star 暴增']
行业吃瓜: ['某大厂裁员 1000 人']
```

- [ ] **Step 3: 提交**

```bash
git add classifier.py
git commit -m "feat: add classifier with keyword-based four-category classification"
```

---

## Task 6: summarizer.py（Prompt 构造）

**Files:**
- Create: `tech-digest-agent/summarizer.py`

- [ ] **Step 1: 创建 summarizer.py**

写入 `tech-digest-agent/summarizer.py`：

```python
"""
summarizer.py — 构造结构化 Prompt，打印到终端供运行环境 AI 接管生成摘要
不调用外部 API，利用 Claude Code / Codex 自身上下文能力
"""

from __future__ import annotations

from typing import Dict, List

from fetcher import FeedItem


def build_prompt(
    category_items: Dict[str, List[FeedItem]],
    categories_cfg: Dict[str, dict],
) -> str:
    """
    构造给运行环境 AI 的摘要 Prompt。

    Args:
        category_items: group_by_category 返回的按维度分组条目
        categories_cfg: config.yaml 中的 categories，含 emoji 信息

    Returns:
        完整 Prompt 字符串
    """
    lines = []
    lines.append("你是一个科技媒体编辑，请基于以下今日收集的科技资讯，生成一份有观点的摘要报告。")
    lines.append("")
    lines.append("## 要求")
    lines.append("- 按四个维度分别总结：AI与大模型、前端与全栈、开源新锐、行业吃瓜")
    lines.append("- 每个维度写 2~3 句有观点的总结，不要只复述标题，要提炼趋势和判断")
    lines.append("- 如果某条目来自知乎（source=zhihu），请尝试提炼其中可能存在的'反驳观点'或'争议视角'")
    lines.append("- 语气：犀利、有态度，像科技媒体编辑而不是机器人")
    lines.append("- 输出格式：直接输出 Markdown，每个维度用三级标题（###）")
    lines.append("")
    lines.append("## 今日数据")
    lines.append("")

    for cat_name, cfg in categories_cfg.items():
        emoji = cfg.get("emoji", "")
        items = category_items.get(cat_name, [])
        lines.append(f"### {emoji} {cat_name}（{len(items)} 条）")
        if not items:
            lines.append("_本维度今日暂无相关内容_")
        else:
            for i, item in enumerate(items, 1):
                source_label = f"[来源:{item.source}]"
                summary_snippet = item.summary[:200].replace("\n", " ") if item.summary else "（无摘要）"
                lines.append(f"{i}. **{item.title}** {source_label}")
                lines.append(f"   链接：{item.url}")
                lines.append(f"   摘要：{summary_snippet}")
        lines.append("")

    lines.append("## 输出格式")
    lines.append("请直接输出以下结构的 Markdown，不要有任何额外解释：")
    lines.append("")
    lines.append("### 🤖 AI 与大模型")
    lines.append("[2~3句有观点的总结]")
    lines.append("")
    lines.append("### 💻 前端与全栈")
    lines.append("[2~3句有观点的总结]")
    lines.append("")
    lines.append("### 🌟 开源新锐")
    lines.append("[2~3句有观点的总结]")
    lines.append("")
    lines.append("### 🍿 行业吃瓜")
    lines.append("[2~3句有观点的总结]")

    return "\n".join(lines)


def print_prompt_and_get_summary(
    category_items: Dict[str, List[FeedItem]],
    categories_cfg: Dict[str, dict],
) -> str:
    """
    打印 Prompt 到终端，并等待运行环境 AI 响应。
    在 Claude Code / Codex 中，AI 会读取此 Prompt 并生成摘要。
    此函数返回一个占位符，writer.py 会用 AI 的实际输出替换。

    Returns:
        Prompt 字符串（同时也是写入 MD 的 AI 摘要区域占位内容）
    """
    prompt = build_prompt(category_items, categories_cfg)

    print("\n" + "="*60)
    print("📋 AI 摘要 Prompt（请将以下内容提交给 AI 生成摘要）")
    print("="*60)
    print(prompt)
    print("="*60 + "\n")

    return prompt
```

- [ ] **Step 2: 验证 Prompt 输出格式**

```bash
cd tech-digest-agent
python -c "
import yaml
from fetcher import FeedItem
from summarizer import build_prompt
from datetime import datetime, timezone

with open('config.yaml') as f:
    cfg = yaml.safe_load(f)

now = datetime.now(timezone.utc)
category_items = {
    'AI与大模型': [FeedItem('GPT-5发布', 'https://openai.com', 'LLM推理加速', now, 'hackernews')],
    '前端与全栈': [FeedItem('React 19正式版', 'https://react.dev', 'React compiler', now, 'github')],
    '开源新锐': [],
    '行业吃瓜': [FeedItem('某厂裁员', 'https://zhihu.com/x', '大规模裁员', now, 'zhihu')],
}
prompt = build_prompt(category_items, cfg['categories'])
print(prompt[:800])
print('...(截断)')
"
```

预期：打印出结构完整的 Prompt，包含各维度条目信息。

- [ ] **Step 3: 提交**

```bash
git add summarizer.py
git commit -m "feat: add summarizer that builds structured prompt for AI summarization"
```

---

## Task 7: writer.py（Markdown 文档输出）

**Files:**
- Create: `tech-digest-agent/writer.py`

- [ ] **Step 1: 创建 writer.py**

写入 `tech-digest-agent/writer.py`：

```python
"""
writer.py — 将条目数据 + AI 摘要渲染为 Markdown，写入双份文件
"""

from __future__ import annotations

import logging
import os
import shutil
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fetcher import FeedItem

logger = logging.getLogger(__name__)

SOURCE_EMOJI = {
    "zhihu": "🔵",
    "github": "🟢",
    "v2ex": "🟡",
    "hackernews": "🔴",
}


def _render_source_section(
    source_name: str,
    display_name: str,
    items: List[FeedItem],
) -> str:
    """渲染单个源的 Top5 条目为 Markdown"""
    emoji = SOURCE_EMOJI.get(source_name, "⚪")
    lines = [f"### {emoji} {display_name} Top {len(items)}"]
    lines.append("")
    if not items:
        lines.append("_今日暂无数据_")
    else:
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. **[{item.title}]({item.url})**")
            if item.summary:
                snippet = item.summary[:150].replace("\n", " ")
                lines.append(f"   > {snippet}...")
            pub_str = item.published.strftime("%H:%M UTC") if item.published else ""
            lines.append(f"   _发布时间：{pub_str} | 评分：{item.score:.2f}_")
            lines.append("")
    return "\n".join(lines)


def _render_document(
    source_items: Dict[str, List[FeedItem]],
    sources_cfg: list,
    ai_summary: str,
    date_str: str,
) -> str:
    """渲染完整 Markdown 文档"""
    lines = []

    # 文档头
    lines.append(f"# 每日科技信息摘要 · {date_str}")
    lines.append("")
    lines.append("> 数据来源：知乎 / GitHub Trending / V2EX / Hacker News  ")
    lines.append(f"> 生成时间：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 按信息源分类
    lines.append("## 📋 按信息源浏览")
    lines.append("")
    for src_cfg in sources_cfg:
        name = src_cfg["name"]
        display = src_cfg.get("display_name", name)
        items = source_items.get(name, [])
        lines.append(_render_source_section(name, display, items))
        lines.append("")

    lines.append("---")
    lines.append("")

    # AI 维度总结
    lines.append("## 🧠 AI 维度总结")
    lines.append("")
    lines.append(ai_summary)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("_本文档由 Tech Digest Agent v1.0 自动生成_")

    return "\n".join(lines)


def write_digest(
    source_items: Dict[str, List[FeedItem]],
    sources_cfg: list,
    ai_summary: str,
    output_dir: str = "output",
) -> tuple[str, str]:
    """
    生成双份 Markdown 文件。

    Returns:
        (dated_path, latest_path) 两个文件的路径
    """
    os.makedirs(output_dir, exist_ok=True)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    content = _render_document(source_items, sources_cfg, ai_summary, date_str)

    dated_path = os.path.join(output_dir, f"{date_str}-tech-digest.md")
    latest_path = os.path.join(output_dir, "latest-digest.md")

    with open(dated_path, "w", encoding="utf-8") as f:
        f.write(content)

    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"文档已生成：{dated_path}")
    logger.info(f"文档已生成：{latest_path}")

    return dated_path, latest_path
```

- [ ] **Step 2: 验证文档渲染**

```bash
cd tech-digest-agent
python -c "
import yaml
from fetcher import FeedItem
from writer import write_digest
from datetime import datetime, timezone

with open('config.yaml') as f:
    cfg = yaml.safe_load(f)

now = datetime.now(timezone.utc)
source_items = {
    'zhihu': [FeedItem('知乎热门：GPT-5来了', 'https://zhihu.com/1', '讨论大模型', now, 'zhihu', score=0.85)],
    'github': [FeedItem('rust-lang/rust v2024', 'https://github.com/rust', 'Rust新版本', now, 'github', score=0.90)],
    'v2ex': [],
    'hackernews': [FeedItem('Ask HN: Best LLM tools', 'https://hn.com/1', 'LLM tools', now, 'hackernews', score=0.75)],
}
ai_summary = '''### 🤖 AI 与大模型\nGPT-5 的到来再次搅动市场，但社区的冷静值得关注。\n\n### 💻 前端与全栈\n暂无数据。\n\n### 🌟 开源新锐\nRust 2024 edition 持续领跑系统编程领域。\n\n### 🍿 行业吃瓜\n暂无数据。'''
dated, latest = write_digest(source_items, cfg['sources'], ai_summary, output_dir='output')
print(f'生成文件: {dated}')
print(f'生成文件: {latest}')
import os; print(open(dated).read()[:500])
"
```

预期：输出文件路径，并打印 MD 文档前500字符。

- [ ] **Step 3: 提交**

```bash
git add writer.py
git commit -m "feat: add writer that renders dual Markdown output files"
```

---

## Task 8: agent.py（主入口串联）

**Files:**
- Create: `tech-digest-agent/agent.py`

- [ ] **Step 1: 创建 agent.py**

写入 `tech-digest-agent/agent.py`：

```python
"""
agent.py — 每日科技信息收集与摘要 Agent 主入口

用法：
    python agent.py
    python agent.py --output-dir ./my-output
    python agent.py --config ./my-config.yaml
    python agent.py --top-n 10
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import yaml

from fetcher import fetch_all
from deduplicator import deduplicate_and_filter
from ranker import rank_and_select
from classifier import classify_items, group_by_category
from summarizer import print_prompt_and_get_summary
from writer import write_digest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run(config_path: str, output_dir: str, top_n: int) -> None:
    cfg = load_config(config_path)

    # 覆盖 top_n（命令行参数优先）
    if top_n:
        cfg["top_n_per_source"] = top_n

    print("\n🚀 Tech Digest Agent 启动")
    print(f"   配置文件: {config_path}")
    print(f"   输出目录: {output_dir}")
    print(f"   每源取Top: {cfg['top_n_per_source']} 条\n")

    # Step 1: 抓取
    print("📡 [1/5] 抓取 RSS 数据源...")
    source_items = fetch_all(cfg["sources"])
    total = sum(len(v) for v in source_items.values())
    print(f"   共抓取 {total} 条原始条目\n")

    # Step 2: 去重过滤
    print("🔍 [2/5] 去重与过滤...")
    source_items = deduplicate_and_filter(
        source_items,
        filter_keywords=cfg.get("filter_keywords", []),
        threshold=cfg.get("dedup_threshold", 0.85),
    )
    total_after = sum(len(v) for v in source_items.values())
    print(f"   去重过滤后剩余 {total_after} 条\n")

    # Step 3: 评分排名
    print("📊 [3/5] 评分排名，每源取 Top {n}...".format(n=cfg["top_n_per_source"]))
    scoring = cfg.get("scoring", {})
    source_items = rank_and_select(
        source_items,
        tech_keywords=cfg.get("tech_keywords", []),
        top_n=cfg["top_n_per_source"],
        freshness_weight=scoring.get("freshness_weight", 0.6),
        keyword_weight=scoring.get("keyword_weight", 0.4),
        keyword_bonus_per_hit=scoring.get("keyword_bonus_per_hit", 0.1),
        freshness_max_hours=scoring.get("freshness_max_hours", 48.0),
    )
    selected_total = sum(len(v) for v in source_items.values())
    print(f"   最终选取 {selected_total} 条\n")

    # Step 4: 分类
    print("🏷️  [4/5] 四维度分类...")
    source_items = classify_items(source_items, cfg["categories"])
    category_items = group_by_category(source_items)
    for cat, items in category_items.items():
        print(f"   {cat}: {len(items)} 条")
    print()

    # Step 5: 构造 Prompt（运行环境 AI 接管生成摘要）
    print("✍️  [5/5] 构造 AI 摘要 Prompt...")
    ai_summary = print_prompt_and_get_summary(category_items, cfg["categories"])

    # Step 6: 输出文档
    print("📝 生成 Markdown 文档...")
    dated_path, latest_path = write_digest(
        source_items,
        cfg["sources"],
        ai_summary,
        output_dir=output_dir,
    )

    print(f"\n✅ 完成！文档已生成：")
    print(f"   📄 {dated_path}")
    print(f"   📄 {latest_path}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="每日科技信息收集与摘要 Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python agent.py
  python agent.py --output-dir ./reports
  python agent.py --top-n 10
  python agent.py --config ./my-config.yaml
        """
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="配置文件路径（默认：config.yaml）"
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="输出目录（默认：output/）"
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=None,
        help="每源取 Top N 条（默认：config.yaml 中的 top_n_per_source）"
    )

    args = parser.parse_args()

    config_path = args.config
    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在：{config_path}")
        sys.exit(1)

    run(
        config_path=config_path,
        output_dir=args.output_dir,
        top_n=args.top_n,
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 端到端运行测试**

```bash
cd tech-digest-agent
python agent.py
```

预期输出流程：
```
🚀 Tech Digest Agent 启动
📡 [1/5] 抓取 RSS 数据源...
🔍 [2/5] 去重与过滤...
📊 [3/5] 评分排名...
🏷️  [4/5] 四维度分类...
✍️  [5/5] 构造 AI 摘要 Prompt...
============================
📋 AI 摘要 Prompt...
============================
📝 生成 Markdown 文档...
✅ 完成！文档已生成：
   📄 output/2026-04-15-tech-digest.md
   📄 output/latest-digest.md
```

- [ ] **Step 3: 验证输出文件结构**

```bash
cd tech-digest-agent
head -50 output/latest-digest.md
```

预期：文档头部包含日期、数据来源说明、按信息源分类的条目列表。

- [ ] **Step 4: 最终提交**

```bash
git add agent.py
git commit -m "feat: add agent.py main entrypoint, complete end-to-end pipeline"
```

---

## 自检清单

- [ ] `python agent.py` 能正常运行，无报错
- [ ] `output/` 目录下生成两份 MD 文件
- [ ] 四个 RSS 源每个至少有1条条目（网络正常时）
- [ ] MD 文档包含「按信息源」和「AI 维度总结」两个大节
- [ ] 新增 RSS 源只需修改 `config.yaml`，无需改代码
