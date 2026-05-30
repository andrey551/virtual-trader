"use client";

import React, { useEffect, useRef, useState } from "react";
import { createChart, ColorType, CrosshairMode, CandlestickSeries, HistogramSeries, LineSeries, createSeriesMarkers } from "lightweight-charts";

interface DynamicChartProps {
  selectedAsset: {
    symbol: string;
    candles?: {
      time: string;
      open: number;
      high: number;
      low: number;
      close: number;
      volume: number;
      isForecast?: boolean;
    }[];
  };
  forecastOffset: number;
  interval: string;
}

export default function DynamicChart({ selectedAsset, forecastOffset, interval }: DynamicChartProps) {
  const container = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<any>(null);
  const candlestickSeriesRef = useRef<any>(null);
  const volumeSeriesRef = useRef<any>(null);
  const sma7SeriesRef = useRef<any>(null);
  const sma25SeriesRef = useRef<any>(null);
  const markerApiRef = useRef<any>(null);
  const hasFitContentForSymbol = useRef<string | null>(null);

  const [ma7, setMa7] = useState<string>("-");
  const [ma25, setMa25] = useState<string>("-");

  // Effect 1: Initialize Chart Container and Config
  useEffect(() => {
    if (!container.current) return;

    // Clear container
    container.current.innerHTML = "";

    // Create chart
    const chart = createChart(container.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#fbf8ee" }, // Warm Cream Theme
        textColor: "#52525b", // zinc-600
        fontFamily: "monospace",
      },
      grid: {
        vertLines: { color: "rgba(235, 220, 185, 0.35)" },
        horzLines: { color: "rgba(235, 220, 185, 0.35)" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: "rgba(180, 83, 9, 0.4)",
          width: 1,
          style: 3, // dashed
        },
        horzLine: {
          color: "rgba(180, 83, 9, 0.4)",
          width: 1,
          style: 3,
        },
      },
      rightPriceScale: {
        borderColor: "#ebdcb9",
        textColor: "#71717a",
      },
      timeScale: {
        borderColor: "#ebdcb9",
        timeVisible: true,
        secondsVisible: false,
      },
      width: container.current.clientWidth,
      height: container.current.clientHeight || 360,
    });

    // Add primary candlestick series
    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#10b981", // emerald-500
      downColor: "#ef4444", // rose-500
      borderVisible: false,
      wickUpColor: "#10b981",
      wickDownColor: "#ef4444",
    });

    // Add secondary volume series
    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: "#26a69a",
      priceFormat: {
        type: "volume",
      },
      priceScaleId: "", // Overlay mode
    });

    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.8, // volume takes bottom 20%
        bottom: 0,
      },
    });

    // Add indicator lines
    const sma7Series = chart.addSeries(LineSeries, {
      color: "#3b82f6", // blue-500
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: true,
    });

    const sma25Series = chart.addSeries(LineSeries, {
      color: "#ec4899", // pink-500
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: true,
    });

    // Create markers plugin
    const markerApi = createSeriesMarkers(candlestickSeries, []);

    // Save references
    chartInstance.current = chart;
    candlestickSeriesRef.current = candlestickSeries;
    volumeSeriesRef.current = volumeSeries;
    sma7SeriesRef.current = sma7Series;
    sma25SeriesRef.current = sma25Series;
    markerApiRef.current = markerApi;

    // Handle responsiveness
    const handleResize = () => {
      if (container.current) {
        chart.applyOptions({
          width: container.current.clientWidth,
          height: container.current.clientHeight,
        });
      }
    };

    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(container.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartInstance.current = null;
      candlestickSeriesRef.current = null;
      volumeSeriesRef.current = null;
      sma7SeriesRef.current = null;
      sma25SeriesRef.current = null;
      markerApiRef.current = null;
    };
  }, [selectedAsset.symbol]); // Recreate chart when symbol changes to clean drawing objects and reset scaling

  // Effect 2: Update candles, volumes, SMAs and markers
  useEffect(() => {
    const chart = chartInstance.current;
    const candlestickSeries = candlestickSeriesRef.current;
    const volumeSeries = volumeSeriesRef.current;
    const sma7Series = sma7SeriesRef.current;
    const sma25Series = sma25SeriesRef.current;

    if (!chart || !candlestickSeries || !volumeSeries || !sma7Series || !sma25Series) return;

    const rawCandles = selectedAsset.candles || [];
    if (rawCandles.length === 0) return;

    // Calculate step seconds based on selected timeframe interval
    let stepSeconds = 24 * 3600; // default 1 day
    if (interval === "1m") stepSeconds = 60;
    else if (interval === "5m") stepSeconds = 5 * 60;
    else if (interval === "15m") stepSeconds = 15 * 60;
    else if (interval === "30m") stepSeconds = 30 * 60;
    else if (interval === "1h") stepSeconds = 3600;

    // Get the last historical candle's time in Unix seconds
    let lastTime = Math.floor(new Date().getTime() / 1000);
    for (let i = rawCandles.length - 1; i >= 0; i--) {
      if (!rawCandles[i].isForecast) {
        const parsed = new Date(rawCandles[i].time);
        if (!isNaN(parsed.getTime())) {
          lastTime = Math.floor(parsed.getTime() / 1000);
          break;
        }
      }
    }

    const formattedCandles = [];
    const forecastTimes = new Set<number>();
    let currentTimestamp = lastTime;

    for (let i = 0; i < rawCandles.length; i++) {
      const c = rawCandles[i];
      let tNum: number;

      if (c.isForecast) {
        currentTimestamp += stepSeconds;
        tNum = currentTimestamp;
        forecastTimes.add(tNum);
      } else {
        const parsed = new Date(c.time);
        if (!isNaN(parsed.getTime())) {
          currentTimestamp = Math.floor(parsed.getTime() / 1000);
          tNum = currentTimestamp;
        } else {
          currentTimestamp += stepSeconds;
          tNum = currentTimestamp;
        }
      }

      // Add dynamic offset to forecast candles
      let openVal = c.open;
      let closeVal = c.close;
      let highVal = c.high;
      let lowVal = c.low;

      if (c.isForecast) {
        openVal += forecastOffset;
        closeVal += forecastOffset;
        highVal += forecastOffset;
        lowVal += forecastOffset;
      }

      const item: any = {
        time: tNum,
        open: openVal,
        high: highVal,
        low: lowVal,
        close: closeVal,
      };

      // Custom visual scheme for AI Prediction/Forecast
      if (c.isForecast) {
        const isUp = closeVal >= openVal;
        const color = isUp ? "#f59e0b" : "#b45309"; // Amber/Gold styling for forecast
        item.color = color;
        item.borderColor = color;
        item.wickColor = color;
      }

      formattedCandles.push(item);
    }

    // Sort and remove duplicate timestamps numerically
    const uniqueCandles: any[] = [];
    const seenTimes = new Set<number>();
    const sortedCandles = [...formattedCandles].sort(
      (a, b) => a.time - b.time
    );

    for (const c of sortedCandles) {
      if (!seenTimes.has(c.time)) {
        seenTimes.add(c.time);
        uniqueCandles.push(c);
      }
    }

    // Set candlestick values
    candlestickSeries.setData(uniqueCandles);

    // Apply markers to demarcate prediction candles
    const markerApi = markerApiRef.current;
    if (markerApi) {
      const firstForecastCandle = uniqueCandles.find((c) => forecastTimes.has(c.time));
      if (firstForecastCandle) {
        markerApi.setMarkers([
          {
            time: firstForecastCandle.time,
            position: "aboveBar",
            color: "#f59e0b",
            shape: "arrowDown",
            text: "AI FORECAST",
            size: 1,
          },
        ]);
      } else {
        markerApi.setMarkers([]);
      }
    }

    // Set volume histogram values
    const volumeData = uniqueCandles.map((c) => {
      const originalCandle = rawCandles.find(
        (rc) => rc.open === c.open && rc.close === c.close
      );
      const isUp = c.close >= c.open;
      return {
        time: c.time,
        value: originalCandle?.volume || Math.round(50000 + Math.random() * 50000),
        color: isUp ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)",
      };
    });
    volumeSeries.setData(volumeData);

    // Compute and set Technical Indicators (SMA 7 & 25)
    const calculateSMA = (data: any[], period: number) => {
      const smaData = [];
      for (let i = 0; i < data.length; i++) {
        if (i < period - 1) continue;
        let sum = 0;
        for (let j = 0; j < period; j++) {
          sum += data[i - j].close;
        }
        smaData.push({
          time: data[i].time,
          value: sum / period,
        });
      }
      return smaData;
    };

    const sma7Data = calculateSMA(uniqueCandles, 7);
    const sma25Data = calculateSMA(uniqueCandles, 25);

    sma7Series.setData(sma7Data);
    sma25Series.setData(sma25Data);

    // Set SMA value labels
    if (sma7Data.length > 0) {
      setMa7(
        sma7Data[sma7Data.length - 1].value.toLocaleString("en-US", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })
      );
    } else {
      setMa7("-");
    }

    if (sma25Data.length > 0) {
      setMa25(
        sma25Data[sma25Data.length - 1].value.toLocaleString("en-US", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })
      );
    } else {
      setMa25("-");
    }

    // Auto-fit content ONCE when symbol changes, preserving user zoom during forecast offsets
    if (hasFitContentForSymbol.current !== selectedAsset.symbol) {
      chart.timeScale().fitContent();
      hasFitContentForSymbol.current = selectedAsset.symbol;
    }
  }, [selectedAsset.candles, forecastOffset, selectedAsset.symbol, interval]);

  return (
    <div className="w-full h-full relative" style={{ minHeight: "360px" }}>
      {/* SMA and Symbol Legend overlay */}
      <div className="absolute top-3 left-3 z-10 font-mono text-[10px] flex items-center gap-3 bg-white/85 backdrop-blur-xs px-2.5 py-1 rounded-lg border border-[#ebdcb9]/40 select-none shadow-xs">
        <span className="text-amber-800 font-bold">{selectedAsset.symbol}</span>
        <span className="text-blue-500 font-semibold">MA(7): {ma7}</span>
        <span className="text-pink-500 font-semibold">MA(25): {ma25}</span>
      </div>

      <div
        ref={container}
        className="w-full h-full"
        style={{ height: "100%", width: "100%" }}
      />
    </div>
  );
}
