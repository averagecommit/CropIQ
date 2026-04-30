

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

# ── Load model artifacts ──
try:
    model          = joblib.load("best_model.pkl")
    feature_columns = joblib.load("feature_columns.pkl")
    meta           = joblib.load("model_meta.pkl")
    print(f"[OK] Model loaded: {type(model).__name__}")
    print(f"     Features: {len(feature_columns)} | R²: {meta.get('best_r2', 'N/A')}")
except Exception as e:
    print(f"[ERROR] {e}")
    print("  Run main_fixed.py to retrain without production leakage.")
    exit(1)

try:
    performance_data = joblib.load("model_performance.pkl")
except Exception as e:
    performance_data = {
        "success": False,
        "models": [],
        "error": f"Could not load model_performance.pkl: {e}",
    }


def to_json_safe(value):
    if isinstance(value, dict):
        return {k: to_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_json_safe(v) for v in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value


def predict_yield(crop, season, state, crop_year,
                  area, annual_rainfall, fertilizer, pesticide):
    """
    Returns predicted yield in t/ha.
    Inputs: agronomic fields only — no Production column.
    """
    row = {
        "Crop_Year":       crop_year,
        "Annual_Rainfall": annual_rainfall,
        "log_Area":        np.log1p(area),
        "log_Fertilizer":  np.log1p(fertilizer),
        "log_Pesticide":   np.log1p(pesticide),
    }
    sample = pd.DataFrame([row])
    for col, val in [("Crop", crop), ("Season", season), ("State", state)]:
        sample[f"{col}_{val}"] = 1

    sample = sample.reindex(columns=feature_columns, fill_value=0)
    log_pred = model.predict(sample)[0]
    return float(np.expm1(log_pred))


@app.route("/")
def index():
    return render_template("crop_yield_app.html")


@app.route("/api/metadata", methods=["GET"])
def get_metadata():
    return jsonify(meta)


@app.route("/api/performance", methods=["GET"])
def get_performance():
    return jsonify(to_json_safe(performance_data))


@app.route("/api/predict", methods=["POST"])
def predict():
    """
    POST /api/predict
    Body (JSON):
    {
        "crop":     "Maize",
        "season":   "Kharif",
        "state":    "Karnataka",
        "year":     2020,        # Optional - not used by model
        "rainfall": 900,
        "area":     50000,
        "fertilizer": 5000000,
        "pesticide":  15000
    }
    Note: "production" field has been removed — it was leaked data.
    """
    try:
        d = request.get_json()

        required = ["crop", "season", "state",
                    "rainfall", "area", "fertilizer", "pesticide"]
        missing = [k for k in required if k not in d]
        if missing:
            return jsonify({"success": False,
                            "error": f"Missing fields: {missing}"}), 400

        # Warn if client accidentally still sends production
        if "production" in d:
            print("[WARN] 'production' field received but ignored (leakage prevention)")

        yield_pred = predict_yield(
            crop           = str(d["crop"]),
            season         = str(d["season"]),
            state          = str(d["state"]),
            crop_year      = int(d.get("year", 2020)),  # Default year, not used by model
            area           = float(d["area"]),
            annual_rainfall= float(d["rainfall"]),
            fertilizer     = float(d["fertilizer"]),
            pesticide      = float(d["pesticide"]),
        )

        return jsonify({
            "success": True,
            "yield":   round(yield_pred, 4),
            "unit":    "tonnes/hectare",
            "model":   type(model).__name__,
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/sensitivity", methods=["POST"])
def sensitivity():
    """
    Batch prediction endpoint for sensitivity analysis.
    POST body: { base inputs + "vary": "rainfall", "range": [300, 2500, 20] }
    Returns array of {x, yield} points for charting.
    """
    try:
        d     = request.get_json()
        vary  = d.get("vary", "rainfall")
        rng   = d.get("range", [300, 2500, 20])
        vals  = np.linspace(rng[0], rng[1], int(rng[2]))

        points = []
        for v in vals:
            kwargs = dict(
                crop=d["crop"], season=d["season"], state=d["state"],
                crop_year=int(d.get("year", 2020)), area=float(d["area"]),
                annual_rainfall=float(d["rainfall"]),
                fertilizer=float(d["fertilizer"]),
                pesticide=float(d["pesticide"]),
            )
            kwargs[{"rainfall":"annual_rainfall","fertilizer":"fertilizer",
                    "pesticide":"pesticide","area":"area"}[vary]] = float(v)
            points.append({"x": round(float(v), 2),
                           "yield": round(predict_yield(**kwargs), 4)})

        return jsonify({"success": True, "points": points, "varied": vary})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status":   "healthy",
        "model":    type(model).__name__,
        "features": len(feature_columns),
        "r2":       meta.get("best_r2"),
        "leakage_free": True,
    })



if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)
    print("\n" + "=" * 60)
    print("  CropIQ — Leakage-Free Prediction Server")
    print("=" * 60)
    print(f"  Model   : {type(model).__name__}")
    print(f"  R²      : {meta.get('best_r2')} (honest, no production leakage)")
    print(f"  Crops   : {len(meta['crops'])}")
    print(f"  States  : {len(meta['states'])}")
    print(f"\n  → http://127.0.0.1:5000")
    print("=" * 60 + "\n")
    app.run(debug=True, host="127.0.0.1", port=5000)
