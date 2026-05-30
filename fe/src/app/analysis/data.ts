import { Asset, GlobalEvent } from "./types";

export const ASSETS_MOCK: Asset[] = [
  {
    id: "btc",
    name: "Bitcoin",
    category: "Crypto",
    symbol: "BTC-USD",
    price: 67250.45,
    change: 1450.25,
    changePercent: 2.2,
    marketCap: "$1.32T",
    volume24h: "$28.4B",
    rsi: 62,
    macd: "Bullish Crossover",
    rating: "BUY",
    confidence: 85,
    candles: [
      { open: 64500, high: 66200, low: 64100, close: 65800 },
      { open: 65800, high: 66900, low: 65200, close: 66400 },
      { open: 66400, high: 67800, low: 66100, close: 67100 },
      // Pivot Point (Historical ends, Forecast begins)
      { open: 67100, high: 68200, low: 66800, close: 67500, isForecast: true },
      { open: 67500, high: 69100, low: 66400, close: 68200, isForecast: true },
      { open: 68200, high: 70800, low: 67900, close: 70100, isForecast: true }
    ],
    technicalReasons: [
      {
        summary: "Bullish MACD crossover executed on the 4-hour chart, signaling structural upward acceleration.",
        detail: "The Moving Average Convergence Divergence (MACD) line crossed above the signal line on the 4-hour timeframe. This crossover occurred below the zero line, which typically signals a strong momentum shift from sellers to buyers. Additionally, the MACD histogram has transitioned from negative to positive values, with expanding bars indicating that buying pressure is accelerating."
      },
      {
        summary: "Price has established support at the 200 EMA ($64,500), displaying strong demand spikes on volume indicators.",
        detail: "The 200-period Exponential Moving Average (EMA) on the daily chart serves as a major psychological barrier. Over the past 48 hours, Bitcoin tested this level three times, and each touch was met with immediate, high-volume buying pressure. This indicates institutional accumulation at the $64,500 zone, establishing a firm price floor for the next leg up."
      },
      {
        summary: "RSI is currently stable at 62, indicating remaining headroom before reaching typical overbought expansion thresholds.",
        detail: "The Relative Strength Index (RSI) stands at 62. Values between 50 and 70 indicate a healthy bullish trend with no signs of exhaustion. Because the asset has not yet entered the overbought territory (above 70), there is substantial headroom for price appreciation before sellers gain control or profit-taking triggers a reversal."
      }
    ],
    fundamentalReasons: [
      "US core inflation rates cooling down to 3.3% opens the window for interest rate cuts in late Q3.",
      "On-chain metrics report record-high cold storage outflows, compounding supply liquidity squeezes on exchanges.",
      "Corporate hedge fund allocations towards regulated ETFs show continuous daily growth."
    ]
  },
  {
    id: "eth",
    name: "Ethereum",
    category: "Crypto",
    symbol: "ETH-USD",
    price: 3450.80,
    change: -45.10,
    changePercent: -1.29,
    marketCap: "$415.2B",
    volume24h: "$14.1B",
    rsi: 48,
    macd: "Neutral",
    rating: "HOLD",
    confidence: 60,
    candles: [
      { open: 3510, high: 3580, low: 3480, close: 3540 },
      { open: 3540, high: 3590, low: 3510, close: 3570 },
      { open: 3570, high: 3620, low: 3520, close: 3530 },
      { open: 3530, high: 3550, low: 3420, close: 3480, isForecast: true },
      { open: 3480, high: 3510, low: 3400, close: 3450.8, isForecast: true },
      { open: 3450.8, high: 3550, low: 3380, close: 3510, isForecast: true }
    ],
    technicalReasons: [
      {
        summary: "Stochastic oscillator resides in intermediate territories, offering no immediate momentum signals.",
        detail: "The Stochastic oscillator is sitting around 50, which is standard equilibrium. It does not indicate either overbought or oversold conditions. Traders should avoid forcing momentum trades based on this indicator until it breaches the 20 or 80 thresholds."
      },
      {
        summary: "Volume Profile displays strong congestion clusters between $3,400 and $3,600, suggesting temporary consolidation.",
        detail: "The Volume Profile (Visible Range) shows a high concentration of trading activity in this range, acting as a magnet for price. Expected price behavior is sideways volatility within this value area until a breakout catalyst occurs."
      },
      {
        summary: "Support holds firmly at $3,380, keeping structural trends intact despite localized pullbacks.",
        detail: "Despite the 1.2% drop today, Ethereum remains above the key pivot support at $3,380. As long as this support is defended on the daily close, the broader medium-term bullish structural framework is preserved."
      }
    ],
    fundamentalReasons: [
      "Gas fee metrics indicate moderate network activity, indicating a lull in retail transaction volumes.",
      "Pending regulatory decisions on smart contract categorizations restrict institutional market commitment.",
      "L2 scaling systems (Arbitrum, Optimism) show rising TVL, maintaining fundamental base layer utility."
    ]
  },
  {
    id: "tsla",
    name: "Tesla Inc.",
    category: "Stock",
    symbol: "TSLA",
    price: 178.46,
    change: -5.84,
    changePercent: -3.17,
    marketCap: "$568.2B",
    volume24h: "$12.4B",
    rsi: 34,
    macd: "Bearish Momentum",
    peRatio: "42.5",
    rating: "SELL",
    confidence: 78,
    candles: [
      { open: 192, high: 194, low: 188, close: 189 },
      { open: 189, high: 191, low: 183, close: 184 },
      { open: 184, high: 186, low: 179, close: 181 },
      { open: 181, high: 183, low: 177, close: 179.2, isForecast: true },
      { open: 179.2, high: 181.5, low: 175.2, close: 178.46, isForecast: true },
      { open: 178.46, high: 180, low: 168.5, close: 170.2, isForecast: true }
    ],
    technicalReasons: [
      {
        summary: "Severe descending price channel structure. Price rejected repeatedly from the channel ceiling.",
        detail: "Tesla continues to print lower highs and lower lows inside a distinct downward channel. Every rally attempt to the upper channel boundary has been met with aggressive selling pressure, demonstrating that sellers control the mid-term trend."
      },
      {
        summary: "50 EMA has crossed below the 200 EMA (Death Cross), reinforcing mid-term bearish continuation paths.",
        detail: "The crossing of the 50-day EMA below the 200-day EMA is a lagging but significant indicator confirming a long-term transition from bull to bear market. This crossover historical invites further algorithmic selling pressure."
      },
      {
        summary: "RSI is oversold (34) but lacks any bullish divergence confirmation, suggesting further room to slide.",
        detail: "While the RSI is low, indicating oversold conditions, there are no structural divergences (such as price making lower lows while RSI makes higher lows) to signal an impending reversal. The trend remains down."
      }
    ],
    fundamentalReasons: [
      "Operating margins compressed down to 17% following price adjustments across key regions.",
      "Supply inventory statistics show elevated production surpluses, triggering distribution delays.",
      "High financing rates in retail credit constrain consumer demand paths for big-ticket EV purchases."
    ]
  },
  {
    id: "nvda",
    name: "NVIDIA Corp.",
    category: "Stock",
    symbol: "NVDA",
    price: 948.22,
    change: 32.40,
    changePercent: 3.54,
    marketCap: "$2.37T",
    volume24h: "$38.2B",
    rsi: 74,
    macd: "Strong Bullish",
    peRatio: "74.8",
    rating: "BUY",
    confidence: 92,
    candles: [
      { open: 880, high: 902, low: 878, close: 895 },
      { open: 895, high: 920, low: 892, close: 914 },
      { open: 914, high: 935, low: 908, close: 922 },
      { open: 922, high: 945, low: 919, close: 938, isForecast: true },
      { open: 938, high: 965, low: 932, close: 948.22, isForecast: true },
      { open: 948.22, high: 985, low: 940, close: 978, isForecast: true }
    ],
    technicalReasons: [
      {
        summary: "Breakout from the $920 level confirmed on high volume, setting new historical resistance boundaries.",
        detail: "NVIDIA spent three weeks consolidating below $920. The breakout was accompanied by trading volumes 40% above the 20-day average, indicating strong institutional buy-in and confirming $920 as the new major support floor."
      },
      {
        summary: "Daily MACD exhibits structural expansion, with expanding positive histogram blocks.",
        detail: "The MACD line is separating bullishly from the signal line on the daily chart. The increasing height of the green histogram bars represents expanding positive momentum, pointing to higher price targets."
      },
      {
        summary: "RSI at 74 signals an overextended market; pullbacks to $920 support should act as buying triggers.",
        detail: "With the Daily RSI entering overbought territory at 74, a short-term pullback is healthy and expected. Investors looking to enter should look for consolidation back towards the $920 breakout point rather than buying at local highs."
      }
    ],
    fundamentalReasons: [
      "Blackwell chip pre-orders are fully booked for the next four fiscal quarters, guaranteeing revenue.",
      "National cloud server investment programs globally have expanded aggregate capital budgets.",
      "Strong pricing leverage maintains gross margins at 76%, outperforming semiconductor competitors."
    ]
  },
  {
    id: "aapl",
    name: "Apple Inc.",
    category: "Stock",
    symbol: "AAPL",
    price: 171.18,
    change: 0.85,
    changePercent: 0.50,
    marketCap: "$2.64T",
    volume24h: "$9.8B",
    rsi: 45,
    macd: "Neutral / Congestion",
    peRatio: "26.2",
    rating: "HOLD",
    confidence: 65,
    candles: [
      { open: 172.5, high: 174, low: 171, close: 171.8 },
      { open: 171.8, high: 173.2, low: 170.8, close: 172.2 },
      { open: 172.2, high: 172.9, low: 169.5, close: 170.1 },
      { open: 170.1, high: 171.5, low: 169.8, close: 170.9, isForecast: true },
      { open: 170.9, high: 172.4, low: 170.5, close: 171.18, isForecast: true },
      { open: 171.18, high: 174.5, low: 169.2, close: 173.1, isForecast: true }
    ],
    technicalReasons: [
      {
        summary: "Price trades inside a sideways consolidation range between $168 and $175.",
        detail: "Apple has been bouncing inside a tight 4% horizontal range. Volumes are declining, confirming a lack of interest from both bulls and bears. A breakout above $175 or breakdown below $168 is needed to trigger a new trend."
      },
      {
        summary: "20 EMA and 50 EMA are flattened and intertwined, indicating complete lack of directional trend.",
        detail: "The short-term and mid-term exponential moving averages have converged. This flattening indicator signals a range-bound market structure where moving average crossovers yield high noise and low reliability."
      },
      {
        summary: "RSI at 45 resides squarely in equilibrium, aligning with near-term range-bound outlooks.",
        detail: "RSI is hovering near 50, indicating neutral momentum. It confirms the consolidation range, with neither buying nor selling pressure dominating the order flow."
      }
    ],
    fundamentalReasons: [
      "Hardware shipments in specific eastern regions recorded soft sales numbers last quarter.",
      "Evolving global app store fee structures create minor friction on software services revenue streams.",
      "Extremely robust share repurchase programs ($110B authorized) buffer lower price boundaries."
    ]
  },
  {
    id: "eurusd",
    name: "EUR/USD",
    category: "Forex",
    symbol: "EUR-USD",
    price: 1.0842,
    change: 0.0034,
    changePercent: 0.31,
    marketCap: "N/A",
    volume24h: "$120B",
    rsi: 54,
    macd: "Slightly Bullish",
    rating: "HOLD",
    confidence: 55,
    candles: [
      { open: 1.0790, high: 1.0820, low: 1.0780, close: 1.0805 },
      { open: 1.0805, high: 1.0830, low: 1.0795, close: 1.0812 },
      { open: 1.0812, high: 1.0845, low: 1.0800, close: 1.0835 },
      { open: 1.0835, high: 1.0850, low: 1.0820, close: 1.0839, isForecast: true },
      { open: 1.0839, high: 1.0862, low: 1.0830, close: 1.0842, isForecast: true },
      { open: 1.0842, high: 1.0910, low: 1.0815, close: 1.0880, isForecast: true }
    ],
    technicalReasons: [
      {
        summary: "EUR/USD rebounded from the lower support bounds of an ascending channel at 1.0780.",
        detail: "The pair successfully retested the floor of its multi-month ascending channel. The immediate bounce off 1.0780 indicates buying interest is clustered at the channel support, supporting a short-term rally back to the channel midline."
      },
      {
        summary: "MACD histogram shows slightly expanding positive bars, pointing towards mild bullish bias.",
        detail: "The MACD line is trending marginally above the signal line. While the momentum is weak, the expansion of green histogram bars indicates that buyers are gradually gaining control of the daily timeframe."
      },
      {
        summary: "Resistance sits at 1.0865, and a daily close above is required to test the next pivot zone at 1.0920.",
        detail: "The 1.0865 level acts as a key horizontal pivot. If bulls can close the day above this resistance, the path opens up to test the psychological resistance at 1.0920."
      }
    ],
    fundamentalReasons: [
      "Expectations of US Federal Reserve policy easing weaken the greenback relative to the Euro.",
      "Eurozone inflation metrics stabilized, reducing immediate ECB rate cut pressure.",
      "Global manufacturing PMIs are recovering, supporting euro-aligned trade flows."
    ]
  },
  {
    id: "gold",
    name: "Gold Spot",
    category: "Commodity",
    symbol: "GOLD",
    price: 2342.15,
    change: 18.50,
    changePercent: 0.80,
    marketCap: "N/A",
    volume24h: "$45B",
    rsi: 68,
    macd: "Bullish Rally",
    rating: "BUY",
    confidence: 80,
    candles: [
      { open: 2310, high: 2325, low: 2305, close: 2318 },
      { open: 2318, high: 2332, low: 2312, close: 2328 },
      { open: 2328, high: 2340, low: 2320, close: 2331 },
      { open: 2331, high: 2338, low: 2322, close: 2335, isForecast: true },
      { open: 2335, high: 2352, low: 2329, close: 2342.15, isForecast: true },
      { open: 2342.15, high: 2380, low: 2330, close: 2372, isForecast: true }
    ],
    technicalReasons: [
      {
        summary: "Bullish continuation flag pattern breakout on daily charts, target extends to $2,420.",
        detail: "Gold spent a week consolidating in a downward flag pattern. Yesterday's breakout above the flag ceiling was confirmed with elevated volume, validating the pattern and pointing to a technical extension target near $2,420."
      },
      {
        summary: "Ascending moving averages configuration provides short-term support buffers at $2,310.",
        detail: "The 20-day, 50-day, and 100-day moving averages are stacked in a bullish alignment. The 20 EMA is currently rising at $2,310, acting as dynamic support on daily market pullbacks."
      },
      {
        summary: "RSI is rising towards 68, signaling strong bullish momentum with minor overbought proximity warning.",
        detail: "RSI is expanding upwards, demonstrating accelerating buying momentum. Because it remains just below the overbought threshold of 70, there is still technical room to run before buyers experience exhaustion."
      }
    ],
    fundamentalReasons: [
      "Central bank purchase volumes remain historically elevated, creating structural support floors.",
      "Escalating geopolitical risk profiles in key shipping corridors incentivize safe-haven hedges.",
      "Long-term inflation hedge allocation demand expands amid high fiscal spending globally."
    ]
  }
];

export const EVENTS_MOCK: GlobalEvent[] = [
  { id: "fed-rate", title: "US Federal Reserve signals interest rate reductions starting Q3 due to inflation cooling.", category: "Macroeconomics", date: "Recent", impactScore: "High Positive", tickers: ["BTC-USD", "NVDA", "EUR-USD", "GOLD"] },
  { id: "oil-rig", title: "North Sea energy rig pipeline explosion disrupts regional Brent crude shipping routes.", category: "Geopolitical Crisis", date: "Recent", impactScore: "Neutral to Negative", tickers: ["GOLD", "TSLA", "EUR-USD"] },
  { id: "ai-chip-ban", title: "EU commission announces stricter compliance rules on computing hardware transfers.", category: "Regulations", date: "Recent", impactScore: "Medium Negative", tickers: ["NVDA", "BTC-USD"] }
];
