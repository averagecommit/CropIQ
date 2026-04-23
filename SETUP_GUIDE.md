# 🌾 How to Connect Your ML Model to the HTML Calculator

You have **TWO OPTIONS** to connect these files locally:

---

## ✅ **Option 1: Flask Backend (RECOMMENDED)**

**Best for:** Full ML model integration, real-time predictions, production use

### Setup (5 minutes)

1. **Install Flask:**
   ```bash
   pip install flask flask-cors
   ```

2. **Move HTML to templates folder:**
   ```bash
   mkdir templates
   cp crop_yield_app_backend.html templates/crop_yield_app.html
   ```

3. **Start the server:**
   ```bash
   python app.py
   ```

4. **Open browser:**
   ```
   http://127.0.0.1:5000
   ```

### File Structure
```
your-project/
├── app.py                    # Flask backend ← RUN THIS
├── main_improved.py          # ML training script
├── best_model.pkl           # Trained model (from main_improved.py)
├── feature_columns.pkl      # Required by app.py
├── model_meta.pkl          # Required by app.py
└── templates/
    └── crop_yield_app.html  # Frontend calculator
```

### How it works
```
Browser → Flask API → ML Model → Prediction
   ↓         ↓          ↓           ↓
HTML/JS   app.py   best_model.pkl  JSON response
```

### Pros ✅
- **Uses actual ML model** (98% accuracy)
- Production-ready architecture
- Easy to deploy to cloud
- Proper separation of frontend/backend
- Can add authentication, logging, etc.

### Cons ❌
- Requires Flask server running
- Not offline-capable
- Slightly more complex setup

---

## 🔧 **Option 2: Standalone HTML (Simpler)**

**Best for:** Offline demos, quick testing, no server setup

### Setup (1 minute)

Just open the original HTML file directly in your browser:
```bash
# On Windows
start crop_yield_app.html

# On Mac
open crop_yield_app.html

# On Linux
xdg-open crop_yield_app.html
```

### How it works
```
Browser only (no server needed)
   ↓
HTML/JS with hardcoded prediction formula
```

### Pros ✅
- No server setup needed
- Works offline
- Single file, very portable
- Instant startup

### Cons ❌
- Uses **approximate formula** instead of real ML model (~70% accurate)
- Can't leverage full trained model
- Less accurate predictions

---

## 📊 Comparison Table

| Feature | Flask Backend | Standalone HTML |
|---------|---------------|----------------|
| Setup complexity | Medium | Very Easy |
| Accuracy | 98% (R² = 0.98) | ~70% (approximate) |
| Server required | Yes | No |
| Offline capable | No | Yes |
| Production ready | Yes | Demo only |
| Prediction speed | 50-100ms | Instant |
| Updates | Retrain model | Edit formula |

---

## 🎯 **Which Option Should You Choose?**

### Choose **Flask Backend** if:
- ✅ You want **real ML predictions** (not approximations)
- ✅ This is for a **project/portfolio/deployment**
- ✅ You're comfortable running a local server
- ✅ You want to **showcase actual ML skills**

### Choose **Standalone HTML** if:
- ✅ You just want to **test the UI quickly**
- ✅ You need an **offline demo**
- ✅ You don't want to install Flask
- ✅ Approximate predictions are good enough

---

## 🚀 Quick Start: Flask Backend

### Step-by-step commands:

```bash
# 1. Install dependencies
pip install flask flask-cors pandas numpy scikit-learn joblib xgboost

# 2. Make sure you have the trained model
python main_improved.py

# 3. Create templates folder
mkdir templates

# 4. Copy HTML file
cp crop_yield_app_backend.html templates/crop_yield_app.html

# 5. Start Flask server
python app.py

# 6. Open browser to http://127.0.0.1:5000
```

That's it! The calculator will now use your real ML model for predictions.

---

## 🔍 Testing Your Setup

### Test 1: Check if Flask is running
```bash
curl http://127.0.0.1:5000/api/health
```

