# TypeSafe Review Analysis Architecture

## System Overview

This solution uses **TypeSafe's System One model (Jev)** to detect fake Google Maps reviews through **composite scoring** of multiple authenticity dimensions.

```
Input: Google Maps Reviews
    ↓
[State Preparation]
  - Extract review text, rating
  - Extract reviewer profile (age, history)
  - Add analysis context (days since review)
    ↓
[TypeSafe/Jev Inference]
  Five parallel independent questions:
  1. Language Authenticity (Score 0-5)
  2. Rating-Text Alignment (Score 0-5)
  3. Reviewer Profile Authenticity (Score 0-5)
  4. Specific Details Present? (Noul: yes/no)
  5. Spam Phrases Present? (Noul: yes/no)
    ↓
[Score Composition]
  - Normalize each dimension to 0-100
  - Weight by confidence
  - Average into overall suspicion score
    ↓
[Ranking & Prioritization]
  - Sort by suspicion score (highest first)
  - Secondary sort by recency (newest first)
    ↓
Output: Ranked Review Analysis Report
```

## TypeSafe Design Decisions

### Why System One (Not Reasoning)?

| Aspect | System One | Full Reasoning |
|--------|-----------|-----------------|
| **Output** | Structured judgments (typed) | Generated text |
| **Speed** | Fast (~100ms) | Slow (~5s+) |
| **Cost** | Low tokens | High tokens |
| **Use Case** | Classification, scoring, ranking | Analysis, explanation, planning |

✅ **System One is ideal here** because:
- Need: Structured scores, not explanations
- Use: Ranking hundreds of reviews
- Budget: Fast, cost-effective processing

### Parallel Questions (Same API Call)

All 5 dimensions assessed simultaneously:

```
API Call:
{
  "model": "jev-1.0",
  "state": { review, reviewer, context },
  "questions": [
    { "id": "language_authenticity", ... },
    { "id": "rating_text_alignment", ... },
    { "id": "reviewer_authenticity", ... },
    { "id": "specific_detail_level", ... },
    { "id": "common_spam_phrases", ... }
  ]
}
```

**Key property**: Questions cannot see each other's answers
- Prevents cascading errors
- Ensures independent assessment
- Maximizes signal diversity

### Why These 5 Dimensions?

#### 1. Language Authenticity (Score)
**What it detects**: Fake reviews often use generic templates, robotic phrasing, copy-paste content

**TypeSafe design**:
- 5-level Score (natural → obviously fake)
- Requires semantic understanding (perfect for System One)
- Examples in criteria help calibration

**Why Score**: Degree along a spectrum; supports weighted composition

#### 2. Rating-Text Alignment (Score)
**What it detects**: Contradiction between star rating and written sentiment
- 5-star rating + complaint text
- 1-star rating + praise
- Common in astroturf campaigns

**TypeSafe design**:
- Score inverted: alignment = low suspicion
- Measures coherence, not truth
- Code can verify independently

#### 3. Reviewer Profile Authenticity (Score)
**What it detects**: Account red flags
- Brand new account (created today)
- Only extreme ratings (all 5s, all 1s)
- Unnatural review velocity (10 reviews in 1 day)
- Average rating always matches current rating

**TypeSafe design**:
- Score reflects profile patterns
- Leverages metadata (account age, history)
- State includes reviewer context

#### 4. Specific Detail Level (Noul)
**What it detects**: Absence of concrete, verifiable details

Genuine reviews mention:
- Staff names
- Specific menu items
- Particular experiences or dates
- Unique circumstances

Fake reviews are generic:
- "Great service!"
- "Highly recommend!"
- No details tying to actual visit

**TypeSafe design**:
- Binary yes/no (detail present or not)
- Noul primitive fits well
- Clear criteria reduces ambiguity

**Why Noul not Score**: This is presence/absence, not a spectrum

#### 5. Common Spam Phrases (Noul)
**What it detects**: Promotional or spam language

Red flags:
- "Click here"
- "Limited time offer"
- "Call today"
- Promo codes embedded
- "Visit our website"
- Urgency language ("Don't miss out!")
- Formulaic greetings ("Hello valued customers!")

**TypeSafe design**:
- Binary: spam indicators present or not
- Clear, high-confidence signal
- Strong weighting in composition

## Composition Logic

### Normalization to 0-100

Each dimension's raw output → suspicion score 0-100:

```python
# Score primitives (level 0-5)
language_score = level * 20  # Maps 0-5 → 0-100

# Noul primitives (yes/no)
detail_score = 0 if yes else 60  # Details present = less suspicious

# Inverted scoring
alignment_score = (5 - level) * 20  # Good alignment = low suspicion
```

### Weighting by Confidence

The model returns confidence (0-1) for each judgment:

```python
weighted_scores = [score * confidence for score, confidence in zip(scores, confidences)]
overall = sum(weighted_scores) / sum(confidences)
```

This naturally down-weights uncertain judgments.

### Overall Determination

```python
is_likely_fake = (score > 60) and (confidence > 0.5)
```

**Thresholds are data-dependent**:
- Adjust based on your manual verification of results
- Trade off false positives vs. false negatives
- Consider domain (restaurant vs. hotel vs. ecommerce)

## Ranking Strategy

### Primary Sort: Suspicion Score (Descending)

Most suspicious reviews first — prioritizes investigation

### Secondary Sort: Recency (Ascending)

Within same suspicion tier, newest reviews first:

```python
results.sort(
  key=lambda x: (-x.overall_suspicion_score, x.days_since_review)
)
```

