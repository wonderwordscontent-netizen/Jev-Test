# Google Maps Integration Guide

Complete walkthrough for analyzing real Google Maps reviews with TypeSafe.

## Overview

```
Google Maps API
     ↓
fetch_gmaps_reviews.py  → gmaps_reviews.json
     ↓
analyze_gmaps.py  →  TypeSafe/Jev Analysis
     ↓
gmaps_analysis_report.json  → Action Items
```

## Step 1: Set Up Google Maps API

### 1.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click "Select a Project" → "New Project"
3. Name it (e.g., "Review Analysis")
4. Click "Create"

### 1.2 Enable Places API

1. Search for "Places API" in the search bar
2. Click "Places API"
3. Click "Enable"
4. Wait for it to enable (1-2 minutes)

### 1.3 Create API Key

1. Go to "Credentials" in the left sidebar
2. Click "Create Credentials" → "API Key"
3. Copy your API key
4. (Recommended) Restrict to Places API only:
   - Click the key to edit it
   - Under "API restrictions" → select "Places API"
   - Save

### 1.4 Get Your Place ID

**Option A: Using Google Maps URL**
1. Open Google Maps
2. Search for your business
3. Look at the URL: `https://www.google.com/maps/place/...`
4. The place ID is in the URL after `!1m1!1s`

