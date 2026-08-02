"""
EDA — AI-Based AQI Prediction System
======================================
Full exploratory data analysis pipeline.
Supports both the real XLSX dataset (AIR_QUALITY_WITH _AQI.xlsx)
and generic CSV datasets.

Real dataset columns:
  Date, Time, pm25, pm10, no2, co, so2, o3,
  Temperature, Humidity, Wind, Rain, AQI, AQI_category, Dominant_Pollutant

Run:
  python ml/notebooks/01_EDA_AQI_Analysis.py
  python ml/notebooks/01_EDA_AQI_Analysis.py path/to/data.xlsx
  python ml/notebooks/01_EDA_AQI_Analysis.py path/to/data.csv

Outputs all plots to  ml/reports/
Saves cleaned data to ml/data/processed/eda_cleaned.csv
"""

import os, sys, warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from sklearn.feature_selection import mutual_info_regression

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT        = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJ_ROOT   = os.path.abspath(os.path.join(ROOT, ".."))
DATA_RAW    = os.path.join(ROOT, "data", "raw")
DATA_PROC   = os.path.join(ROOT, "data", "processed")
REPORTS_DIR = os.path.join(ROOT, "reports")
for d in [DATA_RAW, DATA_PROC, REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)

# Default location of the real dataset
REAL_DATASET = os.path.join(PROJ_ROOT, "dataset", "AIR_QUALITY_WITH _AQI.xlsx")

sns.set_theme(style="whitegrid", palette="husl", font_scale=1.1)
PALETTE = sns.color_palette("husl", 10)

POLLUTANTS   = ["pm25", "pm10", "no2", "so2", "co", "o3", "nh3"]
WEATHER_COLS = ["temperature", "humidity", "wind_speed", "rain", "pressure"]
FEATURES     = POLLUTANTS + WEATHER_COLS

# AQI category bands for the real dataset (Indian AQI scale)
AQI_CATEGORIES = [
    (0,   50,  "Good",          "#00e400"),
    (51,  100, "Satisfactory",  "#a8e05f"),
    (101, 200, "Moderate",      "#ffff00"),
    (201, 300, "Poor",          "#ff7e00"),
    (301, 400, "Very Poor",     "#ff0000"),
    (401, 500, "Severe",        "#7e0023"),
]

# Column name aliases — maps raw names to canonical internal names
COLUMN_ALIASES = {
    # Real dataset columns
    "temperature":          "temperature",
    "Temperature":          "temperature",
    "wind":                 "wind_speed",
    "Wind":                 "wind_speed",
    "rain":                 "rain",
    "Rain":                 "rain",
    "aqi":                  "aqi",
    "AQI":                  "aqi",
    "aqi_category":         "aqi_category",
    "AQI_category":         "aqi_category",
    "dominant_pollutant":   "dominant_pollutant",
    "Dominant_Pollutant":   "dominant_pollutant",
    # Generic CSV variants
    "pm2.5": "pm25", "pm_2_5": "pm25", "pm2_5": "pm25",
    "pm_10": "pm10",
    "nitrogen_dioxide": "no2",
    "sulphur_dioxide": "so2", "sulfur_dioxide": "so2",
    "carbon_monoxide": "co",
    "ozone": "o3",
    "ammonia": "nh3",
    "temp": "temperature", "temp_c": "temperature",
    "rh": "humidity", "relative_humidity": "humidity",
    "Humidity": "humidity",
    "ws": "wind_speed", "wind_speed": "wind_speed",
    "wd": "wind_direction",
    "pres": "pressure", "atm_pressure": "pressure",
    "date": "recorded_at", "datetime": "recorded_at",
    "timestamp": "recorded_at",
    "station": "station_id",
    "lat": "latitude", "lng": "longitude", "lon": "longitude",
}


# ── Data loading ──────────────────────────────────────────────────────────────
def load_data(filepath=None):
    """Load data from XLSX/CSV.  Falls back to real dataset, then raw CSVs,
    then generates synthetic demo data."""
    path = None

    if filepath and os.path.exists(filepath):
        path = filepath
    elif os.path.exists(REAL_DATASET):
        path = REAL_DATASET
        print(f"Using real dataset: {path}")
    else:
        csvs = [f for f in os.listdir(DATA_RAW) if f.endswith(".csv")]
        if csvs:
            path = os.path.join(DATA_RAW, csvs[0])

    if path is None:
        print("No dataset found — generating synthetic demo data…")
        return _synthetic_data()

    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path, low_memory=False)

    print(f"Loaded  {len(df):,} rows × {len(df.columns)} cols  from  {os.path.basename(path)}")
    return df


