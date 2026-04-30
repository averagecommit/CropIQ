import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, KFold, cross_val_score, RandomizedSearchCV
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import warnings
warnings.filterwarnings("ignore")

try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️  XGBoost not installed — skipping. Run: pip install xgboost")

# ---------------------------------------------------------------
# 1. Load & Clean
# ---------------------------------------------------------------
df = pd.read_csv("crop_yield.csv")
df.dropna(inplace=True)

for col in df.select_dtypes(include="object").columns:
    df[col] = df[col].str.strip()

print(f"Dataset shape: {df.shape}")
print(f"Yield range: {df['Yield'].min():.3f} – {df['Yield'].max():.1f} t/ha")

# ---------------------------------------------------------------
# 2. Remove data leakage
# ---------------------------------------------------------------
# Yield (t/ha) = Production (tonnes) / Area (ha)
df = df.drop(columns=["Production"])
print("\n✅ Dropped 'Production' column (data leakage: Yield = Production/Area)")

# ---------------------------------------------------------------
# 3. Feature Engineering
# ---------------------------------------------------------------
for col in ["Area", "Fertilizer", "Pesticide"]:
    df[f"log_{col}"] = np.log1p(df[col])
df["log_Yield"] = np.log1p(df["Yield"])

numeric_features = [
    "Annual_Rainfall",
    "log_Area",
    "log_Fertilizer",
    "log_Pesticide",
]

# ---------------------------------------------------------------
# 4. One-Hot Encode Categoricals
# ---------------------------------------------------------------
cat_cols = ["Crop", "Season", "State"]
df_enc = pd.get_dummies(df[cat_cols + numeric_features], columns=cat_cols)

feature_columns = df_enc.columns.tolist()
print(f"Total features after encoding: {len(feature_columns)}")

X = df_enc
y = df["log_Yield"]

# ---------------------------------------------------------------
# 5. Train / Validation / Test Split (70 / 15 / 15)
# ---------------------------------------------------------------
X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.30, random_state=42
)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.50, random_state=42
)
print(f"Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")

# ---------------------------------------------------------------
# 6. Base Models
# ---------------------------------------------------------------
models = {
    "Ridge Regression": Ridge(alpha=1.0),
    "Random Forest": RandomForestRegressor(
        n_estimators=200, max_depth=12,
        min_samples_leaf=2, random_state=42, n_jobs=-1
    ),
    "Gradient Boosting": GradientBoostingRegressor(
        n_estimators=300, learning_rate=0.05,
        max_depth=6, subsample=0.8, random_state=42
    ),
}
if XGBOOST_AVAILABLE:
    models["XGBoost"] = XGBRegressor(
        n_estimators=300, learning_rate=0.05, max_depth=6,
        subsample=0.8, colsample_bytree=0.8, random_state=42,
        eval_metric="rmse"
    )

# ---------------------------------------------------------------
# 7. Hyperparameter Optimization (RandomizedSearchCV)
# ---------------------------------------------------------------
print("\n===== Hyperparameter Tuning (RandomizedSearchCV) =====")
print("This may take 5–15 minutes depending on your machine.\n")

param_grids = {
    "Ridge Regression": {
        'alpha': [0.01, 0.1, 1.0, 10.0, 100.0]
    },
    "Random Forest": {
        'n_estimators': [100, 200, 300, 400, 500],
        'max_depth': [8, 10, 12, 15, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4]
    },
    "Gradient Boosting": {
        'n_estimators': [200, 300, 400],
        'learning_rate': [0.01, 0.05, 0.1],
        'max_depth': [4, 6, 8],
        'subsample': [0.7, 0.8, 0.9]
    }
}

if XGBOOST_AVAILABLE:
    param_grids["XGBoost"] = {
        'n_estimators': [200, 300, 400],
        'learning_rate': [0.01, 0.05, 0.1],
        'max_depth': [4, 6, 8],
        'subsample': [0.7, 0.8, 0.9],
        'colsample_bytree': [0.7, 0.8, 0.9]
    }

tuned_models = {}
best_cv_scores = {}
n_iter = 20          # ← Increase to 30–50 if you want even better results (takes longer)

