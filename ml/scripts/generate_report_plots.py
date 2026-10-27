"""
Generate additional comparison plots for the ML report.
Produces: RMSE comparison, R² comparison, training time comparison,
and a combined dashboard image.
"""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODELS_DIR = os.path.join(ROOT, "models")
REPORTS_DIR = os.path.join(ROOT, "reports")

# Load comparison data
df = pd.read_csv(os.path.join(MODELS_DIR, "model_comparison.csv"))

# Colors per model
COLORS = {
    "Linear Regression": "#3498db",
    "Decision Tree":     "#e67e22",
    "Random Forest":     "#27ae60",
    "XGBoost":           "#e74c3c",
    "LightGBM":          "#9b59b6",
    "LSTM":              "#1abc9c",
}
colors = [COLORS.get(m, "#95a5a6") for m in df["model"]]

# ── Plot 1: RMSE Comparison ────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))
sorted_df = df.sort_values("rmse")
sc = [COLORS.get(m, "#95a5a6") for m in sorted_df["model"]]
bars = ax.barh(sorted_df["model"], sorted_df["rmse"], color=sc, alpha=0.85, edgecolor="white")
ax.set_xlabel("RMSE (Root Mean Squared Error)", fontsize=11)
ax.set_title("Model Comparison — RMSE (lower is better)", fontsize=13, fontweight="bold")
for bar, val in zip(bars, sorted_df["rmse"]):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
            f"{val:.4f}", va="center", fontsize=10)
