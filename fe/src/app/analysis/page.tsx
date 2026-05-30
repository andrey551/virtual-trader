"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { 
  TrendingUp, 
  TrendingDown, 
  LineChart, 
  ArrowLeft, 
  ChevronRight, 
  FileText, 
  RefreshCw, 
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Info
} from "lucide-react";

// Mock Database of Assets
interface Candle {
  open: number;
  high: number;
  low: number;
  close: number;
  isForecast?: boolean;
}

interface TechnicalReason {
  summary: string;
  detail: string;
}

interface Asset {
  id: string;
  name: string;
  category: 'Crypto' | 'Stock' | 'Forex' | 'Commodity';
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  marketCap: string;
  volume24h: string;
  rsi: number;
  macd: string;
  peRatio?: string;
  rating: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  candles: Candle[];
  technicalReasons: TechnicalReason[];
  fundamentalReasons: string[];
}

const ASSETS_MOCK: Asset[] = [
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
        summary: "Support holds firmly at $3,380, keeping structural uptrends intact despite localized pullbacks.",
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
        detail: "Gold spent a week consolidatng in a downward flag pattern. Yesterday's breakout above the flag ceiling was confirmed with elevated volume, validating the pattern and pointing to a technical extension target near $2,420."
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

// Related Geopolitical Events Mock database
interface GlobalEvent {
  id: string;
  title: string;
  category: string;
  date: string;
  impactScore: string;
  tickers: string[];
}

const EVENTS_MOCK: GlobalEvent[] = [
  { id: "fed-rate", title: "US Federal Reserve signals interest rate reductions starting Q3 due to inflation cooling.", category: "Macroeconomics", date: "Recent", impactScore: "High Positive", tickers: ["BTC-USD", "NVDA", "EUR-USD", "GOLD"] },
  { id: "oil-rig", title: "North Sea energy rig pipeline explosion disrupts regional Brent crude shipping routes.", category: "Geopolitical Crisis", date: "Recent", impactScore: "Neutral to Negative", tickers: ["GOLD", "TSLA", "EUR-USD"] },
  { id: "ai-chip-ban", title: "EU commission announces stricter compliance rules on computing hardware transfers.", category: "Regulations", date: "Recent", impactScore: "Medium Negative", tickers: ["NVDA", "BTC-USD"] }
];

function AnalyticsContent() {
  const searchParams = useSearchParams();
  const symbolParam = searchParams.get("symbol") || "BTC-USD";

  const defaultAsset = ASSETS_MOCK.find(a => a.symbol === symbolParam) || ASSETS_MOCK[0];
  const [selectedAsset, setSelectedAsset] = useState<Asset>(defaultAsset);
  
  const [optimizingMsg, setOptimizingMsg] = useState("Consensus parameters synchronized.");
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [forecastOffset, setForecastOffset] = useState(0);

  // Accordion states
  const [showAllTechnical, setShowAllTechnical] = useState(false);
  const [showAllEvents, setShowAllEvents] = useState(false);

  // Interactive Detailed Reason index (NEW request)
  const [expandedReasonIndex, setExpandedReasonIndex] = useState<number | null>(null);

  // Sync state if symbolParam URL changes
  useEffect(() => {
    const match = ASSETS_MOCK.find(a => a.symbol === symbolParam);
    if (match) {
      setSelectedAsset(match);
      setShowAllTechnical(false);
      setShowAllEvents(false);
      setExpandedReasonIndex(null); // Reset detail expansion
    }
  }, [symbolParam]);

  // Optimization simulation loop
  useEffect(() => {
    const messages = [
      "Crawl indices parameters...",
      "Recalculating exponential moving average trends...",
      "Analyzing order book depths...",
      "Consolidating global news sentiment indices...",
      "Updating price channel predictions..."
    ];

    const interval = setInterval(() => {
      setIsOptimizing(true);
      const randMsg = messages[Math.floor(Math.random() * messages.length)];
      setOptimizingMsg(randMsg);
      
      setForecastOffset((Math.random() - 0.5) * (selectedAsset.price * 0.005));

      setTimeout(() => {
        setIsOptimizing(false);
      }, 1000);
    }, 4500);

    return () => clearInterval(interval);
  }, [selectedAsset]);

  const relatedEvents = EVENTS_MOCK.filter(ev => ev.tickers.includes(selectedAsset.symbol));

  const renderDynamicChart = () => {
    const w = 35;
    const gap = 38;
    const paddingLeft = 35;
    
    const candleData = selectedAsset.candles;
    const candlesToRender = candleData.map((c) => {
      if (c.isForecast) {
        return {
          ...c,
          open: c.open + forecastOffset * 0.3,
          close: c.close + forecastOffset,
          high: Math.max(c.high, c.close + forecastOffset, c.open + forecastOffset * 0.3),
          low: Math.min(c.low, c.close + forecastOffset, c.open + forecastOffset * 0.3)
        };
      }
      return c;
    });

    const values = candlesToRender.map(c => [c.high, c.low]).flat();
    const min = Math.min(...values) * 0.99;
    const max = Math.max(...values) * 1.01;
    // Taller chart rendering logic for h-[360px] view box
    const scale = (val: number) => 300 - ((val - min) / (max - min)) * 260;

    return (
      <svg className="w-full h-full" viewBox="0 0 460 320">
        {/* Grid lines */}
        <g stroke="#ebdcb9" strokeWidth="0.5" strokeOpacity="0.3" strokeDasharray="3">
          <line x1="0" y1="40" x2="460" y2="40" />
          <line x1="0" y1="100" x2="460" y2="100" />
          <line x1="0" y1="160" x2="460" y2="160" />
          <line x1="0" y1="220" x2="460" y2="220" />
          <line x1="0" y1="280" x2="460" y2="280" />
        </g>

        {/* Separator Timeline boundary */}
        <line 
          x1={paddingLeft + 3 * (w + gap) - gap/2} 
          y1="10" 
          x2={paddingLeft + 3 * (w + gap) - gap/2} 
          y2="310" 
          stroke="#b45309" 
          strokeWidth="1.5" 
          strokeDasharray="4" 
        />
        <text 
          x={paddingLeft + 3 * (w + gap) - gap/2 - 5} 
          y="20" 
          fill="#b45309" 
          fontSize="8" 
          fontWeight="bold" 
          textAnchor="end"
        >
          HISTORICAL
        </text>
        <text 
          x={paddingLeft + 3 * (w + gap) - gap/2 + 5} 
          y="20" 
          fill="#b45309" 
          fontSize="8" 
          fontWeight="bold" 
          textAnchor="start"
        >
          FORECAST
        </text>

        {/* Render Candles */}
        {candlesToRender.map((candle, idx) => {
          const x = paddingLeft + idx * (w + gap);
          const yOpen = scale(candle.open);
          const yClose = scale(candle.close);
          const yHigh = scale(candle.high);
          const yLow = scale(candle.low);
          
          const isGreen = candle.close >= candle.open;
          const rectY = Math.min(yOpen, yClose);
          const rectH = Math.max(Math.abs(yOpen - yClose), 4);
          
          return (
            <g key={idx}>
              {candle.isForecast ? (
                <>
                  <line 
                    x1={x + w/2} 
                    y1={yHigh} 
                    x2={x + w/2} 
                    y2={yLow} 
                    stroke={isGreen ? '#10b981' : '#f43f5e'} 
                    strokeWidth="1.5" 
                    strokeDasharray="2"
                  />
                  <rect 
                    x={x} 
                    y={rectY} 
                    width={w} 
                    height={rectH} 
                    fill="none" 
                    stroke={isGreen ? '#10b981' : '#f43f5e'} 
                    strokeWidth="1.5"
                    strokeDasharray="3 1"
                    rx="2"
                  />
                </>
              ) : (
                <>
                  <line 
                    x1={x + w/2} 
                    y1={yHigh} 
                    x2={x + w/2} 
                    y2={yLow} 
                    stroke={isGreen ? '#10b981' : '#f43f5e'} 
                    strokeWidth="2" 
                  />
                  <rect 
                    x={x} 
                    y={rectY} 
                    width={w} 
                    height={rectH} 
                    fill={isGreen ? '#10b981' : '#f43f5e'} 
                    rx="2"
                  />
                </>
              )}
            </g>
          );
        })}

        {/* Forecast dotted trend lines */}
        <path
          d={candlesToRender.reduce((path, candle, idx) => {
            const x = paddingLeft + idx * (w + gap) + w/2;
            const y = scale((candle.open + candle.close) / 2);
            return path + (idx === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`);
          }, "")}
          fill="none"
          stroke="#d97706"
          strokeWidth="1.5"
          strokeDasharray="3"
        />
      </svg>
    );
  };

  const displayedTechnicals = showAllTechnical 
    ? selectedAsset.technicalReasons 
    : selectedAsset.technicalReasons.slice(0, 2);

  const displayedEvents = showAllEvents 
    ? relatedEvents 
    : relatedEvents.slice(0, 2);

  const toggleReasonDetail = (index: number) => {
    setExpandedReasonIndex(expandedReasonIndex === index ? null : index);
  };

  return (
    <div className="p-8 space-y-8 animate-fadeIn max-w-7xl mx-auto">
      {/* Page breadcrumbs / status bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-zinc-500 select-none">
          <Link href="/" className="hover:text-amber-700 transition-colors flex items-center gap-1">
            <ArrowLeft className="w-3.5 h-3.5" /> Market Overview
          </Link>
          <ChevronRight className="w-3 h-3 text-zinc-400" />
          <span className="text-zinc-700 font-semibold">{selectedAsset.symbol} Analysis</span>
        </div>

        {/* Live refinement status indicator */}
        <div className="px-3 py-1.5 rounded-xl bg-amber-500/5 border border-amber-500/10 flex items-center gap-2 text-xs text-amber-800">
          <RefreshCw className={`w-3.5 h-3.5 text-amber-600 ${isOptimizing ? 'animate-spin' : ''}`} />
          <span className="font-semibold">{optimizingMsg}</span>
        </div>
      </div>

      {/* Ticker selector row */}
      <div className="flex items-center gap-3 overflow-x-auto pb-2 scrollbar-thin select-none">
        {ASSETS_MOCK.map((asset) => (
          <button
            key={asset.id}
            onClick={() => setSelectedAsset(asset)}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 shrink-0 border ${
              selectedAsset.id === asset.id 
                ? 'bg-amber-600 text-white border-amber-500 shadow-sm' 
                : 'bg-white text-zinc-600 border-[#ebdcb9] hover:bg-amber-500/5 hover:text-zinc-900'
            }`}
          >
            <span>{asset.symbol}</span>
            <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
              asset.rating === 'BUY' ? 'bg-emerald-100 text-emerald-800' :
              asset.rating === 'SELL' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
            }`}>
              {asset.rating}
            </span>
          </button>
        ))}
      </div>

      {/* FULL-WIDTH Chart & Technical Indicators Panel */}
      <div className="p-6 rounded-2xl border border-[#ebdcb9] bg-white shadow-sm space-y-6">
        
        {/* Box Header containing Title, price and consensus badges (Aliged right edge) */}
        <div className="flex flex-col sm:flex-row sm:items-start justify-between border-b border-zinc-100 pb-4 gap-4">
          <div>
            <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">{selectedAsset.category} Analysis Terminal</span>
            <h2 className="text-xl font-bold text-zinc-900 mt-0.5">{selectedAsset.name} ({selectedAsset.symbol})</h2>
          </div>
          
          {/* PRICE + CONSENSUS BADGES aligned on the right edge */}
          <div className="flex items-center gap-4 ml-0 sm:ml-auto">
            <div className="flex items-center gap-2 shrink-0 select-none">
              <span className={`px-2.5 py-1 rounded-full text-xs font-black uppercase tracking-wider ${
                selectedAsset.rating === 'BUY' ? 'bg-emerald-100 text-emerald-800' :
                selectedAsset.rating === 'SELL' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
              }`}>
                Consensus: {selectedAsset.rating}
              </span>
              <span className="text-[11px] text-zinc-600 font-bold bg-zinc-100 px-2.5 py-1 rounded-full border border-zinc-200/55">
                Confidence: {selectedAsset.confidence}%
              </span>
            </div>
            
            <div className="w-px h-8 bg-zinc-200/60 hidden sm:block"></div>
            
            <div className="text-right shrink-0">
              <p className="text-[10px] text-zinc-400 font-bold tracking-tight">Last Quote</p>
              <p className="font-mono font-bold text-lg text-zinc-900 leading-tight mt-0.5">
                {selectedAsset.price.toLocaleString("en-US", { style: selectedAsset.category === 'Forex' ? 'decimal' : 'currency', currency: "USD", minimumFractionDigits: selectedAsset.category === 'Forex' ? 4 : 2 })}
              </p>
              <span className={`text-[11px] font-mono font-bold ${selectedAsset.changePercent >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                {selectedAsset.changePercent >= 0 ? '+' : ''}{selectedAsset.changePercent}%
              </span>
            </div>
          </div>
        </div>

        {/* 70/30 width and h-[460px] height layout inside the unified top card */}
        <div className="grid grid-cols-1 md:grid-cols-10 gap-6 items-stretch">
          
          {/* Left Sub-Column (70%): MASSIVE Candlestick Chart */}
          <div className="md:col-span-7 flex flex-col justify-between h-[460px]">
            <div className="flex-1 bg-[#fdfbf6] border border-[#ebdcb9]/60 rounded-xl overflow-hidden p-4 min-h-[360px]">
              {renderDynamicChart()}
            </div>
            <div className="flex items-center justify-between text-[9px] text-zinc-400 mt-2">
              <span>* Dotted wicks indicate system forecast models.</span>
              <span className="flex items-center gap-1 font-mono text-amber-700 font-bold">
                <span className="w-1.5 h-1.5 bg-amber-600 rounded-full"></span> Live Updates
              </span>
            </div>
          </div>

          {/* Right Sub-Column (30%): Technical Indicators Audit (Expandable & Interactive Accordion) */}
          <div className="md:col-span-3 border-l border-[#ebdcb9]/30 pl-0 md:pl-6 flex flex-col justify-between h-[460px] overflow-hidden">
            <div className="space-y-4 overflow-y-auto h-full pr-1 flex flex-col justify-between">
              <div className="space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-700 flex items-center gap-2 sticky top-0 bg-white pb-2 border-b border-zinc-100 shrink-0">
                  <LineChart className="w-4 h-4 text-amber-600" />
                  Technical Indicators Audit
                </h3>
                
                <div className="space-y-2">
                  {displayedTechnicals.map((reason, idx) => {
                    const isExpanded = expandedReasonIndex === idx;
                    return (
                      <div 
                        key={idx} 
                        className={`p-3 rounded-xl border transition-all cursor-pointer ${
                          isExpanded 
                            ? 'bg-amber-500/10 border-amber-500/30' 
                            : 'bg-zinc-50 hover:bg-amber-500/5 border-zinc-200/60'
                        }`}
                        onClick={() => toggleReasonDetail(idx)}
                      >
                        <div className="flex items-start gap-2 justify-between">
                          <div className="flex gap-2 items-start">
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-600 shrink-0 mt-1.5"></span>
                            <span className="text-xs text-zinc-700 font-medium leading-relaxed">{reason.summary}</span>
                          </div>
                          <span className="text-zinc-400 shrink-0 mt-0.5">
                            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                          </span>
                        </div>

                        {/* Interactive In-depth detail container (NEW request) */}
                        {isExpanded && (
                          <div className="mt-3 pt-2.5 border-t border-amber-500/10 text-xs text-zinc-600 leading-relaxed space-y-1.5 animate-fadeIn">
                            <div className="flex items-center gap-1.5 font-bold text-amber-800 text-[10px] uppercase tracking-wider">
                              <Info className="w-3 h-3 text-amber-600" /> In-depth Analysis
                            </div>
                            <p className="pl-4 border-l border-amber-600/30 italic">{reason.detail}</p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Expand / Collapse triggers */}
              {selectedAsset.technicalReasons.length > 2 && (
                <button 
                  onClick={() => setShowAllTechnical(!showAllTechnical)}
                  className="mt-3 py-1.5 border border-[#ebdcb9]/50 hover:bg-amber-500/5 text-amber-800 font-bold text-[10px] rounded-lg w-full flex items-center justify-center gap-1 select-none shrink-0 cursor-pointer"
                >
                  {showAllTechnical ? (
                    <>
                      <ChevronUp className="w-3 h-3" /> Hide Reasons
                    </>
                  ) : (
                    <>
                      <ChevronDown className="w-3 h-3" /> Show More ({selectedAsset.technicalReasons.length - 2} reasons)
                    </>
                  )}
                </button>
              )}
            </div>
          </div>

        </div>
      </div>

      {/* Bottom Grid: split 2 columns (Left: Fundamental Audit; Right: stats and events) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Fundamental Audit */}
        <div className="lg:col-span-2 space-y-4">
          <div className="p-6 rounded-2xl border border-[#ebdcb9] bg-white shadow-sm space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-700 flex items-center gap-2 border-b border-[#ebdcb9]/40 pb-3 mb-2">
              <FileText className="w-4 h-4 text-amber-600" />
              Fundamental & Macro Factor Audit
            </h3>
            <ul className="space-y-3">
              {selectedAsset.fundamentalReasons.map((reason, idx) => (
                <li key={idx} className="flex gap-3 text-xs text-zinc-600 leading-relaxed items-start">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-600 shrink-0 mt-1.5"></span>
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Right Column: Events & Indexes */}
        <div className="space-y-8">
          
          {/* Related Event Updates (Accordion Expandable) */}
          <div className="p-6 rounded-2xl border border-[#ebdcb9] bg-white shadow-sm space-y-4 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center gap-2 border-b border-[#ebdcb9]/40 pb-3">
                <AlertCircle className="w-4 h-4 text-amber-600" />
                <h3 className="text-xs font-bold text-zinc-700 uppercase tracking-widest">Related Event Updates</h3>
              </div>
              
              {relatedEvents.length === 0 ? (
                <p className="text-xs text-zinc-400 text-center py-4">No recent major events associated with this ticker.</p>
              ) : (
                <div className="space-y-4">
                  {displayedEvents.map((ev) => (
                    <div key={ev.id} className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/10 space-y-2">
                      <div className="flex justify-between items-center text-[9px] font-bold text-amber-700 uppercase tracking-wider">
                        <span>{ev.category}</span>
                        <span>{ev.impactScore}</span>
                      </div>
                      <p className="text-xs font-semibold text-zinc-800 leading-normal">{ev.title}</p>
                      <Link 
                        href={`/events`}
                        className="text-[10px] text-amber-700 font-bold hover:underline inline-flex items-center gap-1 pt-1"
                      >
                        View Impact Map <ChevronRight className="w-3 h-3" />
                      </Link>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Event expand trigger */}
            {relatedEvents.length > 2 && (
              <button 
                onClick={() => setShowAllEvents(!showAllEvents)}
                className="mt-4 py-1.5 border border-[#ebdcb9]/50 hover:bg-amber-500/5 text-amber-800 font-bold text-[10px] rounded-lg w-full flex items-center justify-center gap-1 select-none shrink-0 cursor-pointer"
              >
                {showAllEvents ? (
                  <>
                    <ChevronUp className="w-3 h-3" /> Hide Updates
                  </>
                ) : (
                  <>
                    <ChevronDown className="w-3 h-3" /> Show All Event Updates ({relatedEvents.length})
                  </>
                )}
              </button>
            )}
          </div>

          {/* Financial Index Stats */}
          <div className="p-6 rounded-2xl border border-[#ebdcb9] bg-white shadow-sm space-y-4">
            <h3 className="text-xs font-bold text-zinc-700 uppercase tracking-widest">Financial Indexes</h3>
            
            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-2 border-b border-zinc-100">
                <span className="text-zinc-500">Consensus Verdict</span>
                <span className={`font-bold ${
                  selectedAsset.rating === 'BUY' ? 'text-emerald-600' :
                  selectedAsset.rating === 'SELL' ? 'text-rose-600' : 'text-amber-600'
                }`}>{selectedAsset.rating}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-zinc-100">
                <span className="text-zinc-500">Verdict Confidence</span>
                <span className="font-semibold text-zinc-800">{selectedAsset.confidence}%</span>
              </div>
              <div className="flex justify-between py-2 border-b border-zinc-100">
                <span className="text-zinc-500">MACD Signal</span>
                <span className="font-semibold text-zinc-800">{selectedAsset.macd}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-zinc-100">
                <span className="text-zinc-500">Market Capitalization</span>
                <span className="font-semibold text-zinc-800">{selectedAsset.marketCap}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-zinc-100">
                <span className="text-zinc-500">24-Hour Trading Volume</span>
                <span className="font-semibold text-zinc-800">{selectedAsset.volume24h}</span>
              </div>
              {selectedAsset.peRatio && (
                <div className="flex justify-between py-2 border-b border-zinc-100">
                  <span className="text-zinc-500">Price-to-Earnings (P/E)</span>
                  <span className="font-semibold text-zinc-800">{selectedAsset.peRatio}</span>
                </div>
              )}
            </div>
          </div>

        </div>
        
      </div>
    </div>
  );
}

export default function AnalysisPage() {
  return (
    <Suspense fallback={
      <div className="flex-1 flex items-center justify-center p-8 text-zinc-500 font-semibold text-sm">
        Loading analytics profiles...
      </div>
    }>
      <AnalyticsContent />
    </Suspense>
  );
}