for name, model in models.items():
    param_grid = param_grids.get(name, {})
    print(f"Tuning {name} ...", end=" ")
    
    if not param_grid:
        tuned_models[name] = model
        best_cv_scores[name] = None
        print("✅ (no tuning needed)")
        continue

    search = RandomizedSearchCV(
        estimator=model,
        param_distributions=param_grid,
        n_iter=n_iter,
        cv=5,
        scoring='r2',
        random_state=42,
        n_jobs=-1,
        verbose=0
    )
    search.fit(X_train, y_train)
    
    tuned_models[name] = search.best_estimator_
    best_cv_scores[name] = float(search.best_score_)
    print(f"✅ Best CV R² = {search.best_score_:.4f}")
    # Optional: print best params
    # print(f"   Best params: {search.best_params_}")

# Use tuned models for final evaluation
models = tuned_models

# ---------------------------------------------------------------
# 8. Final Training & Test Evaluation 
# ---------------------------------------------------------------
print("\n===== Test Set Performance (real-scale yield) =====")
print(f"{'Model':<25} {'MAE':>10} {'RMSE':>10} {'R²':>8}")
print("-" * 56)

best_r2, best_model_name, best_model_obj = -np.inf, None, None
performance_rows = []

for name, model in models.items():
    if name == "XGBoost" and XGBOOST_AVAILABLE:
        model.fit(X_train, y_train,
                  eval_set=[(X_val, y_val)], verbose=False)
    else:
        model.fit(X_train, y_train)

    y_pred_real = np.expm1(model.predict(X_test))
    y_test_real = np.expm1(y_test)

    mae  = mean_absolute_error(y_test_real, y_pred_real)
    rmse = np.sqrt(mean_squared_error(y_test_real, y_pred_real))
    r2   = r2_score(y_test_real, y_pred_real)

    print(f"  {name:<25} {mae:>10.3f} {rmse:>10.3f} {r2:>8.4f}")
    performance_rows.append({
        "name": name,
        "r2": round(float(r2), 4),
        "mae": round(float(mae), 3),
        "rmse": round(float(rmse), 3),
        "cv_r2": (
            round(float(best_cv_scores[name]), 4)
            if best_cv_scores.get(name) is not None
            else None
        ),
        "is_best": False,
    })

    if r2 > best_r2:
        best_r2, best_model_name, best_model_obj = r2, name, model
    
print(f"\n✅ Best model (after tuning): {best_model_name} (R² = {best_r2:.4f})")
print(f"   This R² is honest — no production leakage.")

for row in performance_rows:
    row["is_best"] = row["name"] == best_model_name
performance_rows.sort(key=lambda row: row["r2"], reverse=True)

# ---------------------------------------------------------------
# 9. Save artifacts
# ---------------------------------------------------------------
joblib.dump(best_model_obj, "best_model.pkl")
joblib.dump(feature_columns, "feature_columns.pkl")

meta = {
    "crops":    sorted(df["Crop"].unique().tolist()),
    "seasons":  sorted(df["Season"].unique().tolist()),
    "states":   sorted(df["State"].unique().tolist()),
    "best_model_name": best_model_name,
    "best_r2": round(best_r2, 4),
}
joblib.dump(meta, "model_meta.pkl")
print("\nSaved: best_model.pkl, feature_columns.pkl, model_meta.pkl")

# ---------------------------------------------------------------
# 10. Prediction helper 
# ---------------------------------------------------------------
def predict_yield(crop, season, state, crop_year,
                  area, annual_rainfall, fertilizer, pesticide):
    
    row = {
        "Annual_Rainfall":  annual_rainfall,
        "log_Area":         np.log1p(area),
        "log_Fertilizer":   np.log1p(fertilizer),
        "log_Pesticide":    np.log1p(pesticide),
    }
    sample = pd.DataFrame([row])
    for col, val in [("Crop", crop), ("Season", season), ("State", state)]:
        sample[f"{col}_{val}"] = 1
    sample = sample.reindex(columns=feature_columns, fill_value=0)
    return float(np.expm1(best_model_obj.predict(sample)[0]))

# ===============================================================
# 11. SAVE PERFORMANCE FOR FRONTEND (NEW)
# ===============================================================
performance_data = {
    "success": True,
    "best_model_name": best_model_name,
    "models": performance_rows,
}

joblib.dump(performance_data, "model_performance.pkl")
print("✅ Saved model_performance.pkl for web dashboard")
