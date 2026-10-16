import requests
import pandas as pd
from pathlib import Path
from google.cloud import bigquery

LATITUDE = 50.0755
LONGITUDE = 14.4378

PROJECT_ID = "data-studio-open-meteo"
DATASET_ID = "weather"
TABLE_ID = "prague_actual_weather"

URL = "https://archive-api.open-meteo.com/v1/archive"

PARAMS = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "start_date": "2026-09-16",
    "end_date": "2026-10-14",
    "hourly": [
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "wind_speed_10m",
    ],
    "timezone": "Europe/Prague",
}


def fetch_weather():
    response = requests.get(URL, params=PARAMS, timeout=60)
    response.raise_for_status()
    return response.json()


def transform_weather(data):
    hourly = data["hourly"]

    df = pd.DataFrame({
        "datetime": hourly["time"],
        "temperature": hourly["temperature_2m"],
        "humidity": hourly["relative_humidity_2m"],
        "precipitation": hourly["precipitation"],
        "wind_speed": hourly["wind_speed_10m"],
    })

    df["datetime"] = pd.to_datetime(df["datetime"])
    df["city"] = "Prague"

    # Exclude future dates and the current incomplete day.
    today = pd.Timestamp.now(tz="Europe/Prague").date()
    df = df[df["datetime"].dt.date < today]

    return df


def save_csv(df):
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    output_file = raw_dir / "prague_actual_weather.csv"
    df.to_csv(output_file, index=False)

    print(f"CSV saved: {output_file}")


def save_to_bigquery(df):
    if df.empty:
        print("No completed historical days to load.")
        return

    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    # Create a staging table with the incoming data.
    staging_table_id = (
        f"{PROJECT_ID}.{DATASET_ID}._prague_actual_weather_staging"
    )

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        schema=[
            bigquery.SchemaField("datetime", "DATETIME"),
            bigquery.SchemaField("temperature", "FLOAT"),
            bigquery.SchemaField("humidity", "FLOAT"),
            bigquery.SchemaField("precipitation", "FLOAT"),
            bigquery.SchemaField("wind_speed", "FLOAT"),
            bigquery.SchemaField("city", "STRING"),
        ],
    )

    client.load_table_from_dataframe(
        df,
        staging_table_id,
        job_config=job_config,
    ).result()

    # Create the destination table if it doesn't exist.
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS `{table_id}` (
        datetime DATETIME,
        temperature FLOAT64,
        humidity FLOAT64,
        precipitation FLOAT64,
        wind_speed FLOAT64,
        city STRING
    )
    """

    client.query(create_table_sql).result()

    # Update existing hourly observations and insert new ones.
    merge_sql = f"""
    MERGE `{table_id}` AS target
    USING (
        SELECT * EXCEPT(row_num)
        FROM (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY city, datetime
                    ORDER BY datetime
                ) AS row_num
            FROM `{staging_table_id}`
        )
        WHERE row_num = 1
    ) AS source
    ON target.city = source.city
       AND target.datetime = source.datetime

    WHEN MATCHED THEN UPDATE SET
        temperature = source.temperature,
        humidity = source.humidity,
        precipitation = source.precipitation,
        wind_speed = source.wind_speed

    WHEN NOT MATCHED THEN INSERT (
        datetime,
        temperature,
        humidity,
        precipitation,
        wind_speed,
        city
    )
    VALUES (
        source.datetime,
        source.temperature,
        source.humidity,
        source.precipitation,
        source.wind_speed,
        source.city
    )
    """

    client.query(merge_sql).result()

    # Remove the temporary table.
    client.delete_table(staging_table_id, not_found_ok=True)

    print(f"Upserted {len(df)} rows into {table_id}")


def main():
    print("Fetching historical weather data...")

    data = fetch_weather()
    df = transform_weather(data)

    print(f"Received {len(df)} completed historical hourly records")

    save_csv(df)
    save_to_bigquery(df)

    print("\nFirst 5 rows:")
    print(df.head())


if __name__ == "__main__":
    main()