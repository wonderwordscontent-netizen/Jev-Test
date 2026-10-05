#!/usr/bin/env python3
"""
Extract reviews from a Google Maps listing link without API.

Usage:
1. Open Google Maps and find a listing
2. Copy the link (should be like: https://www.google.com/maps/place/...)
3. Run: python fetch_gmaps_link.py
4. Paste the link when prompted
5. Reviews will be saved to gmaps_reviews.json

Note: Uses web scraping. May need to handle:
- Rate limiting
- Dynamic content loading
- Page structure changes
"""

import json
import re
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse, parse_qs

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


def extract_reviews_from_html(html: str, place_name: str) -> List[dict]:
    """
    Extract reviews from Google Maps HTML using BeautifulSoup.

    Note: Google frequently changes their HTML structure,
    so this may need updates.
    """
    if not REQUESTS_AVAILABLE:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    reviews = []

    # Try multiple selectors as Google changes structure
    review_selectors = [
        'div[data-review-id]',
        'div[role="article"]',
        'div.gws-plugins-hotelbookingreviews__review-item'
    ]

    review_elements = []
    for selector in review_selectors:
        review_elements = soup.select(selector)
        if review_elements:
            print(f"✓ Found {len(review_elements)} reviews using selector: {selector}")
            break

    if not review_elements:
        print("⚠️  Could not find review elements with standard selectors")
        print("   Google Maps may have changed their HTML structure")
        return []

    for i, element in enumerate(review_elements):
        try:
            # Extract review data
            text = element.get_text(strip=True)

            # Try to find rating (1-5 stars)
            rating_elem = element.select_one('span[aria-label*="stars"]')
            if not rating_elem:
                rating_elem = element.select_one('[role="img"][aria-label*="star"]')

            rating = 5  # Default
            if rating_elem:
                aria_label = rating_elem.get('aria-label', '')
                # Extract number from "X stars" format
                match = re.search(r'(\d+)', aria_label)
                if match:
                    rating = int(match.group(1))

            # Extract reviewer name
            name_elem = element.select_one('div.gws-plugins-hotelbookingreviews__review-bit div:first-child')
            if not name_elem:
                name_elem = element.select_one('[data-tooltip] span')

            reviewer_name = name_elem.get_text(strip=True) if name_elem else f"Reviewer_{i}"

            # Extract date
            date_elem = element.select_one('span.gws-plugins-hotelbookingreviews__review-published-date')
            if not date_elem:
                date_elem = element.select_one('.gws-plugins-hotelbookingreviews__review-date')

            date_text = date_elem.get_text(strip=True) if date_elem else "Recently"

            # Parse relative date
            days_since = parse_relative_date(date_text)
            review_date = (datetime.now() - __import__('datetime').timedelta(days=days_since)).isoformat()

            review = {
                "id": f"gmaps_scraped_{len(reviews)}",
                "rating": rating,
                "text": text[:500],  # Limit text length
                "metadata": {
                    "reviewer_name": reviewer_name,
                    "reviewer_account_age_days": 365,  # Default: assume established account
                    "review_date": review_date,
                    "days_since_review": days_since,
                    "reviewer_review_count": 1,  # Unknown from scraping
                    "reviewer_avg_rating": rating,  # Use review rating as proxy
                }
            }

            reviews.append(review)

        except Exception as e:
            print(f"  ⚠️  Error parsing review {i}: {e}")
            continue

    return reviews


def parse_relative_date(date_str: str) -> int:
    """
    Parse Google Maps relative date format.
    Examples: "1 week ago", "2 days ago", "a month ago"
    """
    date_str = date_str.lower().strip()

    if 'week' in date_str:
        match = re.search(r'(\d+)', date_str)
        if match:
            return int(match.group(1)) * 7
        return 7
    elif 'day' in date_str:
        match = re.search(r'(\d+)', date_str)
        if match:
            return int(match.group(1))
        return 1
    elif 'month' in date_str:
        match = re.search(r'(\d+)', date_str)
        if match:
            return int(match.group(1)) * 30
        return 30
    elif 'year' in date_str or 'ago' in date_str:
        return 365
    else:
        return 1  # Default: very recent


