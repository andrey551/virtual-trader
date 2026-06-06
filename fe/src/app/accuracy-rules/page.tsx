"use client";

import React from "react";
import Link from "next/link";
import { 
  ArrowLeft, 
  CheckCircle2, 
  Award, 
  Activity, 
  HelpCircle, 
  TrendingUp, 
  TrendingDown, 
  Lock, 
  Calculator 
} from "lucide-react";

export default function AccuracyRulesPage() {
  return (
    <div className="p-8 space-y-8 animate-fadeIn max-w-5xl mx-auto">
      {/* Header and Back navigation */}
      <div className="flex items-center gap-3">
        <Link 
          href="/" 
          className="p-2 rounded-xl border border-[#ebdcb9] bg-white hover:bg-amber-50/20 text-zinc-650 hover:text-amber-800 transition-all shadow-sm flex items-center justify-center cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <span className="text-[10px] font-mono text-zinc-400 bg-zinc-100 px-1.5 py-0.5 rounded select-none">
            DOCS // CORE_RULE_V1
          </span>
          <h2 className="text-2xl font-black text-zinc-950 tracking-tight font-sans mt-0.5">
            Forecast Accuracy Evaluation Mechanics
          </h2>
        </div>
      </div>

      {/* Main explanation card */}
      <div className="relative p-8 rounded-3xl bg-white/80 backdrop-blur-md border border-[#ebdcb9] shadow-sm space-y-6 overflow-hidden">
        <div className="absolute right-0 top-0 w-1/4 opacity-10 pointer-events-none bg-gradient-to-l from-emerald-500 to-transparent blur-3xl h-full"></div>
        
        <div className="space-y-4 max-w-4xl">
          <div className="flex items-center gap-2 text-emerald-800">
            <CheckCircle2 className="w-5 h-5 shrink-0" />
            <h3 className="text-lg font-bold tracking-tight">What is Forecast Accuracy?</h3>
          </div>
          <p className="text-sm text-zinc-600 leading-relaxed">
            The **Virtual Trader** platform utilizes a multi-agent consensus network (Swarm Consensus) to continuously forecast market directions. To maintain absolute transparency, the system records, audits, and score-evaluates all trade recommendations in a real-time loop.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-4">
          {/* Card: Directional Hit Rate */}
          <div className="p-6 rounded-2xl border border-emerald-500/20 bg-emerald-500/[0.02] space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-emerald-100 text-emerald-800">
                <Calculator className="w-4 h-4" />
              </div>
              <h4 className="text-sm font-bold text-emerald-900 uppercase tracking-wider font-mono">
                1. Directional Hit Rate (Win Rate)
              </h4>
            </div>
            <p className="text-xs text-zinc-500 leading-relaxed">
              The percentage of closed recommendations that yielded a positive return. A forecast is counted as correct if the market price moves in the recommended direction (BUY or SELL) and hits the Target Price before hitting the Stop Loss.
            </p>
            <div className="p-4 rounded-xl bg-white border border-emerald-500/10 font-mono text-[11px] text-emerald-800 space-y-1 shadow-inner">
              <p className="font-bold text-center">FORMULA</p>
              <div className="border-t border-emerald-500/10 my-2 pt-2 text-center text-xs">
                Accuracy = (Successful Forecasts / Total Closed Forecasts) × 100%
              </div>
            </div>
          </div>

          {/* Card: Alpha Outperformance */}
          <div className="p-6 rounded-2xl border border-amber-500/20 bg-amber-500/[0.02] space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-amber-100 text-amber-800">
                <Award className="w-4 h-4" />
              </div>
              <h4 className="text-sm font-bold text-amber-900 uppercase tracking-wider font-mono">
                2. Alpha Outperformance
              </h4>
            </div>
            <p className="text-xs text-zinc-500 leading-relaxed">
              The average realized percentage return of all completed positions compared to their entry prices. This represents the swarm consensus&apos;s ability to capture alpha (excess returns) relative to a passive buy-and-hold strategy.
            </p>
            <div className="p-4 rounded-xl bg-white border border-amber-500/10 font-mono text-[11px] text-emerald-800 space-y-1 shadow-inner">
              <p className="font-bold text-center">FORMULA</p>
              <div className="border-t border-emerald-500/10 my-2 pt-2 text-center text-xs">
                Alpha Outperformance = ∑(Realized Return) / Total Closed Forecasts
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Rules and triggers explanation */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Trigger rules column */}
        <div className="md:col-span-2 p-6 rounded-2xl border border-[#ebdcb9] bg-white/80 backdrop-blur-md shadow-sm space-y-5">
          <div className="flex items-center gap-2.5 text-zinc-805 pb-3 border-b border-[#ebdcb9]/50">
            <Activity className="w-5 h-5 text-amber-700" />
            <h3 className="font-bold text-sm uppercase tracking-wider font-mono">Process & Forecast States</h3>
          </div>
          
          <div className="space-y-4 text-xs text-zinc-600 leading-relaxed">
            <div className="space-y-1">
              <h4 className="font-bold text-zinc-800 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
                ACTIVE Position
              </h4>
              <p className="pl-3">
                When the AI Swarm consensus yields a high-conviction BUY or SELL verdict, a new recommendation is recorded at the current **Entry Price**, registering a **Target Price** (take profit) and a **Stop Loss** parameter.
              </p>
            </div>

            <div className="space-y-1">
              <h4 className="font-bold text-zinc-800 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                TARGET HIT (Success)
              </h4>
              <p className="pl-3">
                - **BUY**: Triggered if the market price rises to or exceeds the Target Price.
                <br />
                - **SELL**: Triggered if the market price falls to or below the Target Price.
                <br />
                The recommendation is marked **CLOSED** with a positive realized return.
              </p>
            </div>

            <div className="space-y-1">
              <h4 className="font-bold text-zinc-800 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
                STOP LOSS HIT (Failure)
              </h4>
              <p className="pl-3">
                - **BUY**: Triggered if the market price falls to or below the Stop Loss.
                <br />
                - **SELL**: Triggered if the market price rises to or exceeds the Stop Loss.
                <br />
                The recommendation is marked **CLOSED** with a negative realized return.
              </p>
            </div>

            <div className="space-y-1">
              <h4 className="font-bold text-zinc-800 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-zinc-500"></span>
                Dynamic Evaluation Loop
              </h4>
              <p className="pl-3">
                A background checker (`accuracy_worker`) runs every **30 seconds** on the backend, fetching live quotes to resolve active triggers and recalculating the consensus statistics for all assets in the database.
              </p>
            </div>
          </div>
        </div>

        {/* Disclaimer & Policy Column */}
        <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-950 text-zinc-350 space-y-4 shadow-md flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-amber-500 pb-2 border-b border-zinc-800">
              <Lock className="w-4 h-4" />
              <h3 className="font-bold text-xs uppercase tracking-widest font-mono">No-Execution Policy</h3>
            </div>
            
            <p className="text-[11px] leading-relaxed text-zinc-400">
              The Virtual Trader system is designed solely as an analytical platform and decision support research tool powered by AI agents.
            </p>
            
            <div className="p-3.5 rounded-xl bg-zinc-900 border border-zinc-800 text-[10px] space-y-2 leading-relaxed">
              <p className="font-bold text-amber-400">Key Information:</p>
              <ul className="list-disc list-inside space-y-1.5 text-zinc-500">
                <li>No trading orders are routed or executed on live brokerage accounts.</li>
                <li>All calculated hit rates are derived from historical real-time pricing data simulations.</li>
                <li>Past accuracy metrics do not guarantee future performance or price movements.</li>
              </ul>
            </div>
          </div>

          <div className="text-[10px] text-zinc-500 font-mono text-center pt-4 border-t border-zinc-900 flex items-center gap-1.5 justify-center">
            <HelpCircle className="w-3.5 h-3.5" />
            <span>Consensus Engine v1.0.0</span>
          </div>
        </div>
      </div>
    </div>
  );
}
