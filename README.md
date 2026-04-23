#  Crop Yield Prediction - Local Setup Guide

This guide shows you how to connect your ML model (`main_improved.py`) with the HTML calculator locally.

## 📋 Prerequisites

1. **Python 3.8+** installed
2. **Required Python packages**:
   ```bash
   pip install flask flask-cors pandas numpy scikit-learn joblib xgboost
   ```
3. **Trained model files** from running `main_improved.py`:
   - `best_model.pkl`
   - `feature_columns.pkl`
   - `model_meta.pkl`

---

## 🚀 Quick Start (3 Steps)

### **Step 1: Train the Model**

First, make sure you have the trained model files:

```bash
python main_improved.py
```

This will create:
- `best_model.pkl` (your trained Gradient Boosting model)
- `feature_columns.pkl` (feature names for encoding)
- `model_meta.pkl` (crop/state/season options for dropdowns)

### **Step 2: Start the Flask Server**

```bash
python app.py
```

You should see:
```
🌾 Crop Yield Prediction Server Starting...
============================================================
   Model: GradientBoostingRegressor
   Crops available: 22
   States available: 15

   Open in browser: http://127.0.0.1:5000
   Press Ctrl+C to stop
============================================================

 * Running on http://127.0.0.1:5000
```

### **Step 3: Open the Calculator**

**Option A - Via Flask (Recommended)**
1. Open your browser
2. Go to: `http://127.0.0.1:5000`
3. The calculator will load with the Flask backend automatically connected

**Option B - Direct HTML file**
1. Move `crop_yield_app_backend.html` to the `templates/` folder:
   ```bash
   mv crop_yield_app_backend.html templates/crop_yield_app.html
   ```
2. Open browser to `http://127.0.0.1:5000`

---

## 📁 File Structure

Your project folder should look like this:

```
your-project/
├── crop_yield.csv              # Original dataset
├── main_improved.py            # Model training script
├── app.py                      # Flask backend (NEW)
├── best_model.pkl             # Trained model (after running main_improved.py)
├── feature_columns.pkl        # Feature names
├── model_meta.pkl             # Dropdown options
├── templates/                 # Flask HTML templates folder
│   └── crop_yield_app.html   # Frontend calculator (backend version)
└── README_SETUP.md           # This file
```

---

## 🔧 How It Works

### Architecture

```
Browser (HTML/JS)  →  Flask API  →  ML Model (Scikit-learn)
     ↓                    ↓              ↓
 User inputs     →   app.py      →  best_model.pkl
 predictions     ←   JSON         ←  predictions
```

### API Endpoints

1. **GET /** - Serves the HTML calculator
2. **POST /api/predict** - Returns yield prediction
   ```json
   // Request
   {
     "crop": "Maize",
     "season": "Kharif",
     "state": "Karnataka",
     "year": 2020,
     "rainfall": 900,
     "area": 50000,
     "production": 80000,
     "fertilizer": 5000000,
     "pesticide": 15000
   }
   
   // Response
   {
     "success": true,
     "yield": 2.847,
     "unit": "tonnes/hectare"
   }
   ```

3. **GET /api/metadata** - Returns dropdown options (crops, states, seasons)
4. **GET /api/health** - Server health check

---

## 🧪 Testing the Connection

### Test 1: API Health Check

```bash
curl http://127.0.0.1:5000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "model": "GradientBoostingRegressor",
  "features": 185
}
```

### Test 2: Manual Prediction

```bash
curl -X POST http://127.0.0.1:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "crop": "Maize",
    "season": "Kharif", 
    "state": "Karnataka",
    "year": 2020,
    "rainfall": 900,
    "area": 50000,
    "production": 80000,
    "fertilizer": 5000000,
    "pesticide": 15000
  }'
```

Expected response:
```json
{
  "success": true,
  "yield": 2.847,
  "unit": "tonnes/hectare"
}
```

### Test 3: Browser Test

1. Open `http://127.0.0.1:5000`
2. Fill in the form with:
   - Crop: Maize
   - Season: Kharif
   - State: Karnataka
   - Year: 2020
   - Rainfall: 900 mm
   - Area: 50,000 ha
   - Production: 80,000 tonnes
   - Fertilizer: 5,000,000 kg
   - Pesticide: 15,000 kg
3. Click "Run Prediction"
4. You should see the predicted yield (~2.85 t/ha)

---

---


---

## 💡 Tips

1. **Keep Flask running** while using the calculator - each prediction calls the API
2. **Use the browser** from http://127.0.0.1:5000 (not opening HTML directly) for best results
3. **Check the Flask terminal** to see prediction logs and debug issues
4. **Sensitivity charts** make ~40 API calls when loading - this is normal

---

## 📊 Performance

- Single prediction: **~50-100ms**
- Sensitivity analysis (40 predictions): **~2-3 seconds**
- Model loading time: **~500ms** (happens once on server start)

---

## 🔄 Making Changes

### To update the model:
1. Modify `main_improved.py`
2. Run `python main_improved.py` to retrain
3. Restart Flask: Ctrl+C, then `python app.py`

### To update the frontend:
1. Edit `templates/crop_yield_app.html`
2. Refresh browser (Ctrl+F5 for hard refresh)
3. No need to restart Flask

---

## ✅ Success Checklist

- [ ] Python 3.8+ installed
- [ ] All packages installed (`pip install flask flask-cors pandas numpy scikit-learn joblib xgboost`)
- [ ] Trained model files exist (`.pkl` files)
- [ ] Flask server running on port 5000
- [ ] Browser shows calculator at http://127.0.0.1:5000
- [ ] Predictions working (test with Maize/Kharif/Karnataka)
- [ ] No CORS errors in browser console

---


---

## 📝 License & Credits

- ML Model: Based on Gradient Boosting Regressor (scikit-learn)
- Dataset: Indian Agriculture Crop Yield Dataset
- Frontend: Custom HTML/CSS/JS with Chart.js

---

**Need help?** Check the Flask server logs first - they show all API calls and errors!
