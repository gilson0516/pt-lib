# pt-lib

Python 图表形态检测库。基于 stock-pattern 框架，吸收 PatternPy / TradingPatternScanner 的形态，覆盖 **28 种形态**（含谐波），CLI + 回测 + 可视化全集成。

> 名字致敬 TA-Lib —— pt-lib = Pattern Library.

---

## 形态总览

| 类别 | 形态 | 模式键 | 来源 |
|------|------|--------|------|
| **H&S** | Head & Shoulders / Inverse H&S | `hnsd` / `hnsu` | stock-pattern |
| **双顶/底** | Double Top / Double Bottom | `dtop` / `dbot` | stock-pattern |
| **VCP** | Volatility Contraction (Bull/Bear) | `vcpu` / `vcpd` | stock-pattern |
| **旗形** | Bullish / Bearish Flag | `flagu` / `flagd` | stock-pattern |
| **三角形** | Symmetric / Ascending / Descending | `trng` | stock-pattern |
| **趋势线** | Uptrend / Downtrend Line | `uptl` / `dntl` | stock-pattern |
| **谐波** | AB=CD / Bat / Gartley / Crab / Butterfly | `abcdu`~`bflyd` (10个) | stock-pattern |
| **楔形** ✨ | Falling Wedge (Bullish) / Rising Wedge (Bearish) | `wedgu` / `wedgd` | **pt-lib 新增** |
| **通道** ✨ | Channel Up (Bullish) / Channel Down (Bearish) | `chnlu` / `chnld` | **pt-lib 新增** |
| **多顶/底** ✨ | Multiple Top (Bearish) / Multiple Bottom (Bullish) | `mltp` / `mltb` | **pt-lib 新增** |
| **S/R** ✨ | Horizontal Support & Resistance | `supr` | **pt-lib 新增** |

✨ = PatternPy / TradingPatternScanner 有但 stock-pattern 没有，pt-lib 补齐的形态。

---

## 开发过程

1. 对比了 3 个 Python 图表形态识别库：

   | 库 | 核心算法 | 代码量 | 质量 |
   |---|---|---|---|
   | **PatternPy / TradingPatternScanner** | rolling window 极值比较 | ~200行 | 虚警率高，原型级别 |
   | **stock-pattern** | pivot + 几何约束 + Fib 比率 | ~3558行 | 生产可用级别 |
   | **TA-Lib** | **CDL 函数全是K线形态**，无图表形态 | — | 不适用 |

2. 选择 stock-pattern 作为基底，因其检测逻辑最严谨（pivot 点 + 趋势线 + 几何约束）

3. 识别 stock-pattern 缺失的 4 个形态族（楔形/通道/多顶底/S/R），从 PatternPy 提取逻辑理念，但用 stock-pattern 的 pivot 框架**重新实现**（非简单搬运 rolling window）

4. 全部集成到 CLI（`init.py`）、回测（`backtest.py`）、可视化（`Plotter.py`）

---

## 安装

```bash
git clone https://github.com/tan-yang/pt-lib.git
cd pt-lib
pip install -r requirements.txt
```

首次运行需要配置数据路径：

```bash
cd src
python setup-config.py
```

---

## CLI 用法

```bash
cd src

# 扫描特定形态
python init.py -p wedgu -f symlist.txt      # Falling Wedge
python init.py -p chnlu -f symlist.txt       # Channel Up
python init.py -p supr -f symlist.txt        # S/R Levels

# 扫描分组
python init.py -p all -f symlist.txt         # 全部经典形态
python init.py -p bull -f symlist.txt        # 全部看涨形态
python init.py -p bear -f symlist.txt        # 全部看跌形态
python init.py -p bull_harm -f symlist.txt   # 全部看涨谐波

# 交互模式（不传 -p）
python init.py -f symlist.txt

# 回测
python backtest.py -p wedgu -d 2024-10-20 --period 60

# 参数
-l/--left   左侧K线数（默认6）
-r/--right  右侧K线数（默认6）
--save      保存图表为PNG
--plot      从JSON结果重新绘图
```

### symlist.txt 格式

每行一个股票代码，对应 `DATA_PATH` 下的 CSV 文件名（不含扩展名）：

```
AAPL
MSFT
GOOGL
TSLA
```

---

## Python API

```python
from utils import get_max_min
from patterns_extended import find_bullish_wedge, find_support_resistance

# OHLCV DataFrame
df = pd.read_csv("data/AAPL.csv", index_col=0, parse_dates=True)

# 提取 pivot 点
pivots = get_max_min(df)

# 检测 Falling Wedge
result = find_bullish_wedge("AAPL", df, pivots, {})
if result:
    print(f"Detected: {result['pattern']} ({result['alt_name']})")
    print(f"Points: {result['points']}")

# 检测 S/R 级别
sr = find_support_resistance("AAPL", df, pivots, {})
if sr:
    print(f"{sr['alt_name']} at {sr['extra_points']['level_start'][1]:.2f}")
```

### 返回格式

每个检测函数返回 `Optional[dict]`：

```python
{
    "sym": "AAPL",          # 股票代码
    "pattern": "WEDGU",     # 模式键
    "alt_name": "Falling Wedge",  # 可读名称
    "start": Timestamp(...),      # 形态起始日期
    "end": Timestamp(...),        # 当前日期
    "df_start": Timestamp(...),   # 数据起始
    "df_end": Timestamp(...),     # 数据结束
    "points": {                   # 标注点（用于标签）
        "A": (Timestamp, price),
        "B": (Timestamp, price),
        ...
    },
    "extra_points": {             # 额外线（用于绘图）
        "upper_start": (Timestamp, price),
        "upper_end": (Timestamp, price),
        ...
    },
}
```

---

## 新增形态检测逻辑

与 PatternPy 的 rolling window 极值比较不同，pt-lib 使用 **pivot + 趋势线几何约束**：

| 形态 | 检测条件 |
|------|----------|
| **Falling Wedge** | 两个高点 + 两个低点均下行，上线斜率 < 下线斜率 → 收敛 |
| **Rising Wedge** | 两个高点 + 两个低点均上行，上线斜率 < 下线斜率 → 收敛 |
| **Channel Up** | 两个高点 + 两个低点均上行，斜率差 < 30% → 平行 |
| **Channel Down** | 两个高点 + 两个低点均下行，斜率差 < 30% → 平行 |
| **Multiple Top** | 3+ 高点在 5% 价格范围内聚类，价格未突破 |
| **Multiple Bottom** | 3+ 低点在 5% 价格范围内聚类，价格未跌破 |
| **S/R Levels** | pivot 点在自适应阈值内聚类，取最高 touch count 的级别 |

所有形态检查 close 是否已突破趋势线/级别（已突破的不输出）。

---

## 项目结构

```
pt-lib/
├── src/
│   ├── init.py                 # CLI 入口
│   ├── backtest.py             # 回测
│   ├── utils.py                # 核心检测（stock-pattern 原版）
│   ├── patterns_extended.py    # 新增形态（楔形/通道/多顶底/S/R）
│   ├── Plotter.py              # mplfinance 可视化
│   ├── setup-config.py         # 配置生成
│   ├── loaders/                # 数据加载
│   │   ├── AbstractLoader.py
│   │   ├── EODFileLoader.py
│   │   └── IEODFileLoader.py
│   └── user.json               # 用户配置
├── tests/
│   ├── test_extended_patterns.py  # 新增形态测试（10 tests）
│   └── ...
└── requirements.txt
```

---

## License

GNU General Public License v3.0 (继承自 stock-pattern)
