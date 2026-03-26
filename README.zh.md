# TraderClaw

**AI驱动的智能交易助手**，利用大型语言模型（DeepSeek、Gemini、Claude）、个人交易策略洞察以及包括Polymarket预测市场情绪在内的实时市场数据，做出智能交易决策。

## 概述

TraderClaw 不是传统的依赖固定技术指标的自动化交易系统，而是一个**AI交易员**，它能够：

- **理解你的策略** —— 通过自然语言对话了解你的交易理念
- **分析市场** —— 使用能够访问实时数据和新闻的大语言模型
- **全天候监控持仓** —— 24/7识别机会和风险
- **整合市场情绪** —— 结合预测市场（Polymarket）和社交信号
- **按你的指令操作** —— 从完全自主到需要审批的多种模式
-**学习和适应** —— 根据交易结果和你的反馈不断优化

## 工作原理

```
┌─────────────────────────────────────────────────────────────────┐
│                        TRADERCLAW AI 代理                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   你的       │    │   公开       │    │  预测        │      │
│  │  洞察        │ +  │ 市场数据     │ +  │  市场        │      │
│  │ & 策略       │    │  & 新闻      │    │ (Polymarket)│      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         └───────────────────┼───────────────────┘               │
│                             ▼                                   │
│              ┌─────────────────────────────┐                   │
│              │    LLM 分析引擎             │                   │
│              │  (Claude / Gemini / DeepSeek)│                  │
│              └─────────────────────────────┘                   │
│                             │                                   │
│                             ▼                                   │
│              ┌─────────────────────────────┐                   │
│              │    交易决策                 │                   │
│              │  - 是否交易？               │                   │
│              │  - 什么操作？               │                   │
│              │  - 仓位大小？               │                   │
│              │  - 风险评估？               │                   │
│              └─────────────────────────────┘                   │
│                             │                                   │
│              ┌──────────────┼──────────────┐                   │
│              ▼              ▼              ▼                   │
│        ┌─────────┐   ┌──────────┐   ┌──────────┐              │
│        │  自动   │   │  建议    │   │  仅通知  │              │
│        │ 执行    │   │ 审批     │   │          │              │
│        └─────────┘   └──────────┘   └──────────┘              │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## 核心概念

### 1. AI 策略理解

无需编写代码，用**自然语言向AI描述你的交易理念**：

> *"当情绪积极但恐慌指数较高时，我看好科技股。当VIX突破25时，我喜欢逐步建仓。"*

> *"对于加密货币，我跟随聪明钱的流向。当预测市场对经济结果表现出高确定性时，如果价格还未变动，我会选择反向操作。"*

AI会解读这些洞察并应用于实时决策。

### 2. 多维度智能分析

AI综合分析：
- **技术分析** —— 价格走势、成交量、技术指标（传统方法）
- **基本面分析** —— 财报、宏观数据、行业趋势
- **情绪分析** —— Polymarket预测、社交媒体、新闻情绪
- **持仓背景** —— 你当前的敞口、盈亏、风险限额
- **市场微观结构** —— 订单簿深度、资金费率、资金流向

### 3. 运行模式

| 模式 | 描述 | 适用场景 |
|------|------|----------|
| **自主模式** | AI在设定的安全范围内自动执行交易 | 有明确策略的经验交易者 |
| **审批模式** | AI提出建议，你逐笔审批 | 正在建立对系统的信任 |
| **咨询模式** | AI给出建议，你手动执行 | 研究和验证阶段 |
| **监控模式** | AI仅监控和提醒 | 放手式监管 |

## 数据源

| 数据源 | 类型 | 用途 |
|--------|------|------|
| **Polymarket** | 预测市场 | 情绪分析、事件概率、反向信号 |
| **Yahoo Finance** | 股票数据 | 价格、基本面、新闻 |
| **CoinGecko** | 加密货币数据 | 价格、成交量、链上指标 |
| **News APIs** | 实时新闻 | 事件检测、情绪变化 |
| **Social Signals** | 社交媒体 | 群体情绪、热门话题 |

## 支持的券商

| 券商 | 资产类别 | 模式 |
|------|----------|------|
| **Alpaca** | 美股 | 模拟盘（默认）/ 实盘 |
| **OKX** | 加密货币 | 演示盘（默认）/ 实盘 |

## 投资组合导入

TraderClaw 可以从券商CSV导出文件导入你的现有持仓：

| 券商 | 导出路径 | 状态 |
|------|----------|------|
| **Fidelity** | 持仓页面 → 下载CSV | ✅ 已支持 |
| Schwab | 即将推出 | 🚧 计划中 |
| E*Trade | 即将推出 | 🚧 计划中 |

### Fidelity CSV 导入

1. 登录 Fidelity.com
2. 进入 投资组合 → 持仓
3. 点击"下载"导出CSV
4. 使用命令导入：`python -m src.interfaces.cli.main import-positions positions.csv`

系统会自动：
- 解析所有账户（个人账户、IRA、ROTH IRA等）
- 提取股票代码、数量、成本基础和盈亏
- 清理股票代码名称（移除"COM"、"CL A"等后缀）
- 计算投资组合总价值和未实现盈亏

## 快速开始

### 安装

```bash
# 克隆仓库
git clone <仓库地址>
cd traderclaw

