#!/usr/bin/env python3
"""
Simple Flask web app for TypeSafe review analyzer.

Run with:
  python web_app.py

Then open: http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime, timedelta
import re

# Import our analyzers
from review_analyzer import analyze_reviews_batch, generate_report
from paste_reviews_manual import parse_review_text

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Store results in memory (for demo)
last_report = None


@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')


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
            return jsonify({'error': 'No reviews provided'}), 400

        # Parse reviews based on source
        if source == 'manual':
            reviews = parse_manual_reviews(content)
        elif source == 'paste':
            reviews = parse_pasted_reviews(content)
        else:
            return jsonify({'error': 'Unknown source'}), 400

        if not reviews:
            return jsonify({'error': 'Could not parse any reviews. Check format.'}), 400

        # Analyze
        if use_api and api_key:
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

            reviews.append({
                "id": f"manual_{i+1}",
                "rating": parsed.get('rating', 5),
                "text": parsed.get('text', line),
                "metadata": {
                    "reviewer_name": parsed.get('reviewer_name', f"Reviewer {i+1}"),
                    "reviewer_account_age_days": 365,
                    "review_date": review_date.isoformat(),
                    "days_since_review": parsed.get('days_since', 0),
                    "reviewer_review_count": 1,
                    "reviewer_avg_rating": float(parsed.get('rating', 5)),
                }
            })

    return reviews


def parse_pasted_reviews(text: str) -> list:
    """Parse reviews from pasted text (one per line, Google Maps format)."""
    return parse_manual_reviews(text)


def analyze_mock(reviews: list) -> dict:
    """Analyze reviews with mock data (no API needed)."""

    mock_scores = {
        0: {'lang': 20, 'detail': 0, 'spam': 0},     # Authentic
        1: {'lang': 90, 'detail': 60, 'spam': 0},    # Suspicious
        2: {'lang': 100, 'detail': 60, 'spam': 70},  # Fake
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
            "confidence": 0.80 + (i * 0.05),
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
    print("TypeSafe Review Analyzer - Web App")
    print("=" * 60)
    print()
    print("Starting Flask app...")
    print()
    print("Open your browser to: http://localhost:5000")
    print()
    print("Features:")
    print("  - Paste reviews manually")
    print("  - Demo with sample data")
    print("  - Mock analysis (no API)")
    print("  - Real analysis (with BeatAPI key)")
    print()
    print("Press Ctrl+C to stop")
    print()

    app.run(debug=True, port=5000)
