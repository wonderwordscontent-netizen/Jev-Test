#!/usr/bin/env python3
"""
Fetch Google Maps reviews and format for TypeSafe analysis.

Setup:
1. Get Google Maps API key from https://console.cloud.google.com
2. Find your Place ID at https://developers.google.com/maps/documentation/places/web-service/overview
3. Set environment variables:
   export GOOGLE_MAPS_API_KEY="your_api_key"
   export GOOGLE_MAPS_PLACE_ID="your_place_id"
4. Run: python fetch_gmaps_reviews.py
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import List, TypedDict

GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
GOOGLE_MAPS_PLACE_ID = os.environ.get("GOOGLE_MAPS_PLACE_ID")

# Expected review format for TypeSafe analyzer
class ReviewForAnalysis(TypedDict):
    id: str
    rating: int
    text: str
    metadata: dict


def fetch_gmaps_reviews(place_id: str, api_key: str) -> List[dict]:
    """
    Fetch reviews from Google Maps Places API.

    Note: Free tier returns limited reviews. Paid tier has higher limits.
    """
    url = "https://maps.googleapis.com/maps/api/place/details/json"

    params = {
        "place_id": place_id,
        "fields": "reviews,name,rating",
        "key": api_key,
        "language": "en"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "OK":
            print(f"API Error: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
            return []

        result = data.get("result", {})
        reviews = result.get("reviews", [])
        place_name = result.get("name", "Unknown Place")
        place_rating = result.get("rating", 0)

        print(f"✓ Fetched {len(reviews)} reviews from '{place_name}' (avg rating: {place_rating})")

        return reviews

    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch reviews: {e}")
        return []


def convert_to_analyzer_format(gmaps_reviews: List[dict]) -> List[ReviewForAnalysis]:
    """
    Convert Google Maps reviews to TypeSafe analyzer format.
    """
    formatted = []
    current_date = datetime.now()

    for review in gmaps_reviews:
        # Extract data from Google Maps response
        author = review.get("author_name", "Unknown")
        rating = review.get("rating", 0)
        text = review.get("text", "")
        time = review.get("time", 0)  # Unix timestamp
        review_count = review.get("review_count", 0)  # Author's total reviews
        profile_photo = review.get("profile_photo_url", "")
        relative_time = review.get("relative_time_description", "")

        # Calculate days since review
        review_date = datetime.fromtimestamp(time) if time else current_date
        days_since = (current_date - review_date).days

        # Estimate account age (approximation based on review count and time)
        # If user has 10 reviews over 2 years, estimate ~73 days per review
        if review_count > 0 and time > 0:
            days_between_reviews = (current_date - review_date).days / max(review_count, 1)
            estimated_account_age = review_count * days_between_reviews
        else:
            estimated_account_age = days_since  # If only 1 review, use review age as proxy

        # Get average rating (Google Maps doesn't provide this, so we use the review's rating)
        avg_rating = rating

        formatted_review = {
            "id": f"gmaps_{time}_{hash(author) % 10000}",  # Unique ID
            "rating": rating,
            "text": text,
            "metadata": {
                "reviewer_name": author,
                "reviewer_account_age_days": int(max(estimated_account_age, 1)),
                "review_date": review_date.isoformat(),
                "days_since_review": days_since,
                "reviewer_review_count": review_count,
                "reviewer_avg_rating": avg_rating,
            }
        }
        formatted.append(formatted_review)

    return formatted


def main():
    print("=" * 60)
    print("Google Maps Review Fetcher")
    print("=" * 60)

    if not GOOGLE_MAPS_API_KEY or not GOOGLE_MAPS_PLACE_ID:
        print("❌ Missing credentials!")
        print("\nSet these environment variables:")
        print("  export GOOGLE_MAPS_API_KEY='your_api_key'")
        print("  export GOOGLE_MAPS_PLACE_ID='your_place_id'")
        print("\nHow to get them:")
        print("  1. API Key: https://console.cloud.google.com")
        print("  2. Place ID: https://developers.google.com/maps/documentation/places")
        return

    print(f"✓ Using Place ID: {GOOGLE_MAPS_PLACE_ID}")
    print(f"✓ Using API Key: {GOOGLE_MAPS_API_KEY[:20]}...\n")

    # Fetch from Google Maps
    print("Fetching reviews from Google Maps...")
    gmaps_reviews = fetch_gmaps_reviews(GOOGLE_MAPS_PLACE_ID, GOOGLE_MAPS_API_KEY)

    if not gmaps_reviews:
        print("No reviews found. Check your Place ID and API key.")
        return

    # Convert to analyzer format
    print(f"\nConverting {len(gmaps_reviews)} reviews to analyzer format...")
    formatted_reviews = convert_to_analyzer_format(gmaps_reviews)

    # Save to file
    output_file = "gmaps_reviews.json"
    with open(output_file, "w") as f:
        json.dump(formatted_reviews, f, indent=2)

    print(f"✓ Saved {len(formatted_reviews)} reviews to {output_file}")

    # Show sample
    if formatted_reviews:
        print("\nSample review:")
        sample = formatted_reviews[0]
        print(f"  ID: {sample['id']}")
        print(f"  Rating: {sample['rating']}★")
        print(f"  Text: {sample['text'][:80]}...")
        print(f"  Reviewer: {sample['metadata']['reviewer_name']}")
        print(f"  Account age: {sample['metadata']['reviewer_account_age_days']} days")
        print(f"  Days since review: {sample['metadata']['days_since_review']}")

    print("\n" + "=" * 60)
    print("Next steps:")
    print("  1. Review gmaps_reviews.json to verify data")
    print("  2. Run: python analyze_gmaps.py")
    print("  3. Check results in gmaps_analysis_report.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