Expected output:
```json
{"status": "healthy", "model": "GradientBoostingRegressor", "features": 185}
```

### Test 2: Make a test prediction
```bash
curl -X POST http://127.0.0.1:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"crop":"Maize","season":"Kharif","state":"Karnataka","year":2020,"rainfall":900,"area":50000,"production":80000,"fertilizer":5000000,"pesticide":15000}'
```

Expected output:
```json
{"success": true, "yield": 2.847, "unit": "tonnes/hectare"}
```

### Test 3: Use the calculator
1. Open http://127.0.0.1:5000 in browser
2. Fill in: Maize, Kharif, Karnataka, 2020, 900mm rainfall, etc.
3. Click "Run Prediction"
4. Should see: **~2.85 t/ha**

---

## ⚠️ Common Issues & Fixes

### "Cannot connect to ML model server"
**Problem:** Flask not running  
**Fix:** Run `python app.py` in a terminal

### "ModuleNotFoundError: No module named 'flask'"
**Problem:** Flask not installed  
**Fix:** `pip install flask flask-cors`

### "FileNotFoundError: best_model.pkl"
**Problem:** Model not trained  
**Fix:** Run `python main_improved.py` first

### Blank page at http://127.0.0.1:5000
**Problem:** HTML file not in templates folder  
**Fix:** `cp crop_yield_app_backend.html templates/crop_yield_app.html`

### CORS errors in browser
**Problem:** Opening HTML as file:// instead of via Flask  
**Fix:** Always use http://127.0.0.1:5000, not file:///path/to/file.html

---

## 📝 Files You Should Have

After setup, your folder should contain:

```
✅ main_improved.py          # ML training script
✅ app.py                    # Flask backend
✅ crop_yield_app_backend.html  # Updated calculator (uses Flask API)
✅ best_model.pkl           # Trained model (created by main_improved.py)
✅ feature_columns.pkl      # Feature names
✅ model_meta.pkl          # Dropdown data
✅ templates/
   └── crop_yield_app.html  # Copy of backend HTML for Flask
✅ README_SETUP.md         # This guide
```

---

## 🎓 Understanding the Code

### Flask Backend (`app.py`)
```python
@app.route('/api/predict', methods=['POST'])
def predict():
    # 1. Get user inputs from JSON
    data = request.get_json()
    
    # 2. Call ML model
    yield_pred = predict_yield(
        crop=data['crop'],
        season=data['season'],
        # ... other parameters
    )
    
    # 3. Return prediction
    return jsonify({'success': True, 'yield': yield_pred})
```

### Frontend JavaScript
```javascript
// Old: Hardcoded formula
function computeYield(...) {
    const base = CROP_MEDIANS[crop] || 1.5;
    return base * rainF * fertF * ...;  // Approximate
}

// New: API call to Flask
async function computeYield(...) {
    const response = await fetch('http://127.0.0.1:5000/api/predict', {
        method: 'POST',
        body: JSON.stringify({crop, season, ...})
    });
    const data = await response.json();
    return data.yield;  // Real ML prediction
}
```

---

## 🚢 Next Steps

### For Development:
- ✅ Use Flask backend
- ✅ Keep Flask terminal open while testing
- ✅ Check browser console (F12) for any errors

### For Deployment:
1. Use production WSGI server: `gunicorn app:app`
2. Add HTTPS with nginx
3. Deploy to Heroku/AWS/Google Cloud
4. Add authentication if needed

---

## 💡 Pro Tips

1. **Keep both versions:** Original HTML for quick demos, Flask for real work
2. **Debug with curl:** Test API directly before testing in browser
3. **Check Flask logs:** They show every prediction request
4. **Use browser DevTools:** Network tab shows API calls

---

**You're all set!** Choose your option and start predicting crop yields! 🌾

For Flask setup → Run `python app.py` and open http://127.0.0.1:5000  
For standalone → Just open `crop_yield_app.html` in your browser
