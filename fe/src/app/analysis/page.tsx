"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { 
  LineChart, 
  ArrowLeft, 
  ChevronRight, 
  FileText, 
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Info,
  Search
} from "lucide-react";

import DynamicChart from "./DynamicChart";
import { BACKEND_URL, WS_URL } from "../../config";

interface ChartCandle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  isForecast?: boolean;
}

interface AnalyticsAsset {
  id: string;
  name: string;
  category: string;
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  marketCap: string;
  volume24h: string;
  rsi: number;
  macd: string;
  peRatio?: string;
  rating: string;
  confidence: number;
  candles: ChartCandle[];
  technicalReasons: { summary: string; detail: string }[];
  fundamentalReasons: string[];
  predictionAccuracy?: number;
}

function AnalyticsContent() {
  const searchParams = useSearchParams();
  const symbolParam = searchParams.get("symbol") || "BTC-USD";

  const [searchQuery, setSearchQuery] = useState("");
  const [assetsList, setAssetsList] = useState<AnalyticsAsset[]>([]);
  
  const [selectedAsset, setSelectedAsset] = useState<AnalyticsAsset>({
    id: "loading",
    name: "Loading asset...",
    category: "Crypto",
    symbol: symbolParam,
    price: 0.0,
    change: 0.0,
    changePercent: 0.0,
    marketCap: "N/A",
    volume24h: "N/A",
    rsi: 50,
    macd: "Neutral",
    rating: "HOLD",
    confidence: 0,
    predictionAccuracy: 0,
    candles: [],
    technicalReasons: [],
    fundamentalReasons: []
  });

  const filteredAssets = assetsList.filter(asset => 
    asset.symbol.toLowerCase().includes(searchQuery.toLowerCase())
  );
  
  const [forecastOffset, setForecastOffset] = useState(0);
  const [liveStatus, setLiveStatus] = useState("SYS_ACTIVE");
  const [selectedInterval, setSelectedInterval] = useState("1d");
  const [selectedPeriod, setSelectedPeriod] = useState("3mo");

  // Accordion states
  const [showAllTechnical, setShowAllTechnical] = useState(false);
  const [showAllEvents, setShowAllEvents] = useState(false);

  // Interactive Detailed Reason index
  const [expandedReasonIndex, setExpandedReasonIndex] = useState<number | null>(null);

  // Reset state during render if asset changed (instead of using a synchronous useEffect)
  const [prevSymbol, setPrevSymbol] = useState(symbolParam);
  if (symbolParam !== prevSymbol) {
    setPrevSymbol(symbolParam);
    setShowAllTechnical(false);
    setShowAllEvents(false);
    setExpandedReasonIndex(null);
    setForecastOffset(0);
    setLiveStatus("SYS_ACTIVE");
    setSelectedInterval("1d");
    setSelectedPeriod("3mo");
  }

  interface ApiAssetSummary {
    id: number;
    ticker: string;
    name: string;
    category: string;
    system_verdict: string;
    confidence_level: string | number;
    accuracy_score: string | number;
    price?: number;
    changePercent?: number;
  }

  // Load assets list on start
  useEffect(() => {
    async function loadAssets() {
      try {
        const res = await fetch(`${BACKEND_URL}/api/assets`);
        if (res.ok) {
          const data = await res.json();
          const mapped = data.map((item: ApiAssetSummary) => {
            let cat = item.category;
            if (cat === "STOCKS") cat = "Stocks";
            else if (cat === "CRYPTO") cat = "Crypto";
            else if (cat === "FOREX") cat = "Forex";
            else if (cat === "INDEX") cat = "Indices";
            
            return {
              id: String(item.id),
              symbol: item.ticker,
              name: item.name,
              category: cat,
              price: Number(item.price || 100.0),
              changePercent: Number(item.changePercent || 0.0),
              rating: item.system_verdict,
              confidence: Number(item.confidence_level),
              predictionAccuracy: Number(item.accuracy_score)
            };
          });
          setAssetsList(mapped);
        }
      } catch {
        // fallback silently
      }
    }
    loadAssets();
  }, []);

  // Load selected asset details and candles on symbol, interval, or period changes
  useEffect(() => {
    async function loadAssetDetail() {
      try {
        const detailRes = await fetch(`${BACKEND_URL}/api/assets/${symbolParam}`);
        const candleRes = await fetch(`${BACKEND_URL}/api/assets/${symbolParam}/candles?interval=${selectedInterval}&period=${selectedPeriod}`);
        
        if (detailRes.ok && candleRes.ok) {
          const detail = await detailRes.json();
          const candleData = await candleRes.json();
          
          interface ApiCandle {
            time: string;
            open: number;
            high: number;
            low: number;
            close: number;
            volume: number;
          }

          const rawCandles = candleData.candles.map((c: ApiCandle) => ({
            time: c.time,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close,
            volume: c.volume
          }));
          
          // Append 8 simulated forecast candles
          const candles = [...rawCandles];
          if (candles.length > 0) {
            let lastClose = candles[candles.length - 1].close;
            const isCrypto = detail.category === "CRYPTO";
            const stepPercent = isCrypto ? 0.015 : 0.005;
            
            for (let i = 1; i <= 8; i++) {
              const bias = detail.system_verdict.includes("BUY") ? 0.35 : (detail.system_verdict.includes("SELL") ? -0.35 : 0.0);
              const change = (Math.random() - 0.5 + bias) * stepPercent;
              const nextClose = lastClose * (1 + change);
              const nextOpen = lastClose;
              const nextHigh = Math.max(nextOpen, nextClose) * (1 + Math.random() * 0.004);
              const nextLow = Math.min(nextOpen, nextClose) * (1 - Math.random() * 0.004);
              
              candles.push({
                time: `Forecast T+${i}`,
                open: nextOpen,
                high: nextHigh,
                low: nextLow,
                close: nextClose,
                volume: 0,
                isForecast: true
              });
              lastClose = nextClose;
            }
          }
          
          const mappedAsset = {
            id: String(detail.id),
            symbol: detail.ticker,
            name: detail.name,
            category: detail.category === "STOCKS" ? "Stocks" : (detail.category === "CRYPTO" ? "Crypto" : (detail.category === "FOREX" ? "Forex" : "Indices")),
            price: Number(detail.price || 0.0),
            change: Number(detail.change || 0.0),
            changePercent: Number(detail.changePercent || 0.0),
            marketCap: detail.marketCap || "N/A",
            volume24h: detail.volume24h || "N/A",
            peRatio: detail.peRatio || undefined,
            rsi: Number(detail.rsi || 50.0),
            macd: detail.macd || "Neutral",
            rating: detail.system_verdict || "HOLD",
            confidence: Number(detail.confidence_level || 0),
            predictionAccuracy: Number(detail.accuracy_score || 0),
            technicalReasons: detail.technicalReasons || [],
            fundamentalReasons: detail.fundamentalReasons || [],
            candles: candles
          };
          setSelectedAsset(mappedAsset);
        }
      } catch (err) {
        console.error("Failed to load asset details:", err);
      }
    }
    loadAssetDetail();
  }, [symbolParam, selectedInterval, selectedPeriod]);

  // WebSocket Live Price wiggler for the selected asset
  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/prices?tickers=${symbolParam}`);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "price_update" && data.ticker === symbolParam) {
          setSelectedAsset((prev: AnalyticsAsset) => {
            if (prev && prev.symbol === symbolParam) {
              return {
                ...prev,
                price: data.price,
                changePercent: data.changePercent
              };
            }
            return prev;
          });
        }
      } catch {
        // ignore
      }
    };
    return () => ws.close();
  }, [symbolParam]);

  // Optimization simulation loop
  useEffect(() => {
    const interval = setInterval(() => {
      setLiveStatus("COMPUTING...");
      setForecastOffset((Math.random() - 0.5) * (selectedAsset.price * 0.005));
      
      setTimeout(() => {
        setLiveStatus("SYS_ACTIVE");
      }, 1500);
    }, 4500);

    return () => clearInterval(interval);
  }, [selectedAsset.symbol, selectedAsset.price]);

  const [relatedEvents, setRelatedEvents] = useState<{
    id: string;
    title: string;
    description: string;
    category: string;
    severity: "high" | "medium" | "low";
    impactScore: string;
  }[]>([]);

  useEffect(() => {
    async function loadRelatedEvents() {
      try {
        const res = await fetch(`${BACKEND_URL}/api/events/search-similar?query_text=${symbolParam}&limit=5`);
        if (res.ok) {
          const data = await res.json();
          interface ApiNewsEvent {
            id: number;
            title: string;
            summary?: string;
            sentiment_score: string | number;
          }
          const mapped = data.map((ev: ApiNewsEvent) => {
            const score = Math.abs(Number(ev.sentiment_score || 0));
            let severity: "high" | "medium" | "low" = "low";
            if (score >= 0.6) severity = "high";
            else if (score >= 0.3) severity = "medium";
            
            return {
              id: String(ev.id),
              title: ev.title,
              description: ev.summary || "",
              category: ev.title.toLowerCase().includes("oil") ? "Energy & Geopolitical" : "Macroeconomics",
              severity: severity,
              impactScore: Number(ev.sentiment_score) >= 0 ? "POSITIVE" : "NEGATIVE"
            };
          });
          setRelatedEvents(mapped);
        }
      } catch {
        // ignore
      }
    }
    loadRelatedEvents();
  }, [symbolParam]);

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
      {/* Page breadcrumbs / Search bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-xs text-zinc-500 select-none">
          <Link href="/" className="hover:text-amber-700 transition-colors flex items-center gap-1">
            <ArrowLeft className="w-3.5 h-3.5" /> Market Overview
          </Link>
          <ChevronRight className="w-3 h-3 text-zinc-400" />
          <span className="text-zinc-700 font-semibold">{selectedAsset.symbol} Analysis</span>
        </div>

        {/* Search Ticker Input replacing the live status indicator */}
        <div className="relative w-full sm:w-64 select-none shrink-0">
          <input 
            type="text" 
            placeholder="Search / switch symbol..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white border border-[#ebdcb9] rounded-xl px-3 py-1.5 pl-8 text-xs text-zinc-850 focus:outline-none focus:border-amber-500 font-mono shadow-inner transition-colors"
          />
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-400" />
          {searchQuery && (
            <button 
              onClick={() => setSearchQuery("")}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[10px] text-zinc-400 hover:text-zinc-700 cursor-pointer"
            >
              ×
            </button>
          )}
        </div>
      </div>

      {/* Ticker selector row */}
      <div className="flex items-center gap-3 overflow-x-auto pb-2 scrollbar-thin select-none">
        {filteredAssets.map((asset) => (
          <Link
            key={asset.id}
            href={`/analysis?symbol=${asset.symbol}`}
            className={`px-4 py-2 rounded-xl text-xs font-mono font-bold transition-all flex items-center gap-2 shrink-0 border ${
              selectedAsset.id === asset.id 
                ? 'bg-amber-600 text-white border-amber-500 shadow-sm' 
                : 'bg-white text-zinc-600 border-[#ebdcb9] hover:bg-amber-500/5 hover:text-zinc-900'
            }`}
          >
            <span className="opacity-40 font-mono text-[9px]">{"//"}</span>
            <span>{asset.symbol}</span>
            <span className={`px-1.5 py-0.5 rounded text-[8px] font-mono font-bold ${
              asset.rating === 'BUY' ? 'bg-emerald-100 text-emerald-800' :
              asset.rating === 'SELL' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
            }`}>
              {asset.rating}
            </span>
          </Link>
        ))}
        {filteredAssets.length === 0 && (
          <span className="text-xs text-zinc-400 font-mono italic">No cached symbols matched</span>
        )}
      </div>

      {/* FULL-WIDTH Chart & Technical Indicators Panel */}
      <div className="relative p-6 rounded-2xl border border-[#ebdcb9] bg-white shadow-sm space-y-6">
        {/* Corner Crosshairs */}
        <span className="absolute -top-1.5 -left-1.5 text-amber-500/30 text-xs select-none pointer-events-none font-mono">+</span>
        <span className="absolute -top-1.5 -right-1.5 text-amber-500/30 text-xs select-none pointer-events-none font-mono">+</span>
        <span className="absolute -bottom-1.5 -left-1.5 text-amber-500/30 text-xs select-none pointer-events-none font-mono">+</span>
        <span className="absolute -bottom-1.5 -right-1.5 text-amber-500/30 text-xs select-none pointer-events-none font-mono">+</span>
        
        {/* Box Header containing Title, price and consensus badges (Aligned right edge) */}
        <div className="relative flex flex-col sm:flex-row sm:items-start justify-between border-b border-zinc-100 pb-4 gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[9px] font-mono text-zinc-400 uppercase tracking-wider bg-zinc-100 px-1.5 py-0.5 rounded select-none">
                {"SYS_PORT // 0X"}{selectedAsset.id.toUpperCase()}
              </span>
              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">{selectedAsset.category} Analysis Terminal</span>
            </div>
            <h2 className="text-xl font-black text-zinc-900 mt-1.5 font-mono">{selectedAsset.name} ({selectedAsset.symbol})</h2>
          </div>
          
          {/* PRICE + CONSENSUS BADGES aligned on the right edge */}
          <div className="flex items-center gap-4 ml-0 sm:ml-auto">
            <div className="flex items-center gap-2 shrink-0 select-none">
              <span className={`px-2.5 py-1 rounded-full text-xs font-mono font-bold uppercase tracking-wider ${
                selectedAsset.rating === 'BUY' ? 'bg-emerald-100 text-emerald-800' :
                selectedAsset.rating === 'SELL' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
              }`}>
                Consensus: {selectedAsset.rating}
              </span>
              <span className="text-[11px] text-zinc-600 font-mono font-bold bg-zinc-100 px-2.5 py-1 rounded-full border border-zinc-200/55">
                Confidence: {selectedAsset.confidence}%
              </span>
              <span className="text-[11px] text-amber-800 font-mono font-bold bg-amber-500/10 px-2.5 py-1 rounded-full border border-amber-500/20">
                Accuracy: {selectedAsset.predictionAccuracy || 85}%
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

        {/* Timeframe/Interval Selector Tab-bar */}
        <div className="flex items-center gap-2 border-b border-zinc-100 pb-2 select-none">
          <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mr-2 font-mono">Timeframe:</span>
          {[
            { label: "1m", value: "1m", period: "1d" },
            { label: "5m", value: "5m", period: "1d" },
            { label: "15m", value: "15m", period: "5d" },
            { label: "1h", value: "1h", period: "1mo" },
            { label: "1d", value: "1d", period: "3mo" }
          ].map((tf) => (
            <button
              key={tf.value}
              onClick={() => {
                setSelectedInterval(tf.value);
                setSelectedPeriod(tf.period);
              }}
              className={`px-3 py-1 rounded-lg text-xs font-mono font-bold transition-all border ${
                selectedInterval === tf.value
                  ? "bg-amber-500/10 text-amber-900 border-amber-500/30"
                  : "bg-zinc-50 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-800 border-transparent cursor-pointer"
              }`}
            >
              {tf.label}
            </button>
          ))}
        </div>

        {/* 70/30 width and h-[460px] height layout inside the unified top card */}
        <div className="grid grid-cols-1 md:grid-cols-10 gap-6 items-stretch">
          
          {/* Left Sub-Column (70%): MASSIVE Candlestick Chart */}
          <div className="md:col-span-7 flex flex-col justify-between h-[460px]">
            <div className="flex-1 bg-[#fdfbf6] border border-[#ebdcb9]/60 rounded-xl overflow-hidden p-4 min-h-[360px]">
              <DynamicChart selectedAsset={selectedAsset} forecastOffset={forecastOffset} interval={selectedInterval} />
            </div>
            <div className="flex items-center justify-between text-[9px] text-zinc-400 mt-2">
              <span>* Dotted wicks indicate system forecast models.</span>
              <span className="flex items-center gap-1.5 font-mono text-amber-700 font-bold select-none text-[9px] bg-amber-500/5 px-2 py-0.5 rounded border border-amber-500/10 transition-all">
                <span className={`w-1.5 h-1.5 rounded-full bg-amber-600 ${liveStatus === 'COMPUTING...' ? 'animate-ping' : 'animate-pulse'}`}></span>
                {liveStatus === 'COMPUTING...' ? 'REFINING FORECAST...' : 'LIVE // UPDATED'}
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
                  {displayedTechnicals.map((reason: { summary: string; detail: string }, idx: number) => {
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

                        {/* Interactive In-depth detail container */}
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
              {selectedAsset.fundamentalReasons.map((reason: string, idx: number) => (
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
                <span className="text-zinc-500">Model Accuracy (Hit Rate)</span>
                <span className="font-bold text-amber-700">{selectedAsset.predictionAccuracy || 85}%</span>
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
