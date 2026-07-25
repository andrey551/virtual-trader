import datetime
import asyncio
from .database import SessionLocal
from src.models.prediction_cache import PredictionCache
from src.models.grade import PredictionGrade
from .evaluator import calculate_mape, calculate_trend_accuracy
from .api_client import fetch_historical_candles
from .aggregator import aggregate_daily_scores

def find_closest_candle_price(candles, target_time: datetime.datetime) -> float:
    best_candle = None
    min_diff = float('inf')
    target_ts = target_time.timestamp()
    
    for c in candles:
        c_time_str = c.get("time")
        if not c_time_str:
            continue
        try:
            if "T" in c_time_str:
                c_time = datetime.datetime.fromisoformat(c_time_str.replace("Z", ""))
            elif " " in c_time_str:
                c_time = datetime.datetime.strptime(c_time_str, "%Y-%m-%d %H:%M:%S")
            else:
                c_time = datetime.datetime.strptime(c_time_str, "%Y-%m-%d")
            
            c_ts = c_time.timestamp()
            diff = abs(target_ts - c_ts)
            if diff < min_diff:
                min_diff = diff
                best_candle = c
        except Exception as pe:
            print(f"[Evaluator Scheduler] Error parsing candle time {c_time_str}: {pe}")
            
    if best_candle:
        return float(best_candle["close"])
    return None

async def evaluate_and_grade_predictions():
    """
    Core execution logic that checks for expired raw predictions, grades them,
    and consolidates them by day.
    """
    print("[Evaluator Scheduler] Starting evaluation run...")
    db = SessionLocal()
    try:
        ungraded = db.query(PredictionCache).filter(PredictionCache.is_graded == False).all()
        if not ungraded:
            print("[Evaluator Scheduler] No ungraded predictions found.")
            return

        now = datetime.datetime.utcnow()
        graded_count = 0

        for pred in ungraded:
            # Check 5d horizon expiry
            expiry_5d = pred.created_at + datetime.timedelta(days=5)
            
            if now < expiry_5d:
                # Still within the 5 days prediction window, skip for final evaluation
                continue

            print(f"[Evaluator Scheduler] Grading prediction ID {pred.id} for {pred.ticker}...")
            
            # Fetch daily candles
            daily_candles = await fetch_historical_candles(pred.ticker, "1d", "1mo")
            if not daily_candles:
                print(f"[Evaluator Scheduler] Warning: No historical daily candles found for {pred.ticker}. Skipping.")
                continue

            actual_prices_5d = []
            for i in range(1, 6):
                target_time = pred.created_at + datetime.timedelta(days=i)
                price = find_closest_candle_price(daily_candles, target_time)
                actual_prices_5d.append(price if price is not None else pred.price_at_predict)

            mape_5d = calculate_mape(actual_prices_5d, pred.predict_price_5d)
            trend_acc_5d = calculate_trend_accuracy(actual_prices_5d, pred.predict_price_5d, pred.price_at_predict)

            # Fetch shorter scale candles
            minute_candles = await fetch_historical_candles(pred.ticker, "1m", "1d")
            hourly_candles = await fetch_historical_candles(pred.ticker, "1h", "5d")

            # 5m horizon
            actual_prices_5m = []
            for i in range(1, 6):
                target_time = pred.created_at + datetime.timedelta(minutes=i)
                price = find_closest_candle_price(minute_candles, target_time) if minute_candles else None
                actual_prices_5m.append(price if price is not None else pred.price_at_predict)
            mape_5m = calculate_mape(actual_prices_5m, pred.predict_price_5m)
            trend_acc_5m = calculate_trend_accuracy(actual_prices_5m, pred.predict_price_5m, pred.price_at_predict)

            # 5h horizon
            actual_prices_5h = []
            for i in range(1, 6):
                target_time = pred.created_at + datetime.timedelta(hours=i)
                price = find_closest_candle_price(hourly_candles, target_time) if hourly_candles else None
                actual_prices_5h.append(price if price is not None else pred.price_at_predict)
            mape_5h = calculate_mape(actual_prices_5h, pred.predict_price_5h)
            trend_acc_5h = calculate_trend_accuracy(actual_prices_5h, pred.predict_price_5h, pred.price_at_predict)

            # 5s horizon
            actual_prices_5s = []
            for i in range(1, 6):
                target_time = pred.created_at + datetime.timedelta(seconds=i*5)
                price = find_closest_candle_price(minute_candles, target_time) if minute_candles else None
                actual_prices_5s.append(price if price is not None else pred.price_at_predict)
            mape_5s = calculate_mape(actual_prices_5s, pred.predict_price_5s)
            trend_acc_5s = calculate_trend_accuracy(actual_prices_5s, pred.predict_price_5s, pred.price_at_predict)

            # Write to DB
            grade = PredictionGrade(
                prediction_cache_id=pred.id,
                ticker=pred.ticker,
                mape_5s=mape_5s,
                mape_5m=mape_5m,
                mape_5h=mape_5h,
                mape_5d=mape_5d,
                trend_acc_5s=trend_acc_5s,
                trend_acc_5m=trend_acc_5m,
                trend_acc_5h=trend_acc_5h,
                trend_acc_5d=trend_acc_5d
            )
            db.add(grade)
            
            # Update prediction cachegraded flag
            pred.is_graded = True
            db.commit()
            graded_count += 1
            print(f"[Evaluator Scheduler] Finished grading prediction ID {pred.id} for {pred.ticker}. MAPE_5d={mape_5d}%, Trend_5d={trend_acc_5d}%")

        if graded_count > 0:
            await aggregate_daily_scores(db)

    except Exception as e:
        print(f"[Evaluator Scheduler] Error in evaluate_and_grade_predictions: {e}")
        db.rollback()
    finally:
        db.close()
