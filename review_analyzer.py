"""
Google Maps Review Fake Detection using TypeSafe/Jev

This module uses TypeSafe's System One model (Jev) to analyze reviews
and detect fake/spammy content using composite scoring of multiple indicators.

Pattern: Composite scoring + verification
- Score primitives rate suspicion dimensions independently
- Noul primitives identify binary red flags
- Code composes scores into ranked suspicion levels
"""

import json
from typing import TypedDict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import requests


# TypeSafe API Configuration
# Using BeatAPI hosted TypeSafe endpoint
TYPESAFE_API_URL = "https://api.beatapi.io/v1/systemone"
TYPESAFE_API_KEY = "${BEATAPI_API_KEY}"  # Set via environment

# Review data structures
class ReviewMetadata(TypedDict):
    """Metadata about a review's source and context"""
    reviewer_name: str
    reviewer_account_age_days: int
    review_date: str  # ISO format
    days_since_review: int
    reviewer_review_count: int
    reviewer_avg_rating: float


class Review(TypedDict):
    """A single Google Maps review"""
    id: str
    rating: int  # 1-5
    text: str
    metadata: ReviewMetadata


@dataclass
class SuspicionDimension:
    """Score for a single suspicion dimension"""
    dimension: str
    score: int  # 0-100 (0=not suspicious, 100=highly suspicious)
    confidence: float  # 0-1 (model confidence in this assessment)
    evidence: str  # Brief explanation of the score


@dataclass
class ReviewSuspicionAnalysis:
    """Complete suspicion analysis for a review"""
    review_id: str
    overall_suspicion_score: int  # 0-100
    overall_confidence: float
    dimensions: List[SuspicionDimension]
    is_likely_fake: bool  # Threshold-based determination
    days_since_review: int
    raw_response: dict  # Full TypeSafe response for inspection


def build_review_state(review: Review) -> dict:
    """
    Build the state object to send to TypeSafe.
    State includes all context needed to judge the review's authenticity.
    """
    return {
        "review": {
            "id": review["id"],
            "rating": review["rating"],
            "text": review["text"],
            "date": review["metadata"]["review_date"],
        },
        "reviewer": {
            "name": review["metadata"]["reviewer_name"],
            "account_age_days": review["metadata"]["reviewer_account_age_days"],
            "total_reviews_written": review["metadata"]["reviewer_review_count"],
            "average_rating_given": review["metadata"]["reviewer_avg_rating"],
        },
        "context": {
            "days_since_review": review["metadata"]["days_since_review"],
        }
    }


def build_analysis_questions() -> List[dict]:
    """
    Build the judgment questions for TypeSafe.
    These are independent assessments of different suspicion dimensions.
    """
    return [
        {
            "id": "language_authenticity",
            "type": "score",
            "instructions": "Rate how authentic and natural the review text is. Look for generic phrases, repetitive patterns, unnatural language flow, or signs of automation.",
            "criteria": [
                "Highly authentic: Natural language with specific details and unique phrasing",
                "Mostly authentic: Genuine feel with minor generic elements",
                "Somewhat suspicious: Mix of natural and generic language, odd phrasing patterns",
                "Highly suspicious: Generic templates, repetitive phrases, unnatural flow",
                "Obviously inauthentic: Clear signs of generation or copy-paste"
            ]
        },
        {
            "id": "rating_text_alignment",
            "type": "score",
            "instructions": "Assess whether the star rating matches the emotional tone and content of the review text. Misalignment (e.g., 5 stars complaining, 1 star praising) suggests fake reviews.",
            "criteria": [
                "Perfectly aligned: Rating clearly matches review sentiment and tone",
                "Well aligned: Rating and text sentiment consistent",
                "Somewhat misaligned: Minor inconsistencies between rating and content",
                "Notably misaligned: Obvious mismatch between rating and review text",
                "Completely misaligned: Rating contradicts the review sentiment"
            ]
        },
        {
            "id": "reviewer_authenticity",
            "type": "score",
            "instructions": "Evaluate the reviewer's account authenticity based on age, review history, and patterns. New accounts with extreme ratings or very few reviews are more suspicious.",
            "criteria": [
                "Highly authentic: Established account with consistent review history",
                "Mostly authentic: Good account age and reasonable review pattern",
                "Somewhat suspicious: Newer account or uneven rating patterns",
                "Highly suspicious: Very new account or extreme rating distribution",
                "Likely fake account: Brand new or bot-like review patterns"
            ]
        },
        {
            "id": "specific_detail_level",
            "type": "noul",
            "instructions": "Does this review contain specific, verifiable details about the product/service (names of staff, specific menu items, particular experiences)? Genuine reviews usually include concrete details.",
            "criteria": {
                "yes": "Review contains multiple specific, contextual details",
                "no": "Review is generic or vague without specific examples"
            }
        },
        {
            "id": "common_spam_phrases",
            "type": "noul",
            "instructions": "Does this review contain common spam/fake review indicators like: call-to-action phrases, promotional language, links/contact info, urgency language, or formulaic greetings?",
            "criteria": {
                "yes": "Contains spam indicators or promotional language",
                "no": "No obvious spam or promotional phrases detected"
            }
        }
    ]


