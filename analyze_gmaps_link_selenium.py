#!/usr/bin/env python3
"""
Google Maps link analyzer using Selenium (handles JavaScript-loaded reviews).

Install:
  pip install selenium
  Download chromedriver: https://chromedriver.chromium.org/

Usage:
  python analyze_gmaps_link_selenium.py
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import re
import sys

print("=" * 60)
print("Google Maps Review Analyzer (Selenium)")
print("=" * 60)
print()

# Get link from user
link = input("Paste your Google Maps listing link: ").strip()

if not link or "maps" not in link.lower():
    print("❌ Invalid link.")
    sys.exit(1)

print("\n📥 Opening browser and fetching reviews...")
print("⏳ This takes 10-20 seconds. Please wait...\n")

try:
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    # You can add --headless to run without opening browser window
    # chrome_options.add_argument("--headless")

    # Try to find chromedriver
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"❌ Chrome/Chromedriver not found: {e}")
        print("\nTo fix:")
        print("1. Download chromedriver from: https://chromedriver.chromium.org/")
        print("2. Add it to your PATH or same folder as this script")
        print("3. Or install via: pip install webdriver-manager")
        sys.exit(1)

    # Open the link
    print("Opening Google Maps...")
    driver.get(link)

    # Wait for reviews to load
    print("Waiting for reviews to load...")
    wait = WebDriverWait(driver, 20)

    try:
        # Wait for review elements to appear
        wait.until(EC.presence_of_all_elements_located((By.XPATH, "//*[contains(@data-review-id, '')]")))
    except:
        # Try alternative selectors
        time.sleep(5)

    # Scroll to load more reviews
    print("Scrolling to load reviews...")
    for _ in range(5):
        driver.execute_script("window.scrollBy(0, 500)")
        time.sleep(2)

    # Extract reviews
    print("Extracting reviews...\n")

    reviews = []

    # Try multiple selectors
    selectors = [
        (By.XPATH, "//*[@data-review-id]"),
        (By.XPATH, "//div[@role='article']"),
        (By.CLASS_NAME, "review")
    ]

    review_elements = []
    for by, selector in selectors:
        try:
            review_elements = driver.find_elements(by, selector)
            if review_elements:
                print(f"✓ Found {len(review_elements)} reviews\n")
                break
        except:
            continue

    if not review_elements:
        print("❌ No reviews found on the page.")
        driver.quit()
        sys.exit(1)

    # Parse reviews
    for i, element in enumerate(review_elements[:100]):  # Limit to 100
        try:
            text = element.text

            # Extract rating
            rating = 5
            rating_match = re.search(r'(\d+)\s*(?:star|★)', text, re.IGNORECASE)
            if rating_match:
                rating = int(rating_match.group(1))

            if len(text) > 20:
                reviews.append({
                    "id": f"review_{i+1}",
                    "rating": rating,
                    "text": text[:300],
                })
        except:
            continue

    driver.quit()

    if not reviews:
        print("❌ Could not parse any reviews.")
        sys.exit(1)

    # Show results
    print("=" * 60)
    print(f"FOUND {len(reviews)} REVIEWS")
    print("=" * 60)
    print()

    for i, review in enumerate(reviews[:10], 1):  # Show first 10
        stars = "★" * review['rating'] + "☆" * (5 - review['rating'])
        print(f"{i}. {stars}")
        print(f"   {review['text'][:80]}...")
        print()

    if len(reviews) > 10:
        print(f"... and {len(reviews) - 10} more reviews\n")

    print("=" * 60)
    print(f"✅ Successfully extracted {len(reviews)} reviews!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Copy reviews from above")
    print("2. Paste into web_app.py")
    print("3. Or run: python quick_start_demo.py to see analysis")
    print()

except Exception as e:
    print(f"❌ Error: {e}")
    try:
        driver.quit()
    except:
        pass
    sys.exit(1)
