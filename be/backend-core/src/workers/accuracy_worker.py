import asyncio
import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.services.mcp_client import mcp_client
from src.models.recommendation import Recommendation
from src.models.asset import Asset

async def evaluate_active_recommendations():
    """
    Scans all ACTIVE recommendations, fetches their latest prices, and checks if target_price
    or stop_loss triggers are hit. If so, updates status to CLOSED and computes realized_return.
    """
    print("[Accuracy Worker] Checking active recommendations for triggers...")
    db = SessionLocal()
    try:
        active_recs = db.query(Recommendation).filter(Recommendation.status == "ACTIVE").all()
        if not active_recs:
            print("[Accuracy Worker] No active recommendations to check.")
            # Still run recalculation to update from seed closed recommendations if any
            await recalculate_all_assets_accuracy(db)
            return

        for rec in active_recs:
            try:
                # Fetch price dynamically via MCP tool
                res = await mcp_client.call_tool("get_market_price", {"ticker": rec.ticker})
                if res.get("status") != "success":
                    print(f"[Accuracy Worker] Failed to fetch current price for {rec.ticker}: {res.get('message')}")
                    continue
                
                curr_price = float(res.get("price"))
                rec.current_price = Decimal(str(curr_price))
                rec.updated_at = datetime.datetime.utcnow()
                
                # Check triggers
                entry = float(rec.entry_price)
                target = float(rec.target_price) if rec.target_price else None
                stop = float(rec.stop_loss) if rec.stop_loss else None
                rec_type = rec.recommendation_type.upper()
                
                is_closed = False
                realized_ret = 0.0
                
                if rec_type == "BUY":
                    if target and curr_price >= target:
                        is_closed = True
                        realized_ret = ((target - entry) / entry) * 100.0
                        print(f"[Accuracy Worker] {rec.ticker} BUY hit TARGET price {target} at current {curr_price}")
                    elif stop and curr_price <= stop:
                        is_closed = True
                        realized_ret = ((stop - entry) / entry) * 100.0
                        print(f"[Accuracy Worker] {rec.ticker} BUY hit STOP LOSS price {stop} at current {curr_price}")
                elif rec_type == "SELL":
                    if target and curr_price <= target:
                        is_closed = True
                        realized_ret = ((entry - target) / entry) * 100.0
                        print(f"[Accuracy Worker] {rec.ticker} SELL hit TARGET price {target} at current {curr_price}")
                    elif stop and curr_price >= stop:
                        is_closed = True
                        realized_ret = ((entry - stop) / entry) * 100.0
                        print(f"[Accuracy Worker] {rec.ticker} SELL hit STOP LOSS price {stop} at current {curr_price}")
                
                if is_closed:
                    rec.status = "CLOSED"
                    rec.realized_return = Decimal(str(round(realized_ret, 2)))
                    
                db.commit()
            except Exception as e:
                print(f"[Accuracy Worker] Error updating recommendation ID {rec.id} ({rec.ticker}): {e}")
                db.rollback()
                
        # Re-calculate accuracy score for all assets
        await recalculate_all_assets_accuracy(db)
        
    finally:
        db.close()

async def recalculate_all_assets_accuracy(db: Session):
    """
    Computes accuracy scores and alpha outperformance for each unique ticker from the closed recommendations.
    Updates the assets table with calculated figures.
    """
    print("[Accuracy Worker] Recalculating asset accuracy scores...")
    try:
        # Get all assets
        assets = db.query(Asset).all()
        for asset in assets:
            # Fetch all CLOSED recommendations for this asset
            closed_recs = db.query(Recommendation).filter(
                Recommendation.ticker == asset.ticker,
                Recommendation.status == "CLOSED"
            ).all()
            
            if not closed_recs:
                # Keep existing score or skip if no closed recommendations yet
                continue
                
            total_closed = len(closed_recs)
            # Profitability is defined as realized_return > 0
            hits = sum(1 for r in closed_recs if r.realized_return and float(r.realized_return) > 0.0)
            
            accuracy = (hits / total_closed) * 100.0
            avg_return = sum(float(r.realized_return or 0.0) for r in closed_recs) / total_closed
            
            asset.accuracy_score = Decimal(str(round(accuracy, 2)))
            asset.alpha_outperformance = Decimal(str(round(avg_return, 2)))
            asset.updated_at = datetime.datetime.utcnow()
            
            db.commit()
            print(f"[Accuracy Worker] Updated accuracy for {asset.ticker}: Accuracy={accuracy:.2f}%, Alpha={avg_return:.2f}% (based on {total_closed} closed recs)")
            
    except Exception as e:
        print(f"[Accuracy Worker] Error recalculating asset accuracy: {e}")
        db.rollback()
