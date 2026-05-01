import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import pandas as pd
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import (
    SNOWFLAKE_ACCOUNT,
    SNOWFLAKE_USER,
    SNOWFLAKE_PASSWORD,
    SNOWFLAKE_DATABASE,
    SNOWFLAKE_WAREHOUSE
)


class SnowflakeLoader:

    def __init__(self):
        self.conn = None

    def connect(self):
        print("Connecting to Snowflake...")

        self.conn = snowflake.connector.connect(
            account=SNOWFLAKE_ACCOUNT,
            user=SNOWFLAKE_USER,
            password=SNOWFLAKE_PASSWORD,
            database=SNOWFLAKE_DATABASE,
            warehouse=SNOWFLAKE_WAREHOUSE,
        )

        print("Connected to Snowflake")
        return self

    def load_raw(self, df: pd.DataFrame):

        df_upload = df[[
            "city", "country", "temperature_c", "feels_like_c",
            "temp_min_c", "temp_max_c", "humidity_pct", "pressure_hpa",
            "wind_speed_mps", "wind_deg", "weather_main", "weather_desc",
            "cloudiness_pct", "visibility_m", "sunrise_utc",
            "sunset_utc", "extracted_at"
        ]].copy()

        df_upload.columns = [c.upper() for c in df_upload.columns]

        cursor = self.conn.cursor()
        cursor.execute("USE SCHEMA WEATHER_DB.RAW")

        success, nchunks, nrows, _ = write_pandas(
            self.conn,
            df_upload,
            "RAW_WEATHER"
        )

        print(f"RAW layer: loaded {nrows} rows into RAW.RAW_WEATHER")

        return nrows

    def load_staging(self, df: pd.DataFrame):

        staging_cols = [
            "city", "country", "temperature_c", "feels_like_c",
            "temp_min_c", "temp_max_c", "humidity_pct", "pressure_hpa",
            "wind_speed_mps", "wind_deg", "weather_main", "weather_desc",
            "cloudiness_pct", "visibility_m", "sunrise_utc", "sunset_utc",
            "extracted_at", "extract_date", "extract_hour",
            "heat_category", "wind_description", "humidity_level",
            "feels_like_diff", "has_null_flag", "temp_out_of_range",
            "humidity_out_of_range", "wind_out_of_range"
        ]

        df_upload = df[staging_cols].copy()

        df_upload.columns = [c.upper() for c in df_upload.columns]

        cursor = self.conn.cursor()
        cursor.execute("USE SCHEMA WEATHER_DB.STAGING")

        success, nchunks, nrows, _ = write_pandas(
            self.conn,
            df_upload,
            "STG_WEATHER"
        )

        print(f"STAGING layer: loaded {nrows} rows into STAGING.STG_WEATHER")

        return nrows

    def refresh_mart(self):

        cursor = self.conn.cursor()

        cursor.execute("USE SCHEMA WEATHER_DB.MART")

        cursor.execute("""
            INSERT INTO DAILY_WEATHER_SUMMARY (
                summary_date,
                city,
                avg_temp_c,
                max_temp_c,
                min_temp_c,
                avg_humidity_pct,
                avg_wind_speed_mps,
                dominant_weather,
                dominant_heat_cat,
                total_readings
            )
            SELECT
                CAST(extracted_at AS DATE) AS summary_date,
                city,
                ROUND(AVG(temperature_c), 2) AS avg_temp_c,
                MAX(temperature_c) AS max_temp_c,
                MIN(temperature_c) AS min_temp_c,
                ROUND(AVG(humidity_pct), 2) AS avg_humidity_pct,
                ROUND(AVG(wind_speed_mps), 2) AS avg_wind_speed_mps,
                MODE(weather_main) AS dominant_weather,
                MODE(heat_category) AS dominant_heat_cat,
                COUNT(*) AS total_readings
            FROM WEATHER_DB.STAGING.STG_WEATHER
            WHERE CAST(extracted_at AS DATE) = CURRENT_DATE()
            GROUP BY 1, 2
        """)

        print("MART layer: DAILY_WEATHER_SUMMARY refreshed")

    def disconnect(self):

        if self.conn:
            self.conn.close()

            print("Snowflake connection closed")


if __name__ == "__main__":

    clean_df = pd.read_csv(
        "logs/weather_clean_test.csv",
        parse_dates=[
            "extracted_at",
            "sunrise_utc",
            "sunset_utc"
        ]
    )

    loader = SnowflakeLoader()

    loader.connect()

    loader.load_raw(clean_df)

    loader.load_staging(clean_df)

    loader.refresh_mart()

    loader.disconnect()