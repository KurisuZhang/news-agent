---
name: tech-digest
description: 每日科技信息摘要工作流。
disable-model-invocation: true
---

# Tech Digest Skill

## 执行步骤

### Step 1：运行 Python 管道

在项目根目录下执行：

```bash
cd .claude/skills/tech-digest && python agent.py
```

运行完毕后，终端输出中会包含一段以 `====` 包围的 Prompt，内含按两个维度（科技技术、实时新闻）分组的当日条目列表。

### Step 2：生成 AI 维度总结

直接根据终端输出的条目列表，以**科技媒体主编**视角，为每个维度生成 2~3 句有观点、有态度的中文总结：

- 🔬 科技技术：关注 AI/Agent 工具实践、开源框架动态、工程化趋势
- 📰 实时新闻：关注大厂动态、商业争议、资本事件，知乎条目提炼高赞反驳意见

### Step 3：将摘要写入输出文件

**必须在 Step 4 之前完成，不得留占位符。**

使用 Edit 工具读取并修改 `.claude/skills/tech-digest/output/latest-digest.md`：
- 将 `## 🧠 AI 维度总结` 下方从 `<!-- AI 摘要` 开头到第一个 `_[摘要待生成` 结尾的整段占位符，替换为 Step 2 生成的摘要内容。
- 再用 `cp` 或直接写入，将同样内容同步到归档文件 `.claude/skills/tech-digest/output/YYYY-MM-DD-tech-digest.md`（YYYY-MM-DD 为当天日期）。

### Step 4：告知用户

输出以下信息：
- 本次抓取条目总数
- 输出文件路径
- 各维度一句话概述
