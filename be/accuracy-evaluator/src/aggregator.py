import datetime
from .database import SessionLocal
from src.models.prediction_cache import PredictionCache
from src.models.grade import PredictionGrade, DailyAssetScore
from src.models.asset import Asset

async def aggregate_daily_scores(db):
    """
    Groups all graded predictions by ticker and creation date,
    calculates average MAPE and Trend Accuracy, and saves exactly one consolidated row per day per ticker.
    """
    graded_preds = db.query(PredictionCache).filter(PredictionCache.is_graded == True).all()
    if not graded_preds:
        return

    groups = {}
    for pred in graded_preds:
        pred_date = pred.created_at.date()
        key = (pred.ticker, pred_date)
        if key not in groups:
            groups[key] = []
        groups[key].append(pred)

    for (ticker, pred_date), preds in groups.items():
        pred_ids = [p.id for p in preds]
        grades = db.query(PredictionGrade).filter(PredictionGrade.prediction_cache_id.in_(pred_ids)).all()
        
        if not grades:
            continue

        valid_mapes = [g.mape_5d for g in grades if g.mape_5d is not None]
        valid_trends = [g.trend_acc_5d for g in grades if g.trend_acc_5d is not None]

        avg_mape = round(sum(valid_mapes) / len(valid_mapes), 2) if valid_mapes else None
        avg_trend = round(sum(valid_trends) / len(valid_trends), 2) if valid_trends else None

        # Upsert daily asset score
        daily_score = db.query(DailyAssetScore).filter(
            DailyAssetScore.ticker == ticker,
            DailyAssetScore.date == pred_date
        ).first()

        if not daily_score:
            daily_score = DailyAssetScore(
                ticker=ticker,
                date=pred_date,
                avg_mape_5d=avg_mape,
                avg_trend_acc_5d=avg_trend,
                total_predictions_evaluated=len(grades)
            )
            db.add(daily_score)
        else:
            daily_score.avg_mape_5d = avg_mape
            daily_score.avg_trend_acc_5d = avg_trend
            daily_score.total_predictions_evaluated = len(grades)
            daily_score.updated_at = datetime.datetime.utcnow()

        db.commit()
        print(f"[Evaluator Aggregator] Consolidated daily score for {ticker} on {pred_date}: Avg_MAPE={avg_mape}%, Avg_Trend={avg_trend}% (from {len(grades)} predictions)")

        # Update the main Asset table's accuracy_score
        asset = db.query(Asset).filter(Asset.ticker == ticker).first()
        if asset and avg_trend is not None:
            asset.accuracy_score = avg_trend
            asset.updated_at = datetime.datetime.utcnow()
            db.commit()
            print(f"[Evaluator Aggregator] Updated Asset {ticker} table accuracy_score to {avg_trend}%")
