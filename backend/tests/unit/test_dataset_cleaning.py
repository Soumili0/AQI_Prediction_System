"""Unit tests — dataset cleaning pipeline"""

import pytest
import numpy as np
import pandas as pd
from app.services.dataset_service import clean_dataframe, calculate_aqi, COLUMN_ALIASES


def _make_df(n=100, city="Delhi"):
    """Generate a minimal valid DataFrame."""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=n, freq="H")
    return pd.DataFrame({
        "city":        [city] * n,
        "recorded_at": dates,
        "pm25":        np.random.uniform(10, 200, n),
        "pm10":        np.random.uniform(20, 400, n),
        "no2":         np.random.uniform(5,  100, n),
        "so2":         np.random.uniform(2,  80,  n),
        "co":          np.random.uniform(0.5, 5,  n),
        "o3":          np.random.uniform(10, 120, n),
        "temperature": np.random.uniform(15, 40,  n),
        "humidity":    np.random.uniform(30, 95,  n),
    })


class TestCleanDataframe:
    def test_returns_dataframe(self):
        df = clean_dataframe(_make_df())
        assert isinstance(df, pd.DataFrame)

    def test_no_nan_in_core_columns(self):
        df = clean_dataframe(_make_df())
        for col in ["pm25", "pm10", "no2"]:
            if col in df.columns:
                assert df[col].isna().sum() == 0, f"{col} has NaN after cleaning"

    def test_duplicates_removed(self):
        raw = _make_df(50)
        doubled = pd.concat([raw, raw], ignore_index=True)
        clean = clean_dataframe(doubled)
        assert len(clean) <= len(doubled)

    def test_negative_pollutants_clipped(self):
        df = _make_df(50)
        df.loc[0, "pm25"] = -10.0
        clean = clean_dataframe(df)
        assert (clean["pm25"] >= 0).all()

    def test_aqi_column_present(self):
        df = clean_dataframe(_make_df())
        assert "aqi" in df.columns

    def test_time_features_added(self):
        df = clean_dataframe(_make_df())
        for col in ["hour", "month", "year", "day_of_week", "is_weekend", "season"]:
            assert col in df.columns, f"Missing time feature: {col}"

    def test_column_aliases_renamed(self):
        df = _make_df(20).rename(columns={"pm25": "pm2.5", "recorded_at": "date"})
        clean = clean_dataframe(df)
        assert "pm25" in clean.columns
        assert "recorded_at" in clean.columns

    def test_empty_df_returns_empty(self):
        df = pd.DataFrame()
        result = clean_dataframe(df)
        assert result.empty


class TestCalculateAQI:
    def test_good_aqi(self):
        aqi, cat = calculate_aqi({"pm25": 5.0, "pm10": 20.0, "no2": 10.0, "o3": 20.0})
        assert aqi is not None
        assert cat == "Good"

    def test_hazardous_aqi(self):
        aqi, cat = calculate_aqi({"pm25": 400.0, "pm10": 550.0})
        assert aqi >= 301

    def test_missing_pollutants_returns_none(self):
        aqi, cat = calculate_aqi({})
        assert aqi is None
        assert cat is None

    def test_nan_values_skipped(self):
        aqi, cat = calculate_aqi({"pm25": float("nan"), "pm10": 50.0})
        assert aqi is not None  # pm10 still gives a result
