"use client";

import React from "react";
import Link from "next/link";
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Sparkles
} from "lucide-react";

// Mock Database of Assets
interface Asset {
  id: string;
  name: string;
  category: 'Crypto' | 'Stock' | 'Forex' | 'Commodity';
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  rating: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
}

const ASSETS_MOCK: Asset[] = [
  { id: "btc", name: "Bitcoin", category: "Crypto", symbol: "BTC-USD", price: 67250.45, change: 1450.25, changePercent: 2.2, rating: "BUY", confidence: 85 },
  { id: "eth", name: "Ethereum", category: "Crypto", symbol: "ETH-USD", price: 3450.80, change: -45.10, changePercent: -1.29, rating: "HOLD", confidence: 60 },
  { id: "tsla", name: "Tesla Inc.", category: "Stock", symbol: "TSLA", price: 178.46, change: -5.84, changePercent: -3.17, rating: "SELL", confidence: 78 },
  { id: "nvda", name: "NVIDIA Corp.", category: "Stock", symbol: "NVDA", price: 948.22, change: 32.40, changePercent: 3.54, rating: "BUY", confidence: 92 },
  { id: "aapl", name: "Apple Inc.", category: "Stock", symbol: "AAPL", price: 171.18, change: 0.85, changePercent: 0.50, rating: "HOLD", confidence: 65 },
  { id: "eurusd", name: "EUR/USD", category: "Forex", symbol: "EUR-USD", price: 1.0842, change: 0.0034, changePercent: 0.31, rating: "HOLD", confidence: 55 },
  { id: "gold", name: "Gold Spot", category: "Commodity", symbol: "GOLD", price: 2342.15, change: 18.50, changePercent: 0.80, rating: "BUY", confidence: 80 }
];

export default function Home() {
  return (
    <div className="p-8 space-y-8 animate-fadeIn">
      {/* Top Header Card Banner */}
      <div className="relative p-8 rounded-2xl bg-white border border-[#ebdcb9] overflow-hidden shadow-sm">
        <div className="absolute right-0 bottom-0 top-0 w-1/3 opacity-10 pointer-events-none bg-gradient-to-l from-amber-500 to-transparent blur-3xl"></div>
        <div className="relative max-w-2xl space-y-3">
          <span className="px-2.5 py-1 rounded-full text-[10px] bg-amber-500/10 text-amber-800 font-bold uppercase tracking-wider">
            Market Consensus Swarm Active
          </span>
          <h2 className="text-2xl font-bold tracking-tight text-zinc-900 sm:text-3xl">
            Global Market Analysis & Advisory
          </h2>
          <p className="text-sm text-zinc-600 leading-relaxed">
            Select any global stock, cryptocurrency, currency, or commodity ticker. The analysis engine constantly scrapes indexes, financial ratios, global central bank rates, and news streams to formulate trade recommendations.
          </p>
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
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      asset.rating === 'BUY' ? 'bg-emerald-100 text-emerald-800' :
                      asset.rating === 'SELL' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
                    }`}>
                      {asset.rating} ({asset.confidence}%)
                    </span>
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

                <div className="text-right">
                  <span className="text-xs font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">BUY</span>
                  <p className="text-[10px] text-amber-800 font-bold mt-1">Confidence: {asset.confidence}%</p>
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