# 安装依赖（推荐使用 uv）
uv pip install -r requirements.txt

# 或使用 pip
pip install -r requirements.txt
```

### 配置

```bash
# 复制环境配置文件示例
cp config/.env.example config/.env

# 编辑 config/.env 填入你的API密钥：
# - GEMINI_API_KEY（用于Google搜索获取数据）
# - DEEPSEEK_API_KEY（用于策略分析）
# - ALPACA_API_KEY / ALPACA_SECRET_KEY（用于美股交易）
# - OKX_API_KEY / OKX_API_SECRET / OKX_PASSPHRASE（用于加密货币交易）
```

### 命令行使用

TraderClaw 提供命令行界面用于导入持仓和获取AI交易建议。

#### 1. 导入你的投资组合

从券商（Fidelity等）导出持仓并导入：

```bash
# 从 Fidelity CSV 导出文件导入
uv run python -m src.interfaces.cli.main import-positions path/to/positions.csv

# 示例输出：
# ==================================================================
# 已导入持仓
# ==================================================================
# ROTH IRA (ROTH_IRA)
# --------------------------------------------------
#   NVDA     |      180.0 | $  175.64 | 盈亏:  +127.8%
#   TSLA     |      120.0 | $  380.85 | 盈亏:   +20.0%
#   ...
# ==================================================================
# 总价值: $279,898.52
```

#### 2. 获取AI交易建议

```bash
# 询问特定持仓的建议
uv run python -m src.interfaces.cli.main advise "Should I take profits on NVDA?" \
    --csv path/to/positions.csv

# 明确指定股票代码
uv run python -m src.interfaces.cli.main advise "比特币看起来看涨吗？" \
    --csv path/to/positions.csv \
    --symbols BTC ETH
```

#### 3. 早间简报

```bash
# 获取投资组合的综合简报
uv run python -m src.interfaces.cli.main morning-briefing \
    --csv path/to/positions.csv
```

---

### 策略管理（新增）

TraderClaw 现支持**自然语言策略**，AI 会解读并执行你的策略描述，无需编写代码。

#### 创建策略

```bash
# 创建简单策略
uv run python -m src.interfaces.cli.main strategy create my_strategy \
    --description "当 RSI 超卖且情绪积极时买入科技股" \
    --symbols AAPL MSFT NVDA \
    --mode hybrid

# 交互模式（推荐用于复杂策略）
uv run python -m src.interfaces.cli.main strategy create my_strategy -i
```

**审批模式：**
- `autonomous`（自主模式）- AI 在安全范围内自动执行交易
- `hybrid`（混合模式）- 高置信度信号自动执行，其他需审批
- `approval`（审批模式）- 每笔交易都需你明确批准
- `notify`（通知模式）- AI 建议交易，你手动执行

#### 列出和管理策略

```bash
# 列出所有策略
uv run python -m src.interfaces.cli.main strategy list

# 查看策略详情
uv run python -m src.interfaces.cli.main strategy show <strategy_id>

# 删除策略
uv run python -m src.interfaces.cli.main strategy delete <strategy_id>
```

#### 运行策略

```bash
# 模拟运行 - 生成信号但不执行
uv run python -m src.interfaces.cli.main strategy run <strategy_id> --dry-run

# 使用指定账户运行
uv run python -m src.interfaces.cli.main strategy run <strategy_id> \
    --account my_paper_account
```

#### 管理券商账户

```bash
# 列出已配置账户
uv run python -m src.interfaces.cli.main strategy accounts --list

# 添加模拟交易账户
uv run python -m src.interfaces.cli.main strategy accounts \
    --add-paper my_paper_account \
    --name "My Paper Trading"

