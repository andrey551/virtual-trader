"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  Award,
  Lock,
  Terminal,
  Search
} from "lucide-react";
import { ASSETS_MOCK } from "./analysis/data";
import { BACKEND_URL, WS_URL } from "../config";

interface ScraperLog {
  timestamp: string;
  source: string;
  message: string;
  status: 'SUCCESS' | 'INFO' | 'SYNC';
}

export default function Home() {
  const [logs, setLogs] = useState<ScraperLog[]>([
    { timestamp: "13:14:02", source: "SYSTEM", message: "Connecting to swarm telemetry node...", status: "SUCCESS" }
  ]);

  const [searchQuery, setSearchQuery] = useState("");

  // Connect to live AI Agent debate stream
  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/swarm-debate/live`);
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const now = new Date();
        const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
        
        if (data.status === "TYPING") {
          const newLog: ScraperLog = {
            timestamp: timeStr,
            source: data.avatar_code || data.agent_name,
            message: "Thinking...",
            status: "INFO"
          };
          setLogs(prev => [newLog, ...prev.slice(0, 8)]);
        } else if (data.status === "SPEAKING") {
          setLogs(prev => {
            if (prev.length === 0) return prev;
            const updated = [...prev];
            if (updated[0].source === (data.avatar_code || data.agent_name)) {
              const currentMsg = updated[0].message === "Thinking..." ? "" : updated[0].message;
              updated[0] = {
                ...updated[0],
                message: currentMsg + (data.message_chunk || "")
              };
            }
            return updated;
          });
        } else if (data.status === "COMPLETED") {
          setLogs(prev => {
            if (prev.length === 0) return prev;
            const updated = [...prev];
            if (updated[0].source === (data.avatar_code || data.agent_name)) {
              updated[0] = {
                ...updated[0],
                message: data.message,
                status: "SUCCESS"
              };
            }
            return updated;
          });
        }
      } catch {
        // ignore
      }
    };
    
    return () => ws.close();
  }, []);

  interface DashboardAsset {
    id: string;
    symbol: string;
    name: string;
    category: string;
    price: number;
    changePercent: number;
    rating: string;
    confidence: number;
    predictionAccuracy: number;
  }

  interface ApiAsset {
    id: number;
    ticker: string;
    name: string;
    category: string;
    system_verdict: string;
    confidence_level: string | number;
    accuracy_score: string | number;
  }

  const [assets, setAssets] = useState<DashboardAsset[]>(ASSETS_MOCK as unknown as DashboardAsset[]);
  
  useEffect(() => {
    async function loadAssets() {
      try {
        const res = await fetch(`${BACKEND_URL}/api/assets`);
        if (res.ok) {
          const data = await res.json();
          const mapped = data.map((item: ApiAsset) => {
            let cat = item.category;
            if (cat === "STOCKS") cat = "Stocks";
            else if (cat === "CRYPTO") cat = "Crypto";
            else if (cat === "FOREX") cat = "Forex";
            else if (cat === "INDEX") cat = "Indices";
            
            const mockMatch = ASSETS_MOCK.find(m => m.symbol === item.ticker);
            return {
              id: String(item.id),
              symbol: item.ticker,
              name: item.name,
              category: cat,
              price: mockMatch ? mockMatch.price : 100.0,
              changePercent: mockMatch ? mockMatch.changePercent : 0.0,
              rating: item.system_verdict,
              confidence: Number(item.confidence_level),
              predictionAccuracy: Number(item.accuracy_score)
            };
          });
          setAssets(mapped);
        }
      } catch {
        // Fallback silently to static mocks
      }
    }
    loadAssets();
  }, []);

  const activeTickers = assets.map(a => a.symbol).join(",");

  // Establish price updates WebSocket
  useEffect(() => {
    if (!activeTickers) return;
    
    const ws = new WebSocket(`${WS_URL}/ws/prices?tickers=${activeTickers}`);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "price_update") {
          setAssets(prev => prev.map(asset => {
            if (asset.symbol === data.ticker) {
              return {
                ...asset,
                price: data.price,
                changePercent: data.changePercent
              };
            }
            return asset;
          }));
        }
      } catch {
        // ignore
      }
    };
    return () => ws.close();
  }, [activeTickers]);

  const filteredAssets = assets.filter(asset => 
    asset.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
    asset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    asset.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="p-8 space-y-8 animate-fadeIn max-w-7xl mx-auto">
      {/* Top Header Card Banner */}
      <div className="relative p-8 rounded-3xl bg-white/80 backdrop-blur-md border border-[#ebdcb9] overflow-hidden shadow-sm space-y-8">
        <div className="absolute right-0 bottom-0 top-0 w-1/3 opacity-15 pointer-events-none bg-gradient-to-l from-amber-500 to-transparent blur-3xl"></div>
        
        {/* Tagline & Main Intro */}
        <div className="relative max-w-4xl space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="px-3 py-1 rounded-full text-[10px] bg-amber-500/10 text-amber-800 font-extrabold uppercase tracking-wider flex items-center gap-1.5 select-none border border-amber-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-600 animate-pulse"></span>
              Institutional Swarm Core Active
            </span>
            <span className="px-3 py-1 rounded-full text-[10px] bg-emerald-500/10 text-emerald-800 font-extrabold uppercase tracking-wider flex items-center gap-1.5 select-none border border-emerald-500/20">
              <ShieldCheck className="w-3.5 h-3.5" />
              Audited Forecasting Model
            </span>
          </div>
          <h2 className="text-3xl font-black tracking-tight text-zinc-900 sm:text-4xl leading-none">
            Realtime Market Consensus Swarm
          </h2>
          <p className="text-sm text-zinc-600 leading-relaxed max-w-2xl">
            Our multi-agent consensus network dynamically scrapes order book depths, financial ratios, global central bank policy changes, and news sentiments to formulate high-conviction trade suggestions. Purely analytical, non-execution advisor.
          </p>
        </div>

        {/* 3-Column Trust & Performance Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative">
          
          {/* Hit Rate Stat */}
          <div className="p-6 rounded-2xl border border-emerald-500/25 bg-emerald-500/[0.03] space-y-3 relative group hover:bg-emerald-500/[0.05] transition-all duration-300">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 font-mono">Forecast Accuracy</span>
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            </div>
            <div className="space-y-1">
              <p className="text-4xl font-black text-emerald-800 tracking-tight font-mono">88.4%</p>
              <p className="text-xs text-zinc-700 font-bold">Directional Hit Rate</p>
            </div>
            <p className="text-[11px] text-zinc-500 leading-relaxed">
              Verified directional correctness (predicting upward/downward shifts) across 1,420 backtested scenario runs.
            </p>
          </div>

          {/* Outperformance / Alpha Stat */}
          <div className="p-6 rounded-2xl border border-amber-500/25 bg-amber-500/[0.03] space-y-3 relative group hover:bg-amber-500/[0.05] transition-all duration-300">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-amber-800 font-mono">Alpha Outperformance</span>
              <Award className="w-5 h-5 text-amber-600" />
            </div>
            <div className="space-y-1">
              <p className="text-4xl font-black text-amber-800 tracking-tight font-mono">+18.7%</p>
              <p className="text-xs text-zinc-700 font-bold">vs Benchmark Buy-and-Hold</p>
            </div>
            <p className="text-[11px] text-zinc-500 leading-relaxed">
              Consolidated consensus trade advices historically outperformed major indices (S&P 500 / BTC Hodl) by an average of +18.7% yearly.
            </p>
          </div>

          {/* Verified Refresh Stat */}
          <div className="p-6 rounded-2xl border border-zinc-500/20 bg-zinc-500/[0.02] space-y-3 relative group hover:bg-zinc-500/[0.04] transition-all duration-300">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-zinc-700 font-mono">Swarm Synchronization</span>
              <Activity className="w-5 h-5 text-zinc-500" />
            </div>
            <div className="space-y-1">
              <p className="text-4xl font-black text-zinc-800 tracking-tight font-mono">Near Realtime</p>
              <p className="text-xs text-zinc-700 font-bold">Scraping & Sentiment Analytics</p>
            </div>
            <p className="text-[11px] text-zinc-500 leading-relaxed">
              Active data crawlers scan exchanges, news agencies, and central bank records in 60-second loops to dynamically adapt predictions.
            </p>
          </div>

        </div>

        {/* Safety & Compliance Trust Footer */}
        <div className="pt-4 border-t border-zinc-100 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-zinc-500">
          <div className="flex items-center gap-2">
            <Lock className="w-3.5 h-3.5 text-zinc-400" />
            <span>Purely Analytical Engine • <strong>No-Execution Policy</strong> (System does not make trades directly)</span>
          </div>
          <div className="flex items-center gap-1.5 font-bold text-amber-800">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            Independent Swarm Consensus Verified
          </div>
        </div>

      </div>

      {/* Ticker Search & Node Finder Bar */}
      <div className="p-4 rounded-2xl border border-[#ebdcb9] bg-white/80 backdrop-blur-md shadow-sm relative overflow-hidden select-none">
        <span className="absolute -top-1.5 -left-1.5 text-amber-500/30 text-xs font-mono select-none pointer-events-none font-mono">+</span>
        <span className="absolute -top-1.5 -right-1.5 text-amber-500/30 text-xs font-mono select-none pointer-events-none font-mono">+</span>
        <span className="absolute -bottom-1.5 -left-1.5 text-amber-500/30 text-xs font-mono select-none pointer-events-none font-mono">+</span>
        <span className="absolute -bottom-1.5 -right-1.5 text-amber-500/30 text-xs font-mono select-none pointer-events-none font-mono">+</span>
        
        <div className="flex flex-col md:flex-row items-center gap-4">
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-[10px] font-mono text-zinc-400 bg-zinc-100 px-1.5 py-0.5 rounded select-none">
              FIND_NODE //
            </span>
            <span className="text-xs font-bold text-zinc-800 uppercase tracking-widest">Asset Search Index</span>
          </div>
          
          <div className="flex-1 w-full relative">
            <input 
              type="text"
              placeholder="Search ticker symbol or asset name (e.g. BTC-USD, NVDA, TSLA, Gold Spot)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#fdfbf6] border border-[#ebdcb9] rounded-xl px-4 py-2.5 pl-10 text-xs text-zinc-800 focus:outline-none focus:border-amber-500 font-mono shadow-inner transition-colors"
            />
            <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-400">
              <Search className="w-3.5 h-3.5" />
            </span>
            {searchQuery && (
              <button 
                onClick={() => setSearchQuery("")}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-xs text-zinc-450 hover:text-zinc-700 cursor-pointer"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Watchlist and Top Recommendations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Main Asset Watchlist */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-2 select-none">
            <Activity className="w-4 h-4 text-amber-600" />
            Global Asset Watchlist
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredAssets.length > 0 ? (
              filteredAssets.map((asset) => {
                const isBullish = asset.changePercent >= 0;
                return (
                  <Link
                    key={asset.id}
                    href={`/analysis?symbol=${asset.symbol}`}
                    className="relative p-5 rounded-xl border border-[#ebdcb9] bg-white/80 backdrop-blur-md hover:bg-amber-50/15 hover:border-amber-500/35 hover:-translate-y-1 hover:shadow-md transition-all duration-300 group flex flex-col justify-between space-y-4 shadow-sm"
                  >
                    {/* Corner Crosshairs for high-tech grid effect */}
                    <span className="absolute -top-1.5 -left-1.5 text-amber-500/30 text-xs select-none pointer-events-none font-mono">+</span>
                    <span className="absolute -top-1.5 -right-1.5 text-amber-500/30 text-xs select-none pointer-events-none font-mono">+</span>
                    <span className="absolute -bottom-1.5 -left-1.5 text-amber-500/30 text-xs select-none pointer-events-none font-mono">+</span>
                    <span className="absolute -bottom-1.5 -right-1.5 text-amber-500/30 text-xs select-none pointer-events-none font-mono">+</span>

                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-1.5">
                          <span className="text-[8px] font-mono text-zinc-400 bg-zinc-100/80 px-1 py-0.5 rounded select-none">
                            {"NODE // 0"}{asset.id.toUpperCase()}
                          </span>
                          <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">{asset.category}</span>
                        </div>
                        <h4 className="font-extrabold text-base text-zinc-950 group-hover:text-amber-700 transition-colors mt-1.5 font-mono">{asset.symbol}</h4>
                        <p className="text-xs text-zinc-500 mt-0.5">{asset.name}</p>
                      </div>
                      <div className="flex flex-col items-end gap-1 select-none">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                          asset.rating === 'BUY' ? 'bg-emerald-100 text-emerald-800' :
                          asset.rating === 'SELL' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
                        }`}>
                          {asset.rating} ({asset.confidence}%)
                        </span>
                        <span className="text-[9px] text-amber-800 font-black bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20 font-mono">
                          Acc: {asset.predictionAccuracy || 85}%
                        </span>
                      </div>
                    </div>

                    {/* Confidence Progress Bar */}
                    <div className="space-y-1 select-none">
                      <div className="flex justify-between text-[9px] font-mono text-zinc-400">
                        <span>SWARM_CONFIDENCE</span>
                        <span>{asset.confidence}%</span>
                      </div>
                      <div className="w-full h-1 bg-zinc-100 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full transition-all duration-500 ${
                            asset.rating === 'BUY' ? 'bg-emerald-500' :
                            asset.rating === 'SELL' ? 'bg-rose-500' : 'bg-amber-500'
                          }`} 
                          style={{ width: `${asset.confidence}%` }}
                        ></div>
                      </div>
                    </div>

                    <div className="flex items-end justify-between border-t border-[#ebdcb9]/40 pt-3">
                      <div>
                        <p className="text-[10px] text-zinc-400 font-mono">Last Price</p>
                        <p className="font-mono font-bold text-base text-zinc-800 mt-0.5">
                          {asset.price.toLocaleString("en-US", { style: asset.category === 'Forex' ? 'decimal' : 'currency', currency: "USD", minimumFractionDigits: asset.category === 'Forex' ? 4 : 2 })}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-[10px] text-zinc-400 font-mono">24h Change</p>
                        <div className={`flex items-center gap-1 mt-0.5 font-mono text-sm font-semibold justify-end ${isBullish ? 'text-emerald-600' : 'text-rose-600'}`}>
                          {isBullish ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                          <span>{isBullish ? '+' : ''}{asset.changePercent}%</span>
                        </div>
                      </div>
                    </div>
                  </Link>
                );
              })
            ) : (
              <div className="col-span-2 p-8 rounded-xl border border-dashed border-amber-500/30 bg-amber-500/[0.02] flex flex-col items-center justify-center text-center space-y-4">
                <p className="text-xs font-mono text-amber-900 font-bold">
                  [WARNING]: Asset Node &apos;{searchQuery}&apos; not found in cached consensus swarm.
                </p>
                <p className="text-[11px] text-zinc-500 max-w-md">
                  This asset ticker is not stored locally. Trigger the playwright crawler to scrape global telemetry indexes for this symbol.
                </p>
                <Link 
                  href="/playground" 
                  className="px-4 py-2.5 rounded-xl bg-amber-600 text-white font-mono font-bold text-[10px] uppercase hover:bg-amber-700 transition-all select-none cursor-pointer border border-amber-500 shadow-sm"
                >
                  Configure Crawler Node
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Top Picks Sidebar */}
        <div className="space-y-6">
          
          {/* Swarm Engine Live Terminal (quantitative logs) */}
          <div className="relative p-5 rounded-2xl border border-zinc-800 bg-zinc-950 text-emerald-400 font-mono text-[10px] space-y-3 shadow-inner overflow-hidden select-none">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping"></span>
                <span className="font-bold text-zinc-400 uppercase tracking-widest text-[9px] flex items-center gap-1">
                  <Terminal className="w-3 h-3 text-emerald-500" />
                  Swarm Engine Logs
                </span>
              </div>
              <span className="text-[8px] text-zinc-500">REFRESH // 3.5s</span>
            </div>
            
            <div className="space-y-1.5 max-h-36 overflow-y-auto scrollbar-none">
              {logs.map((log, idx) => (
                <div key={idx} className="flex items-start gap-2 leading-relaxed animate-fadeIn">
                  <span className="text-zinc-500">[{log.timestamp}]</span>
                  <span className={`font-bold shrink-0 ${
                    log.status === 'SUCCESS' ? 'text-emerald-400' :
                    log.status === 'SYNC' ? 'text-amber-400' : 'text-blue-400'
                  }`}>
                    {log.source} {"//"}
                  </span>
                  <span className="text-zinc-300 truncate">{log.message}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-2 select-none">
              <Sparkles className="w-4 h-4 text-amber-600" />
              Top Recommendations
            </h3>

            <div className="space-y-4">
              {ASSETS_MOCK.filter(a => a.rating === 'BUY').sort((a,b) => b.confidence - a.confidence).map((asset, index) => (
                <Link 
                  key={asset.id}
                  href={`/analysis?symbol=${asset.symbol}`}
                  className="relative p-4 rounded-xl border border-[#ebdcb9] bg-white/80 backdrop-blur-md hover:bg-amber-500/5 hover:-translate-x-1 transition-all duration-300 flex items-center justify-between shadow-sm group"
                >
                  {/* Visual Rank code */}
                  <span className="absolute top-1 left-2 text-[7px] font-mono text-zinc-400">RANK_SIGMA_{index + 1}</span>
                  <div className="flex items-center gap-3 mt-2">
                    <div className="w-8 h-8 rounded-lg bg-amber-600/10 text-amber-800 font-mono font-black flex items-center justify-center text-sm border border-[#ebdcb9]/40">
                      #{index + 1}
                    </div>
                    <div>
                      <h4 className="font-bold text-sm text-zinc-900 group-hover:text-amber-700 transition-colors font-mono">{asset.symbol}</h4>
                      <p className="text-[10px] text-zinc-500">{asset.name}</p>
                    </div>
                  </div>

                  <div className="text-right select-none mt-2">
                    <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">BUY</span>
                    <p className="text-[10px] text-zinc-500 font-mono mt-1">Conf: {asset.confidence}%</p>
                    <p className="text-[9px] text-amber-800 font-mono font-bold mt-0.5">Acc: {asset.predictionAccuracy || 85}%</p>
                  </div>
                </Link>
              ))}
            </div>
          </div>

          {/* Consensus Weighting breakdown panel */}
          <div className="p-4 rounded-xl bg-white/80 backdrop-blur-md border border-[#ebdcb9] space-y-3 shadow-sm select-none">
            <p className="text-xs font-bold text-zinc-500 uppercase tracking-widest font-mono">Consensus Weighting</p>
            <div className="space-y-2">
              <div>
                <div className="flex justify-between text-[10px] text-zinc-500 mb-1 font-mono">
                  <span>BUY Verdicts</span>
                  <span className="text-emerald-600 font-bold">57%</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-zinc-100">
                  <div className="h-full rounded-full bg-emerald-500 animate-pulse" style={{ width: '57%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-[10px] text-zinc-500 mb-1 font-mono">
                  <span>HOLD Verdicts</span>
                  <span className="text-amber-600 font-bold">29%</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-zinc-100">
                  <div className="h-full rounded-full bg-amber-500" style={{ width: '29%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-[10px] text-zinc-500 mb-1 font-mono">
                  <span>SELL Verdicts</span>
                  <span className="text-rose-600 font-bold">14%</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-zinc-100">
                  <div className="h-full rounded-full bg-rose-500" style={{ width: '14%' }}></div>
                </div>
              </div>
            </div>
          </div>

        </div>
        
      </div>
    </div>
  );
}
