"use client";

import React, { useState } from "react";
import { 
  Zap, 
  Activity,
  BookOpen,
  AlertCircle
} from "lucide-react";

type ToolType = "scrape_dynamic_page" | "get_market_price" | "get_historical_candles" | "get_crypto_ticker" | "get_market_news";

interface ToolDef {
  name: ToolType;
  label: string;
  description: string;
}

const TOOLS_LIST: ToolDef[] = [
  {
    name: "scrape_dynamic_page",
    label: "scrape_dynamic_page",
    description: "Cào dữ liệu HTML thô hoặc render JS động từ trang web bất kỳ sử dụng CSS Selectors."
  },
  {
    name: "get_market_price",
    label: "get_market_price",
    description: "Lấy giá near realtime, biến động tuyệt đối và phần trăm của cổ phiếu, forex, crypto hoặc chỉ số thị trường."
  },
  {
    name: "get_historical_candles",
    label: "get_historical_candles",
    description: "Tải dữ liệu biểu đồ nến lịch sử (OHLCV) hỗ trợ vẽ chart và tính toán chỉ báo kỹ thuật."
  },
  {
    name: "get_crypto_ticker",
    label: "get_crypto_ticker",
    description: "Lấy dữ liệu giá và độ sâu sổ lệnh mua bán (Order Book depth) từ sàn Binance."
  },
  {
    name: "get_market_news",
    label: "get_market_news",
    description: "Cào tin tức kinh tế thế giới qua Google News RSS, tính điểm tâm lý và ánh xạ tài sản ảnh hưởng."
  }
];

