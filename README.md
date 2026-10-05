# TypeSafe Google Maps Review Analysis

Detect fake and spammy reviews using TypeSafe's **Jev** System One model. This solution uses **composite scoring** to analyze multiple suspicion indicators independently and rank reviews by authenticity.

## Architecture

### Pattern: Composite Scoring + Verification

The solution implements the TypeSafe pattern for "turning judgments into reusable data":

1. **Multiple independent judgments**: Each review is assessed on 5 dimensions simultaneously
2. **Parallel questions**: TypeSafe runs all questions in parallel (they can't see each other's answers)
3. **Scoring dimensions**:
   - **Language Authenticity** (Score): Detects generic, robotic, or template-like language
   - **Rating-Text Alignment** (Score): Identifies mismatches (5-star complaints, 1-star praise)
   - **Reviewer Authenticity** (Score): Flags new accounts and unnatural review patterns
   - **Specific Detail Level** (Noul): Rewards concrete, verifiable details
   - **Common Spam Phrases** (Noul): Detects promotional language and spam indicators

4. **Composition**: Scores are aggregated into an overall suspicion ranking (0-100)
5. **Prioritization**: Results sorted by suspicion score, then by recency

## Key TypeSafe Concepts Used

### Primitives

- **Score**: Grades a review on a 5-level scale, returning the selected level and confidence
  - Used for: language authenticity, rating alignment, reviewer authenticity
  
- **Noul**: Binary yes/no judgment with probability
  - Used for: specific details presence, spam phrase detection

### State

Complete review context sent to Jev:
- Review content (rating, text, date)
- Reviewer profile (account age, review count, average rating)
- Analysis context (days since review)

### Questions

Each question includes:
- `instructions`: Clear direction for the judgment
- `criteria`: Concrete descriptions of each level
- `id`: For identifying results (not sent to model)

### Confidence

The model returns confidence for each judgment:
- Used to weight dimension scores
- Overall suspicion requires both high score AND high confidence
- Thresholds (>60 score, >0.5 confidence) are data-dependent; adjust based on your domain

## Setup

### Get an API Key

1. Sign up for a free BeatAPI account at https://beatapi.io
2. Get your `BEATAPI_API_KEY` from the dashboard
3. The `jev-1.13-free` model is included with the free tier

### Python Installation

```bash
pip install -r requirements.txt
```

Set environment variable:
```bash
export BEATAPI_API_KEY="your_api_key_here"
```

### TypeScript/Node Installation

```bash
npm install
```

Set environment variable:
```bash
export BEATAPI_API_KEY="your_api_key_here"
```

## Usage

### Python

```python
from review_analyzer import analyze_reviews_batch, generate_report

# Load your reviews
reviews = [
    {
        "id": "review_123",
        "rating": 5,
        "text": "Great service!",
        "metadata": {
            "reviewer_name": "John Doe",
            "reviewer_account_age_days": 500,
            "review_date": "2024-10-04",
            "days_since_review": 1,
            "reviewer_review_count": 15,
            "reviewer_avg_rating": 4.2
        }
    },
    # ... more reviews
]

# Analyze in batch
analyses = analyze_reviews_batch(reviews)
report = generate_report(analyses)

# Results sorted by suspicion (newest first)
for analysis in analyses:
    print(f"Review {analysis.review_id}: {analysis.overall_suspicion_score}/100 (fake: {analysis.is_likely_fake})")
```

### TypeScript

```typescript
import { analyzeReviewsBatch, generateReport } from './review-analyzer';

const reviews = [ /* ... */ ];

const analyses = await analyzeReviewsBatch(reviews);
const report = generateReport(analyses);

console.log(report);
```

## Output Structure

### Analysis Result

```json
{
  "review_id": "review_001",
  "overall_suspicion_score": 75,
  "overall_confidence": 0.87,
  "is_likely_fake": true,
  "days_since_review": 1,
  "dimensions": [
    {
      "dimension": "language_authenticity",
      "score": 85,
      "confidence": 0.92,
      "evidence": "Generic phrasing, repetitive patterns"
    },
    // ... more dimensions
  ]
}
```

### Report Summary

```json
{
  "summary": {
    "total_reviews_analyzed": 100,
    "likely_fake_reviews": 12,
    "likely_fake_percentage": 12.0,
    "suspicious_reviews": 23,
    "average_confidence": 0.81
  },
  "dimension_analysis": {
    "language_authenticity": {
      "avg_score": 42,
      "high_suspicion_count": 8
    },
    // ... analysis per dimension
  },
  "detailed_results": [ /* all analyses */ ]
}
```

## Interpreting Results

### Suspicion Score (0-100)

- **0-30**: Likely authentic
- **30-60**: Mixed signals, worth reviewing
- **60-100**: Highly suspicious

### Confidence (0-1)

- **>0.8**: High confidence in the judgment
- **0.5-0.8**: Moderate confidence
- **<0.5**: Low confidence (uncertain; use caution)

### Decision Logic

A review is flagged as `is_likely_fake = true` when:
- `overall_suspicion_score > 60` AND
- `overall_confidence > 0.5`

Adjust these thresholds based on your tolerance for false positives vs. false negatives.

## Design Decisions

### Why TypeSafe for This?

1. **Structured output**: Returns typed judgments, not generated text
2. **Speed**: System One models are fast (good for bulk analysis)
3. **Composability**: Multiple independent dimensions combined via code
4. **Confidence calibration**: Built for decision-making with probabilities
5. **Cost efficiency**: Smaller model, lower latency than large reasoning models

### Parallel Questions

All 5 dimensions are assessed in a single API call:
- Questions don't see each other's answers
- Prevents cascading errors
- Enables truly independent judgment

### Recency Prioritization

Results sorted by:
1. Suspicion score (highest first)
2. Recency (fewest days since review)

This surfaces the most concerning recent activity.

## Customization

### Adding New Dimensions

Edit `build_analysis_questions()` to add new Score or Noul questions. Examples:

- Photo/video attachment presence (Noul)
- Response sentiment (Score)
- Reviewer name authenticity (Noul)
- Review length appropriateness (Score)

### Adjusting Scoring

Modify how dimension scores map to suspicion (0-100):
- Change multipliers (e.g., `level * 20`)
- Adjust confidence weighting
- Implement domain-specific normalization

### Threshold Tuning

Test thresholds on labeled data:
- Collect reviews you've manually verified as fake/authentic
- Evaluate precision and recall at different thresholds
- Adjust `is_likely_fake` logic to match your accuracy targets

## TypeSafe Documentation

For detailed guidance, read:
- [System One Concepts](https://docs.typesafe.ai/concepts/system-one.md)
- [How to Build with System One](https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md)
- [Composite Scoring Pattern](https://docs.typesafe.ai/patterns/composite-scoring.md)
- [Score Primitive](https://docs.typesafe.ai/primitives/score.md)
- [Noul Primitive](https://docs.typesafe.ai/primitives/noul.md)
- [Confidence Guidance](https://docs.typesafe.ai/confidence.md)
- [API Reference](https://docs.typesafe.ai/api.md)
- [Python SDK](https://docs.typesafe.ai/sdk/python.md)
- [JavaScript SDK](https://docs.typesafe.ai/sdk/javascript.md)

## Next Steps

1. Set up your TypeSafe API key and environment
2. Run the example with sample reviews
3. Integrate with your Google Maps data source
4. Validate results against manually labeled data
5. Adjust thresholds and dimensions based on your findings
6. Deploy to production with monitoring

## License

MIT
