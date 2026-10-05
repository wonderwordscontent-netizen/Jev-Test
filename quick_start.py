#!/usr/bin/env python3
"""
Quick start example for TypeSafe review analysis using BeatAPI.
Run this to test the integration immediately.

Setup:
1. Get API key from https://beatapi.io
2. Set environment variable: export BEATAPI_API_KEY="your_key"
3. Run: python quick_start.py
"""

import os
import json
import requests
from datetime import datetime, timedelta

# Configuration
BEATAPI_API_URL = "https://api.beatapi.io/v1/systemone"
BEATAPI_API_KEY = os.environ.get("BEATAPI_API_KEY")

if not BEATAPI_API_KEY:
    print("❌ Error: BEATAPI_API_KEY environment variable not set")
    print("Set it with: export BEATAPI_API_KEY='your_api_key_here'")
    exit(1)

print("✓ API Key configured")
print(f"✓ Using endpoint: {BEATAPI_API_URL}")

# Sample reviews to analyze
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


def analyze_single_review(review):
    """Analyze a single review using TypeSafe/Jev"""

    days_since_review = (
        datetime.now() - datetime.fromisoformat(review["review_date"])
    ).days

    state = {
        "review": {
            "id": review["id"],
            "rating": review["rating"],
            "text": review["text"],
            "date": review["review_date"],
        },
        "reviewer": {
            "name": review["reviewer"],
            "account_age_days": review["account_age_days"],
            "total_reviews_written": review["review_count"],
            "average_rating_given": review["avg_rating"],
        },
        "context": {"days_since_review": days_since_review},
    }

    questions = {
        "language_authenticity": {
            "type": "score",
            "instructions": "Rate how authentic and natural the review text is. Look for generic phrases, repetitive patterns, unnatural language flow, or signs of automation.",
            "criteria": [
                "Highly authentic: Natural language with specific details and unique phrasing",
                "Mostly authentic: Genuine feel with minor generic elements",
                "Somewhat suspicious: Mix of natural and generic language, odd phrasing patterns",
                "Highly suspicious: Generic templates, repetitive phrases, unnatural flow",
                "Obviously inauthentic: Clear signs of generation or copy-paste",
            ],
        },
        "specific_detail_level": {
            "type": "noul",
            "instructions": "Does this review contain specific, verifiable details about the product/service (names of staff, specific menu items, particular experiences)?",
            "criteria": {
                "yes": "Review contains multiple specific, contextual details",
                "no": "Review is generic or vague without specific examples",
            },
        },
        "common_spam_phrases": {
            "type": "noul",
            "instructions": "Does this review contain common spam/fake review indicators like: call-to-action phrases, promotional language, links/contact info, urgency language?",
            "criteria": {
                "yes": "Contains spam indicators or promotional language",
                "no": "No obvious spam or promotional phrases detected",
            },
        },
    }

    payload = {"model": "jev-1.13-free", "state": state, "questions": questions}

    headers = {
        "Authorization": f"Bearer {BEATAPI_API_KEY}",
        "Content-Type": "application/json",
    }

    print(f"\n📊 Analyzing review {review['id']}...")
    print(f"   Rating: {review['rating']}★ | Account age: {review['account_age_days']} days")

    try:
        response = requests.post(
            BEATAPI_API_URL, json=payload, headers=headers, timeout=30
        )
        response.raise_for_status()
        result = response.json()

        # Extract and display results
        scores = []

        if "language_authenticity" in result:
            lang_result = result["language_authenticity"]
            level = lang_result.get("level", 2)
            confidence = lang_result.get("confidence", 0.5)
            suspicion = level * 20
            scores.append(suspicion)
            print(f"   ✓ Language Authenticity: Level {level} (suspicion: {suspicion}, confidence: {confidence:.2f})")

        if "specific_detail_level" in result:
            detail_result = result["specific_detail_level"]
            value = detail_result.get("value")
            confidence = detail_result.get("confidence", 0.5)
            suspicion = 0 if value == "yes" else 60
            scores.append(suspicion)
            print(f"   ✓ Has Specific Details: {value} (suspicion: {suspicion}, confidence: {confidence:.2f})")

        if "common_spam_phrases" in result:
            spam_result = result["common_spam_phrases"]
            value = spam_result.get("value")
            confidence = spam_result.get("confidence", 0.5)
            suspicion = 70 if value == "yes" else 0
            scores.append(suspicion)
            print(f"   ✓ Has Spam Phrases: {value} (suspicion: {suspicion}, confidence: {confidence:.2f})")

        # Calculate overall suspicion
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
            "raw_response": result,
        }

    except requests.exceptions.RequestException as e:
        print(f"   ❌ API Error: {e}")
        return None


def main():
    print("=" * 60)
    print("TypeSafe Review Fake Detection - Quick Start")
    print("=" * 60)

    results = []
    for review in reviews:
        result = analyze_single_review(review)
        if result:
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

    print("\n✓ Analysis complete!")
    print("\nNext steps:")
    print("1. Review the results above")
    print("2. Tune the suspicion threshold for your use case")
    print("3. Check ARCHITECTURE.md for customization options")
    print("4. Integrate with your Google Maps data source")


if __name__ == "__main__":
    main()
