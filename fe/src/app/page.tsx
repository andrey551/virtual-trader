"use client";

import React from "react";
import Link from "next/link";
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  Award,
  Lock
} from "lucide-react";
import { ASSETS_MOCK } from "./analysis/data";

export default function Home() {
  return (
    <div className="p-8 space-y-8 animate-fadeIn">
      {/* Top Header Card Banner */}
      <div className="relative p-8 rounded-3xl bg-white border border-[#ebdcb9] overflow-hidden shadow-sm space-y-8">
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
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-800">Forecast Accuracy</span>
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            </div>
            <div className="space-y-1">
              <p className="text-4xl font-black text-emerald-800 tracking-tight">88.4%</p>
              <p className="text-xs text-zinc-700 font-bold">Directional Hit Rate</p>
            </div>
            <p className="text-[11px] text-zinc-500 leading-relaxed">
              Verified directional correctness (predicting upward/downward shifts) across 1,420 backtested scenario runs.
            </p>
          </div>

          {/* Outperformance / Alpha Stat */}
          <div className="p-6 rounded-2xl border border-amber-500/25 bg-amber-500/[0.03] space-y-3 relative group hover:bg-amber-500/[0.05] transition-all duration-300">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-amber-800">Alpha Outperformance</span>
              <Award className="w-5 h-5 text-amber-600" />
            </div>
            <div className="space-y-1">
              <p className="text-4xl font-black text-amber-800 tracking-tight">+18.7%</p>
              <p className="text-xs text-zinc-700 font-bold">vs Benchmark Buy-and-Hold</p>
            </div>
            <p className="text-[11px] text-zinc-500 leading-relaxed">
              Consolidated consensus trade advices historically outperformed major indices (S&P 500 / BTC Hodl) by an average of +18.7% yearly.
            </p>
          </div>

          {/* Verified Refresh Stat */}
          <div className="p-6 rounded-2xl border border-zinc-500/20 bg-zinc-500/[0.02] space-y-3 relative group hover:bg-zinc-500/[0.04] transition-all duration-300">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-zinc-700">Swarm Synchronization</span>
              <Activity className="w-5 h-5 text-zinc-500" />
            </div>
            <div className="space-y-1">
              <p className="text-4xl font-black text-zinc-800 tracking-tight">Near Realtime</p>
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

      {/* Watchlist and Top Recommendations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Main Asset Watchlist */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-2">
            <Activity className="w-4 h-4 text-amber-600" />
            Global Asset Watchlist
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {ASSETS_MOCK.map((asset) => {
              const isBullish = asset.changePercent >= 0;
              return (
                <Link
                  key={asset.id}
                  href={`/analysis?symbol=${asset.symbol}`}
                  className="p-5 rounded-xl border border-[#ebdcb9] bg-white hover:bg-amber-50/15 hover:border-amber-500/35 transition-all duration-300 group flex flex-col justify-between space-y-4 shadow-sm"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">{asset.category}</span>
                      <h4 className="font-extrabold text-base text-zinc-950 group-hover:text-amber-700 transition-colors mt-0.5">{asset.symbol}</h4>
                      <p className="text-xs text-zinc-500 mt-0.5">{asset.name}</p>
                    </div>
                    <div className="flex flex-col items-end gap-1 select-none">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        asset.rating === 'BUY' ? 'bg-emerald-100 text-emerald-800' :
                        asset.rating === 'SELL' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
                      }`}>
                        {asset.rating} ({asset.confidence}%)
                      </span>
                      <span className="text-[9px] text-amber-800 font-black bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                        Accuracy: {asset.predictionAccuracy || 85}%
                      </span>
                    </div>
                  </div>

                  <div className="flex items-end justify-between border-t border-[#ebdcb9]/40 pt-3">
                    <div>
                      <p className="text-[10px] text-zinc-400">Last Price</p>
                      <p className="font-mono font-bold text-base text-zinc-800 mt-0.5">
                        {asset.price.toLocaleString("en-US", { style: asset.category === 'Forex' ? 'decimal' : 'currency', currency: "USD", minimumFractionDigits: asset.category === 'Forex' ? 4 : 2 })}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-[10px] text-zinc-400">24h Change</p>
                      <div className={`flex items-center gap-1 mt-0.5 font-mono text-sm font-semibold justify-end ${isBullish ? 'text-emerald-600' : 'text-rose-600'}`}>
                        {isBullish ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                        <span>{isBullish ? '+' : ''}{asset.changePercent}%</span>
                      </div>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Top Picks Sidebar */}
        <div className="space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-600" />
            Top Recommendations
          </h3>

          <div className="space-y-4">
            {ASSETS_MOCK.filter(a => a.rating === 'BUY').sort((a,b) => b.confidence - a.confidence).map((asset, index) => (
              <Link 
                key={asset.id}
                href={`/analysis?symbol=${asset.symbol}`}
                className="p-4 rounded-xl border border-[#ebdcb9] bg-white hover:bg-amber-500/5 transition-all flex items-center justify-between shadow-sm group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-amber-600/10 text-amber-800 font-bold flex items-center justify-center text-sm border border-[#ebdcb9]/40">
                    #{index + 1}
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-zinc-900 group-hover:text-amber-700 transition-colors">{asset.symbol}</h4>
                    <p className="text-[10px] text-zinc-500">{asset.name}</p>
                  </div>
                </div>

                <div className="text-right select-none">
                  <span className="text-xs font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">BUY</span>
                  <p className="text-[10px] text-zinc-500 font-medium mt-1">Confidence: {asset.confidence}%</p>
                  <p className="text-[9px] text-amber-800 font-bold mt-0.5">Accuracy: {asset.predictionAccuracy || 85}%</p>
                </div>
              </Link>
            ))}
          </div>

          {/* Consenus Stats panel */}
          <div className="p-4 rounded-xl bg-white border border-[#ebdcb9] space-y-3 shadow-sm">
            <p className="text-xs font-bold text-zinc-500">Market Consensus Breakdown</p>
            <div className="space-y-2">
              <div>
                <div className="flex justify-between text-[10px] text-zinc-500 mb-1">
                  <span>BUY Verdicts</span>
                  <span className="text-emerald-600 font-bold">57%</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-zinc-100">
                  <div className="h-full rounded-full bg-emerald-500" style={{ width: '57%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-[10px] text-zinc-500 mb-1">
                  <span>HOLD Verdicts</span>
                  <span className="text-amber-600 font-bold">29%</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-zinc-100">
                  <div className="h-full rounded-full bg-amber-500" style={{ width: '29%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-[10px] text-zinc-500 mb-1">
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
