"""
Report Service
==============
Generates downloadable PDF and CSV reports for:
  - Prediction history
  - Analytics summary
  - Model comparison
"""

import os
import csv
import json
from datetime import datetime
from io import StringIO, BytesIO

from flask import current_app

from app import db
from app.models.prediction import Prediction
from app.models.report import Report
from app.models.ml_model import MLModel


REPORTS_DIR = os.path.join("reports")


def _ensure_reports_dir() -> str:
    os.makedirs(REPORTS_DIR, exist_ok=True)
    return REPORTS_DIR


# ---------------------------------------------------------------------------
# CSV Report
# ---------------------------------------------------------------------------

def generate_csv_prediction_history(user_id: int, filters: dict = None) -> bytes:
    """Generate a CSV of the user's prediction history."""
    q = Prediction.query.filter_by(user_id=user_id).order_by(Prediction.requested_at.desc())

    if filters:
        if filters.get("date_from"):
            q = q.filter(Prediction.requested_at >= filters["date_from"])
        if filters.get("date_to"):
            q = q.filter(Prediction.requested_at <= filters["date_to"])
        if filters.get("city"):
            q = q.filter(Prediction.city.ilike(f"%{filters['city']}%"))

    predictions = q.limit(10000).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "City", "Predicted AQI", "AQI Category", "Health Advisory",
        "PM2.5", "PM10", "NO2", "SO2", "CO", "O3",
        "Temperature", "Humidity", "Wind Speed", "Requested At"
    ])

    for p in predictions:
        inp = p.input_features or {}
        writer.writerow([
            p.id, p.city or "", round(p.predicted_aqi, 2), p.aqi_category or "",
            (p.health_advisory or "").replace("\n", " "),
            inp.get("pm25", ""), inp.get("pm10", ""), inp.get("no2", ""),
            inp.get("so2", ""), inp.get("co", ""), inp.get("o3", ""),
            inp.get("temperature", ""), inp.get("humidity", ""),
            inp.get("wind_speed", ""),
            p.requested_at.isoformat(),
        ])

    return output.getvalue().encode("utf-8")


def generate_csv_analytics(city: str = None, days: int = 30) -> bytes:
    """Generate a CSV of AQI readings for analytics."""
    from app.models.aqi_reading import AQIReading
    from datetime import timedelta

    since = datetime.utcnow() - timedelta(days=days)
    q = AQIReading.query.filter(AQIReading.recorded_at >= since)
    if city:
        q = q.filter(AQIReading.city.ilike(f"%{city}%"))

    readings = q.order_by(AQIReading.recorded_at.desc()).limit(50000).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "City", "Country", "Recorded At",
        "PM2.5", "PM10", "NO2", "SO2", "CO", "O3", "NH3",
        "Temperature", "Humidity", "Wind Speed", "Pressure",
        "AQI", "AQI Category"
    ])

    for r in readings:
        writer.writerow([
            r.id, r.city, r.country or "",
            r.recorded_at.isoformat(),
            r.pm25, r.pm10, r.no2, r.so2, r.co, r.o3, r.nh3,
            r.temperature, r.humidity, r.wind_speed, r.pressure,
            r.aqi, r.aqi_category or "",
        ])

    return output.getvalue().encode("utf-8")


# ---------------------------------------------------------------------------
# PDF Report (using fpdf2)
# ---------------------------------------------------------------------------