export default function ScraperPlayground() {
  const [activeTool, setActiveTool] = useState<ToolType>("scrape_dynamic_page");
  const [isLoading, setIsLoading] = useState(false);
  const [responseLog, setResponseLog] = useState<unknown>(null);
  const [latency, setLatency] = useState<number | null>(null);

  // Form states
  // 1. scrape_dynamic_page
  const [url, setUrl] = useState("https://finance.yahoo.com/quote/BTC-USD");
  const [selectors, setSelectors] = useState(`{\n  "price": "span[data-regular-market-price]",\n  "change": "span[data-price-change]"\n}`);
  const [waitSelector, setWaitSelector] = useState("");
  const [rawHtml, setRawHtml] = useState(false);
  const [autoScroll, setAutoScroll] = useState(false);
  const [timeoutMs, setTimeoutMs] = useState(30000);

  // 2. get_market_price
  const [priceTicker, setPriceTicker] = useState("AAPL");

  // 3. get_historical_candles
  const [candlesTicker, setCandlesTicker] = useState("BTC-USD");
  const [candlesInterval, setCandlesInterval] = useState("1d");
  const [candlesPeriod, setCandlesPeriod] = useState("1mo");

  // 4. get_crypto_ticker
  const [cryptoSymbol, setCryptoSymbol] = useState("BTCUSDT");
  const [cryptoDepth, setCryptoDepth] = useState(10);

  // 5. get_market_news
  const [newsQuery, setNewsQuery] = useState("Federal Reserve");
  const [newsLimit, setNewsLimit] = useState(5);

  const getArguments = (): Record<string, unknown> => {
    switch (activeTool) {
      case "scrape_dynamic_page": {
        let parsedSelectors = {};
        try {
          if (selectors.trim()) {
            parsedSelectors = JSON.parse(selectors);
          }
        } catch {
          // Fall through
        }
        return {
          url,
          selectors: parsedSelectors,
          wait_selector: waitSelector.trim() || undefined,
          raw_html: rawHtml,
          auto_scroll: autoScroll,
          timeout: timeoutMs
        };
      }
      case "get_market_price":
        return { ticker: priceTicker.trim() };
      case "get_historical_candles":
        return {
          ticker: candlesTicker.trim(),
          interval: candlesInterval,
          period: candlesPeriod
        };
      case "get_crypto_ticker":
        return {
          symbol: cryptoSymbol.trim(),
          depth: Number(cryptoDepth)
        };
      case "get_market_news":
        return {
          query: newsQuery.trim(),
          limit: Number(newsLimit)
        };
      default:
        return {};
    }
  };

  const handleExecute = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setResponseLog(null);
    setLatency(null);

    // Basic JSON selector validation
    if (activeTool === "scrape_dynamic_page" && selectors.trim()) {
      try {
        JSON.parse(selectors);
      } catch (err) {
        setResponseLog({
          status: "error",
          message: "Invalid selectors JSON: " + (err instanceof Error ? err.message : String(err))
        });
        setIsLoading(false);
        return;
      }
    }

    const toolArgs = getArguments();
    const startTime = performance.now();

    try {
      const res = await fetch("/api/mcp", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          tool: activeTool,
          arguments: toolArgs
        })
      });
      
      const data = await res.json();
      const endTime = performance.now();
      
      setLatency(Math.round(endTime - startTime));
      setResponseLog(data);
    } catch (err) {
      const endTime = performance.now();
      setLatency(Math.round(endTime - startTime));
      setResponseLog({
        status: "error",
        message: "API Request Failed: " + (err instanceof Error ? err.message : String(err))
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-8 space-y-8 animate-fadeIn max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="border-b border-[#ebdcb9] pb-4">
        <div className="flex items-center gap-2">
          <Zap className="w-6 h-6 text-amber-600 animate-pulse" />
          <h2 className="text-2xl font-bold text-zinc-900 tracking-tight">
            MCP Terminal Playground
          </h2>
        </div>
        <p className="text-xs text-zinc-500 mt-1 max-w-2xl leading-relaxed">
          Khu vực thử nghiệm trực tiếp các công cụ của Model Context Protocol. Chọn công cụ, điền các tham số cấu hình và nhấn Execute để thực hiện cuộc gọi thời gian thực qua Python backend bridge.
        </p>
      </div>

      {/* Grid layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Tool selector panel (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Danh sách công cụ</h3>
          <div className="flex flex-col gap-2.5">
            {TOOLS_LIST.map((tool) => {
              const isSelected = activeTool === tool.name;
              return (
                <button
                  key={tool.name}
                  onClick={() => {
                    setActiveTool(tool.name);
                    setResponseLog(null);
                    setLatency(null);
                  }}
                  className={`w-full text-left p-4 rounded-xl border transition-all duration-205 ${
                    isSelected
                      ? "bg-amber-50/70 border-amber-500 shadow-sm"
                      : "bg-white border-[#ebdcb9] hover:bg-zinc-50/50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`font-mono text-xs font-bold ${isSelected ? "text-amber-700" : "text-zinc-800"}`}>
                      {tool.label}
                    </span>
                    {isSelected && (
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-600 animate-ping" />
                    )}
                  </div>
                  <p className="text-[11px] text-zinc-500 mt-1.5 leading-relaxed">
                    {tool.description}
                  </p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Dynamic Parameter Form (4 cols) */}
        <div className="lg:col-span-4 p-6 rounded-2xl border border-[#ebdcb9] bg-white shadow-sm flex flex-col h-fit">
          <div className="border-b border-zinc-100 pb-3 mb-4 flex items-center justify-between">
            <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest">
              Tham số đầu vào
            </h3>
            <span className="text-[10px] font-mono bg-zinc-100 text-zinc-600 px-2 py-0.5 rounded-md">
              JSON format
            </span>
          </div>

          <form onSubmit={handleExecute} className="space-y-4 flex-1">
            
            {/* 1. scrape_dynamic_page form fields */}
            {activeTool === "scrape_dynamic_page" && (
              <div className="space-y-4">
                <div>
                  <label className="block text-[11px] text-zinc-500 font-bold uppercase tracking-wider mb-1.5">
                    Target URL
                  </label>
                  <input
                    type="url"
                    required
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    className="w-full bg-[#fdfbf6] border border-[#ebdcb9] rounded-xl px-3.5 py-2.5 text-xs text-zinc-800 focus:outline-none focus:border-amber-500 font-mono shadow-inner"
                    placeholder="https://example.com"
                  />
                </div>

                <div>
                  <label className="block text-[11px] text-zinc-500 font-bold uppercase tracking-wider mb-1.5">
                    CSS Selectors Mapping (JSON)
                  </label>
                  <textarea
                    rows={4}
                    value={selectors}
                    onChange={(e) => setSelectors(e.target.value)}
                    className="w-full bg-[#fdfbf6] border border-[#ebdcb9] rounded-xl p-3.5 text-xs text-zinc-700 focus:outline-none focus:border-amber-500 font-mono leading-relaxed shadow-inner"
                    placeholder="{}"
                  />
                </div>

                <div>
                  <label className="block text-[11px] text-zinc-500 font-bold uppercase tracking-wider mb-1.5">
                    Wait Selector (Optional)
                  </label>
                  <input
                    type="text"
                    value={waitSelector}
                    onChange={(e) => setWaitSelector(e.target.value)}
                    className="w-full bg-[#fdfbf6] border border-[#ebdcb9] rounded-xl px-3.5 py-2.5 text-xs text-zinc-800 focus:outline-none focus:border-amber-500 font-mono shadow-inner"
                    placeholder="e.g. .price-tag"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3 pt-1">
                  <label className="flex items-center gap-2 p-2.5 bg-zinc-50 rounded-xl border border-zinc-100 cursor-pointer hover:bg-zinc-100/50 transition-all">
                    <input
                      type="checkbox"
                      checked={rawHtml}
                      onChange={(e) => setRawHtml(e.target.checked)}
                      className="rounded border-zinc-300 text-amber-600 focus:ring-amber-500 w-3.5 h-3.5"
                    />
                    <span className="text-[10px] font-bold text-zinc-650 uppercase tracking-wider">Raw HTML</span>
                  </label>

                  <label className="flex items-center gap-2 p-2.5 bg-zinc-50 rounded-xl border border-zinc-100 cursor-pointer hover:bg-zinc-100/50 transition-all">
                    <input
                      type="checkbox"
                      checked={autoScroll}
                      onChange={(e) => setAutoScroll(e.target.checked)}
                      className="rounded border-zinc-300 text-amber-600 focus:ring-amber-500 w-3.5 h-3.5"
                    />
                    <span className="text-[10px] font-bold text-zinc-650 uppercase tracking-wider">Auto Scroll</span>
                  </label>
                </div>

                <div>
                  <label className="block text-[11px] text-zinc-500 font-bold uppercase tracking-wider mb-1.5">
                    Timeout (ms)
                  </label>
                  <input
                    type="number"
                    value={timeoutMs}
                    onChange={(e) => setTimeoutMs(Number(e.target.value))}
                    className="w-full bg-[#fdfbf6] border border-[#ebdcb9] rounded-xl px-3.5 py-2.5 text-xs text-zinc-800 focus:outline-none focus:border-amber-500 font-mono shadow-inner"
                  />
                </div>
              </div>
            )}

            {/* 2. get_market_price form fields */}
            {activeTool === "get_market_price" && (
              <div className="space-y-4">
                <div>
                  <label className="block text-[11px] text-zinc-500 font-bold uppercase tracking-wider mb-1.5">
                    Ticker Symbol
                  </label>
                  <input
                    type="text"
                    required
                    value={priceTicker}
                    onChange={(e) => setPriceTicker(e.target.value)}
                    className="w-full bg-[#fdfbf6] border border-[#ebdcb9] rounded-xl px-3.5 py-2.5 text-xs text-zinc-800 focus:outline-none focus:border-amber-500 font-mono shadow-inner"
                    placeholder="e.g. AAPL, BTC-USD, EURUSD=X, ^GSPC"
                  />
                  <p className="text-[10px] text-zinc-400 mt-1 leading-relaxed">
                    Hỗ trợ chứng khoán Mỹ, Forex (EURUSD=X), Crypto (BTC-USD) và chỉ số chính (^GSPC, ^VIX).
                  </p>
                </div>
              </div>
            )}

            {/* 3. get_historical_candles form fields */}
            {activeTool === "get_historical_candles" && (
              <div className="space-y-4">
                <div>
                  <label className="block text-[11px] text-zinc-500 font-bold uppercase tracking-wider mb-1.5">
                    Ticker Symbol
                  </label>
                  <input
                    type="text"
                    required
                    value={candlesTicker}
                    onChange={(e) => setCandlesTicker(e.target.value)}
                    className="w-full bg-[#fdfbf6] border border-[#ebdcb9] rounded-xl px-3.5 py-2.5 text-xs text-zinc-800 focus:outline-none focus:border-amber-500 font-mono shadow-inner"
                    placeholder="e.g. AAPL, BTC-USD"
                  />
                </div>

                <div>
                  <label className="block text-[11px] text-zinc-500 font-bold uppercase tracking-wider mb-1.5">
                    Time Interval
                  </label>
                  <select
                    value={candlesInterval}
                    onChange={(e) => setCandlesInterval(e.target.value)}
                    className="w-full bg-[#fdfbf6] border border-[#ebdcb9] rounded-xl px-3.5 py-2.5 text-xs text-zinc-800 focus:outline-none focus:border-amber-500 font-mono shadow-inner"
                  >
                    <option value="1m">1m (1 Phút)</option>
                    <option value="5m">5m (5 Phút)</option>
                    <option value="15m">15m (15 Phút)</option>
                    <option value="1h">1h (1 Giờ)</option>
                    <option value="1d">1d (1 Ngày)</option>
                    <option value="1wk">1wk (1 Tuần)</option>
                    <option value="1mo">1mo (1 Tháng)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] text-zinc-500 font-bold uppercase tracking-wider mb-1.5">
                    History Period
                  </label>
                  <select
                    value={candlesPeriod}
                    onChange={(e) => setCandlesPeriod(e.target.value)}
                    className="w-full bg-[#fdfbf6] border border-[#ebdcb9] rounded-xl px-3.5 py-2.5 text-xs text-zinc-800 focus:outline-none focus:border-amber-500 font-mono shadow-inner"
                  >
                    <option value="1d">1d (1 Ngày)</option>
                    <option value="5d">5d (5 Ngày)</option>
                    <option value="1mo">1mo (1 Tháng)</option>
                    <option value="3mo">3mo (3 Tháng)</option>
                    <option value="6mo">6mo (6 Tháng)</option>
                    <option value="1y">1y (1 Năm)</option>
                    <option value="max">max (Toàn bộ)</option>
                  </select>
                </div>
              </div>
            )}

            {/* 4. get_crypto_ticker form fields */}
            {activeTool === "get_crypto_ticker" && (
              <div className="space-y-4">
                <div>
                  <label className="block text-[11px] text-zinc-500 font-bold uppercase tracking-wider mb-1.5">
                    Binance Symbol
                  </label>
                  <input
                    type="text"
                    required
                    value={cryptoSymbol}
                    onChange={(e) => setCryptoSymbol(e.target.value)}
                    className="w-full bg-[#fdfbf6] border border-[#ebdcb9] rounded-xl px-3.5 py-2.5 text-xs text-zinc-800 focus:outline-none focus:border-amber-500 font-mono shadow-inner"
                    placeholder="e.g. BTCUSDT, ETHUSDT"
                  />
                  <p className="text-[10px] text-zinc-400 mt-1 leading-relaxed">
                    Định dạng viết hoa không có dấu gạch ngang (Ví dụ: ETHUSDT, SOLUSDT, BNBUSDT).
                  </p>
                </div>

                <div>
                  <label className="block text-[11px] text-zinc-500 font-bold uppercase tracking-wider mb-1.5">
                    Order Book Depth Limit
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={100}
                    value={cryptoDepth}
                    onChange={(e) => setCryptoDepth(Number(e.target.value))}
                    className="w-full bg-[#fdfbf6] border border-[#ebdcb9] rounded-xl px-3.5 py-2.5 text-xs text-zinc-800 focus:outline-none focus:border-amber-500 font-mono shadow-inner"
                  />
                </div>
              </div>
            )}

            {/* 5. get_market_news form fields */}
            {activeTool === "get_market_news" && (
              <div className="space-y-4">
                <div>
                  <label className="block text-[11px] text-zinc-500 font-bold uppercase tracking-wider mb-1.5">
                    Search Query / Keyword
                  </label>
                  <input
                    type="text"
                    required
                    value={newsQuery}
                    onChange={(e) => setNewsQuery(e.target.value)}
                    className="w-full bg-[#fdfbf6] border border-[#ebdcb9] rounded-xl px-3.5 py-2.5 text-xs text-zinc-800 focus:outline-none focus:border-amber-500 font-mono shadow-inner"
                    placeholder="e.g. Federal Reserve, OPEC, Oil spill"
                  />
                  <p className="text-[10px] text-zinc-400 mt-1 leading-relaxed">
                    Từ khóa quét Google News. Thử các từ khóa sự kiện như: <i>OPEC, oil spill, interest rate, cpi</i> để kiểm tra mapping các tài sản chịu ảnh hưởng.
                  </p>
                </div>

                <div>
                  <label className="block text-[11px] text-zinc-500 font-bold uppercase tracking-wider mb-1.5">
                    Max Articles Limit
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={20}
                    value={newsLimit}
                    onChange={(e) => setNewsLimit(Number(e.target.value))}
                    className="w-full bg-[#fdfbf6] border border-[#ebdcb9] rounded-xl px-3.5 py-2.5 text-xs text-zinc-800 focus:outline-none focus:border-amber-500 font-mono shadow-inner"
                  />
                </div>
              </div>
            )}

            {/* Submit execution button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-6 py-3 rounded-xl bg-amber-600 hover:bg-amber-700 disabled:bg-amber-600/40 text-white font-bold text-xs uppercase tracking-widest transition-all duration-200 flex items-center justify-center gap-2 shadow-sm border border-amber-700"
            >
              {isLoading ? (
                <>
                  <Activity className="w-4 h-4 animate-spin" />
                  Executing subprocess...
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4" />
                  Execute Tool
                </>
              )}
            </button>

          </form>
        </div>

        {/* Structured Output Panel (4 cols) */}
        <div className="lg:col-span-4 p-6 rounded-2xl border border-[#ebdcb9] bg-white shadow-sm flex flex-col min-h-[480px]">
          <div className="border-b border-zinc-100 pb-3 mb-4 flex items-center justify-between">
            <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest">
              Kết quả phản hồi (JSON Log)
            </h3>
            {latency !== null && (
              <span className="text-[10px] font-mono bg-amber-100 text-amber-700 px-2 py-0.5 rounded-md font-bold font-mono">
                {latency} ms
              </span>
            )}
          </div>

          <div className="flex-1 bg-[#fdfbf6] rounded-xl border border-[#ebdcb9]/60 p-5 font-mono text-[10.5px] leading-relaxed overflow-auto select-text text-zinc-850 shadow-inner relative max-h-[500px]">
            {isLoading ? (
              <div className="absolute inset-0 bg-[#fdfbf6]/80 flex flex-col items-center justify-center text-center space-y-3">
                <Activity className="w-6 h-6 animate-spin text-amber-600" />
                <div className="space-y-1">
                  <p className="text-xs font-bold text-zinc-700">Connecting to Python MCP Server...</p>
                  <p className="text-[10px] text-zinc-400 font-mono">Running child_process.spawn</p>
                </div>
              </div>
            ) : responseLog ? (
              <pre className="whitespace-pre-wrap">{JSON.stringify(responseLog, null, 2)}</pre>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center text-zinc-400 py-12">
                <BookOpen className="w-6 h-6 mb-2 text-zinc-300" />
                <p className="text-xs">Cấu hình các tham số bên trái và nhấn Execute để chạy kiểm thử.</p>
                <p className="text-[10px] text-zinc-400 mt-1 max-w-[200px] leading-normal">Kết quả trả về sẽ được hiển thị dưới dạng JSON thô.</p>
              </div>
            )}
          </div>

          {/* Quick telemetry diagnostic details */}
          {!!responseLog && (responseLog as Record<string, unknown>).status === "error" && (
            <div className="mt-4 p-3 bg-red-50 rounded-xl border border-red-100 flex items-start gap-2 animate-fadeIn">
              <AlertCircle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
              <div className="space-y-0.5">
                <p className="text-[10px] font-bold text-red-700 uppercase tracking-wider">Lỗi hệ thống</p>
                <p className="text-[10.5px] text-red-600 leading-normal">
                  {(responseLog as Record<string, string>).message || "Unknown execution error encountered."}
                </p>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