def _build_recorded_at(df: pd.DataFrame) -> pd.DataFrame:
    """Combine Date + Time columns into a single recorded_at datetime."""
    if "Date" in df.columns and "Time" in df.columns:
        df["recorded_at"] = pd.to_datetime(
            df["Date"].astype(str) + " " + df["Time"].astype(str),
            errors="coerce",
        )
        df.drop(columns=["Date", "Time"], inplace=True, errors="ignore")
    elif "recorded_at" not in df.columns:
        # Try generic date/datetime column
        for col in ["date", "datetime", "timestamp"]:
            if col in df.columns:
                df["recorded_at"] = pd.to_datetime(df[col], errors="coerce")
                break
    return df


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase + underscore, then apply aliases, combine Date/Time."""
    # First combine Date+Time before lowercasing destroys the capital-letter detection
    df = _build_recorded_at(df)
    # Now normalise remaining column names
    df.columns = [c.strip().replace(" ", "_").replace("-", "_") for c in df.columns]
    df.rename(columns=COLUMN_ALIASES, inplace=True)
    return df


def _add_city_if_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Real dataset has no city column — add a placeholder."""
    if "city" not in df.columns:
        df["city"] = "Unknown"
    return df


def _synthetic_data(n=6000):
    np.random.seed(42)
    cities = ["Delhi", "Mumbai", "Chennai", "Kolkata", "Bangalore", "Hyderabad"]
    base   = {"Delhi": 180, "Mumbai": 100, "Chennai": 80,
               "Kolkata": 140, "Bangalore": 70, "Hyderabad": 90}
    dates  = pd.date_range("2019-01-01", "2024-12-31", freq="6h")
    rows   = []
    for city in cities:
        b   = base[city]
        idx = np.random.choice(len(dates), n // len(cities), replace=False)
        for i in idx:
            dt = dates[i]
            sf = 1.4 if dt.month in [11, 12, 1, 2] else (0.8 if dt.month in [6, 7, 8] else 1.0)
            pm = max(0, np.random.normal(b * 0.4 * sf, 20))
            rows.append({
                "city": city, "recorded_at": dt,
                "pm25": round(pm, 2),
                "pm10": round(pm * np.random.uniform(1.5, 2.5), 2),
                "no2":  round(max(0, np.random.normal(40, 15)), 2),
                "so2":  round(max(0, np.random.normal(20, 8)), 2),
                "co":   round(max(0, np.random.normal(1.5, .5)), 2),
                "o3":   round(max(0, np.random.normal(50, 20)), 2),
                "temperature": round(np.random.normal(28, 8), 1),
                "humidity":    round(np.clip(np.random.normal(60, 15), 10, 100), 1),
                "wind_speed":  round(max(0, np.random.normal(3, 1.5)), 1),
                "aqi": round(max(0, np.random.normal(b * sf, 30)), 1),
            })
    df = pd.DataFrame(rows)
    df["aqi_category"] = df["aqi"].apply(
        lambda v: next((c for lo, hi, c, _ in AQI_CATEGORIES if lo <= v <= hi), "Severe")
    )
    out = os.path.join(DATA_RAW, "synthetic_aqi_data.csv")
    df.to_csv(out, index=False)
    print(f"Saved synthetic data → {out}")
    return df


def inspect(df):
    print("\n" + "=" * 60)
    print("DATASET OVERVIEW")
    print("=" * 60)
    print(f"Shape  : {df.shape}")
    print(f"Memory : {df.memory_usage(deep=True).sum() / 1024:.1f} KB")
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        print(f"\nMissing values:\n{(missing / len(df) * 100).round(2)}")
    else:
        print("\nNo missing values ✓")
    print(f"\nNumeric summary:\n{df.describe().round(2)}")
    if "aqi_category" in df.columns:
        print(f"\nAQI Category counts:\n{df['aqi_category'].value_counts()}")


# ── Save helper ───────────────────────────────────────────────────────────────
def _save(name):
    p = os.path.join(REPORTS_DIR, name)
    plt.savefig(p, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  → {p}")


# ── Plot 1: Feature distributions ────────────────────────────────────────────
def plot_distributions(df):
    available = [c for c in FEATURES if c in df.columns]
    if not available:
        print("  No feature columns found — skipping.")
        return
    n_cols  = 4
    n_rows  = -(-len(available) // n_cols)      # ceiling division
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, n_rows * 4))
    axes = axes.flatten()
    for i, col in enumerate(available):
        d = df[col].dropna()
        axes[i].hist(d, bins=40, color=PALETTE[i % len(PALETTE)], edgecolor="white", alpha=0.85)
        axes[i].axvline(d.median(), color="red", lw=1.5, linestyle="--",
                        label=f"Median={d.median():.1f}")
        axes[i].set_title(col)
        axes[i].set_xlabel(col)
        axes[i].legend(fontsize=8)
    for ax in axes[len(available):]:
        ax.set_visible(False)
    plt.suptitle("Feature Distributions", fontsize=16, fontweight="bold", y=1.01)
    plt.tight_layout()
    _save("01_feature_distributions.png")


# ── Plot 2: AQI distribution ──────────────────────────────────────────────────
def plot_aqi_distribution(df):
    if "aqi" not in df.columns:
        return
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))
    ax = axes[0]
    ax.hist(df["aqi"].dropna(), bins=50, color="#2d6a4f", edgecolor="white", alpha=0.85)
    for lo, hi, cat, color in AQI_CATEGORIES:
        ax.axvspan(lo, hi, alpha=0.12, color=color)
    ax.set_title("AQI Distribution with Category Bands")
    ax.set_xlabel("AQI")

    if "aqi_category" in df.columns:
        cc = df["aqi_category"].value_counts()
        cat_colors = {c: col for _, _, c, col in AQI_CATEGORIES}
        colors = [cat_colors.get(c, "#cccccc") for c in cc.index]
        axes[1].pie(cc.values, labels=cc.index, autopct="%1.1f%%",
                    colors=colors, startangle=90)
        axes[1].set_title("AQI Category Distribution")
    plt.tight_layout()
    _save("02_aqi_distribution.png")


