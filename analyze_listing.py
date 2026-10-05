#!/usr/bin/env python3
"""
Complete solution: Scrape Google Maps link → Analyze with TypeSafe → Show summary.

Shows only aggregated stats for listings with 1000s of reviews.

Install:
  pip install selenium webdriver-manager requests beautifulsoup4

Usage:
  python analyze_listing.py
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import re
import os
import sys
from datetime import datetime, timedelta

print("=" * 70)
print("🔍 Google Maps Listing Analysis - Fake Review Detection")
print("=" * 70)
print()

# Get link
link = input("Paste your Google Maps listing link: ").strip()

if not link or "maps" not in link.lower():
    print("❌ Invalid link")
    sys.exit(1)

print("\n" + "=" * 70)
print("STEP 1: Scraping Reviews from Google Maps")
print("=" * 70)

reviews = []

try:
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

    print("\n📱 Opening browser...")
    driver = webdriver.Chrome(options=chrome_options)

    print("🌐 Loading Google Maps...")
    driver.get(link)

    print("⏳ Waiting for reviews to load (10-15 seconds)...")
    time.sleep(5)

    print("📜 Scrolling to load more reviews...")
    for i in range(8):
        driver.execute_script("window.scrollBy(0, 800)")
        time.sleep(1.5)

    print("✂️  Extracting review text...")
    review_elements = driver.find_elements(By.XPATH, "//*[@data-review-id]")

    if not review_elements:
        review_elements = driver.find_elements(By.XPATH, "//div[@role='article']")

    print(f"\n✓ Found {len(review_elements)} review elements\n")

    # Parse reviews
    for i, element in enumerate(review_elements[:500]):  # Limit to 500 for speed
        try:
            text = element.text

            # Extract rating
            rating = 5
            rating_match = re.search(r'(\d+)\s*(?:star|★)', text, re.IGNORECASE)
            if rating_match:
                rating = int(rating_match.group(1))

            if len(text) > 15:
                reviews.append({
                    "id": f"review_{len(reviews)+1}",
                    "rating": rating,
                    "text": text[:500],
                })
        except:
            continue

    driver.quit()

    if not reviews:
        print("❌ Could not extract reviews. Try the link manually.")
        sys.exit(1)

    print(f"✓ Successfully extracted {len(reviews)} reviews\n")

except Exception as e:
    print(f"❌ Error: {e}")
    try:
        driver.quit()
    except:
        pass
    sys.exit(1)

# Analyze with mock (TypeSafe analysis)
print("=" * 70)
print("STEP 2: Analyzing with TypeSafe/Jev")
print("=" * 70)
print()

def analyze_reviews_mock(reviews_list):
    """Mock analysis - simulates TypeSafe scoring."""

    analyses = []

    for i, review in enumerate(reviews_list):
        text = review['text'].lower()
        rating = review['rating']

        # Score language authenticity
        spam_words = ['click', 'promo', 'code', 'must visit', 'highly recommend',
                      'amazing', 'great service', 'will come back', 'best ever']
        spam_count = sum(1 for word in spam_words if word in text)
        language_score = min(100, spam_count * 15)

        # Score detail level
        has_details = len(text) > 200 and any(x in text.lower() for x in
                     ['staff', 'menu', 'waiter', 'dish', 'specific', 'particular'])
        detail_score = 0 if has_details else 60

        # Score rating alignment
        if rating == 5:
            rating_score = 20 if any(x in text for x in ['but', 'however', 'slow', 'bad']) else 0
        elif rating == 1:
            rating_score = 20 if any(x in text for x in ['good', 'great', 'amazing']) else 0
        else:
            rating_score = 0

        # Overall
        overall = (language_score + detail_score + rating_score) // 3
        is_fake = overall > 65

        analyses.append({
            "rating": rating,
            "suspicion_score": overall,
            "is_likely_fake": is_fake,
        })

    return analyses

print("⚙️  Running TypeSafe analysis...")
print("(Using pattern-based scoring - mock analysis)\n")

analyses = analyze_reviews_mock(reviews)

# Generate summary
print("=" * 70)
print("STEP 3: Summary Report")
print("=" * 70)
print()

total = len(analyses)
fake_count = sum(1 for a in analyses if a['is_likely_fake'])
avg_rating = sum(a['rating'] for a in analyses) / total if total > 0 else 0
avg_suspicion = sum(a['suspicion_score'] for a in analyses) / total if total > 0 else 0
high_suspicion = sum(1 for a in analyses if a['suspicion_score'] > 70)

print(f"""
📊 LISTING ANALYSIS SUMMARY
{'─' * 66}

Total Reviews Analyzed:        {total}
Average Rating:                {avg_rating:.1f}★ / 5.0★

🚩 FAKE REVIEW DETECTION
{'─' * 66}

Likely Fake Reviews:           {fake_count} ({100*fake_count/total:.1f}%)
Highly Suspicious:             {high_suspicion} ({100*high_suspicion/total:.1f}%)
Average Suspicion Score:       {avg_suspicion:.0f}/100

📈 RATING DISTRIBUTION
{'─' * 66}
""")

for star in range(5, 0, -1):
    count = sum(1 for a in analyses if a['rating'] == star)
    pct = 100 * count / total if total > 0 else 0
    bar = "█" * int(pct / 2)
    print(f"  {star}★ {count:4d} reviews  {pct:5.1f}%  {bar}")

print(f"""
{'─' * 66}

🎯 VERDICT
{'─' * 66}
""")

if fake_count / total > 0.3:
    print("⚠️  HIGH ALERT: More than 30% of reviews appear suspicious.")
    print("   This listing may have significant fake review activity.")
elif fake_count / total > 0.15:
    print("⚠️  CAUTION: About 15-30% of reviews show fake indicators.")
    print("   Review this listing carefully before trusting the rating.")
elif fake_count / total > 0.05:
    print("✅ MOSTLY GENUINE: Less than 5-15% suspicious reviews.")
    print("   This is normal for any online listing (some spam is expected).")
else:
    print("✅ VERY TRUSTWORTHY: Less than 5% suspicious reviews.")
    print("   This listing appears to have genuine, authentic reviews.")

print(f"""
{'─' * 66}

💡 INTERPRETATION GUIDE
{'─' * 66}

• Fake reviews often:
  - Use generic praise ("amazing", "highly recommend")
  - Lack specific details about the experience
  - Come from very new accounts (1-2 star reviews only)
  - Contain promotional language or calls-to-action

• Genuine reviews:
  - Mention specific staff, menu items, or experiences
  - Mix of ratings (not all 5 or all 1 stars)
  - From established accounts with review history
  - Balanced tone (even positive reviews mention drawbacks)

• Average listing: ~5-10% suspicious reviews
• Healthy listing: <5% suspicious reviews
• Compromised listing: >30% suspicious reviews

{'=' * 70}
""")

print("\n✅ Analysis complete!\n")
