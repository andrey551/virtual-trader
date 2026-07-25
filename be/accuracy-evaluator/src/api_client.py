import httpx
from .config import BACKEND_URL

async def fetch_historical_candles(ticker: str, interval: str, period: str):
    async with httpx.AsyncClient() as client:
        try:
            url = f"{BACKEND_URL}/api/assets/{ticker}/candles"
            params = {"interval": interval, "period": period}
            res = await client.get(url, params=params, timeout=15.0)
            if res.status_code == 200:
                data = res.json()
                return data.get("candles") or []
        except Exception as e:
            print(f"[Evaluator API] Failed to fetch candles for {ticker} from backend: {e}")
    return []
