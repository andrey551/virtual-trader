import React, { useEffect, useRef, useState } from "react";

interface DynamicChartProps {
  selectedAsset: {
    symbol: string;
    candles?: {
      open: number;
      high: number;
      low: number;
      close: number;
      isForecast?: boolean;
    }[];
  };
  forecastOffset: number;
}

export default function DynamicChart({ selectedAsset }: DynamicChartProps) {
  const container = useRef<HTMLDivElement>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    if (!container.current) return;
    
    // Clear container content first
    container.current.innerHTML = "";
    setIsLoaded(false);

    const symbol = selectedAsset.symbol;
    let tvSymbol = symbol.toUpperCase();
    
    // Map our tickers to standard TradingView formats
    if (tvSymbol === "BTC-USD" || tvSymbol === "BTCUSDT") {
      tvSymbol = "BINANCE:BTCUSDT";
    } else if (tvSymbol === "ETH-USD" || tvSymbol === "ETHUSDT") {
      tvSymbol = "BINANCE:ETHUSDT";
    } else if (tvSymbol === "SOL-USD" || tvSymbol === "SOLUSDT") {
      tvSymbol = "BINANCE:SOLUSDT";
    } else if (tvSymbol.endsWith("=X")) {
      tvSymbol = `FX_IDC:${tvSymbol.replace("=X", "")}`;
    } else if (tvSymbol === "EUR-USD") {
      tvSymbol = "FX_IDC:EURUSD";
    } else if (tvSymbol.startsWith("^")) {
      if (tvSymbol === "^GSPC") tvSymbol = "SP:SPX";
      else if (tvSymbol === "^IXIC") tvSymbol = "NASDAQ:IXIC";
    } else {
      // Default to NASDAQ for international stocks
      tvSymbol = `NASDAQ:${tvSymbol}`;
    }

    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
    script.type = "text/javascript";
    script.async = true;
    script.innerHTML = JSON.stringify({
      autosize: true,
      symbol: tvSymbol,
      interval: "D",
      timezone: "Etc/UTC",
      theme: "light",
      style: "1",
      locale: "en",
      enable_publishing: false,
      hide_side_toolbar: false,
      allow_symbol_change: false,
      calendar: false,
      studies: [
        "STD;Simple_Moving_Average"
      ],
      support_host: "https://www.tradingview.com"
    });
    
    container.current.appendChild(script);
    setIsLoaded(true);
  }, [selectedAsset.symbol]);

  return (
    <div className="w-full h-full relative" style={{ minHeight: "360px" }}>
      {!isLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-[#fdfbf6] text-xs text-zinc-400 font-mono">
          Loading interactive TradingView Terminal...
        </div>
      )}
      <div 
        ref={container} 
        className="w-full h-full"
        style={{ height: "100%", width: "100%" }}
      />
    </div>
  );
}