# ── Plot 3: Correlation matrix ────────────────────────────────────────────────
def plot_correlation(df):
    feat_cols = [c for c in FEATURES + ["aqi", "rain"] if c in df.columns]
    if len(feat_cols) < 2:
        return
    corr = df[feat_cols].corr()
    fig, ax = plt.subplots(figsize=(14, 11))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f",
                cmap=sns.diverging_palette(230, 20, as_cmap=True),
                vmin=-1, vmax=1, center=0, ax=ax,
                annot_kws={"size": 8}, linewidths=0.5, square=True)
    ax.set_title("Feature Correlation Matrix", fontsize=14, fontweight="bold")
    plt.tight_layout()
    _save("03_correlation_matrix.png")

    if "aqi" in corr.columns:
        aqi_c = corr["aqi"].drop("aqi").sort_values()
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        colors = ["#e74c3c" if v > 0 else "#3498db" for v in aqi_c.values]
        ax2.barh(aqi_c.index, aqi_c.values, color=colors, edgecolor="white")
        ax2.axvline(0, color="black", lw=0.8)
        ax2.set_title("Feature Correlation with AQI", fontsize=13)
        plt.tight_layout()
        _save("04_aqi_correlations.png")


# ── Plot 4: Temporal trends ───────────────────────────────────────────────────
def plot_trends(df):
    if "recorded_at" not in df.columns or "aqi" not in df.columns:
        return
    df = df.copy()
    df["recorded_at"] = pd.to_datetime(df["recorded_at"])
    daily   = df.groupby(df["recorded_at"].dt.date)["aqi"].mean().reset_index()
    monthly = df.groupby(df["recorded_at"].dt.to_period("M"))["aqi"].mean().reset_index()
    monthly["recorded_at"] = monthly["recorded_at"].astype(str)
    yearly  = df.groupby(df["recorded_at"].dt.year)["aqi"].mean().reset_index()

    fig, axes = plt.subplots(3, 1, figsize=(18, 14))

    axes[0].plot(pd.to_datetime(daily["recorded_at"]), daily["aqi"],
                 color="#1e3a5f", lw=0.9, alpha=0.8)
    axes[0].fill_between(pd.to_datetime(daily["recorded_at"]),
                         daily["aqi"], alpha=0.15, color="#1e3a5f")
    axes[0].set_title("Daily Average AQI Trend")
    axes[0].set_ylabel("AQI")
    axes[0].xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    axes[0].xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.setp(axes[0].xaxis.get_majorticklabels(), rotation=30)

    axes[1].bar(range(len(monthly)), monthly["aqi"],
                color="#2d6a4f", edgecolor="white", alpha=0.85)
    step = max(1, len(monthly) // 20)
    axes[1].set_xticks(range(0, len(monthly), step))
    axes[1].set_xticklabels(monthly["recorded_at"].iloc[::step],
                             rotation=45, ha="right", fontsize=7)
    axes[1].set_title("Monthly Average AQI")
    axes[1].set_ylabel("AQI")

    bars = axes[2].bar(yearly["recorded_at"].astype(str), yearly["aqi"],
                       color="#e76f51", edgecolor="white")
    for bar, val in zip(bars, yearly["aqi"]):
        axes[2].text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + 1, f"{val:.0f}",
                     ha="center", fontsize=10)
    axes[2].set_title("Yearly Average AQI")
    axes[2].set_ylabel("AQI")

    plt.suptitle("AQI Temporal Trends", fontsize=16, fontweight="bold")
    plt.tight_layout()
    _save("05_aqi_trends.png")


