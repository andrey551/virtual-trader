"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { 
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

import { ASSETS_MOCK, EVENTS_MOCK } from "./data";
import DynamicChart from "./DynamicChart";

function AnalyticsContent() {
  const searchParams = useSearchParams();
  const symbolParam = searchParams.get("symbol") || "BTC-USD";

  const selectedAsset = ASSETS_MOCK.find(a => a.symbol === symbolParam) || ASSETS_MOCK[0];
  
  const [optimizingMsg, setOptimizingMsg] = useState("Consensus parameters synchronized.");
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [forecastOffset, setForecastOffset] = useState(0);

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
    setOptimizingMsg("Consensus parameters synchronized.");
  }

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
          <Link
            key={asset.id}
            href={`/analysis?symbol=${asset.symbol}`}
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
          </Link>
        ))}
      </div>

      {/* FULL-WIDTH Chart & Technical Indicators Panel */}
      <div className="p-6 rounded-2xl border border-[#ebdcb9] bg-white shadow-sm space-y-6">
        
        {/* Box Header containing Title, price and consensus badges (Aligned right edge) */}
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
              <span className="text-[11px] text-amber-800 font-bold bg-amber-500/10 px-2.5 py-1 rounded-full border border-amber-500/20">
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

        {/* 70/30 width and h-[460px] height layout inside the unified top card */}
        <div className="grid grid-cols-1 md:grid-cols-10 gap-6 items-stretch">
          
          {/* Left Sub-Column (70%): MASSIVE Candlestick Chart */}
          <div className="md:col-span-7 flex flex-col justify-between h-[460px]">
            <div className="flex-1 bg-[#fdfbf6] border border-[#ebdcb9]/60 rounded-xl overflow-hidden p-4 min-h-[360px]">
              <DynamicChart selectedAsset={selectedAsset} forecastOffset={forecastOffset} />
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