**Option B: Using Place ID Finder**
1. Go to [Google Places API Explorer](https://developers.google.com/maps/documentation/places/web-service/overview)
2. Use the interactive console to search your place
3. Copy the `place_id` from the response

**Example Place IDs:**
- Starbucks in NYC: `ChIJFz8uyGVawokR82K8K2t8cqU`
- Apple Store SF: `ChIJ0wZJlgKAhYARF0rHJ7pZjJE`

## Step 2: Configure Environment

### Create `.env` file

```bash
# Google Maps
GOOGLE_MAPS_API_KEY="AIzaSyDxxxxxxxxxxxxxxxxxxxx"
GOOGLE_MAPS_PLACE_ID="ChIJxxxxxxxxxxxxxxxxxx"

# BeatAPI/TypeSafe
BEATAPI_API_KEY="sk-xxxxxxxxxxxxxx"
```

### Or set environment variables

```bash
export GOOGLE_MAPS_API_KEY="AIzaSyDxxxxxxxxxxxxxxxxxxxx"
export GOOGLE_MAPS_PLACE_ID="ChIJxxxxxxxxxxxxxxxxxx"
export BEATAPI_API_KEY="sk-xxxxxxxxxxxxxx"
```

## Step 3: Fetch Reviews

```bash
python fetch_gmaps_reviews.py
```

**Output:**
```
✓ Fetched 47 reviews from 'Joe's Coffee Shop' (avg rating: 4.2)
✓ Saved 47 reviews to gmaps_reviews.json
```

**What it does:**
- Calls Google Maps Places API
- Extracts: rating, text, author, timestamp, review count
- Estimates reviewer account age
- Formats for TypeSafe analyzer
- Saves to `gmaps_reviews.json`

**Sample `gmaps_reviews.json` entry:**
```json
{
  "id": "gmaps_1728115200_5432",
  "rating": 5,
  "text": "Amazing coffee and friendly staff! Will definitely come back.",
  "metadata": {
    "reviewer_name": "Sarah M.",
    "reviewer_account_age_days": 1250,
    "review_date": "2024-10-05T10:20:00",
    "days_since_review": 1,
    "reviewer_review_count": 23,
    "reviewer_avg_rating": 5
  }
}
```

## Step 4: Analyze with TypeSafe

```bash
export BEATAPI_API_KEY="sk-xxxxxxxxxxxxxx"
python analyze_gmaps.py
```

**Output:**
```
✓ Loaded 47 reviews

Analyzing with TypeSafe/Jev...
✓ Saved full report to gmaps_analysis_report.json

ANALYSIS SUMMARY
Total reviews analyzed: 47
Likely fake reviews: 3 (6.4%)
Suspicious reviews: 7
Average confidence: 0.84
```

**What it does:**
- Reads `gmaps_reviews.json`
- Analyzes each review with TypeSafe/Jev
- Scores on 5 dimensions
- Ranks by suspicion + recency
- Saves full report
- Shows summary and actionable items

## Step 5: Review Results

### Full Report (`gmaps_analysis_report.json`)

Contains:
- **Summary**: Overall stats and percentages
- **Dimension Analysis**: Patterns by detection type
- **Detailed Results**: Every review with:
  - Suspicion score (0-100)
  - Confidence (0-1)
  - Per-dimension breakdown
  - Evidence for each flag

### Act on Results

**High Suspicion (>75/100):**
1. Review manually on Google Maps
2. Check if it violates Google's policy
3. Report to Google for removal
4. Look for patterns (same reviewer, IP, etc.)

**Medium Suspicion (60-75/100):**
1. Investigate more context
2. Respond professionally
3. Monitor for similar patterns
4. Decide on manual review

**Low Suspicion (<60/100):**
1. Likely authentic
2. No action needed
3. Use for feedback improvement

## Troubleshooting

### "API Error: INVALID_REQUEST"
- Check your Place ID is correct
- Verify API is enabled in Cloud Console

### "API Error: OVER_QUERY_LIMIT"
- You've hit the free quota
- Upgrade to paid tier at console.cloud.google.com
- Free tier: 1,000 calls/day
- Paid tier: Scales with usage

### "403 Forbidden" (BeatAPI)
- Your BEATAPI_API_KEY is invalid
- Get a new key from https://beatapi.io
- Check it's not expired

### "No reviews found"
- Place ID might be wrong
- Business might have 0 reviews on Google Maps
- API might not be enabled
- Check Place ID with Places API Explorer

## Advanced Usage

### Scheduled Analysis

Run analysis weekly to track new fake reviews:

```bash
#!/bin/bash
# run_weekly_analysis.sh

export GOOGLE_MAPS_API_KEY="..."
export BEATAPI_API_KEY="..."

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

python fetch_gmaps_reviews.py
mv gmaps_reviews.json "data/reviews_${TIMESTAMP}.json"

python analyze_gmaps.py
mv gmaps_analysis_report.json "data/report_${TIMESTAMP}.json"

echo "Analysis complete: data/report_${TIMESTAMP}.json"
```

### Multiple Locations

Analyze multiple Google Maps places:

```python
import json
from analyze_gmaps import analyze_reviews_batch, generate_report

locations = {
    "Downtown": "ChIJxxxx",
    "Airport": "ChIJyyyy",
    "Mall": "ChIJzzzz"
}

for name, place_id in locations.items():
    os.environ["GOOGLE_MAPS_PLACE_ID"] = place_id
    
    reviews = fetch_gmaps_reviews(place_id, api_key)
    formatted = convert_to_analyzer_format(reviews)
    analyses = analyze_reviews_batch(formatted)
    report = generate_report(analyses)
    
    with open(f"{name}_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"{name}: {report['summary']['likely_fake_reviews']} fake reviews")
```

### Export to CSV

```python
import csv
import json

with open("gmaps_analysis_report.json") as f:
    report = json.load(f)

with open("fake_reviews.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "Review ID", "Rating", "Suspicion Score", 
        "Confidence", "Days Old", "Likely Fake"
    ])
    
    for result in report["detailed_results"]:
        if result["is_likely_fake"]:
            writer.writerow([
                result["review_id"],
                # rating from original review...
                result["suspicion_score"],
                result["confidence"],
                result["days_since_review"],
                "Yes"
            ])
```

## API Costs

### Google Maps Places API
- **Free tier**: 1,000 requests/day
- **Paid tier**: $0.01-$0.30 per call depending on data fields

### BeatAPI (TypeSafe)
- **Free tier**: Sufficient for testing (limited queries)
- **Paid tier**: $0.001-$0.005 per review analysis (ballpark)

**Example cost for 10,000 reviews:**
- Google Maps: $0-$100 (depending on tier)
- BeatAPI: $10-$50 (depending on volume)
- **Total: $10-$150/month for 10K reviews**

## Next Steps

1. ✅ Set up Google Cloud project and Places API
2. ✅ Get your Place ID
3. ✅ Configure environment variables
4. ✅ Run `fetch_gmaps_reviews.py`
5. ✅ Run `analyze_gmaps.py`
6. 📊 Review `gmaps_analysis_report.json`
7. 🎯 Take action on flagged reviews
8. 📈 Set up scheduled analysis

## Support

- **Google Maps API**: https://developers.google.com/maps
- **BeatAPI**: https://beatapi.io
- **TypeSafe Docs**: https://docs.typesafe.ai
- **This Project**: See README.md and ARCHITECTURE.md

---

**Ready?** Start with Step 1 above! 🚀
