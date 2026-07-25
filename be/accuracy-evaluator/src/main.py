import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from .scheduler import evaluate_and_grade_predictions

async def main():
    print("[Evaluator Service] Starting up (Modular Architecture)...")
    
    # 1. Boot up delay to allow other services to initialize
    await asyncio.sleep(5)
    
    # 2. Boot-up Trigger: Run evaluation immediately on start
    try:
        await evaluate_and_grade_predictions()
    except Exception as start_e:
        print(f"[Evaluator Service] Startup evaluation failed: {start_e}")

    # 3. Cron Trigger: Schedule evaluation to run every 24 hours (at 23:59:00 UTC)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        evaluate_and_grade_predictions,
        CronTrigger(hour=23, minute=59, second=0)
    )
    scheduler.start()
    print("[Evaluator Service] Scheduled evaluation to run daily at 23:59 UTC.")

    # Keep service running
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    asyncio.run(main())
