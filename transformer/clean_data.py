import pandas as pd
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class WeatherTransformer:

    VALID_TEMP_RANGE = (-10, 55)
    VALID_HUMIDITY_RANGE = (0, 100)
    VALID_WIND_RANGE = (0, 150)

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.log = []

    def cast_types(self):
        numeric_cols = [
            "temperature_c", "feels_like_c", "temp_min_c", "temp_max_c",
            "humidity_pct", "pressure_hpa", "wind_speed_mps",
            "cloudiness_pct", "visibility_m", "wind_deg"
        ]

        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce")

        datetime_cols = ["extracted_at", "sunrise_utc", "sunset_utc"]

        for col in datetime_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_datetime(self.df[col], errors="coerce")

        self.log.append("Data types cast correctly")
        return self

    def handle_nulls(self):
        null_counts = self.df.isnull().sum()
        nulls_found = null_counts[null_counts > 0]

        if not nulls_found.empty:
            self.log.append(f"Nulls found: {nulls_found.to_dict()}")

        self.df["wind_deg"] = self.df["wind_deg"].fillna(-1)
        self.df["visibility_m"] = self.df["visibility_m"].fillna(-1)

        critical = ["temperature_c", "humidity_pct", "city"]
        self.df["has_null_flag"] = self.df[critical].isnull().any(axis=1)

        self.log.append("Nulls handled")
        return self

    def remove_duplicates(self):
        before = len(self.df)

        self.df = self.df.drop_duplicates(subset=["city", "extracted_at"])

        after = len(self.df)

        if before != after:
            self.log.append(f"Removed {before - after} duplicate rows")
        else:
            self.log.append("No duplicates found")

        return self

    def validate_ranges(self):
        self.df["temp_out_of_range"] = ~self.df["temperature_c"].between(
            *self.VALID_TEMP_RANGE
        )

        self.df["humidity_out_of_range"] = ~self.df["humidity_pct"].between(
            *self.VALID_HUMIDITY_RANGE
        )

        self.df["wind_out_of_range"] = ~self.df["wind_speed_mps"].between(
            *self.VALID_WIND_RANGE
        )

        flagged = self.df[
            self.df["temp_out_of_range"] |
            self.df["humidity_out_of_range"] |
            self.df["wind_out_of_range"]
        ]

        if not flagged.empty:
            self.log.append(f"{len(flagged)} rows with out-of-range values flagged")
        else:
            self.log.append("All values within valid ranges")

        return self

    def add_derived_columns(self):

        def heat_category(temp):
            if temp < 20:
                return "Cool"
            elif temp < 28:
                return "Comfortable"
            elif temp < 35:
                return "Warm"
            elif temp < 40:
                return "Hot"
            else:
                return "Extreme Heat"

        self.df["heat_category"] = self.df["temperature_c"].apply(heat_category)

        def wind_description(speed):
            if speed < 0.5:
                return "Calm"
            elif speed < 3.3:
                return "Light Breeze"
            elif speed < 7.9:
                return "Moderate Breeze"
            elif speed < 13:
                return "Strong Breeze"
            else:
                return "Storm"

        self.df["wind_description"] = self.df["wind_speed_mps"].apply(wind_description)

        def humidity_level(h):
            if h < 30:
                return "Dry"
            elif h < 60:
                return "Comfortable"
            elif h < 80:
                return "Humid"
            else:
                return "Very Humid"

        self.df["humidity_level"] = self.df["humidity_pct"].apply(humidity_level)

        self.df["feels_like_diff"] = (
            self.df["feels_like_c"] - self.df["temperature_c"]
        ).round(2)

        self.df["extract_date"] = self.df["extracted_at"].dt.date
        self.df["extract_hour"] = self.df["extracted_at"].dt.hour

        self.log.append("Derived columns added")
        return self

    def standardise_text(self):
        self.df["city"] = self.df["city"].str.strip().str.title()
        self.df["weather_main"] = self.df["weather_main"].str.strip().str.title()
        self.df["weather_desc"] = self.df["weather_desc"].str.strip().str.lower()

        self.log.append("Text columns standardised")
        return self

    def transform(self) -> pd.DataFrame:
        print("\nStarting transformation...\n")

        (
            self
            .cast_types()
            .handle_nulls()
            .remove_duplicates()
            .validate_ranges()
            .add_derived_columns()
            .standardise_text()
        )

        print("\nTransformation Log")
        for entry in self.log:
            print(f"  {entry}")

        print(f"\nTransformation complete — {len(self.df)} rows ready\n")

        return self.df


if __name__ == "__main__":
    raw_df = pd.read_csv("logs/weather_extract_test.csv")
    print(f"Raw rows loaded: {len(raw_df)}")

    transformer = WeatherTransformer(raw_df)
    clean_df = transformer.transform()

    print(clean_df.to_string(index=False))

    clean_df.to_csv("logs/weather_clean_test.csv", index=False)
    print("Saved to logs/weather_clean_test.csv")