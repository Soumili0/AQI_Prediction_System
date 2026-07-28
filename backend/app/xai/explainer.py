"""
XAI Explainer — SHAP + LIME
============================
Provides prediction explanations using:
  - SHAP: TreeExplainer for tree-based models, KernelExplainer as fallback
  - LIME: TabularExplainer for any model

Generates:
  - Feature importance values per prediction
  - Summary / waterfall / force plot images
  - JSON-serialisable explanation dicts for API responses
"""

import os
import io
import json
import base64
import logging
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

# Lazy imports (only loaded when first needed)
_shap  = None
_lime  = None


def _get_shap():
    global _shap
    if _shap is None:
        import shap as shap_lib
        _shap = shap_lib
    return _shap


def _get_lime():
    global _lime
    if _lime is None:
        from lime import lime_tabular
        _lime = lime_tabular
    return _lime


# ---------------------------------------------------------------------------
# SHAP Explanation
# ---------------------------------------------------------------------------

def explain_shap(model, X_sample: np.ndarray, feature_names: list,
                 background: np.ndarray = None) -> dict:
    """Generate SHAP explanation for a single prediction.

    Args:
        model:         Trained sklearn-compatible model.
        X_sample:      2D array of shape (1, n_features) — scaled.
        feature_names: List of feature name strings.
        background:    Background dataset for KernelExplainer (optional).

    Returns:
        dict with keys: shap_values, base_value, feature_names,
        feature_importance, plot_b64 (waterfall plot as base64 PNG).
    """
    shap = _get_shap()

    try:
        # Try TreeExplainer first (fast, exact for tree models)
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_sample)
        base_value  = float(explainer.expected_value)
        method = "tree"
    except Exception:
        # Fallback to KernelExplainer (model-agnostic, slower)
        if background is None:
            background = np.zeros((50, X_sample.shape[1]))
        explainer = shap.KernelExplainer(model.predict, background)
        shap_values = explainer.shap_values(X_sample)
        base_value  = float(explainer.expected_value)
        method = "kernel"

    sv = np.array(shap_values).flatten()

    # Feature importance dict (name → shap value)
    importance = {
        name: round(float(val), 5)
        for name, val in zip(feature_names, sv)
    }
    sorted_importance = dict(
        sorted(importance.items(), key=lambda x: abs(x[1]), reverse=True)
    )

    # Waterfall plot
    plot_b64 = _generate_waterfall_plot(sv, feature_names, base_value, method)

    return {
        "method": "shap",
        "explainer_type": method,
        "base_value": round(base_value, 4),
        "shap_values": [round(float(v), 5) for v in sv],
        "feature_names": feature_names,
        "feature_importance": sorted_importance,
        "waterfall_plot_b64": plot_b64,
    }


def _generate_waterfall_plot(shap_values: np.ndarray, feature_names: list,
                               base_value: float, title_suffix: str = "") -> str:
    """Create a horizontal waterfall bar chart and return as base64 PNG."""
    n = min(15, len(feature_names))
    # Sort by abs value, take top-n
    indices = np.argsort(np.abs(shap_values))[::-1][:n]
    sv  = shap_values[indices]
    fn  = [feature_names[i] for i in indices]

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#e74c3c" if v > 0 else "#3498db" for v in sv]
    bars = ax.barh(range(len(fn)), sv, color=colors, alpha=0.85, edgecolor="white")
    ax.set_yticks(range(len(fn)))
    ax.set_yticklabels(fn, fontsize=10)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("SHAP Value (impact on AQI prediction)")
    ax.set_title(f"SHAP Feature Contributions [{title_suffix}]",
                 fontsize=12, fontweight="bold")

    for bar, val in zip(bars, sv):
        x_pos = bar.get_width() + (0.002 if val >= 0 else -0.002)
        ha = "left" if val >= 0 else "right"
        ax.text(x_pos, bar.get_y() + bar.get_height()/2,
                f"{val:+.3f}", va="center", ha=ha, fontsize=8)

    ax.invert_yaxis()
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


# ---------------------------------------------------------------------------
# LIME Explanation
# ---------------------------------------------------------------------------

def explain_lime(model, X_sample: np.ndarray, feature_names: list,
                 training_data: np.ndarray) -> dict:
    """Generate LIME explanation for a single prediction.

    Args:
        model:         Any predict()-compatible model.
        X_sample:      1D or 2D array for the instance to explain.
        feature_names: Ordered list of feature names.
        training_data: 2D training data for LIME's neighbourhood.

    Returns:
        dict with keys: method, feature_importance, plot_b64.
    """
    lime_tabular = _get_lime()

    instance = X_sample.flatten()

    explainer = lime_tabular.LimeTabularExplainer(
        training_data=training_data,
        feature_names=feature_names,
        mode="regression",
        random_state=42,
        verbose=False,
    )

    explanation = explainer.explain_instance(
        data_row=instance,
        predict_fn=model.predict,
        num_features=min(15, len(feature_names)),
    )

    feature_importance = dict(explanation.as_list())

    # LIME bar plot
    plot_b64 = _generate_lime_plot(feature_importance)

    return {
        "method": "lime",
        "feature_importance": feature_importance,
        "predicted_value": float(explanation.predicted_value),
        "intercept": float(explanation.intercept[0]) if hasattr(explanation.intercept, "__getitem__") else float(explanation.intercept),
        "score": float(explanation.score),
        "plot_b64": plot_b64,
    }


def _generate_lime_plot(feature_importance: dict) -> str:
    """Create a LIME bar chart and return as base64 PNG."""
    items = sorted(feature_importance.items(), key=lambda x: abs(x[1]), reverse=True)
    labels = [i[0] for i in items]
    values = [i[1] for i in items]
    colors = ["#e74c3c" if v > 0 else "#3498db" for v in values]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(range(len(labels)), values, color=colors, alpha=0.85, edgecolor="white")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("LIME Weight (contribution to prediction)")
    ax.set_title("LIME Feature Contributions", fontsize=12, fontweight="bold")
    ax.invert_yaxis()
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")
