"""
Import AIR_QUALITY_WITH _AQI.xlsx → aqi_readings table.
Run once:  python import_dataset.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from datetime import datetime
from app import create_app, db
from app.models.aqi_reading import AQIReading
from app.models.dataset import Dataset
from app.models.user import User

XLSX = os.path.join(os.path.dirname(__file__), "..", "dataset", "AIR_QUALITY_WITH _AQI.xlsx")

app = create_app("development")

with app.app_context():
    # Check already imported
    existing = AQIReading.query.count()
    if existing > 0:
        print(f"Already have {existing:,} readings — skipping import.")
        sys.exit(0)

    print("Loading Excel file...")
    df = pd.read_excel(XLSX)
    print(f"  Loaded {len(df):,} rows")

    # Combine Date + Time → recorded_at
    df["recorded_at"] = pd.to_datetime(
        df["Date"].astype(str) + " " + df["Time"].astype(str),
        errors="coerce"
    )

    # Rename columns
    df.rename(columns={
        "Temperature": "temperature",
        "Wind":        "wind_speed",
        "Rain":        "rain",
        "AQI":         "aqi",
        "AQI_category":    "aqi_category",
        "Dominant_Pollutant": "dominant_pollutant",
        "Humidity":    "humidity",
    }, inplace=True)

    # Create a dataset record
    admin = User.query.filter_by(username="admin").first()
    ds = Dataset(
        user_id=admin.id if admin else 1,
        name="AIR_QUALITY_WITH_AQI (2015-2024)",
        source="csv_upload",
        original_filename="AIR_QUALITY_WITH _AQI.xlsx",
        row_count=len(df),
        column_count=len(df.columns),
        status="ready",
        is_public=True,
        location="India",
        date_from=df["recorded_at"].min().date() if df["recorded_at"].notna().any() else None,
        date_to=df["recorded_at"].max().date() if df["recorded_at"].notna().any() else None,
    )
    db.session.add(ds)
    db.session.flush()  # get ds.id

    # Batch insert
    BATCH = 2000
    total = len(df)
    inserted = 0

    for start in range(0, total, BATCH):
        chunk = df.iloc[start:start + BATCH]
        records = []
        for _, row in chunk.iterrows():
            records.append(AQIReading(
                dataset_id=ds.id,
                city="Unknown",          # dataset has no city column
                recorded_at=row["recorded_at"] if pd.notna(row.get("recorded_at")) else datetime.utcnow(),
                pm25=row.get("pm25") if pd.notna(row.get("pm25")) else None,
                pm10=row.get("pm10") if pd.notna(row.get("pm10")) else None,
                no2=row.get("no2")   if pd.notna(row.get("no2"))  else None,
                so2=row.get("so2")   if pd.notna(row.get("so2"))  else None,
                co=row.get("co")     if pd.notna(row.get("co"))   else None,
                o3=row.get("o3")     if pd.notna(row.get("o3"))   else None,
                temperature=row.get("temperature") if pd.notna(row.get("temperature")) else None,
                humidity=row.get("humidity")       if pd.notna(row.get("humidity"))    else None,
                wind_speed=row.get("wind_speed")   if pd.notna(row.get("wind_speed")) else None,
                aqi=row.get("aqi")                 if pd.notna(row.get("aqi"))         else None,
                aqi_category=str(row.get("aqi_category", "")) or None,
                source="historical",
            ))
        db.session.bulk_save_objects(records)
        db.session.commit()
        inserted += len(records)
        print(f"  Inserted {inserted:,} / {total:,}", end="\r")

    print(f"\nDone! {inserted:,} readings imported ✓")
    print(f"Dataset ID: {ds.id}")
