import requests
import pandas as pd
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import API_KEY, CITIES

class WeatherExtractor:
    
     BASE_URL = "http://api.openweathermap.org/data/2.5/weather"
     
     def __init__(self):
          self.api_key = API_KEY
          self.cities = CITIES
          
     def fetch_one_city(self, city: str)-> dict:
         params = {
             "q":  city + ",IN",
             "appid": self.api_key,
             "units": "metric"
         }
         
         response = requests.get(self.BASE_URL, params=params,timeout=10)
         
         response.raise_for_status()
         
         data = response.json()
         
         return{
            "city":            city,
            "country":         data["sys"]["country"],
            "temperature_c":   data["main"]["temp"],
            "feels_like_c":    data["main"]["feels_like"],
            "temp_min_c":      data["main"]["temp_min"],
            "temp_max_c":      data["main"]["temp_max"],
            "humidity_pct":    data["main"]["humidity"],
            "pressure_hpa":    data["main"]["pressure"],
            "wind_speed_mps":  data["wind"]["speed"],
            "wind_deg":        data["wind"].get("deg", None),
            "weather_main":    data["weather"][0]["main"],
            "weather_desc":    data["weather"][0]["description"],
            "cloudiness_pct":  data["clouds"]["all"],
            "visibility_m":    data.get("visibility", None),
            "sunrise_utc":     datetime.utcfromtimestamp(data["sys"]["sunrise"]).strftime("%Y-%m-%d %H:%M:%S"),
            "sunset_utc":      datetime.utcfromtimestamp(data["sys"]["sunset"]).strftime("%Y-%m-%d %H:%M:%S"),
            "extracted_at":    datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
         }
         
     def fetch_all_cities(self) -> pd.DataFrame:
       
            records = []

            for city in self.cities:
                try:
                    record = self.fetch_one_city(city)
                    records.append(record)
                    print(f"Fetched: {city} — {record['temperature_c']}°C, {record['weather_desc']}")

                except requests.exceptions.HTTPError as e:
                    print(f" HTTP Error for {city}: {e}")

                except requests.exceptions.ConnectionError:
                    print(f" Connection failed for {city}. Check your internet.")

                except Exception as e:
                    print(f" Unexpected error for {city}: {e}")

            df = pd.DataFrame(records)
            return df
        
        
if __name__ == "__main__":
    extractor = WeatherExtractor()
    df = extractor.fetch_all_cities()

    print("\n── Extracted Data ──")
    print(df.to_string(index=False))

    df.to_csv("logs/weather_extract_test.csv", index=False)
    print("\n Saved to logs/weather_extract_test.csv")
         
         
       