def call_typesafe_api(review: Review) -> dict:
    """
    Call TypeSafe API to analyze a single review.
    Returns the structured judgment response.
    """
    state = build_review_state(review)
    questions = build_analysis_questions()

    # Convert questions list to dict format expected by BeatAPI
    questions_dict = {q["id"]: {
        "type": q["type"],
        "instructions": q["instructions"],
        "criteria": q["criteria"]
    } for q in questions}

    payload = {
        "model": "jev-1.13-free",
        "state": state,
        "questions": questions_dict
    }

    headers = {
        "Authorization": f"Bearer {TYPESAFE_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        TYPESAFE_API_URL,
        json=payload,
        headers=headers,
        timeout=30
    )
    response.raise_for_status()
    return response.json()


def analyze_review(review: Review) -> ReviewSuspicionAnalysis:
    """
    Analyze a single review using TypeSafe and return suspicion scores.
    """
    # Call TypeSafe API
    response = call_typesafe_api(review)

    # Extract and normalize dimension scores
    dimensions: List[SuspicionDimension] = []
    scores = []
    confidences = []

    # Language authenticity (Score: 0-100 scale maps to suspicion)
    if "language_authenticity" in response:
        result = response["language_authenticity"]
        suspicion = result.get("level", 2) * 20  # Map levels to 0-100
        dimensions.append(SuspicionDimension(
            dimension="language_authenticity",
            score=suspicion,
            confidence=result.get("confidence", 0.5),
            evidence=result.get("reasoning", "")
        ))
        scores.append(suspicion)
        confidences.append(result.get("confidence", 0.5))

    # Rating-text alignment
    if "rating_text_alignment" in response:
        result = response["rating_text_alignment"]
        suspicion = (5 - result.get("level", 2)) * 20  # Invert: good alignment = low suspicion
        dimensions.append(SuspicionDimension(
            dimension="rating_text_alignment",
            score=suspicion,
            confidence=result.get("confidence", 0.5),
            evidence=result.get("reasoning", "")
        ))
        scores.append(suspicion)
        confidences.append(result.get("confidence", 0.5))

    # Reviewer authenticity
    if "reviewer_authenticity" in response:
        result = response["reviewer_authenticity"]
        suspicion = result.get("level", 2) * 20
        dimensions.append(SuspicionDimension(
            dimension="reviewer_authenticity",
            score=suspicion,
            confidence=result.get("confidence", 0.5),
            evidence=result.get("reasoning", "")
        ))
        scores.append(suspicion)
        confidences.append(result.get("confidence", 0.5))

    # Specific detail level (Noul: yes=low suspicion, no=high suspicion)
    if "specific_detail_level" in response:
        result = response["specific_detail_level"]
        suspicion = 0 if result.get("value") == "yes" else 60
        dimensions.append(SuspicionDimension(
            dimension="specific_detail_level",
            score=suspicion,
            confidence=result.get("confidence", 0.5),
            evidence="Lacks specific details" if suspicion > 50 else "Contains specific details"
        ))
        scores.append(suspicion)
        confidences.append(result.get("confidence", 0.5))

    # Common spam phrases (Noul: yes=high suspicion, no=low suspicion)
    if "common_spam_phrases" in response:
        result = response["common_spam_phrases"]
        suspicion = 70 if result.get("value") == "yes" else 0
        dimensions.append(SuspicionDimension(
            dimension="common_spam_phrases",
            score=suspicion,
            confidence=result.get("confidence", 0.5),
            evidence="Contains spam indicators" if suspicion > 50 else "No spam indicators detected"
        ))
        scores.append(suspicion)
        confidences.append(result.get("confidence", 0.5))

    # Compute overall suspicion score (weighted average)
    if scores:
        overall_score = int(sum(scores) / len(scores))
        overall_confidence = sum(confidences) / len(confidences)
    else:
        overall_score = 0
        overall_confidence = 0

    # Determine if likely fake (threshold: >60 = suspicious, with good confidence)
    is_likely_fake = (overall_score > 60) and (overall_confidence > 0.5)

    return ReviewSuspicionAnalysis(
        review_id=review["id"],
        overall_suspicion_score=overall_score,
        overall_confidence=overall_confidence,
        dimensions=dimensions,
        is_likely_fake=is_likely_fake,
        days_since_review=review["metadata"]["days_since_review"],
        raw_response=response
    )


