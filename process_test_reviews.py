#!/usr/bin/env python3
"""
Process test reviews from test_reviews.txt
Simulates what paste_reviews_manual.py does.
"""

import json
import re
from datetime import datetime, timedelta


def parse_review_text(review_str: str):
    """Parse a review in Google Maps format."""
    review_str = review_str.strip()

    # Extract rating
    rating_match = re.search(r'(\d+)\s*(?:stars?|★)', review_str)
    rating = int(rating_match.group(1)) if rating_match else 5

    # Extract name
    name_match = re.search(r'·\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+·', review_str)
    reviewer_name = name_match.group(1) if name_match else "Unknown"

    # Extract time
    time_match = re.search(
        r'(\d+)\s*(second|minute|hour|day|week|month|year)s?\s*ago|just now',
        review_str,
        re.IGNORECASE
    )
    days_since = 0
    if time_match:
        if 'just' in time_match.group(0).lower():
            days_since = 0
        else:
            num = int(time_match.group(1)) if time_match.group(1) else 1
            unit = time_match.group(2).lower() if time_match.group(2) else 'day'

            if unit.startswith('day'):
                days_since = num
            elif unit.startswith('week'):
                days_since = num * 7
            elif unit.startswith('month'):
                days_since = num * 30
            elif unit.startswith('year'):
                days_since = num * 365

    # Extract text (between first bullet and name)
    text_match = re.search(r'★\s+(.+?)\s+·\s+[A-Z]', review_str)
    if text_match:
        text = text_match.group(1)
    else:
        text = review_str

    text = text.strip()

    review_date = (datetime.now() - timedelta(days=days_since)).isoformat()

    return {
        "id": f"test_{hash(text) % 10000}",
        "rating": rating,
        "text": text,
        "metadata": {
            "reviewer_name": reviewer_name,
            "reviewer_account_age_days": 365,
            "review_date": review_date,
            "days_since_review": days_since,
            "reviewer_review_count": 1,
            "reviewer_avg_rating": float(rating),
        }
    }


def main():
    print("=" * 60)
    print("Processing Test Reviews")
    print("=" * 60)
    print()

    # Read test reviews
    with open("test_reviews.txt") as f:
        lines = [line.strip() for line in f if line.strip()]

    print(f"Found {len(lines)} reviews in test_reviews.txt\n")

    reviews = []
    for i, line in enumerate(lines, 1):
        print(f"Review #{i}:")
        parsed = parse_review_text(line)
        reviews.append(parsed)

        print(f"  Rating: {parsed['rating']}★")
        print(f"  Reviewer: {parsed['metadata']['reviewer_name']}")
        print(f"  Days since: {parsed['metadata']['days_since_review']}")
        print(f"  Text: {parsed['text'][:60]}...")
        print()

    # Save
    with open("gmaps_reviews.json", "w") as f:
        json.dump(reviews, f, indent=2)

    print("=" * 60)
    print(f"✓ Saved {len(reviews)} reviews to gmaps_reviews.json")
    print("=" * 60)
    print()
    print("Next: Analyze with TypeSafe")
    print("  export BEATAPI_API_KEY='sk-xxxxx...'")
    print("  python analyze_gmaps.py")


if __name__ == "__main__":
    main()
