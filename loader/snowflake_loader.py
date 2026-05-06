import snowflake.connector
import pandas as pd
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
            account   = SNOWFLAKE_ACCOUNT,
            user      = SNOWFLAKE_USER,
            password  = SNOWFLAKE_PASSWORD,
            database  = SNOWFLAKE_DATABASE,
            warehouse = SNOWFLAKE_WAREHOUSE,
        )
        print("Connected to Snowflake")
        return self

    def _clean_val(self, val):
    
        if val is None:
            return None
        if hasattr(val, 'isoformat'):
            return str(val)           
        if hasattr(val, 'item'):
            return val.item()        
        return val

    def _format_row(self, row: dict) -> tuple:
        return tuple(self._clean_val(v) for v in row.values())

    def load_raw(self, df: pd.DataFrame):

        df_upload = df[[
            "city", "country", "temperature_c", "feels_like_c",
            "temp_min_c", "temp_max_c", "humidity_pct", "pressure_hpa",
            "wind_speed_mps", "wind_deg", "weather_main", "weather_desc",
            "cloudiness_pct", "visibility_m", "sunrise_utc",
            "sunset_utc", "extracted_at"
        ]].copy()

    
        for col in ["extracted_at", "sunrise_utc", "sunset_utc"]:
            df_upload[col] = pd.to_datetime(df_upload[col], errors="coerce")
            df_upload[col] = df_upload[col].dt.strftime("%Y-%m-%d %H:%M:%S")

        df_upload = df_upload.drop_duplicates(subset=["city", "extracted_at"])

        cursor = self.conn.cursor()
        cursor.execute("USE SCHEMA WEATHER_DB.RAW")

        sql = """
            INSERT INTO RAW_WEATHER (
                CITY, COUNTRY, TEMPERATURE_C, FEELS_LIKE_C,
                TEMP_MIN_C, TEMP_MAX_C, HUMIDITY_PCT, PRESSURE_HPA,
                WIND_SPEED_MPS, WIND_DEG, WEATHER_MAIN, WEATHER_DESC,
                CLOUDINESS_PCT, VISIBILITY_M, SUNRISE_UTC,
                SUNSET_UTC, EXTRACTED_AT
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                TO_TIMESTAMP(%s, 'YYYY-MM-DD HH24:MI:SS'),
                TO_TIMESTAMP(%s, 'YYYY-MM-DD HH24:MI:SS'),
                TO_TIMESTAMP(%s, 'YYYY-MM-DD HH24:MI:SS')
            )
        """

        count = 0
        for _, row in df_upload.iterrows():
            cursor.execute(sql, (
                row["city"], row["country"],
                float(row["temperature_c"]), float(row["feels_like_c"]),
                float(row["temp_min_c"]), float(row["temp_max_c"]),
                int(row["humidity_pct"]), int(row["pressure_hpa"]),
                float(row["wind_speed_mps"]),
                float(row["wind_deg"]) if row["wind_deg"] is not None else None,
                row["weather_main"], row["weather_desc"],
                int(row["cloudiness_pct"]),
                float(row["visibility_m"]) if row["visibility_m"] is not None else None,
                row["sunrise_utc"],
                row["sunset_utc"],
                row["extracted_at"],
            ))
            count += 1

        print(f"  RAW layer: loaded {count} new rows into RAW.RAW_WEATHER")
        return count

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

        
        for col in ["extracted_at", "sunrise_utc", "sunset_utc"]:
            df_upload[col] = pd.to_datetime(df_upload[col], errors="coerce")
            df_upload[col] = df_upload[col].dt.strftime("%Y-%m-%d %H:%M:%S")

        df_upload = df_upload.drop_duplicates(subset=["city", "extracted_at"])

        cursor = self.conn.cursor()
        cursor.execute("USE SCHEMA WEATHER_DB.STAGING")

        sql = """
            INSERT INTO STG_WEATHER (
                CITY, COUNTRY, TEMPERATURE_C, FEELS_LIKE_C,
                TEMP_MIN_C, TEMP_MAX_C, HUMIDITY_PCT, PRESSURE_HPA,
                WIND_SPEED_MPS, WIND_DEG, WEATHER_MAIN, WEATHER_DESC,
                CLOUDINESS_PCT, VISIBILITY_M, SUNRISE_UTC, SUNSET_UTC,
                EXTRACTED_AT, EXTRACT_DATE, EXTRACT_HOUR,
                HEAT_CATEGORY, WIND_DESCRIPTION, HUMIDITY_LEVEL,
                FEELS_LIKE_DIFF, HAS_NULL_FLAG, TEMP_OUT_OF_RANGE,
                HUMIDITY_OUT_OF_RANGE, WIND_OUT_OF_RANGE
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                TO_TIMESTAMP(%s, 'YYYY-MM-DD HH24:MI:SS'),
                TO_TIMESTAMP(%s, 'YYYY-MM-DD HH24:MI:SS'),
                TO_TIMESTAMP(%s, 'YYYY-MM-DD HH24:MI:SS'),
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """

        count = 0
        for _, row in df_upload.iterrows():
            cursor.execute(sql, (
                row["city"], row["country"],
                float(row["temperature_c"]), float(row["feels_like_c"]),
                float(row["temp_min_c"]), float(row["temp_max_c"]),
                int(row["humidity_pct"]), int(row["pressure_hpa"]),
                float(row["wind_speed_mps"]),
                float(row["wind_deg"]) if row["wind_deg"] is not None else None,
                row["weather_main"], row["weather_desc"],
                int(row["cloudiness_pct"]),
                float(row["visibility_m"]) if row["visibility_m"] is not None else None,
                row["sunrise_utc"],
                row["sunset_utc"],
                row["extracted_at"],
                str(row["extract_date"]),
                int(row["extract_hour"]),
                row["heat_category"], row["wind_description"], row["humidity_level"],
                float(row["feels_like_diff"]),
                bool(row["has_null_flag"]),
                bool(row["temp_out_of_range"]),
                bool(row["humidity_out_of_range"]),
                bool(row["wind_out_of_range"]),
            ))
            count += 1

        print(f"  STAGING layer: loaded {count} new rows into STAGING.STG_WEATHER")
        return count

    def refresh_mart(self):

        cursor = self.conn.cursor()
        cursor.execute("USE SCHEMA WEATHER_DB.MART")

        cursor.execute("DELETE FROM DAILY_WEATHER_SUMMARY WHERE 1=1")

        cursor.execute("""
            INSERT INTO DAILY_WEATHER_SUMMARY (
                summary_date, city, avg_temp_c, max_temp_c, min_temp_c,
                avg_humidity_pct, avg_wind_speed_mps,
                dominant_weather, dominant_heat_cat, total_readings
            )
            SELECT
                CAST(EXTRACTED_AT AS DATE)       AS summary_date,
                CITY,
                ROUND(AVG(TEMPERATURE_C), 2)     AS avg_temp_c,
                MAX(TEMPERATURE_C)               AS max_temp_c,
                MIN(TEMPERATURE_C)               AS min_temp_c,
                ROUND(AVG(HUMIDITY_PCT), 2)      AS avg_humidity_pct,
                ROUND(AVG(WIND_SPEED_MPS), 2)    AS avg_wind_speed_mps,
                MAX(WEATHER_MAIN)                AS dominant_weather,
                MAX(HEAT_CATEGORY)               AS dominant_heat_cat,
                COUNT(*)                         AS total_readings
            FROM WEATHER_DB.STAGING.STG_WEATHER
            GROUP BY CAST(EXTRACTED_AT AS DATE), CITY
        """)

        cursor.execute("SELECT COUNT(*) FROM DAILY_WEATHER_SUMMARY")
        rows = cursor.fetchone()[0]
        print(f"  MART layer: {rows} rows loaded into DAILY_WEATHER_SUMMARY")

    def disconnect(self):
        if self.conn:
            self.conn.close()
            print("Snowflake connection closed")