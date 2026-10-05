# Getting Started with TypeSafe Review Analysis

Quick guide to get the review analyzer running in 5 minutes.

## Step 1: Get a Free BeatAPI Account (1 min)

1. Go to https://beatapi.io
2. Sign up for a free account
3. Get your `BEATAPI_API_KEY` from the dashboard
4. The free tier includes access to `jev-1.13-free` model

## Step 2: Install Dependencies (1 min)

**Python:**
```bash
pip install -r requirements.txt
```

**Node/TypeScript:**
```bash
npm install
```

## Step 3: Set Your API Key (30 sec)

```bash
export BEATAPI_API_KEY="your_key_from_beatapi_dashboard"
```

## Step 4: Run the Quick Start (2 min)

```bash
python quick_start.py
```

You should see output like:

```
============================================================
TypeSafe Review Fake Detection - Quick Start
============================================================

📊 Analyzing review review_001...
   Rating: 5★ | Account age: 2 days
   ✓ Language Authenticity: Level 4 (suspicion: 80, confidence: 0.89)
   ✓ Has Specific Details: no (suspicion: 60, confidence: 0.91)
   ✓ Has Spam Phrases: no (suspicion: 0, confidence: 0.88)

   🎯 Overall Suspicion Score: 47/100
   ✅ Appears authentic

...

============================================================
SUMMARY
============================================================
Total reviews analyzed: 3
Flagged as fake: 2 (66.7%)

Detailed Results:
  review_001: 47/100 - ✅ OK
  review_002: 28/100 - ✅ OK
  review_003: 72/100 - 🚩 FAKE

✓ Analysis complete!
```

## Step 5: Understand the Output

### Suspicion Dimensions

Each review is analyzed on multiple dimensions:

1. **Language Authenticity** (Score 0-5)
   - Detects generic, robotic, or templated language
   - Level 4-5 = suspicious

2. **Specific Details** (Yes/No)
   - Genuine reviews mention staff names, menu items, specific experiences
   - "No" = suspicious

3. **Spam Phrases** (Yes/No)
   - Flags promotional language, promo codes, urgency language
   - "Yes" = very suspicious

### Suspicion Scoring

- **0-30**: Likely authentic
- **30-60**: Mixed signals (worth reviewing)
- **60-100**: Highly suspicious 🚩

## Using with Your Own Data

### Python Implementation

```python
from review_analyzer import analyze_reviews_batch, generate_report

# Your reviews
reviews = [
    {
        "id": "your_review_id",
        "rating": 5,
        "text": "Review text here...",
        "metadata": {
            "reviewer_name": "John Doe",
            "reviewer_account_age_days": 500,
            "review_date": "2024-10-05",
            "days_since_review": 1,
            "reviewer_review_count": 15,
            "reviewer_avg_rating": 4.2
        }
    },
    # ... more reviews
]

# Analyze
analyses = analyze_reviews_batch(reviews)
report = generate_report(analyses)

# View results
print(f"Fake reviews: {report['summary']['likely_fake_reviews']} of {report['summary']['total_reviews_analyzed']}")
for analysis in analyses:
    if analysis.is_likely_fake:
        print(f"  - {analysis.review_id}: {analysis.overall_suspicion_score}/100")
```

### TypeScript Implementation

```typescript
import { analyzeReviewsBatch, generateReport } from './review-analyzer';

const reviews = [ /* ... */ ];

const analyses = await analyzeReviewsBatch(reviews);
const report = generateReport(analyses);

console.log(`Fake: ${report.summary.likelyFakeReviews} of ${report.summary.totalReviewsAnalyzed}`);
```

## Integrating with Google Maps

To connect with real Google Maps data:

1. Use Google Maps API to fetch reviews
2. Format each review with required fields (see `Review` type in code)
3. Pass to `analyze_reviews_batch()`

Example field mapping:
```python
review = {
    "id": gmaps_review["reviewId"],
    "rating": gmaps_review["rating"],
    "text": gmaps_review["text"],
    "metadata": {
        "reviewer_name": gmaps_review["reviewer"]["displayName"],
        "reviewer_account_age_days": calculate_account_age(gmaps_review["reviewer"]["joinedDate"]),
        "review_date": gmaps_review["publishTime"],
        "days_since_review": calculate_days_since(gmaps_review["publishTime"]),
        "reviewer_review_count": gmaps_review["reviewer"].get("totalReviews", 0),
        "reviewer_avg_rating": gmaps_review["reviewer"].get("avgRating", 0)
    }
}
```

## Common Questions

### How much does it cost?

BeatAPI free tier includes sufficient usage for testing. Check their pricing for production volumes.

### Can I adjust sensitivity?

Yes! Edit the thresholds in the code:

```python
# In analyze_review()
is_likely_fake = (overall_score > 60) and (confidence > 0.5)
# Increase 60 → more permissive (fewer false positives)
# Decrease 60 → more strict (fewer false negatives)
```

### How do I add new detection rules?

Add new questions in `build_analysis_questions()`:

```python
{
    "id": "review_length",
    "type": "noul",
    "instructions": "Is this review unusually short (1-2 words)?",
    "criteria": {
        "yes": "Very short review",
        "no": "Normal length review"
    }
}
```

Then process the result in `analyze_review()`.

### Can I batch process thousands of reviews?

Yes. The implementation handles sequential processing safely. For parallel:

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(analyze_review, reviews))
```

## Next Steps

1. ✅ Run `quick_start.py` to verify setup
2. 📖 Read `ARCHITECTURE.md` to understand the design
3. 🔧 Customize dimensions and thresholds for your domain
4. 📊 Connect your Google Maps data source
5. ✔️ Validate results on labeled fake/authentic reviews

## Troubleshooting

**"BEATAPI_API_KEY not set"**
```bash
export BEATAPI_API_KEY="your_key_here"
python quick_start.py
```

**"API Error: 401"**
- Check your API key is correct
- Verify it's not expired or revoked at beatapi.io

**"API Error: 429"**
- Rate limit hit (free tier has limits)
- Wait a moment and retry
- Check BeatAPI pricing for higher quotas

**"Connection timeout"**
- BeatAPI servers may be temporarily down
- Check https://beatapi.io status
- Try again in a few moments

## Support & Documentation

- **BeatAPI Docs**: https://beatapi.io/docs
- **TypeSafe Docs**: https://docs.typesafe.ai
- **Architecture Details**: See `ARCHITECTURE.md` in this repo
- **Full Implementation**: See `review_analyzer.py` (Python) or `review-analyzer.ts` (TypeScript)

---

Ready? Start with:
```bash
export BEATAPI_API_KEY="your_key"
python quick_start.py
```