# 删除账户
uv run python -m src.interfaces.cli.main strategy accounts --remove <account_id>
```

#### 示例：完整策略工作流

```bash
# 1. 添加模拟交易账户
uv run python -m src.interfaces.cli.main strategy accounts \
    --add-paper tech_strategy_paper \
    --name "Tech Strategy Paper Account"

# 2. 创建策略
uv run python -m src.interfaces.cli.main strategy create tech_momentum \
    --description "买入超卖科技股（RSI < 30）且新闻情绪积极。仓位大小：每笔交易 5%。最多 3 个持仓。" \
    --symbols AAPL MSFT NVDA GOOGL \
    --mode hybrid \
    --threshold 0.85 \
    --max-positions 3

# 3. 运行策略（先模拟）
uv run python -m src.interfaces.cli.main strategy run tech_momentum --dry-run

# 4. 实盘运行（模拟盘）
uv run python -m src.interfaces.cli.main strategy run tech_momentum \
    --account tech_strategy_paper
```

---

### Web 界面（新增）

TraderClaw 现在包含现代化的 Web 界面，专为非技术用户设计。Web 界面提供单一屏幕仪表板，你可以管理持仓、使用自然语言创建策略，并审批交易信号。

#### 启动 Web 界面

```bash
# 1. 安装前端依赖
cd web
npm install

# 2. 启动前端开发服务器
npm run dev

# 3. 在另一个终端启动后端 API
uv run python -m src.interfaces.web.main
```

然后在浏览器中打开 `http://localhost:3000`。

#### Web 界面功能

**单一屏幕仪表板：**
- **投资组合概览** - 总价值、每日变动、所有持仓
- **持仓管理** - 点击任意持仓查看详情、盈亏和活跃策略
- **AI 聊天界面** - 输入自然语言命令，如"在 $800 时卖出 50% 的 NVDA"
- **信号审批** - 内联审查和批准交易信号
- **实时更新** - WebSocket 连接实现实时价格和信号更新

**在 Web 界面中创建策略：**
1. 点击持仓以展开
2. 点击"+ 添加退出策略"或在 AI 聊天中输入
3. 用 plain English 描述你的策略
4. 查看 AI 的解读
5. 确认激活

**示例命令：**
- "当 NVDA 达到 $800 时卖出一半"
- "在 AAPL 上设置 10% 的跟踪止损"
- "如果 TSLA 跌破 $300，全部卖出"
- "将 NVDA 减仓至投资组合的 20%"

#### Web 界面架构

```
web/
├── src/
│   ├── components/
│   │   ├── PositionList.tsx    # 持仓显示，支持展开/折叠
│   │   ├── AIChat.tsx          # 自然语言聊天界面
│   │   ├── AlertPanel.tsx      # 信号和提醒
│   │   └── Header.tsx          # 投资组合摘要标题
│   ├── App.tsx                 # 主仪表板布局
│   └── types.ts                # TypeScript 接口
├── package.json
└── vite.config.ts
```

后端 API 端点（FastAPI）：
- `GET /api/portfolio` - 投资组合及持仓
- `POST /api/strategies/parse` - 从自然语言预览策略
- `POST /api/strategies` - 创建确认的策略
- `GET /api/signals/pending` - 待审批的信号
- `WS /ws` - 实时 WebSocket 更新

### Python API 使用

程序化访问：

```python
import asyncio
import os
from src.ai import TradingOrchestrator, StrategyModel

async def main():
    # 初始化编排器
    orchestrator = TradingOrchestrator(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        strategy_model=StrategyModel.DEEPSEEK,
        strategy_api_key=os.getenv("DEEPSEEK_API_KEY"),
        execution_mode="advisory",  # advisory, approval, or autonomous
    )

    # 从CSV加载持仓
    portfolio = orchestrator.position_service.load_from_csv("positions.csv")
    print(f"已加载投资组合: ${portfolio['total_portfolio_value']:,.2f}")

    # 获取AI建议
    advice = await orchestrator.advise(
        user_id="user_123",
        query="我应该卖出NVDA持仓吗？已经涨了127%",
        symbols=["NVDA"]
    )

    print(f"建议: {advice.decision.recommendation}")
    print(f"信心度: {advice.decision.confidence}")
    print(f"理由: {advice.decision.rationale}")

asyncio.run(main())
```

### 运行模式

