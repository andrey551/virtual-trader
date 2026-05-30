"use client";

import React, { useEffect, useRef, useMemo } from "react";
import {
  createChart,
  ColorType,
  CrosshairMode,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  createSeriesMarkers,
  IChartApi,
  ISeriesApi,
  ISeriesMarkersPluginApi,
  Time
} from "lightweight-charts";

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

interface ChartCandleData {
  time: Time;
  open: number;
  high: number;
  low: number;
  close: number;
  color?: string;
  borderColor?: string;
  wickColor?: string;
}

export default function DynamicChart({ selectedAsset, forecastOffset, interval }: DynamicChartProps) {
  const container = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick", Time> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram", Time> | null>(null);
  const sma7SeriesRef = useRef<ISeriesApi<"Line", Time> | null>(null);
  const sma25SeriesRef = useRef<ISeriesApi<"Line", Time> | null>(null);
  const markerApiRef = useRef<ISeriesMarkersPluginApi<Time> | null>(null);
  const hasFitContentForSymbol = useRef<string | null>(null);

  // 1. Memoized Calculations during render phase to avoid setState cascading render warnings
  const { uniqueCandles, rawCandles, sma7Data, sma25Data, forecastTimes, ma7Label, ma25Label } = useMemo(() => {
    const candlesList = selectedAsset.candles || [];

    // Calculate step seconds based on selected timeframe interval
    let stepSeconds = 24 * 3600; // default 1 day
    if (interval === "1m") stepSeconds = 60;
    else if (interval === "5m") stepSeconds = 5 * 60;
    else if (interval === "15m") stepSeconds = 15 * 60;
    else if (interval === "30m") stepSeconds = 30 * 60;
    else if (interval === "1h") stepSeconds = 3600;

    // Get the last historical candle's time in Unix seconds
    let lastTime = Math.floor(new Date().getTime() / 1000);
    for (let i = candlesList.length - 1; i >= 0; i--) {
      if (!candlesList[i].isForecast) {
        const parsed = new Date(candlesList[i].time);
        if (!isNaN(parsed.getTime())) {
          lastTime = Math.floor(parsed.getTime() / 1000);
          break;
        }
      }
    }

    const formattedCandles: ChartCandleData[] = [];
    const forecastTimesSet = new Set<Time>();
    let currentTimestamp = lastTime;

    for (let i = 0; i < candlesList.length; i++) {
      const c = candlesList[i];
      let tNum: number;

      if (c.isForecast) {
        currentTimestamp += stepSeconds;
        tNum = currentTimestamp;
        forecastTimesSet.add(tNum as Time);
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

      const item: ChartCandleData = {
        time: tNum as Time,
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
    const uniqueList: ChartCandleData[] = [];
    const seenTimes = new Set<Time>();
    const sortedCandles = [...formattedCandles].sort((a, b) => (a.time as number) - (b.time as number));

    for (const c of sortedCandles) {
      if (!seenTimes.has(c.time)) {
        seenTimes.add(c.time);
        uniqueList.push(c);
      }
    }

    // Compute Moving Averages (SMA)
    const calculateSMA = (data: ChartCandleData[], period: number) => {
      const smaDataList = [];
      for (let i = 0; i < data.length; i++) {
        if (i < period - 1) continue;
        let sum = 0;
        for (let j = 0; j < period; j++) {
          sum += data[i - j].close;
        }
        smaDataList.push({
          time: data[i].time,
          value: sum / period,
        });
      }
      return smaDataList;
    };

    const s7 = calculateSMA(uniqueList, 7);
    const s25 = calculateSMA(uniqueList, 25);

    // Format labels
    const m7Label = s7.length > 0 
      ? s7[s7.length - 1].value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      : "-";
    const m25Label = s25.length > 0 
      ? s25[s25.length - 1].value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      : "-";

    return {
      uniqueCandles: uniqueList,
      rawCandles: candlesList,
      sma7Data: s7,
      sma25Data: s25,
      forecastTimes: forecastTimesSet,
      ma7Label: m7Label,
      ma25Label: m25Label
    };
  }, [selectedAsset.candles, forecastOffset, interval]);

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
    const markerApi = markerApiRef.current;

    if (!chart || !candlestickSeries || !volumeSeries || !sma7Series || !sma25Series) return;
    if (uniqueCandles.length === 0) return;

    // Set candlestick values
    candlestickSeries.setData(uniqueCandles);

    // Apply markers to demarcate prediction candles
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

    // Set SMAs
    sma7Series.setData(sma7Data);
    sma25Series.setData(sma25Data);

    // Auto-fit content ONCE when symbol changes, preserving user zoom during forecast offsets
    if (hasFitContentForSymbol.current !== selectedAsset.symbol) {
      chart.timeScale().fitContent();
      hasFitContentForSymbol.current = selectedAsset.symbol;
    }
  }, [uniqueCandles, rawCandles, sma7Data, sma25Data, forecastTimes, selectedAsset.symbol]);

  return (
    <div className="w-full h-full relative" style={{ minHeight: "360px" }}>
      {/* SMA and Symbol Legend overlay */}
      <div className="absolute top-3 left-3 z-10 font-mono text-[10px] flex items-center gap-3 bg-white/85 backdrop-blur-xs px-2.5 py-1 rounded-lg border border-[#ebdcb9]/40 select-none shadow-xs">
        <span className="text-amber-800 font-bold">{selectedAsset.symbol}</span>
        <span className="text-blue-500 font-semibold">MA(7): {ma7Label}</span>
        <span className="text-pink-500 font-semibold">MA(25): {ma25Label}</span>
      </div>

      <div
        ref={container}
        className="w-full h-full"
        style={{ height: "100%", width: "100%" }}
      />
    </div>
  );
}
