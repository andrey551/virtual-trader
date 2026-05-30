export interface Candle {
  open: number;
  high: number;
  low: number;
  close: number;
  isForecast?: boolean;
}

export interface TechnicalReason {
  summary: string;
  detail: string;
}

export interface Asset {
  id: string;
  name: string;
  category: 'Crypto' | 'Stock' | 'Forex' | 'Commodity';
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  marketCap: string;
  volume24h: string;
  rsi: number;
  macd: string;
  peRatio?: string;
  rating: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  candles: Candle[];
  technicalReasons: TechnicalReason[];
  fundamentalReasons: string[];
}

export interface GlobalEvent {
  id: string;
  title: string;
  category: string;
  date: string;
  impactScore: string;
  tickers: string[];
}
