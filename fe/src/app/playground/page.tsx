"use client";

import React, { useState } from "react";
import { 
  Zap, 
  Activity,
  BookOpen
} from "lucide-react";

export default function ScraperPlayground() {
  const [scrapedUrl, setScrapedUrl] = useState("https://finance.yahoo.com/quote/BTC-USD");
  const [scrapeSelectors, setScrapeSelectors] = useState(`{\n  "price": "span[data-regular-market-price]",\n  "change": "span[data-price-change]"\n}`);
  const [isScraping, setIsScraping] = useState(false);
  const [scrapeResult, setScrapeResult] = useState<unknown>(null);

  // Scraper Simulation Run
  const handleScrape = (e: React.FormEvent) => {
    e.preventDefault();
    setIsScraping(true);
    setScrapeResult(null);
    setTimeout(() => {
      try {
        JSON.parse(scrapeSelectors);
        setScrapeResult({
          status: "success",
          url: scrapedUrl,
          data: {
            _page_title: "Bitcoin USD (BTC-USD) Price, Value & News - Yahoo Finance",
            price: "$67,250.45",
            change: "+1,450.25 (2.20%)"
          },
          timestamp: new Date().toISOString()
        });
      } catch (err) {
        const errMsg = err instanceof Error ? err.message : String(err);
        setScrapeResult({
          status: "error",
          url: scrapedUrl,
          message: "Invalid selectors JSON schema: " + errMsg,
          timestamp: new Date().toISOString()
        });
      }
      setIsScraping(false);
    }, 1500);
  };

  return (
    <div className="p-8 space-y-8 animate-fadeIn">
      {/* Page Header */}
      <div className="border-b border-[#ebdcb9] pb-4">
        <h2 className="text-xl font-bold text-zinc-900 flex items-center gap-2">
          <Zap className="w-5 h-5 text-amber-600" />
          MCP Playwright Scraper Playground
        </h2>
        <p className="text-xs text-zinc-500 mt-1">
          Execute and simulate running the Playwright crawler MCP server. Input any URL and CSS selectors to retrieve formatted JSON data logs.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Parameter Inputs Card */}
        <div className="p-6 rounded-2xl border border-[#ebdcb9] bg-white shadow-sm h-fit">
          <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-4">Crawler Parameter Form</h3>
          
          <form onSubmit={handleScrape} className="space-y-4">
            <div>
              <label className="block text-xs text-zinc-500 font-bold mb-1.5">Scrape URL Target</label>
              <input 
                type="url" 
                required
                value={scrapedUrl}
                onChange={(e) => setScrapedUrl(e.target.value)}
                className="w-full bg-[#fdfbf6] border border-[#ebdcb9] rounded-xl px-4 py-3 text-sm text-zinc-800 focus:outline-none focus:border-amber-500 font-mono shadow-inner"
              />
            </div>

            <div>
              <label className="block text-xs text-zinc-500 font-bold mb-1.5">CSS Selectors Mapping (JSON Schema)</label>
              <textarea
                rows={5}
                required
                value={scrapeSelectors}
                onChange={(e) => setScrapeSelectors(e.target.value)}
                className="w-full bg-[#fdfbf6] border border-[#ebdcb9] rounded-xl p-4 text-xs text-zinc-700 focus:outline-none focus:border-amber-500 font-mono leading-relaxed shadow-inner"
              />
            </div>

            <button 
              type="submit"
              disabled={isScraping}
              className="w-full py-3 rounded-xl bg-amber-600 hover:bg-amber-700 disabled:bg-amber-600/40 text-white font-semibold text-xs transition-all flex items-center justify-center gap-2 shadow-sm"
            >
              {isScraping ? (
                <>
                  <Activity className="w-4 h-4 animate-spin" />
                  Booting Headless Browser...
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4" />
                  Execute scrape_dynamic_page
                </>
              )}
            </button>
          </form>
        </div>

        {/* Structured Output Card */}
        <div className="p-6 rounded-2xl border border-[#ebdcb9] bg-white shadow-sm flex flex-col min-h-[350px]">
          <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-4">Structured JSON output</h3>
          
          <div className="flex-1 bg-[#fdfbf6] rounded-xl border border-[#ebdcb9]/60 p-5 font-mono text-[11px] leading-relaxed overflow-x-auto select-text text-zinc-800 shadow-inner">
            {isScraping ? (
              <div className="h-full flex flex-col items-center justify-center text-center space-y-2 text-zinc-400">
                <Activity className="w-5 h-5 animate-spin text-amber-600" />
                <p>Crawling target & parsing dynamic components...</p>
              </div>
            ) : scrapeResult ? (
              <pre>{JSON.stringify(scrapeResult, null, 2)}</pre>
            ) : (
              <div className="h-full flex items-center justify-center text-center text-zinc-400">
                <BookOpen className="w-5 h-5 mr-2 text-zinc-300" />
                Execute the scraper to view structured outputs.
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
