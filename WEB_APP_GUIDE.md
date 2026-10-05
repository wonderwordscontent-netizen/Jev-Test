# TypeSafe Review Analyzer - Web App

Simple web interface to analyze reviews without command line.

## Quick Start

### 1. Install Flask

```bash
pip install flask
```

### 2. Run the Web App

```bash
python web_app.py
```

**Output:**
```
Starting Flask app...
Open your browser to: http://localhost:5000
```

### 3. Open in Browser

Go to: **http://localhost:5000**

---

## How to Use

### Option 1: Try Demo (Instant)

1. Click **"Demo Data"** button
2. See sample reviews analyzed
3. Check results with 3 sample reviews (1 fake, 2 authentic)

### Option 2: Paste Your Reviews

1. Copy reviews from Google Maps (or anywhere)
2. Paste into the text area
3. Click **"Analyze Reviews"**
4. See results instantly

### Supported Formats

**Google Maps Format (Full):**
```
5 stars · Amazing coffee! · Sarah M. · 2 days ago
```

**Simplified:**
```
5 Great service!
```

**Just text:**
```
Great service!
```
(Will default rating to 5)

---

## Features

### Dashboard Tabs

- **All Reviews** - See every review analyzed
- **🚩 Fake Only** - Show just the suspicious reviews
- **✅ Authentic Only** - Show just the real reviews

### Metrics Shown

- **Total Reviews** - Number analyzed
- **Likely Fake** - Count and percentage
- **Suspicious** - Total with high suspicion
- **Confidence** - Average model confidence

### Per-Review Analysis

Each review shows:
- ⭐ Star rating
- 📊 Suspicion score (0-100)
- 📝 Full review text
- 📅 Days since posted
- 🎯 Confidence percentage
- 🚩/✅ Fake/Authentic badge

### Suspicion Meter

Visual bar showing:
- 🟢 Green (0-33) = Authentic
- 🟡 Yellow (33-66) = Mixed signals
- 🔴 Red (66-100) = Suspicious

---

## API Checkbox

**"Use Real TypeSafe API"** option:

- ☑️ Checked: Uses real Jev analysis (requires `BEATAPI_API_KEY` environment variable)
- ☐ Unchecked: Uses mock analysis (instant, no API key needed)

### Enable Real Analysis

```bash
export BEATAPI_API_KEY="sk-xxxxx..."
python web_app.py
```

Then check the API box in the web interface.

---

## Example Workflow

### 1. Quick Test (30 seconds)

```bash
python web_app.py
# Visit http://localhost:5000
# Click "Demo Data"
# See results instantly
```

### 2. Analyze Your Reviews

**On Google Maps:**
1. Find a listing
2. Copy a few reviews

**In Web App:**
1. Paste into text area
2. Click "Analyze Reviews"
3. See which are likely fake

**Example reviews to paste:**
```
5 stars · Great coffee and friendly staff! · Sarah M. · 2 days ago
4 stars · Good but slow today · John D. · 5 days ago
5 stars · MUST VISIT! Click for promo code SAVE20! · Mark · 1 day ago
```

### 3. Review Results

- See suspicion score for each
- Identify fake reviews
- Check confidence levels
- Filter by tab (all/fake/authentic)

---

## Stopping the Server

Press **Ctrl+C** in the terminal where `web_app.py` is running.

---

## Troubleshooting

### "Port 5000 already in use"

```bash
# Use a different port
python web_app.py --port 8000
# Then visit http://localhost:8000
```

### "ModuleNotFoundError: No module named 'flask'"

```bash
pip install flask
```

### "Can't connect to http://localhost:5000"

- Make sure `python web_app.py` is still running
- Try refreshing the page
- Check the terminal for error messages

### Real API returns "Unauthorized"

- Make sure `BEATAPI_API_KEY` is set correctly
- Get key from https://beatapi.io
- Check it's not expired

---

## File Structure

```
Jev-Test/
├── web_app.py              # Flask backend
├── templates/
│   └── index.html          # Web interface
├── review_analyzer.py      # TypeSafe analyzer
├── paste_reviews_manual.py # Review parser
└── analyze_gmaps.py        # Google Maps analysis
```

---

## Architecture

```
Browser (http://localhost:5000)
    ↓
HTML Form (paste reviews)
    ↓
JavaScript (client-side)
    ↓
Flask Backend (web_app.py)
    ↓
Review Parser
    ↓
TypeSafe Analyzer (mock or real)
    ↓
JSON Results
    ↓
Display in Browser
```

---

## Keyboard Shortcuts

- **Tab** key: Navigate between fields
- **Enter** in textarea: New line (not submit)
- **Ctrl+A**: Select all text
- **Ctrl+V**: Paste reviews

---

## Tips

1. **Format matters**: Copy-paste full review text works best
2. **Batch processing**: Paste multiple reviews at once
3. **Demo first**: Try "Demo Data" to understand results
4. **Check confidence**: Higher confidence = more reliable
5. **Use tabs**: Filter results to see fake reviews easily

---

## Next Steps

1. ✅ Run `python web_app.py`
2. ✅ Visit http://localhost:5000
3. ✅ Click "Demo Data" or paste reviews
4. ✅ Review results
5. ✅ Try with real API key for actual analysis

---

## Support

- **TypeSafe Docs**: https://docs.typesafe.ai
- **BeatAPI**: https://beatapi.io
- **This Project**: See README.md and ARCHITECTURE.md

---

Enjoy analyzing reviews! 🚀
