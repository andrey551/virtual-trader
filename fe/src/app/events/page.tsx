"use client";

import React, { useState, useEffect } from "react";
import { 
  Globe, 
  ChevronRight
} from "lucide-react";
import Link from "next/link";
import { BACKEND_URL } from "../../config";

interface GlobalEvent {
  id: string;
  title: string;
  description: string;
  severity: 'high' | 'medium' | 'low';
  category: string;
  impactedAssets: { symbol: string; impact: number; reason: string }[];
}

const EVENTS_MOCK: GlobalEvent[] = [
  {
    id: "fed-rate",
    title: "Fed Interest Rate Cuts Hinted",
    description: "Federal Reserve chair signals interest rate reductions starting Q3 due to moderating core inflation data.",
    severity: "high",
    category: "Macroeconomics",
    impactedAssets: [
      { symbol: "BTC-USD", impact: 4.5, reason: "Increased liquidity in financial markets drives speculative capital into crypto." },
      { symbol: "NVDA", impact: 3.2, reason: "Lower cost of debt encourages tech conglomerates to expand capital expenditure on AI." },
      { symbol: "EUR-USD", impact: 1.2, reason: "Weakening Dollar index (DXY) pushes EUR/USD higher." },
      { symbol: "GOLD", impact: 2.8, reason: "Lower treasury yields increase demand for non-yielding safe-haven assets." }
    ]
  },
  {
    id: "oil-rig",
    title: "Oil Rig Pipeline Explosion",
    description: "A major pipeline explosion in the North Sea disrupts 8% of European regional Brent crude supply capacity.",
    severity: "high",
    category: "Geopolitical Crisis",
    impactedAssets: [
      { symbol: "GOLD", impact: 2.1, reason: "Geopolitical panic and general inflation risk hedge buying." },
      { symbol: "TSLA", impact: -2.5, reason: "Rising transportation and shipping component costs drag margins." },
      { symbol: "EUR-USD", impact: -1.1, reason: "Higher energy costs damage Eurozone manufacturing competitiveness." }
    ]
  },
  {
    id: "ai-chip-ban",
    title: "EU AI Safety & Chip Export Restrictions",
    description: "EU commission announces stricter compliance rules on high-end computing server farms and hardware transfers.",
    severity: "medium",
    category: "Regulations",
    impactedAssets: [
      { symbol: "NVDA", impact: -3.8, reason: "Compliance overhead and export friction points in European markets." },
      { symbol: "BTC-USD", impact: -1.5, reason: "Regulatory crackdowns on data centers trigger miner relocations." }
    ]
  }
];

interface ApiEventImpact {
  asset_ticker: string;
  impact_direction: string;
  estimated_impact_factor: string | number;
}

interface ApiEvent {
  id: number;
  title: string;
  summary?: string;
  sentiment_score: string | number;
  impacts?: ApiEventImpact[];
}

