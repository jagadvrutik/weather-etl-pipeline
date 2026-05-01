import pandas as pd
from datetime import datetime
import sys
import os

from extractor.weather_api import WeatherExtractor
from transformer.clean_data import WeatherTransformer
from loader.snowflake_loader import SnowflakeLoader


def run_pipeline():
    start_time = datetime.now()

    print(f"\n{'=' * 50}")
    print("  WEATHER ETL PIPELINE")
    print(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 50}\n")

    print("STEP 1/3: Extracting from API...")

    extractor = WeatherExtractor()

    raw_df = extractor.fetch_all_cities()

    print(f"   {len(raw_df)} cities extracted\n")

    print("STEP 2/3: Transforming data...")

    transformer = WeatherTransformer(raw_df)

    clean_df = transformer.transform()

    print(f"   {len(clean_df)} rows ready for load\n")

    print("STEP 3/3: Loading into Snowflake...")

    loader = SnowflakeLoader()

    loader.connect()

    loader.load_raw(raw_df)

    loader.load_staging(clean_df)

    loader.refresh_mart()

    loader.disconnect()

    end_time = datetime.now()

    duration = (end_time - start_time).seconds

    print(f"\n{'=' * 50}")
    print("  PIPELINE COMPLETE")
    print(f"  Duration : {duration} seconds")
    print(f"  Finished : {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    run_pipeline()