"""
Dataset Service
===============
Handles all dataset ingestion pipelines:
  - CSV / XLSX upload and validation
  - OpenAQ API fetch
  - Government / historical dataset import
  - Full cleaning pipeline: missing values, duplicates, outliers,
    feature engineering, and AQI calculation
"""

import os
import json
import requests
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional
from flask import current_app
from werkzeug.datastructures import FileStorage

from app import db
from app.models.dataset import Dataset
from app.models.aqi_reading import AQIReading
from app.utils.audit import log_action


# ---------------------------------------------------------------------------
# AQI Calculation (US EPA Standard)
# ---------------------------------------------------------------------------

AQI_BREAKPOINTS = {
    "pm25": [
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 350.4, 301, 400),
        (350.5, 500.4, 401, 500),
    ],
    "pm10": [
        (0, 54, 0, 50),
        (55, 154, 51, 100),
        (155, 254, 101, 150),
        (255, 354, 151, 200),
        (355, 424, 201, 300),
        (425, 504, 301, 400),
        (505, 604, 401, 500),
    ],
    "no2": [
        (0, 53, 0, 50),
        (54, 100, 51, 100),
        (101, 360, 101, 150),
        (361, 649, 151, 200),
        (650, 1249, 201, 300),
        (1250, 1649, 301, 400),
        (1650, 2049, 401, 500),
    ],
    "o3": [
        (0, 54, 0, 50),
        (55, 70, 51, 100),
        (71, 85, 101, 150),
        (86, 105, 151, 200),
        (106, 200, 201, 300),
    ],
    "co": [
        (0, 4.4, 0, 50),
        (4.5, 9.4, 51, 100),
        (9.5, 12.4, 101, 150),
        (12.5, 15.4, 151, 200),
        (15.5, 30.4, 201, 300),
        (30.5, 40.4, 301, 400),
        (40.5, 50.4, 401, 500),
    ],
    "so2": [
        (0, 35, 0, 50),
        (36, 75, 51, 100),
        (76, 185, 101, 150),
        (186, 304, 151, 200),
        (305, 604, 201, 300),
        (605, 804, 301, 400),
        (805, 1004, 401, 500),
    ],
}

AQI_CATEGORIES = [
    (0, 50, "Good"),
    (51, 100, "Moderate"),
    (101, 150, "Unhealthy for Sensitive Groups"),
    (151, 200, "Unhealthy"),
    (201, 300, "Very Unhealthy"),
    (301, 500, "Hazardous"),
]


def _calc_sub_aqi(concentration: float, breakpoints: list) -> Optional[float]:
    """Calculate sub-index AQI for a single pollutant."""
    for c_lo, c_hi, i_lo, i_hi in breakpoints:
        if c_lo <= concentration <= c_hi:
            return ((i_hi - i_lo) / (c_hi - c_lo)) * (concentration - c_lo) + i_lo
    return None


def calculate_aqi(row: dict) -> tuple:
    """Return (aqi_value, aqi_category) for a pollutant reading row."""
    sub_indices = []
    for pollutant, bps in AQI_BREAKPOINTS.items():
        val = row.get(pollutant)
        if val is not None and not np.isnan(float(val)):
            si = _calc_sub_aqi(float(val), bps)
            if si is not None:
                sub_indices.append(si)

    if not sub_indices:
        return None, None

    aqi = max(sub_indices)
    category = "Unknown"
    for lo, hi, cat in AQI_CATEGORIES:
        if lo <= aqi <= hi:
            category = cat
            break

    return round(aqi, 2), category


# ---------------------------------------------------------------------------
# Cleaning Pipeline
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = ["city", "recorded_at"]
POLLUTANT_COLUMNS = ["pm25", "pm10", "no2", "so2", "co", "o3", "nh3"]
NUMERIC_COLUMNS = POLLUTANT_COLUMNS + ["temperature", "humidity", "wind_speed",
                                        "wind_direction", "pressure"]