export default function EventsPage() {
  const [events, setEvents] = useState<GlobalEvent[]>(EVENTS_MOCK);
  const [selectedEvent, setSelectedEvent] = useState<GlobalEvent>(EVENTS_MOCK[0]);

  useEffect(() => {
    async function fetchEvents() {
      try {
        const res = await fetch(`${BACKEND_URL}/api/events`);
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            const mapped = data.map((ev: ApiEvent): GlobalEvent => {
              const absSentiment = Math.abs(Number(ev.sentiment_score || 0));
              let severity: 'high' | 'medium' | 'low' = 'low';
              if (absSentiment >= 0.6) {
                severity = 'high';
              } else if (absSentiment >= 0.3) {
                severity = 'medium';
              }

              const titleLower = ev.title.toLowerCase();
              let category = "Global News";
              if (titleLower.includes("fed") || titleLower.includes("interest rate") || titleLower.includes("inflation") || titleLower.includes("macro")) {
                category = "Macroeconomics";
              } else if (titleLower.includes("opec") || titleLower.includes("oil") || titleLower.includes("spill") || titleLower.includes("gas") || titleLower.includes("crude")) {
                category = "Energy & Geopolitical";
              } else if (titleLower.includes("ai") || titleLower.includes("chip") || titleLower.includes("tech") || titleLower.includes("regulation")) {
                category = "Regulations & Tech";
              }

              const impactedAssets = (ev.impacts || []).map((imp: ApiEventImpact) => {
                const ticker = imp.asset_ticker;
                const factor = Number(imp.estimated_impact_factor || 0);
                const impactVal = Math.round(factor * 10 * 10) / 10;
                
                let reason = `Estimated ${imp.impact_direction.toLowerCase()} movement of ${impactVal}% based on AI correlation analysis.`;
                if (ticker === "USO" || ticker === "CL=F") {
                  if (imp.impact_direction === "POSITIVE") {
                    reason = "OPEC crude supply reductions increase energy commodity valuation and price pressure.";
                  } else {
                    reason = "Accidents or spill disruptions cause operational friction and temporary output decline.";
                  }
                } else if (ticker === "^GSPC" || ticker === "TLT") {
                  if (imp.impact_direction === "POSITIVE") {
                    reason = "Expected interest rate cuts improve market liquidity, driving corporate valuations higher.";
                  } else {
                    reason = "Macroeconomic tightening or higher inflation drags treasury and index benchmarks.";
                  }
                } else if (ticker === "NVDA" || ticker === "BTC-USD") {
                  if (imp.impact_direction === "POSITIVE") {
                    reason = "Expansion of server farm facilities and capital expenditures fuels high-performance growth.";
                  } else {
                    reason = "Strict regulatory guidelines and safety policies cause overhead compliance friction.";
                  }
                }
                
                return {
                  symbol: ticker,
                  impact: impactVal,
                  reason: reason
                };
              });

              return {
                id: String(ev.id),
                title: ev.title,
                description: ev.summary || "",
                severity,
                category,
                impactedAssets
              };
            });
            setEvents(mapped);
            setSelectedEvent(mapped[0]);
          }
        }
      } catch (err) {
        console.error("Failed to fetch events, using fallback mock data", err);
      }
    }
    fetchEvents();
  }, []);

  return (
    <div className="p-8 space-y-8 animate-fadeIn">
      {/* Page Header */}
      <div className="border-b border-[#ebdcb9] pb-4">
        <h2 className="text-xl font-bold text-zinc-900 flex items-center gap-2">
          <Globe className="w-5 h-5 text-amber-600" />
          Geopolitical & Global Event Impact Mapping
        </h2>
        <p className="text-xs text-zinc-500 mt-1">
          Monitor international developments and trace how macroeconomic policies or geopolitical crises ripple into global asset indices.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Events Watch List */}
        <div className="space-y-4">
          <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest">Active Global Events</h3>
          
          <div className="space-y-4">
            {events.map((ev) => (
              <div
                key={ev.id}
                onClick={() => setSelectedEvent(ev)}
                className={`p-5 rounded-xl border cursor-pointer transition-all shadow-sm ${
                  selectedEvent.id === ev.id 
                    ? 'bg-amber-500/10 border-amber-500/35' 
                    : 'bg-white border-[#ebdcb9] hover:bg-amber-500/5'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[9px] font-bold text-amber-700 uppercase tracking-widest">{ev.category}</span>
                  <span className={`px-2 py-0.5 rounded text-[8px] font-bold ${
                    ev.severity === 'high' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
                  }`}>
                    {ev.severity.toUpperCase()} RISK
                  </span>
                </div>
                <h4 className="font-bold text-sm text-zinc-900 mb-1.5">{ev.title}</h4>
                <p className="text-xs text-zinc-500 line-clamp-2 leading-relaxed">{ev.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Tree Map Display */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Node map container */}
          <div className="p-6 rounded-2xl border border-[#ebdcb9] bg-white shadow-sm flex flex-col justify-between">
            <div>
              <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-4">Correlation Impact Tree</h3>
              
              <div className="h-64 relative border border-[#ebdcb9]/60 rounded-xl bg-[#fdfbf6] flex items-center justify-center p-4">
                <svg className="w-full h-full" viewBox="0 0 400 200">
                  {/* Connector lines */}
                  {selectedEvent.impactedAssets.map((asset, idx) => {
                    const y = 35 + idx * (140 / (selectedEvent.impactedAssets.length - 1 || 1));
                    return (
                      <g key={idx} className="opacity-80">
                        <path 
                          d={`M 80 100 C 130 100, 150 ${y}, 250 ${y}`}
                          fill="none"
                          stroke={asset.impact > 0 ? '#10b981' : '#f43f5e'}
                          strokeWidth="1.5"
                          strokeDasharray="4"
                        />
                        <circle cx="80" cy="100" r="4" fill="#a8a29e" />
                        <circle cx="250" cy={y} r="3" fill={asset.impact > 0 ? '#10b981' : '#f43f5e'} />
                      </g>
                    );
                  })}

                  {/* Root Node: Event */}
                  <g transform="translate(40, 85)">
                    <rect width="80" height="30" rx="6" fill="#b45309" fillOpacity="0.15" stroke="#b45309" strokeWidth="1" />
                    <text x="40" y="19" fill="#b45309" fontSize="8" fontWeight="bold" textAnchor="middle">EVENT TRIGGER</text>
                  </g>

                  {/* Leaf Nodes: Affected tickers */}
                  {selectedEvent.impactedAssets.map((asset, idx) => {
                    const y = 20 + idx * (140 / (selectedEvent.impactedAssets.length - 1 || 1));
                    const isPositive = asset.impact > 0;
                    return (
                      <g key={idx} transform={`translate(260, ${y})`}>
                        <rect width="90" height="30" rx="6" fill={isPositive ? '#10b981' : '#f43f5e'} fillOpacity="0.1" stroke={isPositive ? '#10b981' : '#f43f5e'} strokeWidth="1" />
                        <text x="10" y="18" fill="#2b2d31" fontSize="9" fontWeight="bold">{asset.symbol}</text>
                        <text x="80" y="18" fill={isPositive ? '#059669' : '#e11d48'} fontSize="9" fontWeight="bold" textAnchor="end">
                          {isPositive ? '+' : ''}{asset.impact}%
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </div>
            </div>
          </div>

          {/* Detailed explanations */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest">Impact Mechanics Report</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {selectedEvent.impactedAssets.map((asset, idx) => (
                <div key={idx} className="p-5 rounded-xl border border-[#ebdcb9] bg-white shadow-sm flex flex-col justify-between">
                  <div className="flex items-center justify-between mb-3 border-b border-[#ebdcb9]/40 pb-2">
                    <h4 className="font-bold text-sm text-zinc-900">{asset.symbol}</h4>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                      asset.impact > 0 ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                    }`}>
                      {asset.impact > 0 ? '+' : ''}{asset.impact}% Impact
                    </span>
                  </div>
                  <p className="text-xs text-zinc-600 leading-relaxed mb-4">{asset.reason}</p>
                  
                  <Link 
                    href={`/analysis?symbol=${asset.symbol}`}
                    className="text-[10px] text-amber-700 font-bold hover:underline inline-flex items-center gap-1 mt-auto"
                  >
                    Open Deep-Dive Analytics <ChevronRight className="w-3 h-3" />
                  </Link>
                </div>
              ))}
            </div>
          </div>
          
        </div>
        
      </div>
    </div>
  );
}
