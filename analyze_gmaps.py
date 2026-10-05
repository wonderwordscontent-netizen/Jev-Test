#!/usr/bin/env python3
"""
Analyze Google Maps reviews using TypeSafe.

Usage:
1. Run fetch_gmaps_reviews.py first to get gmaps_reviews.json
2. Set BEATAPI_API_KEY: export BEATAPI_API_KEY="your_key"
3. Run: python analyze_gmaps.py

Output: gmaps_analysis_report.json with full analysis
"""

import json
import os
from review_analyzer import analyze_reviews_batch, generate_report

def main():
    print("=" * 60)
    print("TypeSafe Google Maps Review Analysis")
    print("=" * 60)

    # Check for BEATAPI key
    api_key = os.environ.get("BEATAPI_API_KEY")
    if not api_key:
        print("❌ Error: BEATAPI_API_KEY not set")
        print("   Run: export BEATAPI_API_KEY='your_key'")
        return

    print("✓ API Key configured\n")

    # Load reviews from fetch_gmaps_reviews.py
    if not os.path.exists("gmaps_reviews.json"):
        print("❌ Error: gmaps_reviews.json not found")
        print("   Run fetch_gmaps_reviews.py first")
        return

    print("Loading reviews from gmaps_reviews.json...")
    with open("gmaps_reviews.json") as f:
        reviews = json.load(f)

    print(f"✓ Loaded {len(reviews)} reviews\n")

    # Analyze with TypeSafe
    print("Analyzing with TypeSafe/Jev...")
    print("-" * 60)

    analyses = analyze_reviews_batch(reviews)
    report = generate_report(analyses)

    # Save report
    output_file = "gmaps_analysis_report.json"
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print("-" * 60)
    print(f"✓ Saved full report to {output_file}\n")

    # Display summary
    summary = report["summary"]
    print("=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Total reviews analyzed: {summary['total_reviews_analyzed']}")
    print(f"Likely fake reviews: {summary['likely_fake_reviews']} ({summary['likely_fake_percentage']:.1f}%)")
    print(f"Suspicious reviews: {summary['suspicious_reviews']}")
    print(f"Average confidence: {summary['average_confidence']:.2f}")

    # Show fake reviews
    fake_reviews = [r for r in report["detailed_results"] if r["is_likely_fake"]]
    if fake_reviews:
        print(f"\n⚠️  {len(fake_reviews)} LIKELY FAKE REVIEWS:")
        print("-" * 60)
        for i, review in enumerate(fake_reviews[:5], 1):  # Show top 5
            print(f"\n{i}. Review ID: {review['review_id']}")
            print(f"   Suspicion Score: {review['suspicion_score']}/100")
            print(f"   Confidence: {review['confidence']:.2f}")
            print(f"   Days since review: {review['days_since_review']}")

            # Show which dimensions flagged it
            for dim in review["dimensions"]:
                if dim["score"] > 60:
                    print(f"   🚩 {dim['dimension']}: {dim['score']}/100 - {dim['evidence']}")

    # Show dimension analysis
    print(f"\n" + "=" * 60)
    print("DIMENSION ANALYSIS")
    print("=" * 60)

    for dim_name, dim_stats in report["dimension_analysis"].items():
        print(f"\n{dim_name}:")
        print(f"  Average suspicion: {dim_stats['avg_score']}/100")
        print(f"  High suspicion count: {dim_stats['high_suspicion_count']}")

    # Actionable recommendations
    print(f"\n" + "=" * 60)
    print("RECOMMENDED ACTIONS")
    print("=" * 60)

    if summary['likely_fake_reviews'] > 0:
        print(f"\n🚨 {summary['likely_fake_reviews']} reviews should be reviewed for removal:")
        print("   1. Check Google Maps policy on review removal")
        print("   2. Report flagged reviews to Google")
        print("   3. Monitor new reviews for patterns")

    if summary['suspicious_reviews'] > summary['likely_fake_reviews']:
        gray_area = summary['suspicious_reviews'] - summary['likely_fake_reviews']
        print(f"\n⚠️  {gray_area} suspicious reviews worth investigating:")
        print("   1. Review manually for context")
        print("   2. Check if they follow up with responses")
        print("   3. Assess if they provide legitimate concerns")

    print(f"\n✓ Analysis complete!")
    print(f"   Full report saved to: {output_file}")


if __name__ == "__main__":
    main()
