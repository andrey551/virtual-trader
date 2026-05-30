import React from "react";
import { Asset } from "./types";

interface DynamicChartProps {
  selectedAsset: Asset;
  forecastOffset: number;
}

export default function DynamicChart({ selectedAsset, forecastOffset }: DynamicChartProps) {
  const w = 35;
  const gap = 38;
  const paddingLeft = 35;
  
  const candleData = selectedAsset.candles;
  const candlesToRender = candleData.map((c) => {
    if (c.isForecast) {
      return {
        ...c,
        open: c.open + forecastOffset * 0.3,
        close: c.close + forecastOffset,
        high: Math.max(c.high, c.close + forecastOffset, c.open + forecastOffset * 0.3),
        low: Math.min(c.low, c.close + forecastOffset, c.open + forecastOffset * 0.3)
      };
    }
    return c;
  });

  const values = candlesToRender.map(c => [c.high, c.low]).flat();
  const min = Math.min(...values) * 0.99;
  const max = Math.max(...values) * 1.01;
  // Taller chart rendering logic for h-[360px] view box
  const scale = (val: number) => 300 - ((val - min) / (max - min)) * 260;

  return (
    <svg className="w-full h-full" viewBox="0 0 460 320">
      {/* Grid lines */}
      <g stroke="#ebdcb9" strokeWidth="0.5" strokeOpacity="0.3" strokeDasharray="3">
        <line x1="0" y1="40" x2="460" y2="40" />
        <line x1="0" y1="100" x2="460" y2="100" />
        <line x1="0" y1="160" x2="460" y2="160" />
        <line x1="0" y1="220" x2="460" y2="220" />
        <line x1="0" y1="280" x2="460" y2="280" />
      </g>

      {/* Separator Timeline boundary */}
      <line 
        x1={paddingLeft + 3 * (w + gap) - gap/2} 
        y1="10" 
        x2={paddingLeft + 3 * (w + gap) - gap/2} 
        y2="310" 
        stroke="#b45309" 
        strokeWidth="1.5" 
        strokeDasharray="4" 
      />
      <text 
        x={paddingLeft + 3 * (w + gap) - gap/2 - 5} 
        y="20" 
        fill="#b45309" 
        fontSize="8" 
        fontWeight="bold" 
        textAnchor="end"
      >
        HISTORICAL
      </text>
      <text 
        x={paddingLeft + 3 * (w + gap) - gap/2 + 5} 
        y="20" 
        fill="#b45309" 
        fontSize="8" 
        fontWeight="bold" 
        textAnchor="start"
      >
        FORECAST
      </text>

      {/* Render Candles */}
      {candlesToRender.map((candle, idx) => {
        const x = paddingLeft + idx * (w + gap);
        const yOpen = scale(candle.open);
        const yClose = scale(candle.close);
        const yHigh = scale(candle.high);
        const yLow = scale(candle.low);
        
        const isGreen = candle.close >= candle.open;
        const rectY = Math.min(yOpen, yClose);
        const rectH = Math.max(Math.abs(yOpen - yClose), 4);
        
        return (
          <g key={idx}>
            {candle.isForecast ? (
              <>
                <line 
                  x1={x + w/2} 
                  y1={yHigh} 
                  x2={x + w/2} 
                  y2={yLow} 
                  stroke={isGreen ? '#10b981' : '#f43f5e'} 
                  strokeWidth="1.5" 
                  strokeDasharray="2"
                />
                <rect 
                  x={x} 
                  y={rectY} 
                  width={w} 
                  height={rectH} 
                  fill="none" 
                  stroke={isGreen ? '#10b981' : '#f43f5e'} 
                  strokeWidth="1.5"
                  strokeDasharray="3 1"
                  rx="2"
                />
              </>
            ) : (
              <>
                <line 
                  x1={x + w/2} 
                  y1={yHigh} 
                  x2={x + w/2} 
                  y2={yLow} 
                  stroke={isGreen ? '#10b981' : '#f43f5e'} 
                  strokeWidth="2" 
                />
                <rect 
                  x={x} 
                  y={rectY} 
                  width={w} 
                  height={rectH} 
                  fill={isGreen ? '#10b981' : '#f43f5e'} 
                  rx="2"
                />
              </>
            )}
          </g>
        );
      })}

      {/* Forecast dotted trend lines */}
      <path
        d={candlesToRender.reduce((path, candle, idx) => {
          const x = paddingLeft + idx * (w + gap) + w/2;
          const y = scale((candle.open + candle.close) / 2);
          return path + (idx === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`);
        }, "")}
        fill="none"
        stroke="#d97706"
        strokeWidth="1.5"
        strokeDasharray="3"
      />
    </svg>
  );
}
