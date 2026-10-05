#!/usr/bin/env python3
"""
Manually paste Google Maps reviews for testing.

Usage:
1. Open Google Maps listing
2. Copy reviews text (rating + text)
3. Run: python paste_reviews_manual.py
4. Paste reviews one by one
5. Reviews will be saved to gmaps_reviews.json

Example review to paste:
"5 stars · Great coffee and friendly staff! Will come back again. · Sarah M. · 2 weeks ago"

Or just paste the review text and it will prompt for rating.
"""

import json
import re
from datetime import datetime, timedelta
from typing import List, Optional


def parse_review_text(review_str: str) -> Optional[dict]:
    """
    Parse a review string in various formats.

    Supported formats:
    - "5 stars · Great service! · John D. · 2 days ago"
    - "5★ Great service!"
    - "5 Great service! - John D."
    - Just the review text (will prompt for other info)
    """
    review_str = review_str.strip()

    # Try to extract rating with "X stars" or "X★" format
    rating_match = re.search(r'(\d+)\s*(?:stars?|★)', review_str)
    rating = int(rating_match.group(1)) if rating_match else None

    # Try to extract name (usually in quotes or after dash)
    name_match = re.search(r'[""](.+?)[""]|[-–]?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', review_str)
    reviewer_name = None
    if name_match:
        reviewer_name = name_match.group(1) or name_match.group(2)

    # Try to extract relative time
    time_match = re.search(
        r'(\d+)\s*(second|minute|hour|day|week|month|year)s?\s*ago|just now|recently',
        review_str,
        re.IGNORECASE
    )
    days_since = 0
    if time_match:
        if 'just' in time_match.group(0).lower() or 'recently' in time_match.group(0).lower():
            days_since = 0
        else:
            num = int(time_match.group(1)) if time_match.group(1) else 1
            unit = time_match.group(2).lower() if time_match.group(2) else 'day'

            if unit.startswith('second'):
                days_since = 0
            elif unit.startswith('minute'):
                days_since = 0
            elif unit.startswith('hour'):
                days_since = 0
            elif unit.startswith('day'):
                days_since = num
            elif unit.startswith('week'):
                days_since = num * 7
            elif unit.startswith('month'):
                days_since = num * 30
            elif unit.startswith('year'):
                days_since = num * 365

    # Extract main text (remove metadata)
    text = re.sub(r'^\d+\s*(?:stars?|★)\s*·\s*', '', review_str)  # Remove "5 stars · "
    text = re.sub(r'\s*·\s*.*$', '', text)  # Remove everything after last bullet
    text = text.strip()

    if not text or len(text) < 5:
        return None

    return {
        "rating": rating,
        "text": text,
        "reviewer_name": reviewer_name,
        "days_since": days_since
    }


def get_review_interactively(review_num: int) -> Optional[dict]:
    """
    Get review details interactively from user.
    """
    print(f"\n--- Review #{review_num} ---")
    print("Paste review text (or 'q' to finish):")
    print("Format: '5 stars · Great service! · John D. · 2 days ago'")
    print("Or just paste the text and I'll ask for details:")

    text_input = input("> ").strip()

    if text_input.lower() in ['q', 'quit', 'done', 'exit', '']:
        return None

    # Try to parse
    parsed = parse_review_text(text_input)

    if not parsed:
        print("❌ Couldn't parse that review. Try again.")
        return None

    # Prompt for missing fields
    rating = parsed.get("rating")
    if not rating:
        try:
            rating = int(input("Rating (1-5): ").strip())
        except ValueError:
            print("❌ Invalid rating")
            return None

    reviewer_name = parsed.get("reviewer_name") or f"Reviewer_{review_num}"

    days_since = parsed.get("days_since", 0)

    text = parsed.get("text")
    if not text or len(text) < 5:
        print("❌ Review text too short")
        return None

    review_date = (datetime.now() - timedelta(days=days_since)).isoformat()

    return {
        "id": f"gmaps_manual_{review_num}",
        "rating": rating,
        "text": text,
        "metadata": {
            "reviewer_name": reviewer_name,
            "reviewer_account_age_days": 365,  # Default: assume established
            "review_date": review_date,
            "days_since_review": days_since,
            "reviewer_review_count": 1,  # Unknown
            "reviewer_avg_rating": float(rating),
        }
    }


def main():
    print("=" * 60)
    print("Google Maps Review Analyzer - Manual Entry")
    print("=" * 60)
    print()
    print("Paste reviews from Google Maps below.")
    print("Type 'q' or just hit Enter when done.")
    print()

    reviews = []
    review_num = 1

    while True:
        review = get_review_interactively(review_num)

        if review is None:
            break

        reviews.append(review)
        print(f"✓ Saved review #{review_num}")
        print(f"  Rating: {review['rating']}★")
        print(f"  Text: {review['text'][:60]}...")
        print(f"  Reviewer: {review['metadata']['reviewer_name']}")
        print(f"  Days ago: {review['metadata']['days_since_review']}")

        review_num += 1

    if not reviews:
        print("\n❌ No reviews saved.")
        return

    # Save to file
    output_file = "gmaps_reviews.json"
    with open(output_file, "w") as f:
        json.dump(reviews, f, indent=2)

    print()
    print("=" * 60)
    print(f"✓ Saved {len(reviews)} reviews to {output_file}")
    print("=" * 60)
    print()
    print("Next step: Analyze with TypeSafe")
    print("  export BEATAPI_API_KEY='sk-xxxxx...'")
    print("  python analyze_gmaps.py")
    print()


if __name__ == "__main__":
    main()
