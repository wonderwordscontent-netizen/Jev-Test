#!/usr/bin/env python3
"""
Flask web app for TypeSafe review analyzer with Google Maps link support.

Run with:
  python web_app_v2.py

Then open: http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify
import json
import os
import re
from datetime import datetime, timedelta

# Try to import optional scraping libraries
try:
    import requests
    from bs4 import BeautifulSoup
    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False

# Import our analyzers
try:
    from review_analyzer import analyze_reviews_batch, generate_report
except ImportError:
    analyze_reviews_batch = None
    generate_report = None

from paste_reviews_manual import parse_review_text

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Store results in memory (for demo)
last_report = None


@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index_v2.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze reviews from various sources."""
    global last_report

    try:
        data = request.get_json()
        source = data.get('source', 'manual')
        content = data.get('content', '').strip()
        use_api = data.get('use_api', False)
        api_key = os.environ.get('BEATAPI_API_KEY') if use_api else None

        if not content:
            return jsonify({'error': 'No input provided'}), 400

        # Parse reviews based on source
        if source == 'link':
            # Scrape from Google Maps link
            reviews = scrape_gmaps_link(content)
            if not reviews:
                return jsonify({'error': 'Could not extract reviews from link. Try pasting reviews manually instead.'}), 400
        elif source == 'manual':
            reviews = parse_manual_reviews(content)
        elif source == 'paste':
            reviews = parse_pasted_reviews(content)
        else:
            return jsonify({'error': 'Unknown source'}), 400

        if not reviews:
            return jsonify({'error': 'Could not parse any reviews. Check format.'}), 400

        # Analyze
        if use_api and api_key and analyze_reviews_batch:
            # Use real TypeSafe API
            analyses = analyze_reviews_batch(reviews)
            last_report = generate_report(analyses)
        else:
            # Use mock analysis
            last_report = analyze_mock(reviews)

        return jsonify({
            'success': True,
            'review_count': len(reviews),
            'report': last_report
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def scrape_gmaps_link(url: str) -> list:
    """Scrape reviews from a Google Maps link."""

    if not SCRAPING_AVAILABLE:
        return []

    # Validate it's a Google Maps URL
    if 'google.com/maps' not in url and 'maps.google.com' not in url:
        return []

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        reviews = []

        # Try to find review elements
        review_selectors = [
            'div[data-review-id]',
            'div[role="article"]',
            'div.gws-plugins-hotelbookingreviews__review-item',
            'div.review'
        ]

        review_elements = []
        for selector in review_selectors:
            review_elements = soup.select(selector)
            if review_elements:
                break

        if not review_elements:
            # Try to extract from JSON-LD if available
            scripts = soup.find_all('script', {'type': 'application/ld+json'})
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'review' in data:
                        for review_data in data.get('review', []):
                            review = {
                                "id": f"gmaps_{reviews.__len__()}",
                                "rating": int(review_data.get('reviewRating', {}).get('ratingValue', 5)),
                                "text": review_data.get('reviewBody', ''),
                                "metadata": {
                                    "reviewer_name": review_data.get('author', {}).get('name', 'Unknown'),
                                    "reviewer_account_age_days": 365,
                                    "review_date": datetime.now().isoformat(),
                                    "days_since_review": 0,
                                    "reviewer_review_count": 1,
                                    "reviewer_avg_rating": float(review_data.get('reviewRating', {}).get('ratingValue', 5) or 5),
                                }
                            }
                            if review['text']:
                                reviews.append(review)
                except:
                    continue

            return reviews

        # Parse HTML review elements
        for i, element in enumerate(review_elements[:20]):  # Limit to first 20
            try:
                text = element.get_text(strip=True)[:500]

                # Extract rating
                rating = 5
                rating_match = re.search(r'(\d+)\s*(?:star|★)', text, re.IGNORECASE)
                if rating_match:
                    rating = int(rating_match.group(1))

                # Extract name
                name_elem = element.select_one('[data-tooltip]')
                reviewer_name = name_elem.get('data-tooltip', f'Reviewer {i}') if name_elem else f'Reviewer {i}'

                if text and len(text) > 10:
                    review = {
                        "id": f"gmaps_{i}",
                        "rating": rating,
                        "text": text,
                        "metadata": {
                            "reviewer_name": reviewer_name,
                            "reviewer_account_age_days": 365,
                            "review_date": datetime.now().isoformat(),
                            "days_since_review": 0,
                            "reviewer_review_count": 1,
                            "reviewer_avg_rating": float(rating or 5),
                        }
                    }
                    reviews.append(review)
            except:
                continue

        return reviews

    except Exception as e:
        print(f"Scraping error: {e}")
        return []


@app.route('/api/demo', methods=['GET'])
def demo():
    """Load demo data."""
    global last_report

    demo_reviews = [
        {
            "id": "demo_001",
            "rating": 5,
            "text": "Amazing coffee and friendly staff! Will definitely come back.",
            "metadata": {
                "reviewer_name": "Sarah M.",
                "reviewer_account_age_days": 1250,
                "review_date": (datetime.now() - timedelta(days=2)).isoformat(),
                "days_since_review": 2,
                "reviewer_review_count": 23,
                "reviewer_avg_rating": 4.1,
            }
        },
        {
            "id": "demo_002",
            "rating": 1,
            "text": "Terrible experience, rude staff. Waste of money.",
            "metadata": {
                "reviewer_name": "Mike L.",
                "reviewer_account_age_days": 800,
                "review_date": (datetime.now() - timedelta(days=3)).isoformat(),
                "days_since_review": 3,
                "reviewer_review_count": 15,
                "reviewer_avg_rating": 3.5,
            }
        },
        {
            "id": "demo_003",
            "rating": 5,
            "text": "MUST VISIT! Click here for promo code SAVE20. 5 stars always!!!",
            "metadata": {
                "reviewer_name": "Mark S.",
                "reviewer_account_age_days": 5,
                "review_date": (datetime.now() - timedelta(days=1)).isoformat(),
                "days_since_review": 1,
                "reviewer_review_count": 2,
                "reviewer_avg_rating": 5.0,
            }
        }
    ]

    last_report = analyze_mock(demo_reviews)

    return jsonify({
        'success': True,
        'review_count': len(demo_reviews),
        'report': last_report
    })


def parse_manual_reviews(text: str) -> list:
    """Parse reviews entered one per line."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    reviews = []

    for i, line in enumerate(lines):
        parsed = parse_review_text(line)
        if parsed:
            review_date = datetime.now() - timedelta(days=parsed.get('days_since', 0))
            rating = parsed.get('rating') or 5
            if rating is None:
                rating = 5

            reviews.append({
                "id": f"manual_{i+1}",
                "rating": rating,
                "text": parsed.get('text', line),
                "metadata": {
                    "reviewer_name": parsed.get('reviewer_name', f"Reviewer {i+1}"),
                    "reviewer_account_age_days": 365,
                    "review_date": review_date.isoformat(),
                    "days_since_review": parsed.get('days_since', 0),
                    "reviewer_review_count": 1,
                    "reviewer_avg_rating": float(rating or 5),
                }
            })

    return reviews


def parse_pasted_reviews(text: str) -> list:
    """Parse reviews from pasted text."""
    return parse_manual_reviews(text)


def analyze_mock(reviews: list) -> dict:
    """Analyze reviews with mock data (no API needed)."""

    mock_scores = {
        0: {'lang': 20, 'detail': 0, 'spam': 0},
        1: {'lang': 90, 'detail': 60, 'spam': 0},
        2: {'lang': 100, 'detail': 60, 'spam': 70},
    }

    analyses = []
    for i, review in enumerate(reviews):
        scores = mock_scores.get(i, {'lang': 50, 'detail': 30, 'spam': 20})

        overall = (scores['lang'] + scores['detail'] + scores['spam']) // 3
        is_fake = overall > 60

        analyses.append({
            "review_id": review["id"],
            "rating": review["rating"],
            "text": review["text"],
            "suspicion_score": overall,
            "confidence": 0.80 + (i * 0.05) if i < 20 else 0.85,
            "is_likely_fake": is_fake,
            "days_since_review": review["metadata"]["days_since_review"],
            "dimensions": [
                {
                    "dimension": "language_authenticity",
                    "score": scores['lang'],
                    "confidence": 0.89,
                    "evidence": "Generic phrasing" if scores['lang'] > 60 else "Natural language"
                },
                {
                    "dimension": "specific_detail_level",
                    "score": scores['detail'],
                    "confidence": 0.91,
                    "evidence": "Lacks specific details" if scores['detail'] > 50 else "Contains specific details"
                },
                {
                    "dimension": "common_spam_phrases",
                    "score": scores['spam'],
                    "confidence": 0.88,
                    "evidence": "Contains spam indicators" if scores['spam'] > 50 else "No spam detected"
                }
            ]
        })

    total = len(analyses)
    fake_count = sum(1 for a in analyses if a['is_likely_fake'])

    return {
        "summary": {
            "total_reviews_analyzed": total,
            "likely_fake_reviews": fake_count,
            "likely_fake_percentage": round(100 * fake_count / total, 1) if total > 0 else 0,
            "suspicious_reviews": sum(1 for a in analyses if a['suspicion_score'] > 60),
            "average_confidence": round(sum(a['confidence'] for a in analyses) / total, 2) if total > 0 else 0
        },
        "detailed_results": sorted(
            analyses,
            key=lambda x: (-x['suspicion_score'], x['days_since_review'])
        )
    }


if __name__ == '__main__':
    print("=" * 60)
    print("TypeSafe Review Analyzer - Web App v2")
    print("=" * 60)
    print()
    print("Starting Flask app...")
    print()
    print("Open your browser to: http://localhost:5000")
    print()
    print("Features:")
    print("  - Paste Google Maps listing link")
    print("  - Paste reviews manually")
    print("  - Demo with sample data")
    print("  - Mock analysis (no API)")
    print("  - Real analysis (with BeatAPI key)")
    print()
    if not SCRAPING_AVAILABLE:
        print("⚠️  Note: Link scraping requires: pip install requests beautifulsoup4")
    print()
    print("Press Ctrl+C to stop")
    print()

    app.run(debug=True, port=5000)