ax.invert_yaxis()
plt.tight_layout()
plt.savefig(os.path.join(REPORTS_DIR, "11_rmse_comparison.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved: 11_rmse_comparison.png")

# ── Plot 2: R² Comparison ──────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))
sorted_df = df.sort_values("r2", ascending=False)
sc = [COLORS.get(m, "#95a5a6") for m in sorted_df["model"]]
bars = ax.barh(sorted_df["model"], sorted_df["r2"], color=sc, alpha=0.85, edgecolor="white")
ax.set_xlabel("R² Score (higher is better)", fontsize=11)
ax.set_title("Model Comparison — R² Score (higher is better)", fontsize=13, fontweight="bold")
for bar, val in zip(bars, sorted_df["r2"]):
    ax.text(bar.get_width() + 0.001, bar.get_y() + bar.get_height()/2,
            f"{val:.4f}", va="center", fontsize=10)
ax.invert_yaxis()
plt.tight_layout()
plt.savefig(os.path.join(REPORTS_DIR, "12_r2_comparison.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved: 12_r2_comparison.png")

# ── Plot 3: Training Time Comparison ──────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))
sorted_df = df.sort_values("train_time_s", ascending=False)
sc = [COLORS.get(m, "#95a5a6") for m in sorted_df["model"]]
bars = ax.barh(sorted_df["model"], sorted_df["train_time_s"], color=sc, alpha=0.85, edgecolor="white")
ax.set_xlabel("Training Time (seconds)", fontsize=11)
ax.set_title("Model Comparison — Training Time (lower is faster)", fontsize=13, fontweight="bold")
for bar, val in zip(bars, sorted_df["train_time_s"]):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
            f"{val:.2f}s", va="center", fontsize=10)
ax.invert_yaxis()
plt.tight_layout()
plt.savefig(os.path.join(REPORTS_DIR, "13_training_time_comparison.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved: 13_training_time_comparison.png")

# ── Plot 4: Combined Dashboard (2x2) ──────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle("ML Model Performance Dashboard", fontsize=16, fontweight="bold", y=0.98)

# MAE
ax = axes[0, 0]
sd = df.sort_values("mae")
sc = [COLORS.get(m, "#95a5a6") for m in sd["model"]]
ax.barh(sd["model"], sd["mae"], color=sc, alpha=0.85, edgecolor="white")
ax.set_title("MAE (lower is better)", fontweight="bold")
ax.invert_yaxis()
for i, (m, v) in enumerate(zip(sd["model"], sd["mae"])):
    ax.text(v + 0.3, i, f"{v:.4f}", va="center", fontsize=9)

# RMSE
ax = axes[0, 1]
sd = df.sort_values("rmse")
sc = [COLORS.get(m, "#95a5a6") for m in sd["model"]]
ax.barh(sd["model"], sd["rmse"], color=sc, alpha=0.85, edgecolor="white")
ax.set_title("RMSE (lower is better)", fontweight="bold")
ax.invert_yaxis()
for i, (m, v) in enumerate(zip(sd["model"], sd["rmse"])):
    ax.text(v + 0.3, i, f"{v:.4f}", va="center", fontsize=9)

# R²
ax = axes[1, 0]
sd = df.sort_values("r2", ascending=False)
sc = [COLORS.get(m, "#95a5a6") for m in sd["model"]]
ax.barh(sd["model"], sd["r2"], color=sc, alpha=0.85, edgecolor="white")
ax.set_title("R² Score (higher is better)", fontweight="bold")
ax.invert_yaxis()
for i, (m, v) in enumerate(zip(sd["model"], sd["r2"])):
    ax.text(v + 0.001, i, f"{v:.4f}", va="center", fontsize=9)

# Training Time
ax = axes[1, 1]
sd = df.sort_values("train_time_s", ascending=False)
sc = [COLORS.get(m, "#95a5a6") for m in sd["model"]]
ax.barh(sd["model"], sd["train_time_s"], color=sc, alpha=0.85, edgecolor="white")
ax.set_title("Training Time (lower is faster)", fontweight="bold")
ax.invert_yaxis()
for i, (m, v) in enumerate(zip(sd["model"], sd["train_time_s"])):
    ax.text(v + 0.3, i, f"{v:.2f}s", va="center", fontsize=9)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig(os.path.join(REPORTS_DIR, "14_performance_dashboard.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved: 14_performance_dashboard.png")

# ── Plot 5: Best Model Highlight ──────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 7))
models = df["model"].values
rmse_vals = df["rmse"].values
r2_vals = df["r2"].values

x = np.arange(len(models))
width = 0.35

# Normalize RMSE to 0-1 for visual comparison (invert so lower is better)
rmse_norm = 1 - (rmse_vals / rmse_vals.max())

bars1 = ax.bar(x - width/2, rmse_norm, width, label="1 - RMSE/max(RMSE) (higher=better)",
               color="#3498db", alpha=0.8, edgecolor="white")
bars2 = ax.bar(x + width/2, r2_vals, width, label="R² Score (higher=better)",
               color="#27ae60", alpha=0.8, edgecolor="white")

# Highlight best model
best_idx = df["rmse"].idxmin()
best_model = df.loc[best_idx, "model"]
bars1[best_idx].set_color("#e74c3c")
bars2[best_idx].set_color("#e74c3c")

ax.set_xticks(x)
ax.set_xticklabels(models, rotation=15, ha="right", fontsize=10)
ax.set_ylabel("Score", fontsize=11)
ax.set_title(f"Best Model: {best_model} (highlighted in red)", fontsize=13, fontweight="bold")
ax.legend(loc="lower right")
ax.set_ylim(0, 1.1)

# Annotate best model bars
ax.annotate(f"RMSE={df.loc[best_idx, 'rmse']:.4f}",
            xy=(best_idx - width/2, rmse_norm[best_idx]),
            xytext=(best_idx - width/2, rmse_norm[best_idx] + 0.05),
            ha="center", fontsize=9, fontweight="bold", color="#e74c3c")
ax.annotate(f"R²={df.loc[best_idx, 'r2']:.4f}",
            xy=(best_idx + width/2, r2_vals[best_idx]),
            xytext=(best_idx + width/2, r2_vals[best_idx] + 0.05),
            ha="center", fontsize=9, fontweight="bold", color="#e74c3c")

plt.tight_layout()
plt.savefig(os.path.join(REPORTS_DIR, "15_best_model_highlight.png"), dpi=150, bbox_inches="tight")
plt.close()
print("Saved: 15_best_model_highlight.png")

print("\nAll report plots generated successfully!")
