# X 平台获客技能 (x-acquisition)

🐦 AI 驱动的 X (Twitter) 获客全自动解决方案

基于 BrowserWing 浏览器自动化 + DeepSeek API 实现，无需 X API Key，只需 Cookie 登录即可运营。

## 功能特性

- 📝 **自动发帖**: 根据产品链接 AI 生成内容（≤280字符）并自动发布
- 🎯 **评论区获客**: 搜索相关帖子 → AI 评分 → 生成评论 → 自动评论
- 🤖 **AI 驱动**: DeepSeek 生成内容和评分，智能筛选高价值帖子
- 🔒 **安全可靠**: 反爬策略、历史去重、风控限制
- 🧪 **Dry-run 模式**: 测试模式，不发真实内容

## Quick Start

### 1. 环境准备

```bash
# Python 3.8+
python3 --version

# 安装依赖
pip install requests
```

### 2. 配置环境变量

```bash
# DeepSeek API Key（必填）
export DEEPSEEK_API_KEY="your-deepseek-api-key"

# BrowserWing 地址（默认）
export BROWSERWING_EXECUTOR_URL="http://127.0.0.1:8080"

# 可选：默认产品信息
export X_PRODUCT_URL="https://your-product.com"
export X_PRODUCT_NAME="产品名称"
```

### 3. 启动 BrowserWing

确保 BrowserWing 服务已启动：

```bash
# 默认端口 8080
curl http://127.0.0.1:8080/health
```

### 4. 在 BrowserWing 中登录 X

1. 打开 `https://x.com` 在 BrowserWing 浏览器中
2. 使用账号密码或扫码登录
3. 登录成功后保持浏览器运行

### 5. 运行测试

```bash
cd x-acquisition

# 初始化配置
python3 scripts/x_campaign.py --init-config

# 测试模式 - 发帖（不实际发布）
python3 scripts/x_campaign.py --post --product-url "https://your-product.com" --dry-run

# 测试模式 - 评论区获客
python3 scripts/x_campaign.py --acquire --product-url "https://your-product.com" --dry-run

# 正式运行 - 完整流程
python3 scripts/x_campaign.py --all --product-url "https://your-product.com"
```

## 依赖清单

### 系统依赖

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | 3.8+ | 运行环境 |
| BrowserWing | latest | 浏览器自动化服务 |
| Chrome/Chromium | latest | BrowserWing 依赖 |

### Python 依赖

```bash
pip install requests
```

### 外部服务

