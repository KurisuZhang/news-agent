# 每日科技信息收集与摘要 Agent — 设计文档

**日期：** 2026-04-15  
**状态：** 已确认，待实现

---

## 1. 目标

构建一个可在 Claude Code / Codex 环境中一条命令运行的 Python Agent，自动抓取多个 RSS 源、去重过滤、评分排名、分类总结，最终输出一份结构化的每日科技摘要 Markdown 文档。

---

## 2. 数据源

通过 `config.yaml` 管理，可随时增删，无需改代码：

| 名称 | URL |
|------|-----|
| 知乎热榜 | https://decemberpei.cyou/rssbox/zhihu.xml |
| GitHub Trending | https://mshibanami.github.io/GitHubTrendingRSS/daily/all.xml |
| V2EX 技术 | https://rsshub.liumingye.cn/v2ex/tab/tech |
| Hacker News Best | https://rsshub.liumingye.cn/hackernews/best |

---

## 3. 整体数据流

```
config.yaml
     ↓
[Fetcher]        并发抓取所有 RSS Feed（feedparser + concurrent.futures）
     ↓
[Deduplicator]   同源内 URL 精确去重 + 标题余弦相似度去重 + 标题党关键词过滤
     ↓
[Ranker]         每源独立按 freshness_score + keyword_bonus 排序，各取 Top 5
     ↓
[Classifier]     按 config.yaml 关键词规则将每条目分配到4个维度
     ↓
[Summarizer]     构造结构化 Prompt，打印到终端供运行环境 AI 接管生成摘要
     ↓
[Writer]         将原始条目列表 + AI 摘要组合，输出双份 MD 文档
```

---

## 4. 文件结构

```
tech-digest-agent/
├── agent.py            # 主入口，串联所有模块
├── config.yaml         # RSS源 + 过滤词 + 分类关键词 + 评分权重
├── fetcher.py          # 并发抓取，返回 List[FeedItem]
├── deduplicator.py     # 去重 + 标题党过滤
├── ranker.py           # 每源 Top5 评分排序
├── classifier.py       # 四维度关键词分类
├── summarizer.py       # 构造 Prompt，输出给运行环境 AI
├── writer.py           # 渲染 Markdown 并写入文件
├── requirements.txt    # feedparser, requests, scikit-learn, pyyaml
└── output/             # 生成的 md 文件目录（git ignored）
```

---

## 5. 数据模型

```python
@dataclass
class FeedItem:
    title: str          # 条目标题
    url: str            # 原始链接
    summary: str        # 摘要文本（可为空）
    published: datetime # 发布时间
    source: str         # 来源名称（zhihu / github / v2ex / hackernews）
    score: float        # 评分（由 ranker 填充）
    category: str       # 分类（由 classifier 填充）
```

---

## 6. 各模块设计

### 6.1 fetcher.py

- 使用 `concurrent.futures.ThreadPoolExecutor` 并发抓取所有 RSS URL
- 每个 URL 超时设置 10s，失败时打印警告并跳过（不中断整体流程）
- 返回 `Dict[str, List[FeedItem]]`，key 为源名称

### 6.2 deduplicator.py

**两阶段去重：**
1. **URL 精确去重**：同源内对 `url` 字段做 set 去重
2. **标题相似度去重**：用 `sklearn` TF-IDF + 余弦相似度，阈值 0.85，同源内合并相似条目

**标题党过滤（关键词黑名单，config.yaml 可配置）：**
```yaml
filter_keywords:
  - 震惊
  - 不敢相信
  - 颠覆认知
  - 看完沉默
  - 求扩散
  - 广告
  - 推广
```

### 6.3 ranker.py

每源独立打分，公式：
```
score = freshness_score(pubDate) * 0.6 + keyword_bonus * 0.4
```

- `freshness_score`：24h 内满分 1.0，超过 48h 为 0.0，线性衰减
- `keyword_bonus`：命中科技核心关键词每个 +0.1，上限 1.0
- 每源按 score 降序取 Top 5

### 6.4 classifier.py

- 对每条 FeedItem 的 `title + summary` 匹配四个维度关键词
- 每个维度命中词数作为得分，取最高维度为主分类
- 无命中则归入得分最高的维度（兜底）

四个维度关键词（config.yaml 可扩展）：
- **AI与大模型**：GPT, Claude, LLM, 大模型, 推理, RAG, embedding, Ollama, Gemini 等
- **前端与全栈**：React, Vue, Next.js, TypeScript, CSS, Tailwind, Vite, Node.js 等
- **开源新锐**：GitHub, open source, 开源, star, release, rust, go, CLI 等
- **行业吃瓜**：裁员, 融资, 收购, 争议, lawsuit, layoff, drama, 大厂 等

### 6.5 summarizer.py

不调用外部 API。构造一段结构化 Prompt，打印到终端，由 Claude Code / Codex 运行环境的 AI 读取并生成摘要，摘要结果再由 `writer.py` 嵌入文档。

Prompt 包含：
- 角色设定（科技媒体编辑，犀利有态度）
- 按四维度分组的条目列表（标题 + 来源 + 链接 + 摘要片段）
- 对知乎条目要求提炼高赞反驳意见
- 每维度输出 2~3 句有观点的总结
- 输出格式要求（直接输出 Markdown）

### 6.6 writer.py

生成两份文件：
1. `output/YYYY-MM-DD-tech-digest.md`（日期归档）
2. `output/latest-digest.md`（始终覆盖）

**MD 文档结构：**
```markdown
# 每日科技信息摘要 · YYYY-MM-DD

> 数据来源：知乎 / GitHub Trending / V2EX / Hacker News

---

## 📋 按信息源

### 🔵 知乎 Top 5
### 🟢 GitHub Trending Top 5
### 🟡 V2EX Top 5
### 🔴 Hacker News Top 5

---

## 🧠 AI 维度总结

### 🤖 AI 与大模型
### 💻 前端与全栈
### 🌟 开源新锐
### 🍿 行业吃瓜

---
_生成时间：YYYY-MM-DD HH:MM | Agent 版本：1.0_
```

---

## 7. 依赖

```
feedparser>=6.0
requests>=2.28
scikit-learn>=1.3
pyyaml>=6.0
```

---

## 8. 运行方式

```bash
# 安装依赖
pip install -r requirements.txt

# 运行 Agent
python agent.py

# 指定输出目录（可选）
python agent.py --output-dir ./my-output
```

---

## 9. 错误处理策略

- RSS 抓取失败：打印警告，跳过该源，不中断流程
- 某源条目少于 5 条：取全部可用条目（不补充其他源）
- AI 摘要生成失败（运行环境无 AI）：`writer.py` 用条目原始摘要填充，标注"[摘要待生成]"

---

## 10. 扩展方式

新增 RSS 源只需在 `config.yaml` 的 `sources` 列表加一项：
```yaml
sources:
  - name: 新源名称
    url: https://example.com/feed.xml
    language: zh  # 或 en
```
