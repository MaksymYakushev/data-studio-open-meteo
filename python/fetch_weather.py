import requests
import pandas as pd
from pathlib import Path

# Prague coordinates
latitude = 50.0755
longitude = 14.4378

# Open-Meteo API
url = "https://api.open-meteo.com/v1/forecast"

params = {
    "latitude": latitude,
    "longitude": longitude,
    "hourly": [
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "windspeed_10m"
    ],
    "timezone": "Europe/Prague"
}

# Get data from API
response = requests.get(url, params=params)
response.raise_for_status()

# Convert response to JSON
data = response.json()

# Convert JSON to DataFrame
df = pd.DataFrame({
    "datetime": data["hourly"]["time"],
    "temperature": data["hourly"]["temperature_2m"],
    "humidity": data["hourly"]["relative_humidity_2m"],
    "precipitation": data["hourly"]["precipitation"],
    "wind_speed": data["hourly"]["windspeed_10m"]
})


# Save CSV
df["city"] = "Prague"
raw_dir = Path("data/raw")
raw_dir.mkdir(parents=True, exist_ok=True)
output_file = raw_dir / "prague_weather.csv"
df.to_csv(output_file, index=False)

print(f"Data saved to: {output_file}")
print(f"Rows: {len(df)}")
print(df.head())