COLUMN_ALIASES = {
    # Common CSV header variations → canonical name
    "pm2.5": "pm25", "pm_2_5": "pm25", "pm2_5": "pm25",
    "pm_10": "pm10",
    "nitrogen_dioxide": "no2",
    "sulphur_dioxide": "so2", "sulfur_dioxide": "so2",
    "carbon_monoxide": "co",
    "ozone": "o3",
    "ammonia": "nh3",
    "temp": "temperature", "temp_c": "temperature",
    "rh": "humidity", "relative_humidity": "humidity",
    "ws": "wind_speed",
    "wd": "wind_direction",
    "pres": "pressure", "atm_pressure": "pressure",
    "date": "recorded_at", "datetime": "recorded_at", "timestamp": "recorded_at",
    "station": "station_id",
    "lat": "latitude", "lng": "longitude", "lon": "longitude",
}


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Run the full cleaning pipeline on a raw DataFrame.

    Pipeline steps:
    1. Normalise column names
    2. Drop fully empty rows
    3. Remove duplicate rows
    4. Parse datetime
    5. Coerce numeric columns
    6. Clip negative pollutant values to 0
    7. Remove outliers (IQR method, 3× IQR fence)
    8. Impute missing values (forward fill → median)
    9. Calculate AQI if not present
    10. Add derived time features

    Returns:
        Cleaned DataFrame ready for DB insertion or ML training.
    """
    # 1. Normalise column names
    df.columns = [c.strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]
    df.rename(columns=COLUMN_ALIASES, inplace=True)

    # 2. Drop completely empty rows
    df.dropna(how="all", inplace=True)

    # 3. Remove exact duplicates
    df.drop_duplicates(inplace=True)

    # 4. Parse datetime
    if "recorded_at" in df.columns:
        df["recorded_at"] = pd.to_datetime(df["recorded_at"], errors="coerce", utc=True)
        df.dropna(subset=["recorded_at"], inplace=True)
        df["recorded_at"] = df["recorded_at"].dt.tz_localize(None)

    # 5. Coerce numeric
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 6. Clip negative pollutant values
    for col in POLLUTANT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].clip(lower=0)

    # 7. Outlier removal (IQR × 3)
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 3 * iqr
            upper = q3 + 3 * iqr
            df[col] = df[col].where(df[col].between(lower, upper), other=np.nan)

    # 8. Impute missing: forward-fill within city groups, then median
    if "city" in df.columns:
        df.sort_values(["city", "recorded_at"], inplace=True, ignore_index=True)
        for col in NUMERIC_COLUMNS:
            if col in df.columns:
                df[col] = df.groupby("city")[col].transform(
                    lambda s: s.ffill().bfill()
                )

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col].fillna(df[col].median(), inplace=True)

    # 9. Calculate AQI
    if "aqi" not in df.columns or df["aqi"].isna().all():
        aqi_results = df[POLLUTANT_COLUMNS + ["temperature"]].apply(
            lambda row: calculate_aqi(row.to_dict()), axis=1, result_type="expand"
        )
        df["aqi"] = aqi_results[0]
        df["aqi_category"] = aqi_results[1]

    # 10. Feature engineering — time-based features
    if "recorded_at" in df.columns:
        df["hour"] = df["recorded_at"].dt.hour
        df["day_of_week"] = df["recorded_at"].dt.dayofweek
        df["month"] = df["recorded_at"].dt.month
        df["year"] = df["recorded_at"].dt.year
        df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
        df["season"] = df["month"].map(
            {12: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 1,
             6: 2, 7: 2, 8: 2, 9: 3, 10: 3, 11: 3}
        )

    # Drop rows still missing the target AQI
    df.dropna(subset=["aqi"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


# ---------------------------------------------------------------------------
# CSV Upload Pipeline
# ---------------------------------------------------------------------------

def upload_csv_dataset(
    file: FileStorage,
    user_id: int,
    name: str,
    description: str = "",
    location: str = "",
    is_public: bool = False,
) -> dict:
    """Save an uploaded CSV/XLSX, clean it, and store readings in DB.

    Returns:
        dict with dataset metadata.

    Raises:
        ValueError: on unsupported file type or empty dataset.
    """
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in ("csv", "xlsx"):
        raise ValueError("Only CSV and XLSX files are supported.")

    upload_dir = os.path.join("uploads", "datasets")
    os.makedirs(upload_dir, exist_ok=True)

    safe_name = f"{user_id}_{int(datetime.utcnow().timestamp())}_{filename}"
    file_path = os.path.join(upload_dir, safe_name)
    file.save(file_path)

    file_size_kb = os.path.getsize(file_path) // 1024

    # Create DB record immediately as "processing"
    dataset = Dataset(
        user_id=user_id,
        name=name,
        source=Dataset.SOURCE_CSV,
        file_path=file_path,
        original_filename=filename,
        file_size_kb=file_size_kb,
        description=description,
        location=location,
        is_public=is_public,
        status=Dataset.STATUS_PROCESSING,
    )
    db.session.add(dataset)
    db.session.commit()

    try:
        # Load data
        if ext == "csv":
            df = pd.read_csv(file_path, low_memory=False)
        else:
            df = pd.read_excel(file_path)

        if df.empty:
            raise ValueError("Uploaded file is empty.")

        # Run cleaning pipeline
        df = clean_dataframe(df)

        if df.empty:
            raise ValueError("No valid rows remain after cleaning.")

        dataset.row_count = len(df)
        dataset.column_count = len(df.columns)

        # Store readings in DB in batches
        _bulk_insert_readings(df, dataset.id)

        dataset.status = Dataset.STATUS_READY
        dataset.processing_log = f"Cleaned {len(df)} rows; {dataset.column_count} features."

    except Exception as exc:
        dataset.status = Dataset.STATUS_FAILED
        dataset.processing_log = str(exc)
        db.session.commit()
        raise ValueError(f"Dataset processing failed: {exc}") from exc

    db.session.commit()
    log_action("dataset.upload", entity="datasets", entity_id=dataset.id, user_id=user_id)
    return dataset.to_dict()


# ---------------------------------------------------------------------------
# OpenAQ API Fetch
# ---------------------------------------------------------------------------

def fetch_openaq_data(
    city: str,
    country: str,
    date_from: str,
    date_to: str,
    user_id: int,
    limit: int = 10000,
) -> dict:
    """Fetch air quality data from OpenAQ API v2.

    Returns:
        dict with dataset metadata.

    Raises:
        ValueError: on API errors or no data found.
    """
    api_key = current_app.config.get("OPENAQ_API_KEY", "")
    base_url = current_app.config.get("OPENAQ_BASE_URL", "https://api.openaq.io/v2")

    headers = {"X-API-Key": api_key} if api_key else {}

    params = {
        "city": city,
        "country": country,
        "date_from": date_from,
        "date_to": date_to,
        "limit": limit,
        "order_by": "datetime",
        "sort": "desc",
    }

    response = requests.get(f"{base_url}/measurements", params=params, headers=headers, timeout=30)

    if response.status_code != 200:
        raise ValueError(f"OpenAQ API error {response.status_code}: {response.text[:200]}")

    results = response.json().get("results", [])
    if not results:
        raise ValueError("No data found for the specified parameters.")

    # Transform OpenAQ response to standard format
    rows = []
    for r in results:
        rows.append({
            "city": city,
            "country": country,
            "station_id": r.get("location"),
            "latitude": r.get("coordinates", {}).get("latitude"),
            "longitude": r.get("coordinates", {}).get("longitude"),
            "recorded_at": r.get("date", {}).get("utc"),
            r.get("parameter", "unknown"): r.get("value"),
            "source": "openaq",
        })

    df = pd.DataFrame(rows)

    # Pivot so each pollutant is a column
    if "parameter" in df.columns:
        df_pivot = df.pivot_table(
            index=["city", "country", "station_id", "latitude", "longitude", "recorded_at", "source"],
            columns="parameter",
            values="value",
            aggfunc="mean",
        ).reset_index()
        df = df_pivot

    df = clean_dataframe(df)

    if df.empty:
        raise ValueError("No valid readings after processing OpenAQ data.")

    dataset_name = f"OpenAQ — {city}, {country} ({date_from} to {date_to})"
    dataset = Dataset(
        user_id=user_id,
        name=dataset_name,
        source=Dataset.SOURCE_OPENAQ,
        row_count=len(df),
        column_count=len(df.columns),
        location=f"{city}, {country}",
        date_from=date_from,
        date_to=date_to,
        status=Dataset.STATUS_READY,
        processing_log=f"Fetched {len(df)} readings from OpenAQ API.",
    )
    db.session.add(dataset)
    db.session.commit()

    _bulk_insert_readings(df, dataset.id)
    db.session.commit()

    log_action("dataset.openaq_fetch", entity="datasets", entity_id=dataset.id, user_id=user_id)
    return dataset.to_dict()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bulk_insert_readings(df: pd.DataFrame, dataset_id: int, batch_size: int = 500) -> None:
    """Insert cleaned DataFrame rows into aqi_readings table in batches."""
    records = []
    for _, row in df.iterrows():
        r = AQIReading(
            dataset_id=dataset_id,
            station_id=str(row.get("station_id", ""))[:100] if row.get("station_id") else None,
            city=str(row.get("city", "Unknown"))[:100],
            country=str(row.get("country", ""))[:100] if row.get("country") else None,
            latitude=float(row["latitude"]) if row.get("latitude") is not None and not (isinstance(row["latitude"], float) and np.isnan(row["latitude"])) else None,
            longitude=float(row["longitude"]) if row.get("longitude") is not None and not (isinstance(row["longitude"], float) and np.isnan(row["longitude"])) else None,
            recorded_at=row.get("recorded_at") or datetime.utcnow(),
            pm25=_safe_float(row.get("pm25")),
            pm10=_safe_float(row.get("pm10")),
            no2=_safe_float(row.get("no2")),
            so2=_safe_float(row.get("so2")),
            co=_safe_float(row.get("co")),
            o3=_safe_float(row.get("o3")),
            nh3=_safe_float(row.get("nh3")),
            temperature=_safe_float(row.get("temperature")),
            humidity=_safe_float(row.get("humidity")),
            wind_speed=_safe_float(row.get("wind_speed")),
            wind_direction=_safe_float(row.get("wind_direction")),
            pressure=_safe_float(row.get("pressure")),
            aqi=_safe_float(row.get("aqi")),
            aqi_category=str(row.get("aqi_category", ""))[:50] if row.get("aqi_category") else None,
            source="csv_upload",
        )
        records.append(r)

        if len(records) >= batch_size:
            db.session.bulk_save_objects(records)
            db.session.flush()
            records = []

    if records:
        db.session.bulk_save_objects(records)
        db.session.flush()


def _safe_float(val) -> Optional[float]:
    """Return float or None, handling NaN gracefully."""
    try:
        f = float(val)
        return None if np.isnan(f) else f
    except (TypeError, ValueError):
        return None


def get_dataset_list(user_id: int, include_public: bool = True) -> list:
    """Return list of datasets accessible to the user."""
    query = Dataset.query
    if include_public:
        query = query.filter(
            (Dataset.user_id == user_id) | (Dataset.is_public == True)
        )
    else:
        query = query.filter_by(user_id=user_id)
    return [d.to_dict() for d in query.order_by(Dataset.created_at.desc()).all()]


def delete_dataset(dataset_id: int, user_id: int) -> None:
    """Delete a dataset and all its readings (cascade)."""
    dataset = Dataset.query.get(dataset_id)
    if not dataset:
        raise ValueError("Dataset not found.")
    if dataset.user_id != user_id:
        raise PermissionError("You do not own this dataset.")

    db.session.delete(dataset)
    db.session.commit()
    log_action("dataset.delete", entity="datasets", entity_id=dataset_id, user_id=user_id)
