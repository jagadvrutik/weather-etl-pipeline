import schedule
import time
from datetime import datetime
from pipeline import run_pipeline
from utils.logger import get_logger

logger = get_logger()


def scheduled_run():
    logger.info(f"Scheduled trigger fired at {datetime.now().strftime('%H:%M:%S')}")
    run_pipeline()


if __name__ == "__main__":
    logger.info("Scheduler started — pipeline will run every hour")
    logger.info("First run: NOW")
    logger.info("Then every: 60 minutes")

    scheduled_run()

    schedule.every(60).minutes.do(scheduled_run)

    logger.info("Waiting for next scheduled run... (press CTRL+C to stop)")

    while True:
        schedule.run_pending()
        time.sleep(30)