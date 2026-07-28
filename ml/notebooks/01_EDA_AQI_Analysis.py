"""
EDA — AI-Based AQI Prediction System
======================================
Full exploratory data analysis pipeline.

Run:  python ml/notebooks/01_EDA_AQI_Analysis.py
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

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT        = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_RAW    = os.path.join(ROOT, "data", "raw")
DATA_PROC   = os.path.join(ROOT, "data", "processed")
REPORTS_DIR = os.path.join(ROOT, "reports")
for d in [DATA_RAW, DATA_PROC, REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)

sns.set_theme(style="whitegrid", palette="husl", font_scale=1.1)
PALETTE = sns.color_palette("husl", 10)

POLLUTANTS   = ["pm25", "pm10", "no2", "so2", "co", "o3", "nh3"]
WEATHER_COLS = ["temperature", "humidity", "wind_speed", "wind_direction", "pressure"]
FEATURES     = POLLUTANTS + WEATHER_COLS

AQI_CATEGORIES = [
    (0,   50,  "Good",                          "#00e400"),
    (51,  100, "Moderate",                      "#ffff00"),
    (101, 150, "Unhealthy for Sensitive Groups", "#ff7e00"),
    (151, 200, "Unhealthy",                     "#ff0000"),
    (201, 300, "Very Unhealthy",                "#8f3f97"),
    (301, 500, "Hazardous",                     "#7e0023"),
]

COLUMN_ALIASES = {
    "pm2.5":"pm25","pm_2_5":"pm25","pm2_5":"pm25",
    "pm_10":"pm10","nitrogen_dioxide":"no2",
    "sulphur_dioxide":"so2","sulfur_dioxide":"so2",
    "carbon_monoxide":"co","ozone":"o3","ammonia":"nh3",
    "temp":"temperature","temp_c":"temperature",
    "rh":"humidity","relative_humidity":"humidity",
    "ws":"wind_speed","wd":"wind_direction",
    "pres":"pressure","atm_pressure":"pressure",
    "date":"recorded_at","datetime":"recorded_at","timestamp":"recorded_at",
    "station":"station_id","lat":"latitude",
    "lng":"longitude","lon":"longitude",
}


# ── Data loading ─────────────────────────────────────────────────────────────
def load_data(filepath=None):
    if filepath and os.path.exists(filepath):
        df = pd.read_csv(filepath, low_memory=False)
    else:
        csvs = [f for f in os.listdir(DATA_RAW) if f.endswith(".csv")]
        if csvs:
            df = pd.read_csv(os.path.join(DATA_RAW, csvs[0]), low_memory=False)
        else:
            print("No CSV found — generating synthetic demo data…")
            df = _synthetic_data()
    print(f"Loaded  {len(df):,} rows × {len(df.columns)} cols")
    return df


def _synthetic_data(n=6000):
    np.random.seed(42)
    cities = ["Delhi","Mumbai","Chennai","Kolkata","Bangalore","Hyderabad"]
    base   = {"Delhi":180,"Mumbai":100,"Chennai":80,
              "Kolkata":140,"Bangalore":70,"Hyderabad":90}
    dates  = pd.date_range("2019-01-01","2024-12-31",freq="6H")
    rows   = []
    for city in cities:
        b   = base[city]
        idx = np.random.choice(len(dates), n//len(cities), replace=False)
        for i in idx:
            dt  = dates[i]
            sf  = 1.4 if dt.month in [11,12,1,2] else (0.8 if dt.month in [6,7,8] else 1.0)
            pm  = max(0, np.random.normal(b*0.4*sf, 20))
            rows.append({
                "city":city,"recorded_at":dt,
                "pm25":round(pm,2),"pm10":round(pm*np.random.uniform(1.5,2.5),2),
                "no2":round(max(0,np.random.normal(40,15)),2),
                "so2":round(max(0,np.random.normal(20,8)),2),
                "co":round(max(0,np.random.normal(1.5,.5)),2),
                "o3":round(max(0,np.random.normal(50,20)),2),
                "nh3":round(max(0,np.random.normal(15,5)),2),
                "temperature":round(np.random.normal(28,8),1),
                "humidity":round(np.clip(np.random.normal(60,15),10,100),1),
                "wind_speed":round(max(0,np.random.normal(3,1.5)),1),
                "pressure":round(np.random.normal(1013,10),1),
                "aqi":round(max(0,np.random.normal(b*sf,30)),1),
            })
    df = pd.DataFrame(rows)
    df["aqi_category"] = df["aqi"].apply(
        lambda v: next((c for lo,hi,c,_ in AQI_CATEGORIES if lo<=v<=hi),"Hazardous")
    )
    df.to_csv(os.path.join(DATA_RAW,"synthetic_aqi_data.csv"),index=False)
    print(f"Saved synthetic data → {DATA_RAW}/synthetic_aqi_data.csv")
    return df


def inspect(df):
    print("\n" + "="*60)
    print("DATASET OVERVIEW")
    print("="*60)
    print(f"Shape  : {df.shape}")
    print(f"Memory : {df.memory_usage(deep=True).sum()/1024:.1f} KB")
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        print(f"\nMissing values:\n{(missing/len(df)*100).round(2)}")
    else:
        print("\nNo missing values ✓")
    print(f"\nNumeric summary:\n{df.describe().round(2)}")


# ── Save helper ───────────────────────────────────────────────────────────────
def _save(name):
    p = os.path.join(REPORTS_DIR, name)
    plt.savefig(p, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  → {p}")


# ── Plot 1: Feature distributions ────────────────────────────────────────────
def plot_distributions(df):
    available = [c for c in FEATURES if c in df.columns]
    n_cols, n_rows = 4, -(-len(available)//4)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, n_rows*4))
    axes = axes.flatten()
    for i, col in enumerate(available):
        d = df[col].dropna()
        axes[i].hist(d, bins=40, color=PALETTE[i%len(PALETTE)], edgecolor="white", alpha=0.85)
        axes[i].axvline(d.median(), color="red", lw=1.5, linestyle="--", label=f"Median={d.median():.1f}")
        axes[i].set_title(col); axes[i].set_xlabel(col); axes[i].legend(fontsize=8)
    for ax in axes[len(available):]: ax.set_visible(False)
    plt.suptitle("Feature Distributions", fontsize=16, fontweight="bold", y=1.01)
    plt.tight_layout(); _save("01_feature_distributions.png")


# ── Plot 2: AQI distribution ─────────────────────────────────────────────────
def plot_aqi_distribution(df):
    if "aqi" not in df.columns: return
    fig, axes = plt.subplots(1,2,figsize=(16,5))
    ax = axes[0]
    ax.hist(df["aqi"].dropna(), bins=50, color="#2d6a4f", edgecolor="white", alpha=0.85)
    for lo,hi,cat,color in AQI_CATEGORIES:
        ax.axvspan(lo,hi,alpha=0.12,color=color)
    ax.set_title("AQI Distribution with Category Bands"); ax.set_xlabel("AQI")

    if "aqi_category" in df.columns:
        cc = df["aqi_category"].value_counts()
        axes[1].pie(cc.values, labels=cc.index, autopct="%1.1f%%",
                    colors=[c for _,_,_,c in AQI_CATEGORIES][:len(cc)], startangle=90)
        axes[1].set_title("Category Distribution")
    plt.tight_layout(); _save("02_aqi_distribution.png")


# ── Plot 3: Correlation matrix ───────────────────────────────────────────────
def plot_correlation(df):
    cols = [c for c in FEATURES+["aqi"] if c in df.columns]
    corr = df[cols].corr()
    fig, ax = plt.subplots(figsize=(14,11))
    mask = np.triu(np.ones_like(corr,dtype=bool))
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f",
                cmap=sns.diverging_palette(230,20,as_cmap=True),
                vmin=-1, vmax=1, center=0, ax=ax,
                annot_kws={"size":8}, linewidths=0.5, square=True)
    ax.set_title("Feature Correlation Matrix", fontsize=14, fontweight="bold")
    plt.tight_layout(); _save("03_correlation_matrix.png")

    if "aqi" in corr.columns:
        aqi_c = corr["aqi"].drop("aqi").sort_values()
        fig2,ax2 = plt.subplots(figsize=(10,6))
        colors = ["#e74c3c" if v>0 else "#3498db" for v in aqi_c.values]
        ax2.barh(aqi_c.index, aqi_c.values, color=colors, edgecolor="white")
        ax2.axvline(0, color="black", lw=0.8)
        ax2.set_title("Feature Correlation with AQI", fontsize=13)
        plt.tight_layout(); _save("04_aqi_correlations.png")


# ── Plot 4: Temporal trends ──────────────────────────────────────────────────
def plot_trends(df):
    if "recorded_at" not in df.columns: return
    df = df.copy()
    df["recorded_at"] = pd.to_datetime(df["recorded_at"])
    daily   = df.groupby(df["recorded_at"].dt.date)["aqi"].mean().reset_index()
    monthly = df.groupby(df["recorded_at"].dt.to_period("M"))["aqi"].mean().reset_index()
    monthly["recorded_at"] = monthly["recorded_at"].astype(str)
    yearly  = df.groupby(df["recorded_at"].dt.year)["aqi"].mean().reset_index()

    fig, axes = plt.subplots(3,1,figsize=(18,14))
    axes[0].plot(pd.to_datetime(daily["recorded_at"]), daily["aqi"], color="#1e3a5f", lw=0.9, alpha=0.8)
    axes[0].fill_between(pd.to_datetime(daily["recorded_at"]), daily["aqi"], alpha=0.15, color="#1e3a5f")
    axes[0].set_title("Daily Average AQI Trend"); axes[0].set_ylabel("AQI")
    axes[0].xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    axes[0].xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(axes[0].xaxis.get_majorticklabels(), rotation=30)

    axes[1].bar(range(len(monthly)), monthly["aqi"], color="#2d6a4f", edgecolor="white", alpha=0.85)
    axes[1].set_xticks(range(len(monthly)))
    axes[1].set_xticklabels(monthly["recorded_at"], rotation=45, ha="right", fontsize=7)
    axes[1].set_title("Monthly Average AQI"); axes[1].set_ylabel("AQI")

    bars = axes[2].bar(yearly["recorded_at"].astype(str), yearly["aqi"], color="#e76f51", edgecolor="white")
    for bar,val in zip(bars, yearly["aqi"]):
        axes[2].text(bar.get_x()+bar.get_width()/2, bar.get_height()+1, f"{val:.0f}", ha="center", fontsize=10)
    axes[2].set_title("Yearly Average AQI"); axes[2].set_ylabel("AQI")

    plt.suptitle("AQI Temporal Trends", fontsize=16, fontweight="bold")
    plt.tight_layout(); _save("05_aqi_trends.png")


# ── Plot 5: Seasonal analysis ────────────────────────────────────────────────
def plot_seasonal(df):
    if "recorded_at" not in df.columns or "aqi" not in df.columns: return
    df = df.copy()
    df["recorded_at"] = pd.to_datetime(df["recorded_at"])
    df["month_name"]  = df["recorded_at"].dt.strftime("%b")
    df["season"]      = df["recorded_at"].dt.month.map(
        {12:"Winter",1:"Winter",2:"Winter",
         3:"Spring",4:"Spring",5:"Spring",
         6:"Summer",7:"Summer",8:"Summer",
         9:"Autumn",10:"Autumn",11:"Autumn"}
    )
    fig, axes = plt.subplots(1,2,figsize=(18,6))
    season_colors = {"Winter":"#74b9ff","Spring":"#55efc4","Summer":"#ffeaa7","Autumn":"#fdcb6e"}
    sns.boxplot(data=df, x="season", y="aqi", order=["Winter","Spring","Summer","Autumn"],
                palette=season_colors, ax=axes[0], width=0.5)
    axes[0].set_title("AQI by Season")

    month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    avail = [m for m in month_order if m in df["month_name"].values]
    sns.boxplot(data=df, x="month_name", y="aqi", order=avail, palette="husl", ax=axes[1])
    axes[1].set_title("AQI by Month")

    plt.suptitle("Seasonal Analysis", fontsize=16, fontweight="bold")
    plt.tight_layout(); _save("06_seasonal_analysis.png")


# ── Plot 6: City comparison ──────────────────────────────────────────────────
def plot_cities(df):
    if "city" not in df.columns or "aqi" not in df.columns: return
    stats = df.groupby("city")["aqi"].agg(["mean","std"]).round(1).reset_index()
    stats = stats.sort_values("mean", ascending=False)

    fig, axes = plt.subplots(1,2,figsize=(18,6))
    axes[0].bar(stats["city"], stats["mean"], yerr=stats["std"],
                color=PALETTE[:len(stats)], capsize=5, edgecolor="white", alpha=0.85)
    axes[0].set_title("Average AQI by City (± std dev)")
    axes[0].set_ylabel("Mean AQI")

    sns.violinplot(data=df, x="city", y="aqi", order=stats["city"].tolist(),
                   palette=PALETTE[:len(stats)], ax=axes[1], cut=0)
    axes[1].set_title("AQI Distribution by City")

    plt.suptitle("City-wise AQI Comparison", fontsize=16, fontweight="bold")
    plt.tight_layout(); _save("07_city_comparison.png")


# ── Plot 7: Pollutant heatmap ────────────────────────────────────────────────
def plot_pollutant_heatmap(df):
    avail = [c for c in POLLUTANTS if c in df.columns]
    if not avail or "city" not in df.columns: return
    pivot = df.groupby("city")[avail].mean()
    fig, ax = plt.subplots(figsize=(12,max(4, len(pivot)*0.8)))
    sns.heatmap(pivot, annot=True, fmt=".1f", cmap="YlOrRd",
                ax=ax, linewidths=0.5, linecolor="white", annot_kws={"size":9})
    ax.set_title("Pollutant Heatmap (City × Pollutant)", fontsize=14, fontweight="bold")
    plt.tight_layout(); _save("08_pollutant_heatmap.png")


# ── Plot 8: Feature importance (mutual info) ─────────────────────────────────
def plot_feature_importance(df):
    feat_cols = [c for c in FEATURES if c in df.columns]
    if "aqi" not in df.columns or len(feat_cols) < 2: return
    sub = df[feat_cols+["aqi"]].dropna()
    if len(sub) < 100: return
    mi = mutual_info_regression(sub[feat_cols], sub["aqi"], random_state=42)
    mi_df = pd.DataFrame({"feature":feat_cols,"score":mi}).sort_values("score")

    fig, ax = plt.subplots(figsize=(10,7))
    colors = [PALETTE[i%len(PALETTE)] for i in range(len(mi_df))]
    ax.barh(mi_df["feature"], mi_df["score"], color=colors, edgecolor="white")
    for i,(val,name) in enumerate(zip(mi_df["score"],mi_df["feature"])):
        ax.text(val+0.002, i, f"{val:.3f}", va="center", fontsize=9)
    ax.set_xlabel("Mutual Information Score")
    ax.set_title("Feature Importance w.r.t. AQI", fontsize=14, fontweight="bold")
    plt.tight_layout(); _save("09_feature_importance.png")


# ── Main ──────────────────────────────────────────────────────────────────────
def run(filepath=None):
    print("\n" + "="*60)
    print("  AI AQI Prediction — Full EDA Pipeline")
    print("="*60)
    df = load_data(filepath)
    # Normalise column names
    df.columns = [c.strip().lower().replace(" ","_").replace("-","_") for c in df.columns]
    df.rename(columns=COLUMN_ALIASES, inplace=True)
    inspect(df)

    steps = [
        ("Feature distributions",  plot_distributions),
        ("AQI distribution",        plot_aqi_distribution),
        ("Correlation matrix",      plot_correlation),
        ("Temporal trends",         plot_trends),
        ("Seasonal analysis",       plot_seasonal),
        ("City comparison",         plot_cities),
        ("Pollutant heatmap",       plot_pollutant_heatmap),
        ("Feature importance",      plot_feature_importance),
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
