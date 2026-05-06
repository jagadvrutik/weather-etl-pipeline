import pandas as pd
from datetime import datetime
import sys
import os

from extractor.weather_api import WeatherExtractor
from transformer.clean_data import WeatherTransformer
from loader.snowflake_loader import SnowflakeLoader
from utils.logger import get_logger

logger = get_logger()


def run_pipeline():
    start_time = datetime.now()

    logger.info("=" * 50)
    logger.info("WEATHER ETL PIPELINE STARTED")
    logger.info("=" * 50)

    try:
        logger.info("STEP 1/3: Extracting weather data from API...")

        extractor = WeatherExtractor()
        raw_df = extractor.fetch_all_cities()

        logger.info(f"Extracted {len(raw_df)} city records successfully")

        if raw_df.empty:
            logger.error("No data extracted — aborting pipeline")
            return

        logger.info("STEP 2/3: Transforming and cleaning data...")

        transformer = WeatherTransformer(raw_df)
        clean_df = transformer.transform()

        logger.info(f"Transformation complete — {len(clean_df)} rows ready")

        logger.info("STEP 3/3: Loading into Snowflake...")

        loader = SnowflakeLoader()

        loader.connect()
        loader.load_raw(raw_df)
        loader.load_staging(clean_df)
        loader.refresh_mart()
        loader.disconnect()

        duration = (datetime.now() - start_time).seconds

        logger.info(f"PIPELINE COMPLETE — Duration: {duration}s")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"PIPELINE FAILED: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_pipeline()