def analyze_reviews_batch(reviews: List[Review]) -> List[ReviewSuspicionAnalysis]:
    """
    Analyze multiple reviews and return sorted by suspicion (newest first).
    This demonstrates the parallel question capability of TypeSafe.
    """
    results = []

    for review in reviews:
        try:
            analysis = analyze_review(review)
            results.append(analysis)
        except Exception as e:
            print(f"Error analyzing review {review['id']}: {e}")
            continue

    # Sort by: suspicious first, then by recency (newest = lower days_since_review)
    results.sort(
        key=lambda x: (-x.overall_suspicion_score, x.days_since_review)
    )

    return results


def generate_report(analyses: List[ReviewSuspicionAnalysis]) -> dict:
    """
    Generate a summary report from the batch analysis.
    """
    total = len(analyses)
    likely_fake = sum(1 for a in analyses if a.is_likely_fake)
    suspicious = sum(1 for a in analyses if a.overall_suspicion_score > 60)
    high_confidence = sum(1 for a in analyses if a.overall_confidence > 0.8)

    # Group by dimension to identify patterns
    dimension_summary = {}
    for analysis in analyses:
        for dim in analysis.dimensions:
            if dim.dimension not in dimension_summary:
                dimension_summary[dim.dimension] = {
                    "avg_score": 0,
                    "count": 0,
                    "high_suspicion_count": 0
                }
            dimension_summary[dim.dimension]["avg_score"] += dim.score
            dimension_summary[dim.dimension]["count"] += 1
            if dim.score > 60:
                dimension_summary[dim.dimension]["high_suspicion_count"] += 1

    # Normalize averages
    for dim in dimension_summary:
        count = dimension_summary[dim]["count"]
        if count > 0:
            dimension_summary[dim]["avg_score"] = int(
                dimension_summary[dim]["avg_score"] / count
            )

    return {
        "summary": {
            "total_reviews_analyzed": total,
            "likely_fake_reviews": likely_fake,
            "likely_fake_percentage": round(100 * likely_fake / total, 1) if total > 0 else 0,
            "suspicious_reviews": suspicious,
            "high_confidence_assessments": high_confidence,
            "average_confidence": round(
                sum(a.overall_confidence for a in analyses) / total, 2
            ) if total > 0 else 0
        },
        "dimension_analysis": dimension_summary,
        "detailed_results": [
            {
                "review_id": a.review_id,
                "suspicion_score": a.overall_suspicion_score,
                "confidence": a.overall_confidence,
                "is_likely_fake": a.is_likely_fake,
                "days_since_review": a.days_since_review,
                "dimensions": [asdict(d) for d in a.dimensions]
            }
            for a in analyses
        ]
    }


if __name__ == "__main__":
    # Example usage
    sample_reviews: List[Review] = [
        {
            "id": "review_001",
            "rating": 5,
            "text": "Amazing service! The staff was incredibly helpful and the food was delicious. Highly recommend!",
            "metadata": {
                "reviewer_name": "John D.",
                "reviewer_account_age_days": 2,
                "review_date": "2024-10-04",
                "days_since_review": 1,
                "reviewer_review_count": 1,
                "reviewer_avg_rating": 5.0
            }
        },
        {
            "id": "review_002",
            "rating": 5,
            "text": "Had lunch here with my family. The grilled salmon was perfectly cooked, chef knew exactly how to season it. Waitress Sarah remembered our drink order without asking. Will definitely come back next Thursday.",
            "metadata": {
                "reviewer_name": "Maria Garcia",
                "reviewer_account_age_days": 1250,
                "review_date": "2024-10-02",
                "days_since_review": 3,
                "reviewer_review_count": 47,
                "reviewer_avg_rating": 4.1
            }
        },
        {
            "id": "review_003",
            "rating": 5,
            "text": "MUST VISIT! Click here for promo code SAVE20. Great experience, 5 stars always!",
            "metadata": {
                "reviewer_name": "Mark S.",
                "reviewer_account_age_days": 5,
                "review_date": "2024-10-03",
                "days_since_review": 2,
                "reviewer_review_count": 3,
                "reviewer_avg_rating": 5.0
            }
        }
    ]

    print("Analyzing reviews with TypeSafe/Jev...")
    print("=" * 60)

    analyses = analyze_reviews_batch(sample_reviews)
    report = generate_report(analyses)

    print(json.dumps(report, indent=2))
