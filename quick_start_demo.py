#!/usr/bin/env python3
"""
Demo version - Shows how the analyzer works with MOCK data
(doesn't require API key or network access)
"""

import json
from datetime import datetime, timedelta

# Mock API responses simulating what Jev would return
MOCK_RESPONSES = {
    "review_001": {
        "language_authenticity": {
            "level": 4,
            "confidence": 0.89,
            "reasoning": "Generic phrasing, repetitive patterns"
        },
        "specific_detail_level": {
            "value": "no",
            "confidence": 0.91,
            "reasoning": "No specific details provided"
        },
        "common_spam_phrases": {
            "value": "no",
            "confidence": 0.88,
            "reasoning": "No spam indicators detected"
        }
    },
    "review_002": {
        "language_authenticity": {
            "level": 1,
            "confidence": 0.91,
            "reasoning": "Natural language with specific details and unique phrasing"
        },
        "specific_detail_level": {
            "value": "yes",
            "confidence": 0.93,
            "reasoning": "Multiple specific details: grilled salmon, staff name Sarah, timing info"
        },
        "common_spam_phrases": {
            "value": "no",
            "confidence": 0.89,
            "reasoning": "No promotional or spam language detected"
        }
    },
    "review_003": {
        "language_authenticity": {
            "level": 5,
            "confidence": 0.92,
            "reasoning": "Clear signs of generation, generic templates"
        },
        "specific_detail_level": {
            "value": "no",
            "confidence": 0.91,
            "reasoning": "Completely generic, no verifiable details"
        },
        "common_spam_phrases": {
            "value": "yes",
            "confidence": 0.90,
            "reasoning": "Contains 'MUST VISIT', promo code reference, urgency language"
        }
    }
}

# Sample reviews
reviews = [
    {
        "id": "review_001",
        "rating": 5,
        "text": "Amazing service! The staff was incredibly helpful and the food was delicious. Highly recommend!",
        "reviewer": "John D.",
        "account_age_days": 2,
        "review_date": (datetime.now() - timedelta(days=1)).isoformat(),
        "review_count": 1,
        "avg_rating": 5.0,
    },
    {
        "id": "review_002",
        "rating": 5,
        "text": "Had lunch here with my family. The grilled salmon was perfectly cooked, chef knew exactly how to season it. Waitress Sarah remembered our drink order without asking. Will definitely come back next Thursday.",
        "reviewer": "Maria Garcia",
        "account_age_days": 1250,
        "review_date": (datetime.now() - timedelta(days=3)).isoformat(),
        "review_count": 47,
        "avg_rating": 4.1,
    },
    {
        "id": "review_003",
        "rating": 5,
        "text": "MUST VISIT! Click here for promo code SAVE20. Great experience, 5 stars always!",
        "reviewer": "Mark S.",
        "account_age_days": 5,
        "review_date": (datetime.now() - timedelta(days=2)).isoformat(),
        "review_count": 3,
        "avg_rating": 5.0,
    },
]


def analyze_single_review_mock(review):
    """Analyze using MOCK data (no API call)"""

    mock_response = MOCK_RESPONSES.get(review["id"], {})
    scores = []

    print(f"\n📊 Analyzing review {review['id']}...")
    print(f"   Rating: {review['rating']}★ | Account age: {review['account_age_days']} days")

    # Language authenticity
    if "language_authenticity" in mock_response:
        result = mock_response["language_authenticity"]
        level = result.get("level", 2)
        confidence = result.get("confidence", 0.5)
        suspicion = level * 20
        scores.append(suspicion)
        print(f"   ✓ Language Authenticity: Level {level} (suspicion: {suspicion}, confidence: {confidence:.2f})")

    # Specific details
    if "specific_detail_level" in mock_response:
        result = mock_response["specific_detail_level"]
        value = result.get("value")
        confidence = result.get("confidence", 0.5)
        suspicion = 0 if value == "yes" else 60
        scores.append(suspicion)
        print(f"   ✓ Has Specific Details: {value} (suspicion: {suspicion}, confidence: {confidence:.2f})")

    # Spam phrases
    if "common_spam_phrases" in mock_response:
        result = mock_response["common_spam_phrases"]
        value = result.get("value")
        confidence = result.get("confidence", 0.5)
        suspicion = 70 if value == "yes" else 0
        scores.append(suspicion)
        print(f"   ✓ Has Spam Phrases: {value} (suspicion: {suspicion}, confidence: {confidence:.2f})")

    # Overall
    if scores:
        overall_suspicion = int(sum(scores) / len(scores))
    else:
        overall_suspicion = 0

    is_fake = overall_suspicion > 60

    print(f"\n   🎯 Overall Suspicion Score: {overall_suspicion}/100")
    if is_fake:
        print(f"   ⚠️  FLAGGED AS LIKELY FAKE")
    else:
        print(f"   ✅ Appears authentic")

    return {
        "review_id": review["id"],
        "suspicion_score": overall_suspicion,
        "is_likely_fake": is_fake,
    }


def main():
    print("=" * 60)
    print("TypeSafe Review Fake Detection - DEMO (Mock Data)")
    print("=" * 60)
    print("(This demo uses simulated Jev responses - no API calls)")
    print("(Run on local machine with real API for actual analysis)\n")

    results = []
    for review in reviews:
        result = analyze_single_review_mock(review)
        results.append(result)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total = len(results)
    fake_count = sum(1 for r in results if r["is_likely_fake"])

    print(f"Total reviews analyzed: {total}")
    print(f"Flagged as fake: {fake_count} ({100*fake_count/total:.1f}%)")

    print("\nDetailed Results:")
    for r in results:
        status = "🚩 FAKE" if r["is_likely_fake"] else "✅ OK"
        print(f"  {r['review_id']}: {r['suspicion_score']}/100 - {status}")

    print("\n" + "=" * 60)
    print("INTERPRETATION")
    print("=" * 60)
    print("""
Review 001: Generic language (Level 4), no specific details → SUSPICIOUS
Review 002: Natural phrasing, specific details (staff name), established account → AUTHENTIC
Review 003: Generic + spam phrases (promo code, MUST VISIT) → DEFINITELY FAKE

The System One model (Jev) analyzes 3 key dimensions:
1. Language Authenticity: Detects templated/robotic text
2. Specific Details: Genuine reviews mention concrete details
3. Spam Phrases: Catches promotional language

Results are ranked by suspicion score and recency for action.
    """)

    print("\n✓ Demo complete!")
    print("\n📌 To run with REAL TypeSafe API on your machine:")
    print("   1. Clone the repo")
    print("   2. Get API key from https://beatapi.io")
    print("   3. Run: export BEATAPI_API_KEY='your_key' && python quick_start.py")


if __name__ == "__main__":
    main()
