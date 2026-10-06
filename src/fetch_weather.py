import requests
import pandas as pd
from pathlib import Path
from google.cloud import bigquery

LATITUDE = 50.0755
LONGITUDE = 14.4378

PROJECT_ID = "data-studio-open-meteo"
DATASET_ID = "weather"
TABLE_ID = "prague_weather"

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


def save_to_bigquery(df):
    client = bigquery.Client(project=PROJECT_ID)

    table_id = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE"
    )

    job = client.load_table_from_dataframe(
        df,
        table_id,
        job_config=job_config,
    )

    job.result()

    print(f"Loaded {len(df)} rows into {table_id}")


def save_csv(df):
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    output_file = raw_dir / "prague_weather.csv"

    df.to_csv(output_file, index=False)

    print(f"CSV saved: {output_file}")


def main():
    print("Fetching weather data...")

    data = fetch_weather()

    df = transform_weather(data)

    print(f"Received {len(df)} rows")

    save_csv(df)

    save_to_bigquery(df)

    print("\nFirst 5 rows:")
    print(df.head())


if __name__ == "__main__":
    main()