def extract_place_info_from_url(url: str) -> Optional[dict]:
    """
    Extract place ID or name from Google Maps URL.
    """
    # Try to extract place ID
    place_id_match = re.search(r'/place/([^/]+)', url)
    if place_id_match:
        place_name = place_id_match.group(1).replace('+', ' ')
        return {"name": place_name, "type": "name"}

    # Try to extract data parameter
    data_match = re.search(r'!1m1!1s([^&]+)', url)
    if data_match:
        place_id = data_match.group(1)
        return {"id": place_id, "type": "id"}

    return None


def scrape_with_selenium(url: str) -> List[dict]:
    """
    Scrape reviews using Selenium (more reliable for dynamic content).
    """
    if not SELENIUM_AVAILABLE:
        print("❌ Selenium not installed")
        print("   Install with: pip install selenium")
        return []

    print("Opening browser to fetch reviews (this may take a moment)...")

    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)

        # Wait for reviews to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_all_elements_located((By.ROLE, "article")))

        # Scroll to load more reviews
        print("Scrolling to load reviews...")
        for _ in range(5):
            driver.execute_script("window.scrollBy(0, 500)")
            __import__('time').sleep(1)

        # Get page HTML
        html = driver.page_source
        place_name = driver.title.split(' -')[0] if ' -' in driver.title else "Unknown Place"

        print(f"✓ Loaded page: {place_name}")

        return extract_reviews_from_html(html, place_name)

    except Exception as e:
        print(f"❌ Selenium error: {e}")
        return []
    finally:
        if driver:
            driver.quit()


def scrape_with_requests(url: str) -> List[dict]:
    """
    Try to scrape using requests library.
    Less reliable than Selenium but doesn't require browser installation.
    """
    if not REQUESTS_AVAILABLE:
        print("❌ requests/BeautifulSoup not installed")
        print("   Install with: pip install requests beautifulsoup4")
        return []

    print("Fetching page...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Extract place name from URL or page
        place_info = extract_place_info_from_url(url)
        place_name = place_info.get("name", "Unknown Place") if place_info else "Unknown Place"

        print(f"✓ Fetched page: {place_name}")

        return extract_reviews_from_html(response.text, place_name)

    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return []


def main():
    print("=" * 60)
    print("Google Maps Review Scraper (No API needed)")
    print("=" * 60)
    print()

    # Get URL from user
    url = input("Paste your Google Maps listing link: ").strip()

    if not url.startswith("http"):
        print("❌ Invalid URL. Make sure it starts with http")
        return

    if "google.com/maps" not in url:
        print("❌ Doesn't look like a Google Maps link")
        return

    print()

    # Try different scraping methods
    reviews = []

    # Try Selenium first (more reliable)
    if SELENIUM_AVAILABLE:
        print("Method 1: Using Selenium (browser automation)...")
        reviews = scrape_with_selenium(url)

    # Fall back to requests
    if not reviews and REQUESTS_AVAILABLE:
        print("Method 2: Using requests + BeautifulSoup...")
        reviews = scrape_with_requests(url)

    # Handle errors
    if not reviews:
        print()
        print("❌ Could not extract reviews. This can happen because:")
        print("   1. Google changed their HTML structure")
        print("   2. Missing dependencies (install with below commands)")
        print("   3. Google blocked the request (rate limiting)")
        print()
        print("Install dependencies for better compatibility:")
        print("   pip install selenium beautifulsoup4 requests")
        print()
        print("Or use the API-based method instead:")
        print("   python fetch_gmaps_reviews.py")
        return

    print(f"✓ Extracted {len(reviews)} reviews\n")

    # Show sample
    if reviews:
        print("Sample review:")
        sample = reviews[0]
        print(f"  Rating: {sample['rating']}★")
        print(f"  Reviewer: {sample['metadata']['reviewer_name']}")
        print(f"  Text: {sample['text'][:80]}...")
        print()

    # Save to file
    output_file = "gmaps_reviews.json"
    with open(output_file, "w") as f:
        json.dump(reviews, f, indent=2)

    print(f"✓ Saved {len(reviews)} reviews to {output_file}")
    print()
    print("Next steps:")
    print("  1. Review gmaps_reviews.json")
    print("  2. Run: python analyze_gmaps.py")
    print("  3. Check gmaps_analysis_report.json for results")


if __name__ == "__main__":
    main()