def generate_pdf_prediction_history(user_id: int, filters: dict = None) -> bytes:
    """Generate a styled PDF report of prediction history."""
    from fpdf import FPDF

    predictions = (
        Prediction.query
        .filter_by(user_id=user_id)
        .order_by(Prediction.requested_at.desc())
        .limit(500)
        .all()
    )

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_fill_color(30, 58, 95)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, "AQI Prediction History Report", ln=True, fill=True, align="C")
    pdf.ln(3)

    # Metadata
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | "
                   f"Total Records: {len(predictions)}", ln=True)
    pdf.ln(4)

    # Table header
    headers = ["ID", "City", "AQI", "Category", "PM2.5", "PM10", "Date"]
    widths   = [15, 35, 20, 55, 20, 20, 35]

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(45, 106, 79)
    pdf.set_text_color(255, 255, 255)
    for h, w in zip(headers, widths):
        pdf.cell(w, 8, h, border=1, fill=True, align="C")
    pdf.ln()

    # Table rows
    pdf.set_font("Helvetica", "", 8)
    for i, p in enumerate(predictions):
        inp = p.input_features or {}
        fill = i % 2 == 0
        pdf.set_fill_color(245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(40, 40, 40)

        # Colour-code the AQI cell
        aqi_val = round(p.predicted_aqi, 1)
        row_data = [
            str(p.id),
            (p.city or "-")[:18],
            str(aqi_val),
            (p.aqi_category or "-")[:25],
            str(inp.get("pm25", "-")),
            str(inp.get("pm10", "-")),
            p.requested_at.strftime("%Y-%m-%d %H:%M"),
        ]

        for val, w in zip(row_data, widths):
            pdf.cell(w, 7, val, border=1, fill=fill, align="C")
        pdf.ln()

    return pdf.output()


def generate_pdf_analytics(city: str = None, days: int = 30) -> bytes:
    """Generate analytics summary PDF."""
    from fpdf import FPDF
    from app.services.analytics_service import (
        get_aqi_overview, get_pollutant_averages, get_city_comparison
    )

    overview    = get_aqi_overview(city=city, days=days)
    pollutants  = get_pollutant_averages(city=city, days=days)
    cities_data = get_city_comparison()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_fill_color(30, 58, 95)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, "AQI Analytics Report", ln=True, fill=True, align="C")
    pdf.ln(4)

    # Overview
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 58, 95)
    pdf.cell(0, 8, f"Overview — Last {days} Days | {city or 'All Cities'}", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(50, 50, 50)
    for k, v in overview.items():
        if k != "category_breakdown":
            pdf.cell(0, 7, f"  {k.replace('_', ' ').title()}: {v}", ln=True)

    # Category breakdown
    if "category_breakdown" in overview:
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "Category Breakdown:", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for cat, cnt in overview["category_breakdown"].items():
            pdf.cell(0, 6, f"  {cat}: {cnt} readings", ln=True)

    # Pollutant averages
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 58, 95)
    pdf.cell(0, 8, "Average Pollutant Concentrations", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)
    for p, v in pollutants.get("pollutants", {}).items():
        unit = "mg/m³" if p == "co" else "µg/m³"
        pdf.cell(0, 6, f"  {p.upper()}: {v} {unit}" if v is not None else f"  {p.upper()}: N/A", ln=True)

    # City comparison table
    if cities_data.get("cities"):
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(30, 58, 95)
        pdf.cell(0, 8, "City Comparison", ln=True)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(45, 106, 79)
        pdf.set_text_color(255, 255, 255)
        for h, w in zip(["City", "Mean AQI", "Min", "Max", "Readings"], [60, 35, 30, 30, 35]):
            pdf.cell(w, 7, h, border=1, fill=True, align="C")
        pdf.ln()
        pdf.set_font("Helvetica", "", 9)
        for i, c in enumerate(cities_data["cities"][:20]):
            fill = i % 2 == 0
            pdf.set_fill_color(245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(40, 40, 40)
            for val, w in zip([c["city"], c["mean_aqi"], c["min_aqi"], c["max_aqi"], c["count"]], [60, 35, 30, 30, 35]):
                pdf.cell(w, 6, str(val), border=1, fill=fill, align="C")
            pdf.ln()

    pdf.ln(5)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, f"Generated by AI AQI Prediction System | {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
             ln=True, align="C")

    return pdf.output()


# ---------------------------------------------------------------------------
# Report record management
# ---------------------------------------------------------------------------

def save_report_record(user_id: int, title: str, report_type: str,
                       fmt: str, file_path: str, parameters: dict,
                       file_size_kb: int) -> Report:
    """Persist a report record to the database."""
    report = Report(
        user_id=user_id, title=title, report_type=report_type,
        format=fmt, file_path=file_path, parameters=parameters,
        file_size_kb=file_size_kb,
    )
    db.session.add(report)
    db.session.commit()
    return report


def list_reports(user_id: int) -> list:
    return [r.to_dict() for r in
            Report.query.filter_by(user_id=user_id)
                        .order_by(Report.created_at.desc()).all()]
