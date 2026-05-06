---
name: x-acquisition
description: |
  X (Twitter) 平台获客全技能
  功能：自动发帖 + 评论区获客
  基于 BrowserWing 实现浏览器自动化 + DeepSeek API 驱动 AI 内容生成
metadata:
  openclaw:
    emoji: "🐦"
    skillKey: "x-acquisition"
    requires:
      env: ["BROWSERWING_EXECUTOR_URL", "DEEPSEEK_API_KEY"]
    category: "acquisition"
    tags: ["x", "twitter", "acquisition", "publish", "comment", "browserwing", "ai"]
---

# X 平台获客技能 (x-acquisition)

AI 驱动的 X (Twitter) 获客全自动解决方案。两个核心能力：

## 功能矩阵

| 功能 | 说明 | 关联脚本 | BW 脚本 ID |
|------|------|----------|------------|
| 📝 自动发帖 | LLM 生成内容 → BW 自动发布 | `x_post.py` | `315acb7e-e73e-4af2-b351-575ce7065d9b` |
| 🎯 评论区获客 | 搜索 → AI评分 → LLM评论 → BW 评论 | `x_comment_acquisition.py` | `d38f7868-bf25-4943-8cc3-87bc48617c41`, `529333b7-d324-409b-8812-3285b3a12cd0` |

## 依赖

- Python 3.8+
- BrowserWing 服务（默认 `http://127.0.0.1:8080`）
- DeepSeek API Key（环境变量 `DEEPSEEK_API_KEY`）
- BrowserWing 注册脚本：
  - `315acb7e-e73e-4af2-b351-575ce7065d9b` — X 平台发帖
  - `d38f7868-bf25-4943-8cc3-87bc48617c41` — X 平台搜索帖子
  - `529333b7-d324-409b-8812-3285b3a12cd0` — X 平台评论

## 快速使用

```bash
# 测试模式（不实际发布）
python3 scripts/x_campaign.py --dry-run --post --product-url "https://example.com"

# 自动发帖
python3 scripts/x_campaign.py --post --product-url "https://example.com"

# 评论区获客
python3 scripts/x_campaign.py --acquire --product-url "https://example.com"

# 完整流程（发帖 + 获客）
python3 scripts/x_campaign.py --all --product-url "https://example.com"

# 指定关键词评论获客
python3 scripts/x_campaign.py --acquire --product-url "https://example.com" --keywords "AI,工具,效率"
```

## 文件结构

```
x-acquisition/
├── SKILL.md                     ← 本文
├── scripts/
│   ├── x_campaign.py            ← 统一编排入口
│   ├── x_post.py                ← 发帖模块
│   ├── x_comment_acquisition.py ← 评论区获客模块
│   └── x_llm.py                 ← LLM API 封装
├── bw-scripts/                  ← BrowserWing 脚本 (从BW下载的完整脚本)
│   ├── x-post.json              ← 发帖脚本 (ID: 315acb7e...)
│   ├── x-search-posts.json      ← 搜索帖子脚本 (ID: d38f7868...)
│   └── x-comment.json           ← 评论脚本 (ID: 529333b7...)
├── templates/                   ← LLM 提示词模板
│   ├── post-prompt.md           ← 发帖内容生成提示词
│   ├── comment-prompt.md        ← 评论生成提示词
│   └── keyword-generation.md    ← 关键词生成提示词
├── config/                      ← 配置
│   ├── keywords.json            ← 种子关键词
│   └── filter.json              ← 过滤规则
└── data/                        ← 运行时数据（自动创建）
    ├── posted-history.json      ← 已发帖记录
    └── commented-history.json   ← 已评论记录
```

## BrowserWing 脚本

所有 BW 脚本配置存放在 `bw-scripts/` 目录：

| 脚本文件 | 功能 | BW 脚本 ID | 说明 |
|----------|------|------------|------|
| `x-post.json` | 自动发帖 | `315acb7e-e73e-4af2-b351-575ce7065d9b` | 发布推文，参数：内容(≤280字符) |
| `x-search-posts.json` | 搜索帖子 | `d38f7868-bf25-4943-8cc3-87bc48617c41` | 搜索帖子，参数：关键词；返回：result0/1/2 |
| `x-comment.json` | 自动评论 | `529333b7-d324-409b-8812-3285b3a12cd0` | 发表评论，参数：内容(≤280字符), 帖子链接 |

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API Key | 必填 |
| `BROWSERWING_EXECUTOR_URL` | BrowserWing 地址 | `http://127.0.0.1:8080` |
| `X_PRODUCT_URL` | 默认产品链接 | 可选 |
| `X_PRODUCT_NAME` | 默认产品名称 | 可选 |

## 评论区获客流程

```
[1. 生成关键词] → AI 根据产品链接生成搜索关键词
      ↓
[2. 搜索帖子] → BW 脚本搜索相关帖子（返回 result0/1/2）
      ↓
[3. 去重] → 合并结果，去除已评论帖子
      ↓
[4. AI评分] → 4维评分（热度40 + 相关性30 + 时效20 + 质量10）
      ↓
[5. 生成评论] → LLM 根据帖子内容生成 X 风格评论
      ↓
[6. 发表评论] → BW 脚本自动评论
      ↓
[7. 记录] → JSON 持久化已评论帖子
```

## 风控策略

- ✅ 反爬策略：随机延迟 + 每日/小时上限
- ✅ 历史去重：JSON 持久化，永不重复发帖/评论
- ✅ AI 生成内容：动态内容，避免模板化
- ✅ Dry-run 模式：安全测试，不发真实内容

## 评论风格（AI 选择）

| 风格 | 说明 |
|------|------|
| 赞同共鸣型 | 对帖子内容表示认同，引发情感连接 |
| 补充分享型 | 补充相关经验，增加价值 |
| 提问互动型 | 提出开放性问题，引导回复 |
| 经验交流型 | 分享自身经历，建立平等交流 |
