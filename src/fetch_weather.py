import requests
import pandas as pd
from pathlib import Path


LATITUDE = 50.0755
LONGITUDE = 14.4378

URL = "https://api.open-meteo.com/v1/forecast"

PARAMS = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "hourly": [
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "windspeed_10m",
    ],
    "timezone": "Europe/Prague",
}


def fetch_weather():
    response = requests.get(URL, params=PARAMS)
    response.raise_for_status()

    return response.json()


def transform_weather(data):
    df = pd.DataFrame({
        "datetime": data["hourly"]["time"],
        "temperature": data["hourly"]["temperature_2m"],
        "humidity": data["hourly"]["relative_humidity_2m"],
        "precipitation": data["hourly"]["precipitation"],
        "wind_speed": data["hourly"]["windspeed_10m"],
    })

    df["city"] = "Prague"

    return df


def save_data(df):
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    output_file = raw_dir / "prague_weather.csv"

    df.to_csv(output_file, index=False)

    print(f"Saved: {output_file}")
    print(f"Rows: {len(df)}")


def main():
    data = fetch_weather()
    df = transform_weather(data)
    save_data(df)

    print("\nFirst 5 rows:")
    print(df.head())


if __name__ == "__main__":
    main()