# ── Plot 5: Seasonal & hourly analysis ───────────────────────────────────────
def plot_seasonal(df):
    if "recorded_at" not in df.columns or "aqi" not in df.columns:
        return
    df = df.copy()
    df["recorded_at"] = pd.to_datetime(df["recorded_at"])
    df["month_name"] = df["recorded_at"].dt.strftime("%b")
    df["season"] = df["recorded_at"].dt.month.map(
        {12: "Winter", 1: "Winter",  2: "Winter",
          3: "Spring",  4: "Spring",  5: "Spring",
          6: "Summer",  7: "Summer",  8: "Summer",
          9: "Autumn", 10: "Autumn", 11: "Autumn"}
    )
    df["hour"] = df["recorded_at"].dt.hour

    fig, axes = plt.subplots(1, 3, figsize=(22, 6))
    season_colors = {"Winter": "#74b9ff", "Spring": "#55efc4",
                     "Summer": "#ffeaa7", "Autumn": "#fdcb6e"}
    sns.boxplot(data=df, x="season", y="aqi",
                order=["Winter", "Spring", "Summer", "Autumn"],
                palette=season_colors, ax=axes[0], width=0.5)
    axes[0].set_title("AQI by Season")

    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    avail = [m for m in month_order if m in df["month_name"].values]
    sns.boxplot(data=df, x="month_name", y="aqi", order=avail,
                palette="husl", ax=axes[1])
    axes[1].set_title("AQI by Month")
    axes[1].tick_params(axis="x", rotation=45)

    hourly = df.groupby("hour")["aqi"].mean().reset_index()
    axes[2].plot(hourly["hour"], hourly["aqi"], marker="o",
                 color="#6c5ce7", lw=2)
    axes[2].fill_between(hourly["hour"], hourly["aqi"], alpha=0.2, color="#6c5ce7")
    axes[2].set_title("Average AQI by Hour of Day")
    axes[2].set_xlabel("Hour")
    axes[2].set_ylabel("AQI")
    axes[2].set_xticks(range(0, 24, 2))

    plt.suptitle("Seasonal & Hourly Analysis", fontsize=16, fontweight="bold")
    plt.tight_layout()
    _save("06_seasonal_analysis.png")


# ── Plot 6: Pollutant trends over years ───────────────────────────────────────
def plot_pollutant_trends(df):
    """Yearly average of each pollutant — useful when no city column exists."""
    if "recorded_at" not in df.columns:
        return
    df = df.copy()
    df["recorded_at"] = pd.to_datetime(df["recorded_at"])
    df["year"] = df["recorded_at"].dt.year
    available = [c for c in ["pm25", "pm10", "no2", "so2", "co", "o3"] if c in df.columns]
    if not available:
        return
    yearly = df.groupby("year")[available].mean()

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()
    for i, col in enumerate(available):
        axes[i].plot(yearly.index, yearly[col], marker="o",
                     color=PALETTE[i], lw=2)
        axes[i].fill_between(yearly.index, yearly[col], alpha=0.15, color=PALETTE[i])
        axes[i].set_title(f"{col.upper()} — Yearly Average")
        axes[i].set_xlabel("Year")
        axes[i].set_ylabel("Concentration")
    for ax in axes[len(available):]:
        ax.set_visible(False)
    plt.suptitle("Pollutant Concentration Trends by Year",
                 fontsize=16, fontweight="bold")
    plt.tight_layout()
    _save("07_pollutant_yearly_trends.png")


# ── Plot 7: Dominant pollutant ────────────────────────────────────────────────
def plot_dominant_pollutant(df):
    if "dominant_pollutant" not in df.columns:
        return
    counts = df["dominant_pollutant"].value_counts()
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    axes[0].bar(counts.index, counts.values,
                color=PALETTE[:len(counts)], edgecolor="white", alpha=0.85)
    axes[0].set_title("Dominant Pollutant Frequency")
    axes[0].set_xlabel("Pollutant")
    axes[0].set_ylabel("Count")
    for bar, val in zip(axes[0].patches, counts.values):
        axes[0].text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + 100, f"{val:,}",
                     ha="center", fontsize=9)

    axes[1].pie(counts.values, labels=counts.index, autopct="%1.1f%%",
                colors=PALETTE[:len(counts)], startangle=90)
    axes[1].set_title("Dominant Pollutant Share")

    plt.suptitle("Dominant Pollutant Analysis", fontsize=16, fontweight="bold")
    plt.tight_layout()
    _save("08_dominant_pollutant.png")


