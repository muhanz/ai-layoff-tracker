# AI Layoff Tracker ⚠️

自 GPT-4 发布（2023年3月14日）以来，全球因 AI 被裁员的人数实时追踪。数据每日自动更新，来源可查。

## 快速开始

### 1. 初始化历史数据

```bash
pip install requests openai
python scripts/import_historical_data.py
```

这会生成 `data/events.json`，包含43起已确认的重大AI裁员事件。

### 2. 生成页面

```bash
python scripts/generate_page.py
```

生成 `public/index.html`，可直接在浏览器中打开预览。

### 3. 配置自动更新

1. 在 GitHub 仓库 Settings → Secrets 中添加：
   - `GNEWS_API_KEY`：从 https://gnews.io 免费注册获取
   - `OPENAI_API_KEY`：从 https://platform.openai.com 获取

2. 将 `.github/workflows/daily-update.yml` 推送到仓库，GitHub Actions 会每天自动运行。

### 4. 部署到 Cloudflare Pages

1. 登录 https://dash.cloudflare.com
2. Workers & Pages → Create → Pages → Connect to Git
3. 选择本仓库，Build output directory 填 `public`，Build command 留空
4. 每次 push 自动部署

## 项目结构

```
├── .github/workflows/
│   └── daily-update.yml          # 每日定时任务
├── scripts/
│   ├── import_historical_data.py # 一次性：导入历史基线数据
│   ├── fetch_news.py             # 每日：抓取AI裁员新闻
│   ├── analyze.py                # 每日：LLM分析提取事件
│   ├── generate_page.py          # 每日：生成静态HTML
│   └── supplement_from_trueup.py # 可选：从TrueUp补充数据
├── data/
│   └── events.json               # 裁员事件数据库
└── public/
    └── index.html                # 部署的静态页面
```

## 数据说明

### 归因分类

| 分类 | 含义 | 标准 |
| :--- | :--- | :--- |
| **confirmed** | 公司明确因AI裁员 | 公司官方声明中提到AI/自动化是裁员原因 |
| **likely** | 高度相关 | 公司在大规模投资AI的同时裁员，或媒体分析为AI相关 |
| **unclear** | 可能相关 | 科技公司裁员，可能与AI转型有关但未明确 |

### 数据来源

- **Challenger, Gray & Christmas**：美国月度裁员报告（仅美国，每月校准）
- **Layoffs.fyi**：全球科技公司裁员追踪
- **TrueUp.io**：实时科技裁员追踪
- **公开新闻报道**：通过GNews API每日抓取

### 已知局限

1. BT Group 的 55,000 是到2030年的计划数字，实际已执行的远少于此
2. 部分 "likely" 事件可能与AI无直接因果关系
3. 此数据集仅包含公开报道的重大事件，小规模裁员未被统计
4. Challenger 数据仅覆盖美国

## 成本

| 项目 | 月费 |
| :--- | :--- |
| GNews.io 免费版 | $0 |
| OpenAI GPT-4o-mini | ~$0.05 |
| GitHub Actions | $0 |
| Cloudflare Pages | $0 |
| **合计** | **< $0.10/月** |

## 补充数据

如果你想添加更多历史事件：

1. 直接编辑 `scripts/import_historical_data.py` 中的 `HISTORICAL_EVENTS` 列表
2. 或从 TrueUp.io 复制数据到 `data/trueup_raw.txt`，运行 `python scripts/supplement_from_trueup.py`

## License

MIT
