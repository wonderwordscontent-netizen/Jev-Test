#!/usr/bin/env python3
"""
Simple script to analyze reviews from a Google Maps link.
No web server needed, no Flask, just direct analysis.

Usage:
  python analyze_gmaps_link.py
  > Paste your Google Maps link
  > See results
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re

print("=" * 60)
print("Google Maps Review Analyzer")
print("=" * 60)
print()

# Get link from user
link = input("Paste your Google Maps listing link: ").strip()

if not link or ("maps" not in link.lower()):
    print("❌ Invalid link. Must be a Google Maps URL.")
    exit(1)

print("\n📥 Fetching reviews from link...")
print("⏳ This may take a moment...\n")

# Scrape reviews
try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    response = requests.get(link, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract reviews
    reviews = []

    # Try multiple selectors
    selectors = ['div[data-review-id]', 'div[role="article"]', 'div.review']
    review_elements = []

    for selector in selectors:
        review_elements = soup.select(selector)
        if review_elements:
            print(f"✓ Found {len(review_elements)} reviews")
            break

    if not review_elements:
        print("❌ No reviews found. The listing may have no reviews or the format changed.")
        exit(1)

    # Parse each review
    for i, element in enumerate(review_elements[:50]):  # Limit to 50
        try:
            text = element.get_text(strip=True)

            # Extract rating
            rating = 5
            rating_match = re.search(r'(\d+)\s*(?:star|★)', text, re.IGNORECASE)
            if rating_match:
                rating = int(rating_match.group(1))

            # Extract name
            name_elem = element.select_one('[data-tooltip]')
            name = name_elem.get('data-tooltip', f'Reviewer {i+1}') if name_elem else f'Reviewer {i+1}'

            if len(text) > 20:
                reviews.append({
                    "id": f"review_{i+1}",
                    "rating": rating,
                    "text": text[:300],
                    "reviewer": name
                })
        except:
            continue

    if not reviews:
        print("❌ Could not parse any reviews from the page.")
        exit(1)

    print(f"✓ Extracted {len(reviews)} reviews\n")

    # Show results
    print("=" * 60)
    print("REVIEWS FOUND")
    print("=" * 60)
    print()

    for i, review in enumerate(reviews, 1):
        stars = "★" * review['rating'] + "☆" * (5 - review['rating'])
        print(f"{i}. {stars} - {review['reviewer']}")
        print(f"   {review['text'][:80]}...")
        print()

    print("=" * 60)
    print(f"✅ Successfully extracted {len(reviews)} reviews!")
    print("=" * 60)
    print()
    print("Save these reviews to analyze with TypeSafe:")
    print()
    print("Option 1: Copy reviews above and paste into web_app.py")
    print("Option 2: Run: python quick_start_demo.py")
    print()

except requests.exceptions.RequestException as e:
    print(f"❌ Failed to fetch the page: {e}")
    print("\nTroubleshooting:")
    print("- Check your internet connection")
    print("- Make sure the link is correct")
    print("- Google may be blocking the request")
    exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
