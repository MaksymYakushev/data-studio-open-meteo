"""Incrementally load completed Prague weather days from Open-Meteo Archive."""

import argparse
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests
from google.api_core.exceptions import NotFound
from google.cloud import bigquery

LATITUDE = 50.0755
LONGITUDE = 14.4378
TIMEZONE = "Europe/Prague"
CITY = "Prague"

PROJECT_ID = "data-studio-open-meteo"
DATASET_ID = "weather"
TABLE_ID = "prague_actual_weather"
FULL_TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

URL = "https://archive-api.open-meteo.com/v1/archive"
HOURLY_FIELDS = ["temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m"]
SCHEMA = [
    bigquery.SchemaField("datetime", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("temperature", "FLOAT64"),
    bigquery.SchemaField("humidity", "INT64"),
    bigquery.SchemaField("precipitation", "FLOAT64"),
    bigquery.SchemaField("wind_speed", "FLOAT64"),
    bigquery.SchemaField("city", "STRING", mode="REQUIRED"),
]

LOGGER = logging.getLogger(__name__)


def yesterday_prague() -> date:
    """Return the last fully completed calendar date in Prague."""
    return (pd.Timestamp.now(tz=TIMEZONE) - pd.Timedelta(days=1)).date()


def latest_loaded_date(client: bigquery.Client) -> date | None:
    """Read the latest loaded local date without modifying data."""
    query = f"SELECT MAX(DATE(datetime)) AS latest_date FROM `{FULL_TABLE_ID}`"
    try:
        result = client.query(query).result()
    except NotFound as error:
        raise RuntimeError(
            f"Target table {FULL_TABLE_ID} does not exist. Create it once before running the loader."
        ) from error
    return next(iter(result)).latest_date


def fetch_weather(start_date: date, end_date: date) -> dict:
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "hourly": HOURLY_FIELDS,
        "timezone": TIMEZONE,
    }
    LOGGER.info("Requesting Open-Meteo Archive data from %s through %s", start_date, end_date)
    response = requests.get(URL, params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def expected_hour_count(day: date) -> int:
    """Return 23, 24, or 25 according to the Prague DST transition for *day*."""
    start = pd.Timestamp(day).tz_localize(TIMEZONE)
    end = pd.Timestamp(day + timedelta(days=1)).tz_localize(TIMEZONE)
    return len(pd.date_range(start=start, end=end, freq="h", inclusive="left"))


def transform_weather(data: dict, start_date: date, completed_through: date) -> pd.DataFrame:
    """Return the contiguous run of complete, not-yet-loaded dates from the API."""
    try:
        hourly = data["hourly"]
        columns = {
            "datetime": hourly["time"],
            "temperature": hourly["temperature_2m"],
            "humidity": hourly["relative_humidity_2m"],
            "precipitation": hourly["precipitation"],
            "wind_speed": hourly["wind_speed_10m"],
        }
    except KeyError as error:
        raise RuntimeError(f"Open-Meteo response is missing expected hourly field: {error}") from error

    lengths = {name: len(values) for name, values in columns.items()}
    if len(set(lengths.values())) != 1:
        raise RuntimeError(f"Open-Meteo hourly fields have inconsistent lengths: {lengths}")

    df = pd.DataFrame(columns)
    # The existing BigQuery column is TIMESTAMP. The API returns Prague local
    # wall-clock values without an offset; preserve those calendar values as UTC
    # timestamps to stay compatible with the existing DATE(datetime) view.
    df["datetime"] = pd.to_datetime(df["datetime"], errors="raise").dt.tz_localize("UTC")
    df["humidity"] = pd.to_numeric(df["humidity"], errors="raise").astype("Int64")
    df["city"] = CITY
    df["date"] = df["datetime"].dt.date
    complete_frames = []
    for day in pd.date_range(start_date, completed_through, freq="D").date:
        day_frame = df[df["date"] == day]
        actual_rows = len(day_frame)
        expected_rows = expected_hour_count(day)
        if actual_rows != expected_rows:
            LOGGER.warning(
                "Stopping at incomplete %s: received %d hourly rows; expected %d for %s.",
                day,
                actual_rows,
                expected_rows,
                TIMEZONE,
            )
            break
        complete_frames.append(day_frame.drop(columns="date"))

    if not complete_frames:
        return pd.DataFrame(columns=[field.name for field in SCHEMA])
    result = pd.concat(complete_frames, ignore_index=True)
    return result[[field.name for field in SCHEMA]]


def save_csv(df: pd.DataFrame) -> Path:
    """Persist the successfully appended incremental batch for local inspection."""
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_file = raw_dir / "prague_actual_weather.csv"
    df.to_csv(output_file, index=False)
    LOGGER.info("Saved %d appended rows to %s", len(df), output_file)
    return output_file


def append_to_bigquery(client: bigquery.Client, df: pd.DataFrame) -> None:
    """Append a validated batch; no staging table or BigQuery DML is used."""
    job_config = bigquery.LoadJobConfig(
        schema=SCHEMA,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        create_disposition=bigquery.CreateDisposition.CREATE_NEVER,
    )
    job = client.load_table_from_dataframe(df, FULL_TABLE_ID, job_config=job_config)
    job.result()
    LOGGER.info("Load job %s appended %d rows to %s", job.job_id, len(df), FULL_TABLE_ID)


def main(dry_run: bool = False) -> int:
    client = bigquery.Client(project=PROJECT_ID)
    latest_date = latest_loaded_date(client)
    completed_through = yesterday_prague()
    start_date = (latest_date + timedelta(days=1)) if latest_date else completed_through

    LOGGER.info("Latest date in %s: %s", FULL_TABLE_ID, latest_date or "none")
    if start_date > completed_through:
        LOGGER.info("No new completed Prague dates to load.")
        return 0

    data = fetch_weather(start_date, completed_through)
    df = transform_weather(data, start_date, completed_through)
    day_count = df["datetime"].dt.date.nunique() if not df.empty else 0
    LOGGER.info("Validated %d rows across %d complete day(s).", len(df), day_count)
    if df.empty:
        LOGGER.warning("No complete new dates were returned; nothing was appended.")
        return 0
    if dry_run:
        LOGGER.info("Dry run: BigQuery and local CSV were not changed.")
        return 0

    append_to_bigquery(client, df)
    save_csv(df)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Validate data without writing it.")
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stdout,
    )
    try:
        raise SystemExit(main(dry_run=args.dry_run))
    except Exception:
        LOGGER.exception("Incremental actual-weather ingestion failed.")
        raise SystemExit(1)