# ── Plot 8: Feature importance (mutual info) ──────────────────────────────────
def plot_feature_importance(df):
    # Build unique feature list (avoid duplicates from FEATURES + extra cols)
    seen = set()
    feat_cols = []
    for c in FEATURES + ["rain"]:
        if c in df.columns and c not in seen:
            seen.add(c)
            feat_cols.append(c)
    if "aqi" not in df.columns or len(feat_cols) < 2:
        return
    sub = df[feat_cols + ["aqi"]].dropna()
    if len(sub) < 100:
        return
    mi = mutual_info_regression(sub[feat_cols], sub["aqi"], random_state=42)
    mi_df = pd.DataFrame({"feature": feat_cols, "score": mi}).sort_values("score")

    fig, ax = plt.subplots(figsize=(10, 7))
    colors = [PALETTE[i % len(PALETTE)] for i in range(len(mi_df))]
    ax.barh(mi_df["feature"], mi_df["score"], color=colors, edgecolor="white")
    for i, (val, name) in enumerate(zip(mi_df["score"], mi_df["feature"])):
        ax.text(val + 0.002, i, f"{val:.3f}", va="center", fontsize=9)
    ax.set_xlabel("Mutual Information Score")
    ax.set_title("Feature Importance w.r.t. AQI", fontsize=14, fontweight="bold")
    plt.tight_layout()
    _save("09_feature_importance.png")


# ── Plot 9: Pollutant vs AQI scatter grid ─────────────────────────────────────
def plot_pollutant_vs_aqi(df):
    pollutants = [c for c in ["pm25", "pm10", "no2", "so2", "co", "o3"] if c in df.columns]
    if "aqi" not in df.columns or not pollutants:
        return
    n_cols = 3
    n_rows = -(-len(pollutants) // n_cols)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, n_rows * 5))
    axes = axes.flatten()
    sample = df.sample(min(5000, len(df)), random_state=42)
    for i, col in enumerate(pollutants):
        axes[i].scatter(sample[col], sample["aqi"],
                        alpha=0.15, s=5, color=PALETTE[i])
        # Trend line
        valid = sample[[col, "aqi"]].dropna()
        if len(valid) > 10:
            z = np.polyfit(valid[col], valid["aqi"], 1)
            p = np.poly1d(z)
            x_line = np.linspace(valid[col].min(), valid[col].max(), 100)
            axes[i].plot(x_line, p(x_line), color="red", lw=1.5)
        axes[i].set_xlabel(col)
        axes[i].set_ylabel("AQI")
        axes[i].set_title(f"{col.upper()} vs AQI")
    for ax in axes[len(pollutants):]:
        ax.set_visible(False)
    plt.suptitle("Pollutant vs AQI Scatter Plots", fontsize=16, fontweight="bold")
    plt.tight_layout()
    _save("10_pollutant_vs_aqi.png")


# ── Main ──────────────────────────────────────────────────────────────────────
def run(filepath=None):
    print("\n" + "=" * 60)
    print("  AI AQI Prediction — Full EDA Pipeline")
    print("=" * 60)

    df = load_data(filepath)

    # Normalise columns & combine Date+Time → recorded_at
    df = _normalise_columns(df)
    df = _add_city_if_missing(df)

    inspect(df)

    steps = [
        ("Feature distributions",       plot_distributions),
        ("AQI distribution",             plot_aqi_distribution),
        ("Correlation matrix",           plot_correlation),
        ("Temporal trends",              plot_trends),
        ("Seasonal & hourly analysis",   plot_seasonal),
        ("Pollutant yearly trends",      plot_pollutant_trends),
        ("Dominant pollutant",           plot_dominant_pollutant),
        ("Feature importance",           plot_feature_importance),
        ("Pollutant vs AQI scatter",     plot_pollutant_vs_aqi),
    ]
    for label, fn in steps:
        print(f"\n[EDA] {label}…")
        try:
            fn(df)
        except Exception as e:
            print(f"  ⚠  Skipped ({e})")

    out = os.path.join(DATA_PROC, "eda_cleaned.csv")
    df.to_csv(out, index=False)
    print(f"\nCleaned data → {out}")
    print(f"All plots    → {REPORTS_DIR}")
    print("\nEDA complete ✓")
    return df


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else None)
