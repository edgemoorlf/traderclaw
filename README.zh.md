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
│   ├── market_data.yaml        # 数据源配置
│   ├── brokers.yaml            # 券商设置
│   └── ai_personality.yaml     # AI行为偏好
├── src/
│   ├── ai/
│   │   ├── llm_client.py       # Claude/Gemini/DeepSeek接口
│   │   ├── strategy_memory.py  # 学习你的偏好
│   │   ├── decision_engine.py  # 分析和决策
│   │   └── prompt_templates.py # 上下文组装
│   ├── application/
│   │   ├── interfaces/         # 抽象基类
│   │   └── services/           # 核心业务逻辑
│   ├── infrastructure/
│   │   ├── market_data/        # Polymarket, Yahoo等
│   │   └── brokers/            # Alpaca, OKX
│   └── interfaces/
│       └── cli.py              # 聊天式界面
├── memory/                     # 对话历史
├── logs/                       # 决策审计日志
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
| **Claude** | 细致推理、安全 | 复杂策略解读 |
| **Gemini** | 实时数据访问 | 新闻和情绪分析 |
| **DeepSeek** | 性价比高、速度快 | 高频监控 |

你可以组合使用多个模型 —— 例如用Claude做策略分析，用Gemini做新闻分析。

## 许可证

MIT

---

*TraderClaw: 懂你所想的AI交易伙伴。*