| 模式 | 命令 | 描述 |
|------|------|------|
| **咨询模式** | （默认） | AI建议，你手动执行 |
| **审批模式** | 在代码中设置 | AI提议，你逐笔审批 |
| **自主模式** | 在代码中设置 | AI在设定安全范围内自动执行 |

## 交互示例

### 每日早间简报
```
🤖 TraderClaw: 早上好！这是今日市场简报：

持仓情况: AAPL +2.3%, TSLA -1.1%, BTC +5.4%

关键信号：
• Polymarket 显示美联储下周暂停加息的概率为78%
• AAPL 接近你的目标区间（$185-190）
• BTC 资金费率转负（可能出现轧空）

建议：减持50% AAPL仓位，如果BTC突破$43k则加仓
风险：中等 | 信心度：高

[批准] [修改] [跳过] [详细解释]
```

### 实时提醒
```
🤖 TraderClaw: 持仓警报！

你的TSLA持仓在30分钟内下跌4%。
• 新闻：电池供应商问题报道
• Polymarket 电动车情绪指数下跌15点
• 你的止损规则："坏消息时-5%止损"

建议：平仓（-4.2%实际亏损）
替代方案：用QQQ看跌期权对冲

[执行] [持有] [设置-5%警报] [解释]
```

### 策略优化
```
你："当VIX高于30时，我想更激进一些"

🤖 TraderClaw: 明白了。我将调整策略：
• 当前：最大仓位5%
• VIX > 30: 增加到10%，收紧止损
• VIX > 40: 考虑反向ETF，减少多头敞口

这与你之前关于波动率机会的观点一致。
确认这些更改吗？[是] [调整] [取消]
```

## 项目结构

```
traderclaw/
├── config/
│   ├── .env                    # API密钥（git忽略）
│   ├── .env.example            # 环境文件示例
│   ├── strategies.yaml         # 策略存储
│   └── brokers.yaml            # 多账户券商设置
├── src/
│   ├── ai/
│   │   ├── llm_client.py       # DeepSeek/Gemini/Qwen接口
│   │   ├── trading_orchestrator.py  # 主交易协调器
│   │   └── models.py           # AI模型枚举和配置
│   ├── strategies/
│   │   ├── execution_engine.py # 自然语言策略引擎
│   │   └── consensus.py        # 多模型共识
│   ├── indicators/
│   │   └── technical.py        # 技术指标计算
│   ├── application/
│   │   ├── interfaces/         # 抽象基类
│   │   │   ├── broker.py       # 券商接口
│   │   │   └── market_data_source.py
│   │   └── services/
│   │       └── position_service.py  # 投资组合管理
│   ├── infrastructure/
│   │   ├── market_data/        # 数据客户端
│   │   │   ├── yahoo_client.py
│   │   │   ├── coingecko_client.py
│   │   │   └── polymarket_client.py
│   │   └── brokers/            # 券商实现
│   │       ├── alpaca_broker.py
│   │       ├── okx_broker.py
│   │       └── broker_manager.py  # 多账户支持
│   └── interfaces/
│       └── cli/
│           ├── main.py         # 主CLI入口
│           └── strategy_cli.py # 策略管理命令
├── data/
│   └── imported_positions/     # 保存的投资组合快照
└── tests/
```

## 安全与风控

- **默认模拟盘**：所有新策略都从模拟交易开始
- **仓位限制**：AI遵守你设定的最大仓位限制
- **亏损限制**：每日/每周亏损熔断机制
- **可解释性**：每笔交易都包含可供审核的理由
- **审计追踪**：所有AI决策和推理的完整日志
- **紧急停止**：通过CLI或手机通知即时停止

## AI 模型推荐

| 模型 | 优势 | 最适用于 |
|------|------|----------|
| **DeepSeek** | 性价比高、快速、推理能力强 | 主要策略分析 |
| **Gemini** | 通过 Google 搜索访问实时数据 | 新闻和市场数据获取 |
| **Qwen (DashScope)** | 快速、适合共识验证 | 多模型验证 |

**多模型共识**：TraderClaw 支持同时运行多个模型以获得更高置信度的决策。启用后，DeepSeek 和 Qwen 会同时分析策略，并综合它们的信号形成共识。

你可以在 `.env` 中配置模型：
```bash
# 必需
GEMINI_API_KEY=your_gemini_key

# 用于策略执行（至少一个）
DEEPSEEK_API_KEY=your_deepseek_key
DASHSCOPE_API_KEY=your_qwen_key
```

## 许可证

MIT

---

*TraderClaw: 懂你所想的AI交易伙伴。*
