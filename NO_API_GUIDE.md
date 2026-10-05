# Test Without Google Maps API

Three ways to get reviews without needing the Google Maps API:

## Option 1: Paste Reviews Manually (Easiest) ⭐

```bash
python paste_reviews_manual.py
```

**What you do:**
1. Open a Google Maps listing
2. Copy each review (you can manually type or copy-paste)
3. Paste into the script one at a time
4. Press Enter to save, then paste the next one
5. Type 'q' when done

**Example review to paste:**
```
5 stars · Amazing coffee and friendly staff! Will definitely come back. · Sarah M. · 2 days ago
```

**Or even simpler:**
```
5 Great service!
```

The script will prompt for any missing info.

**Output:** `gmaps_reviews.json` with your reviews

---

## Option 2: Process Test Reviews (For Demo)

```bash
python process_test_reviews.py
```

**What it does:**
- Reads 5 sample reviews from `test_reviews.txt`
- Parses them (extracts rating, text, reviewer, date)
- Saves to `gmaps_reviews.json`

**Already includes:**
- ✅ Authentic reviews (specific details, natural language)
- ✅ Suspicious reviews (generic + spam phrases)
- ✅ Negative reviews (1-star complaint)
- ✅ Various review ages (1 day to 1 week old)

**Good for:** Quick testing without manual work

---

## Option 3: Scrape from Google Maps Link

```bash
python fetch_gmaps_link.py
```

**What you need:**
- A Google Maps listing link (e.g., https://www.google.com/maps/place/Starbucks+NYC)

**What it does:**
- Attempts to scrape reviews from the page
- Extracts rating, text, reviewer name, date
- Saves to `gmaps_reviews.json`

**Limitations:**
- Google actively blocks scrapers
- May fail if they changed HTML structure
- Slower (loads browser or makes requests)
- Requires additional libraries:
  ```bash
  pip install selenium beautifulsoup4 requests
  ```

**Best for:** One-time scraping if you have a specific listing

---

## Complete Workflow

### Quick Test (5 minutes)

```bash
# 1. Create reviews from test data
python process_test_reviews.py

# 2. Verify reviews.json was created
cat gmaps_reviews.json

# 3. Run demo analysis (no API needed)
python quick_start_demo.py
```

**Result:** See fake reviews detected without needing any API!

---

### With Real Reviews (10 minutes)

```bash
# 1. Paste reviews manually
python paste_reviews_manual.py
# (Follow the prompts, paste reviews one by one)

# 2. Verify reviews were saved
cat gmaps_reviews.json

# 3. Analyze with TypeSafe (requires BeatAPI key)
export BEATAPI_API_KEY="sk-xxxxx..."
python analyze_gmaps.py
```

**Result:** Full analysis with real TypeSafe/Jev

---

### Batch of Reviews (Copy-Paste)

1. Create `my_reviews.txt` with reviews (one per line):
```
5 stars · Great coffee! · John · 2 days ago
4 stars · Good but slow · Sarah · 5 days ago
5 stars · BEST EVER! PROMO CODE SAVE20! · Mark · 1 day ago
```

2. Update `process_test_reviews.py` to read from `my_reviews.txt`

3. Run:
```bash
python process_test_reviews.py
python analyze_gmaps.py
```

---

## Review Format Guide

### Recognized Formats

**Google Maps Official:**
```
5 stars · Great service! · John Doe · 2 days ago
```

**Simplified:**
```
5 Great service!
```

**With dashes:**
```
5 Great service! - John Doe
```

**Just text:**
```
Great service!
```
(Script will prompt for rating)

### What the Parser Extracts

From the example: `5 stars · Amazing coffee and friendly staff! · Sarah M. · 2 days ago`

- **Rating:** 5
- **Text:** "Amazing coffee and friendly staff!"
- **Reviewer:** Sarah M.
- **Days since:** 2 (converts "2 days ago" → 2 days)

Automatically formats into:
```json
{
  "id": "gmaps_manual_1",
  "rating": 5,
  "text": "Amazing coffee and friendly staff!",
  "metadata": {
    "reviewer_name": "Sarah M.",
    "reviewer_account_age_days": 365,
    "review_date": "2024-10-03T10:20:00",
    "days_since_review": 2,
    "reviewer_review_count": 1,
    "reviewer_avg_rating": 5.0
  }
}
```

---

## Testing the Analysis

### Demo Only (No API)

```bash
python quick_start_demo.py
```

Uses mock Jev responses to show how analysis works.

### With Real TypeSafe API

```bash
export BEATAPI_API_KEY="sk-xxxxx..."
python analyze_gmaps.py
```

Calls real Jev System One model and returns actual analysis.

---

## Troubleshooting

### "No reviews found" 
- Make sure `gmaps_reviews.json` exists
- Run `python process_test_reviews.py` first to create it

### "BEATAPI_API_KEY not set"
- Get a free key from https://beatapi.io
- Set it: `export BEATAPI_API_KEY="sk-xxxxx..."`

### Parsing issues
- The manual parser is lenient - just include rating and text
- It will ask for missing info
- Copy-paste directly from Google Maps works great

### Can't install Selenium/BeautifulSoup
- They're optional - only needed for `fetch_gmaps_link.py`
- Use `paste_reviews_manual.py` instead
- Or just use test data: `python process_test_reviews.py`

---

## Quick Start Commands

**One minute test:**
```bash
python process_test_reviews.py
python quick_start_demo.py
```

**With API key:**
```bash
export BEATAPI_API_KEY="sk-xxxxx..."
python process_test_reviews.py
python analyze_gmaps.py
```

**Manual reviews:**
```bash
python paste_reviews_manual.py
# (follow prompts)
export BEATAPI_API_KEY="sk-xxxxx..."
python analyze_gmaps.py
```

---

## What's Happening

### Data Flow (No API)

```
Your Reviews
    ↓
paste_reviews_manual.py OR process_test_reviews.py
    ↓
gmaps_reviews.json
    ↓
quick_start_demo.py (mock analysis)
    ↓
Console output with results
```

### Data Flow (With API)

```
Your Reviews
    ↓
gmaps_reviews.json
    ↓
analyze_gmaps.py → BEATAPI (TypeSafe/Jev)
    ↓
gmaps_analysis_report.json
    ↓
Summary + detailed results
```

---

## Next Steps

1. ✅ Test with demo: `python quick_start_demo.py`
2. ✅ Create your own reviews: `python paste_reviews_manual.py`
3. ✅ Get BeatAPI key: https://beatapi.io
4. ✅ Analyze: `python analyze_gmaps.py`
5. 📊 Review results in `gmaps_analysis_report.json`
6. 🎯 Take action on flagged reviews

---

Need the full Google Maps API integration? See `GOOGLE_MAPS_INTEGRATION.md`

Happy analyzing! 🎯