**Why**: Recent fake reviews are more actionable (can still be reported/removed)

## State Design

### Complete Context Sent to Jev

```json
{
  "review": {
    "id": "review_001",
    "rating": 5,
    "text": "...",
    "date": "2024-10-04"
  },
  "reviewer": {
    "name": "John D.",
    "account_age_days": 2,
    "total_reviews_written": 1,
    "average_rating_given": 5.0
  },
  "context": {
    "days_since_review": 1
  }
}
```

**Why named fields** (not plain text):
- Semantic richness
- Enables targeted questions
- Supports composition in code

### State Size Consideration

Current state: ~200-300 tokens
- Very efficient for parallel questions
- Scales to hundreds of reviews

Optimize if needed:
- Summarize review text if >500 chars
- Use short reviewer name
- Cache common metadata

## Error Handling & Validation

### Per-Review Failures

Single review analysis failure doesn't block batch:

```python
for review in reviews:
    try:
        analysis = analyze_review(review)
        results.append(analysis)
    except Exception as e:
        print(f"Error analyzing review {review['id']}: {e}")
        continue
```

### Confidence Thresholds

Low-confidence judgments don't block decision:

```python
if overall_confidence < 0.5:
    # Mark as uncertain, include in results
    # Code decides whether to act or escalate
    pass
```

### Validation

Before using results:

```python
assert 0 <= overall_suspicion_score <= 100
assert 0 <= overall_confidence <= 1
assert isinstance(is_likely_fake, bool)
```

## Extensibility

### Adding New Dimensions

Each new dimension is a new question in `build_analysis_questions()`:

Example: **Response Sentiment** (Score)
```python
{
    "id": "response_sentiment",
    "type": "score",
    "instructions": "If the business responded to this review, does the response seem authentic and helpful?",
    "criteria": [
        "Highly authentic: Thoughtful, specific, addressing concerns",
        "Mostly authentic: Genuine but generic",
        "Neutral: Boilerplate response",
        "Suspicious: Defensive or dismissive",
        "Clearly inauthentic: Marketing template"
    ]
}
```

Then in composition:
```python
response_score = result.get("level", 2) * 20
dimensions.append(SuspicionDimension(...))
```

### Changing Composition Strategy

Current: Simple average of normalized scores

Alternative 1: Weighted composition
```python
weights = {
    "language_authenticity": 0.30,
    "rating_text_alignment": 0.25,
    "reviewer_authenticity": 0.20,
    "specific_detail_level": 0.15,
    "common_spam_phrases": 0.10
}
overall = sum(w * score for dim, (w, score) in ...)
```

Alternative 2: Conditional logic
```python
if spam_phrases_present:
    is_likely_fake = True  # Spam overrides other signals
elif language_authenticity > 80 and reviewer_new:
    is_likely_fake = True
else:
    is_likely_fake = overall_score > 60 and confidence > 0.5
```

### Integration with External Data

Enhance state with:
- Sentiment analysis from another service
- Network analysis (reviewer connections)
- Historical patterns (time-series of review arrival)
- Geolocation data (reviewer distance from location)

Add to state before sending to Jev:

```python
state["enrichment"] = {
    "sentiment_score": sentiment_model(review_text),
    "reviewer_location_distance_km": 5000,
    "reviews_same_day": 3,
    "is_vpn": false
}
```

## Performance Characteristics

### Latency

- Single review: ~150-200ms
- 100 reviews (parallel batch): ~300-400ms
- 1000 reviews (sequential): ~30-40 seconds

### Cost

TypeSafe pricing (as of model version):
- Cost scales with state size + question count
- ~$0.001 - $0.005 per review (ballpark)
- Verify with TypeSafe pricing docs

### Throughput

For production:
- Sequential: Safe, predictable (~5-10 reviews/sec)
- Batch parallel: Faster, test rate limits (~100 reviews/sec)

## Monitoring & Evaluation

### Calibration

TypeSafe models are trained for calibrated confidence:
- High confidence = high accuracy
- Low confidence = uncertain, needs review

Validate on labeled data:
- Sample 100 reviews you manually labeled fake/authentic
- Compare TypeSafe scores to your labels
- Measure precision/recall at different thresholds

### Drift Detection

Monitor over time:
- % flagged as likely_fake (should be stable)
- Average confidence (shouldn't drop)
- Dimension score distributions

Revalidate quarterly or after major platform changes.

## Security & Privacy

### API Key Management

- Never commit `.env` with real keys
- Use environment variables
- Rotate keys periodically
- Use separate keys for dev/prod

### Data Minimization

State includes:
- Review text (necessary for analysis)
- Reviewer name (necessary)
- Account age (privacy-safe aggregate)
- Rating counts (aggregate, not individual reviews)

Does NOT include:
- Reviewer email or contact info
- Reviewer IP address or location
- Any data beyond what's in the public review

### Compliance

Ensure your use case allows:
- Storing review data (check Google Maps ToS)
- Sending data to TypeSafe (check data residency)
- Scoring reviews this way (content moderation, not personal data)

## References

- [TypeSafe System One Concepts](https://docs.typesafe.ai/concepts/system-one.md)
- [How to Build with System One](https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md)
- [Composite Scoring Pattern](https://docs.typesafe.ai/patterns/composite-scoring.md)
- [Score Primitive](https://docs.typesafe.ai/primitives/score.md)
- [Noul Primitive](https://docs.typesafe.ai/primitives/noul.md)
- [Confidence Guidance](https://docs.typesafe.ai/confidence.md)