| 服务 | 用途 | 获取方式 |
|------|------|----------|
| DeepSeek API | AI 内容生成 | [DeepSeek](https://platform.deepseek.com/) |
| BrowserWing | 浏览器自动化 | 本地部署 |
| X 账号 | 运营账号 | 自行准备 |

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     X 平台获客技能                           │
├─────────────────────────────────────────────────────────────┤
│  编排层 (scripts/x_campaign.py)                              │
│     ├── 统一入口                                            │
│     ├── 流程编排                                            │
│     └── 参数解析                                            │
├─────────────────────────────────────────────────────────────┤
│  业务层                                                       │
│     ├── x_post.py              # 发帖模块                    │
│     ├── x_comment_acquisition.py # 评论区获客模块            │
│     └── x_llm.py               # LLM API 封装               │
├─────────────────────────────────────────────────────────────┤
│  驱动层                                                       │
│     ├── DeepSeek API           # AI 内容生成/评分           │
│     └── BrowserWing API        # 浏览器自动化               │
├─────────────────────────────────────────────────────────────┤
│  存储层                                                       │
│     ├── data/posted-history.json       # 发帖历史           │
│     └── data/commented-history.json    # 评论历史           │
└─────────────────────────────────────────────────────────────┘
```

### BrowserWing 脚本架构

```
bw-scripts/
├── x-post.json           # 发帖: 点击Post → 输入内容 → 发布
├── x-search-posts.json   # 搜索: 滚动三屏 → JS提取帖子数据
└── x-comment.json        # 评论: 打开帖子 → 输入评论 → 点击Reply
```

### 数据流

```
产品链接 → AI生成关键词 → BW搜索帖子 → 去重 → AI评分 → 
生成评论 → BW发表评论 → 记录历史
```

## 实现逻辑

### 1. 自动发帖流程

```python
# scripts/x_post.py

产品链接 → AI生成内容(≤280字符) → 查重 → BW发帖 → 记录历史

详细步骤:
1. 调用 DeepSeek 生成帖子内容（限制280字符）
2. 检查是否已发过相同内容（去重）
3. 调用 BW 脚本 x-post.json 发布
4. 保存到 posted-history.json
```

### 2. 评论区获客流程

```python
# scripts/x_comment_acquisition.py

产品链接 → 生成关键词 → BW搜索 → 合并结果 → 去重 → 
AI评分 → 生成评论 → BW评论 → 记录历史

详细步骤:
1. 生成5-10个搜索关键词
2. 对每个关键词调用 BW 脚本 x-search-posts.json
3. 合并 result0/result1/result2 三组结果
4. 基于 URL 去重，排除已评论帖子
5. AI 4维评分（热度40 + 相关性30 + 时效20 + 质量10）
6. 筛选 ≥60分 的高价值帖子
7. 生成 X 风格评论（≤280字符）
8. 调用 BW 脚本 x-comment.json 发表评论
9. 保存到 commented-history.json
```

### 3. AI 评分逻辑

```python
评分维度:
- 热度 (40分): 互动潜力、话题热度、点赞/评论数
- 相关性 (30分): 与产品的相关程度
- 时效 (20分): 内容的时效性
- 质量 (20分): 内容质量、可信度

最低阈值: 60分（可配置）
```

### 4. 评论风格

AI 自动选择以下风格之一：

| 风格 | 策略 | 示例 |
|------|------|------|
| 赞同共鸣型 | 对帖子内容表示认同 | "确实！我也觉得..." |
| 补充分享型 | 补充相关经验 | "补充一下，还可以..." |
| 提问互动型 | 提出开放性问题 | "请问你用的是...?" |
| 经验交流型 | 分享自身经历 | "我之前用过类似的..." |

### 5. 风控策略

```python
# config/filter.json

{
  "min_score": 60,              # 最低评分阈值
  "max_comments_per_run": 5,    # 每次最多评论数
  "max_comments_per_day": 20,   # 每天最多评论数
  "min_comment_interval": 180,  # 评论间隔（秒）
  "active_hours": {"start": 8, "end": 23}  # 活跃时段
}

随机延迟: 1-5秒（防检测）
滚动模式: 人类化滚动，带停顿
```

## 文件结构

```
x-acquisition/
├── SKILL.md                     # OpenClaw 技能定义
├── README.md                    # 本文档
├── scripts/                     # Python 脚本
│   ├── x_campaign.py            # 统一编排入口
│   ├── x_post.py                # 发帖模块
│   ├── x_comment_acquisition.py # 评论区获客模块
│   └── x_llm.py                 # LLM API 封装
├── bw-scripts/                  # BrowserWing 脚本（从BW下载）
│   ├── x-post.json              # 发帖脚本
│   ├── x-search-posts.json      # 搜索帖子脚本
│   └── x-comment.json           # 评论脚本
├── templates/                   # LLM 提示词模板
│   ├── post-prompt.md
│   ├── comment-prompt.md
│   └── keyword-generation.md
├── config/                      # 配置文件
│   ├── keywords.json            # 种子关键词
│   └── filter.json              # 风控配置
└── data/                        # 运行时数据（自动创建）
    ├── posted-history.json      # 已发帖记录
    └── commented-history.json   # 已评论记录
```

## 使用示例

### 基本用法

```bash
# 发帖
python3 scripts/x_post.py --product-url "https://your-product.com"

# 获客
python3 scripts/x_comment_acquisition.py --product-url "https://your-product.com"

# 完整流程
python3 scripts/x_campaign.py --all --product-url "https://your-product.com"
```

### 高级用法

```bash
# 指定关键词获客
python3 scripts/x_campaign.py --acquire \
  --product-url "https://your-product.com" \
  --keywords "AI,工具,效率" \
  --max-comments 3

# 手动指定发帖内容
python3 scripts/x_campaign.py --post \
  --product-url "https://your-product.com" \
  --content "自定义帖子内容"

# 调整评分阈值
python3 scripts/x_comment_acquisition.py \
  --product-url "https://your-product.com" \
  --min-score 70 \
  --max-comments 10
```

## BrowserWing 脚本详情

### 1. 发帖脚本 (x-post.json)

- **ID**: `315acb7e-e73e-4af2-b351-575ce7065d9b`
- **参数**: `内容` (string, ≤280字符)
- **流程**: 点击Post按钮 → 等待 → 输入内容 → 等待 → 点击发布 → 等待
- **注意**: 内容超过280字符会被截断或报错

### 2. 搜索脚本 (x-search-posts.json)

- **ID**: `d38f7868-bf25-4943-8cc3-87bc48617c41`
- **参数**: `关键词` (string)
- **流程**: 等待 → 滚动 → 等待 → JS提取(result0) → 滚动 → 等待 → JS提取(result1) → 滚动 → 等待 → JS提取(result2)
- **返回**: `result0`, `result1`, `result2` (JSON字符串)
- **数据结构**: `{author, handle, content, link, likes, replies}`

### 3. 评论脚本 (x-comment.json)

- **ID**: `529333b7-d324-409b-8812-3285b3a12cd0`
- **参数**: `内容` (string, ≤280字符), `帖子链接` (string)
- **流程**: 等待 → 输入评论 → 等待 → 点击Reply → 等待
- **注意**: 需在BrowserWing中保持X登录状态

## 环境变量

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `DEEPSEEK_API_KEY` | ✓ | - | DeepSeek API Key |
| `BROWSERWING_EXECUTOR_URL` | ✗ | `http://127.0.0.1:8080` | BW服务地址 |
| `X_PRODUCT_URL` | ✗ | - | 默认产品链接 |
| `X_PRODUCT_NAME` | ✗ | - | 默认产品名称 |

## 配置文件

### config/filter.json

```json
{
  "min_score": 60,              // 最低评分阈值
  "max_comments_per_run": 5,    // 每次最多评论数
  "max_comments_per_day": 20,   // 每天最多评论数
  "min_comment_interval": 180,  // 评论间隔（秒）
  "banned_keywords": ["spam", "scam"],  // 屏蔽关键词
  "active_hours": {"start": 8, "end": 23}  // 活跃时段
}
```

### config/keywords.json

```json
{
  "seed_keywords": ["AI", "工具", "效率"],
  "default_product_url": "",
  "default_product_name": ""
}
```

## 注意事项

1. **280字符限制**: X 平台硬性限制，内容+链接+标签必须≤280字符
2. **登录状态**: 使用 BrowserWing 前需手动登录 X 账号
3. **风控**: 建议首次使用 `--dry-run` 测试，避免频繁操作导致封号
4. **历史记录**: 自动保存在 `data/` 目录，防止重复发帖/评论
5. **Cookie 有效期**: 如登录失效，需重新在 BrowserWing 中登录

## 故障排查

### 问题：LLM API 调用失败
```bash
# 检查环境变量
echo $DEEPSEEK_API_KEY
# 或未设置则报错
```

### 问题：BrowserWing 连接失败
```bash
# 检查服务状态
curl http://127.0.0.1:8080/health
# 确保 BrowserWing 已启动
```

### 问题：搜索无结果
```bash
# 检查关键词
# 检查 BW 搜索脚本是否正常运行
# 尝试更换关键词
```

### 问题：评论/发帖失败
```bash
# 检查 X 登录状态（BrowserWing中）
# 检查内容是否超过280字符
# 检查账号是否受限
```

## 开发计划

- [ ] 支持图片发帖
- [ ] 支持定时发布
- [ ] 支持多账号切换
- [ ] 支持评论回复追踪
- [ ] 支持数据分析报表

## License

MIT License

## 作者

贾绍杉 (jiashaoshan)

---

如有问题或建议，欢迎提交 Issue 或 PR。
