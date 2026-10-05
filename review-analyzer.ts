/**
 * Google Maps Review Fake Detection using TypeSafe/Jev (TypeScript)
 *
 * This module uses TypeSafe's System One model (Jev) to analyze reviews
 * and detect fake/spammy content using composite scoring of multiple indicators.
 */

import { TypeSafeClient, Question, Score, Noul } from "@typesafe-ai/sdk";

// Configuration
const TYPESAFE_API_KEY = process.env.TYPESAFE_API_KEY || "";
const client = new TypeSafeClient({ apiKey: TYPESAFE_API_KEY });

// Type definitions
interface ReviewerProfile {
  name: string;
  accountAgeDays: number;
  totalReviewsWritten: number;
  averageRatingGiven: number;
}

interface ReviewMetadata {
  reviewerName: string;
  reviewerAccountAgeDays: number;
  reviewDate: string; // ISO format
  daysSinceReview: number;
  reviewerReviewCount: number;
  reviewerAvgRating: number;
}

interface GoogleMapReview {
  id: string;
  rating: number; // 1-5
  text: string;
  metadata: ReviewMetadata;
}

interface SuspicionDimension {
  dimension: string;
  score: number; // 0-100
  confidence: number; // 0-1
  evidence: string;
}

interface ReviewAnalysisResult {
  reviewId: string;
  overallSuspicionScore: number;
  overallConfidence: number;
  dimensions: SuspicionDimension[];
  isLikelyFake: boolean;
  daysSinceReview: number;
}

interface AnalysisReport {
  summary: {
    totalReviewsAnalyzed: number;
    likelyFakeReviews: number;
    likelyFakePercentage: number;
    suspiciousReviews: number;
    averageConfidence: number;
  };
  dimensionAnalysis: Record<string, any>;
  detailedResults: ReviewAnalysisResult[];
}

/**
 * Build state object for TypeSafe analysis.
 * State includes all context needed to judge authenticity.
 */
function buildReviewState(review: GoogleMapReview): Record<string, any> {
  return {
    review: {
      id: review.id,
      rating: review.rating,
      text: review.text,
      date: review.metadata.reviewDate,
    },
    reviewer: {
      name: review.metadata.reviewerName,
      accountAgeDays: review.metadata.reviewerAccountAgeDays,
      totalReviewsWritten: review.metadata.reviewerReviewCount,
      averageRatingGiven: review.metadata.reviewerAvgRating,
    },
    context: {
      daysSinceReview: review.metadata.daysSinceReview,
    },
  };
}

/**
 * Build the judgment questions for TypeSafe.
 * These are independent assessments of different suspicion dimensions.
 * TypeSafe runs these in parallel - they cannot see each other's answers.
 */
function buildAnalysisQuestions(): Question<any>[] {
  return [
    {
      id: "language_authenticity",
      type: "score",
      instructions:
        "Rate how authentic and natural the review text is. Look for generic phrases, repetitive patterns, unnatural language flow, or signs of automation.",
      criteria: [
        "Highly authentic: Natural language with specific details and unique phrasing",
        "Mostly authentic: Genuine feel with minor generic elements",
        "Somewhat suspicious: Mix of natural and generic language, odd phrasing patterns",
        "Highly suspicious: Generic templates, repetitive phrases, unnatural flow",
        "Obviously inauthentic: Clear signs of generation or copy-paste",
      ],
    } as Score,

    {
      id: "rating_text_alignment",
      type: "score",
      instructions:
        "Assess whether the star rating matches the emotional tone and content of the review text. Misalignment (e.g., 5 stars complaining, 1 star praising) suggests fake reviews.",
      criteria: [
        "Perfectly aligned: Rating clearly matches review sentiment and tone",
        "Well aligned: Rating and text sentiment consistent",
        "Somewhat misaligned: Minor inconsistencies between rating and content",
        "Notably misaligned: Obvious mismatch between rating and review text",
        "Completely misaligned: Rating contradicts the review sentiment",
      ],
    } as Score,

    {
      id: "reviewer_authenticity",
      type: "score",
      instructions:
        "Evaluate the reviewer's account authenticity based on age, review history, and patterns. New accounts with extreme ratings or very few reviews are more suspicious.",
      criteria: [
        "Highly authentic: Established account with consistent review history",
        "Mostly authentic: Good account age and reasonable review pattern",
        "Somewhat suspicious: Newer account or uneven rating patterns",
        "Highly suspicious: Very new account or extreme rating distribution",
        "Likely fake account: Brand new or bot-like review patterns",
      ],
    } as Score,

    {
      id: "specific_detail_level",
      type: "noul",
      instructions:
        "Does this review contain specific, verifiable details about the product/service (names of staff, specific menu items, particular experiences)? Genuine reviews usually include concrete details.",
      criteria: {
        yes: "Review contains multiple specific, contextual details",
        no: "Review is generic or vague without specific examples",
      },
    } as Noul,

    {
      id: "common_spam_phrases",
      type: "noul",
      instructions:
        "Does this review contain common spam/fake review indicators like: call-to-action phrases, promotional language, links/contact info, urgency language, or formulaic greetings?",
      criteria: {
        yes: "Contains spam indicators or promotional language",
        no: "No obvious spam or promotional phrases detected",
      },
    } as Noul,
  ];
}

/**
 * Analyze a single review using TypeSafe.
 */
async function analyzeReview(
  review: GoogleMapReview
): Promise<ReviewAnalysisResult> {
  const state = buildReviewState(review);
  const questions = buildAnalysisQuestions();

  try {
    // Call TypeSafe API - questions run in parallel
    const response = await client.analyze({
      model: "jev-1.0",
      state,
      questions,
    });

    const dimensions: SuspicionDimension[] = [];
    const scores: number[] = [];
    const confidences: number[] = [];

    // Process language authenticity (Score)
    if (response.language_authenticity) {
      const result = response.language_authenticity;
      const suspicion = (result.level || 2) * 20; // Map to 0-100
      dimensions.push({
        dimension: "language_authenticity",
        score: suspicion,
        confidence: result.confidence || 0.5,
        evidence: result.reasoning || "",
      });
      scores.push(suspicion);
      confidences.push(result.confidence || 0.5);
    }

    // Process rating-text alignment
    if (response.rating_text_alignment) {
      const result = response.rating_text_alignment;
      const suspicion = (5 - (result.level || 2)) * 20; // Invert: good alignment = low suspicion
      dimensions.push({
        dimension: "rating_text_alignment",
        score: suspicion,
        confidence: result.confidence || 0.5,
        evidence: result.reasoning || "",
      });
      scores.push(suspicion);
      confidences.push(result.confidence || 0.5);
    }

    // Process reviewer authenticity
    if (response.reviewer_authenticity) {
      const result = response.reviewer_authenticity;
      const suspicion = (result.level || 2) * 20;
      dimensions.push({
        dimension: "reviewer_authenticity",
        score: suspicion,
        confidence: result.confidence || 0.5,
        evidence: result.reasoning || "",
      });
      scores.push(suspicion);
      confidences.push(result.confidence || 0.5);
    }

    // Process specific detail level (Noul)
    if (response.specific_detail_level) {
      const result = response.specific_detail_level;
      const suspicion = result.value === "yes" ? 0 : 60;
      dimensions.push({
        dimension: "specific_detail_level",
        score: suspicion,
        confidence: result.confidence || 0.5,
        evidence:
          suspicion > 50
            ? "Lacks specific details"
            : "Contains specific details",
      });
      scores.push(suspicion);
      confidences.push(result.confidence || 0.5);
    }

    // Process common spam phrases (Noul)
    if (response.common_spam_phrases) {
      const result = response.common_spam_phrases;
      const suspicion = result.value === "yes" ? 70 : 0;
      dimensions.push({
        dimension: "common_spam_phrases",
        score: suspicion,
        confidence: result.confidence || 0.5,
        evidence:
          suspicion > 50
            ? "Contains spam indicators"
            : "No spam indicators detected",
      });
      scores.push(suspicion);
      confidences.push(result.confidence || 0.5);
    }

    // Compute overall suspicion score (weighted average)
    const overallScore =
      scores.length > 0
        ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
        : 0;
    const overallConfidence =
      confidences.length > 0
        ? confidences.reduce((a, b) => a + b, 0) / confidences.length
        : 0;

    // Determine if likely fake
    const isLikelyFake = overallScore > 60 && overallConfidence > 0.5;

    return {
      reviewId: review.id,
      overallSuspicionScore: overallScore,
      overallConfidence: overallConfidence,
      dimensions,
      isLikelyFake,
      daysSinceReview: review.metadata.daysSinceReview,
    };
  } catch (error) {
    console.error(`Error analyzing review ${review.id}:`, error);
    throw error;
  }
}

/**
 * Analyze multiple reviews in batch.
 * Returns results sorted by suspicion (newest first).
 */
async function analyzeReviewsBatch(
  reviews: GoogleMapReview[]
): Promise<ReviewAnalysisResult[]> {
  const results: ReviewAnalysisResult[] = [];

  // Analyze reviews sequentially (or use Promise.all for parallel processing)
  for (const review of reviews) {
    try {
      const analysis = await analyzeReview(review);
      results.push(analysis);
    } catch (error) {
      console.error(`Failed to analyze review ${review.id}`);
    }
  }

  // Sort by: suspicious first, then by recency (newest = lower daysSinceReview)
  results.sort(
    (a, b) =>
      b.overallSuspicionScore - a.overallSuspicionScore ||
      a.daysSinceReview - b.daysSinceReview
  );

  return results;
}

/**
 * Generate a summary report from batch analysis.
 */
function generateReport(analyses: ReviewAnalysisResult[]): AnalysisReport {
  const total = analyses.length;
  const likelyFake = analyses.filter((a) => a.isLikelyFake).length;
  const suspicious = analyses.filter(
    (a) => a.overallSuspicionScore > 60
  ).length;

  // Group by dimension to identify patterns
  const dimensionSummary: Record<string, any> = {};
  for (const analysis of analyses) {
    for (const dim of analysis.dimensions) {
      if (!dimensionSummary[dim.dimension]) {
        dimensionSummary[dim.dimension] = {
          avgScore: 0,
          count: 0,
          highSuspicionCount: 0,
        };
      }
      dimensionSummary[dim.dimension].avgScore += dim.score;
      dimensionSummary[dim.dimension].count += 1;
      if (dim.score > 60) {
        dimensionSummary[dim.dimension].highSuspicionCount += 1;
      }
    }
  }

  // Normalize averages
  for (const dim in dimensionSummary) {
    const count = dimensionSummary[dim].count;
    if (count > 0) {
      dimensionSummary[dim].avgScore = Math.round(
        dimensionSummary[dim].avgScore / count
      );
    }
  }

  return {
    summary: {
      totalReviewsAnalyzed: total,
      likelyFakeReviews: likelyFake,
      likelyFakePercentage:
        total > 0 ? Math.round((100 * likelyFake) / total * 10) / 10 : 0,
      suspiciousReviews: suspicious,
      averageConfidence:
        total > 0
          ? Math.round(
              (analyses.reduce((sum, a) => sum + a.overallConfidence, 0) /
                total) *
                100
            ) / 100
          : 0,
    },
    dimensionAnalysis: dimensionSummary,
    detailedResults: analyses,
  };
}

// Example usage
async function main() {
  const sampleReviews: GoogleMapReview[] = [
    {
      id: "review_001",
      rating: 5,
      text: "Amazing service! The staff was incredibly helpful and the food was delicious. Highly recommend!",
      metadata: {
        reviewerName: "John D.",
        reviewerAccountAgeDays: 2,
        reviewDate: "2024-10-04",
        daysSinceReview: 1,
        reviewerReviewCount: 1,
        reviewerAvgRating: 5.0,
      },
    },
    {
      id: "review_002",
      rating: 5,
      text: "Had lunch here with my family. The grilled salmon was perfectly cooked, chef knew exactly how to season it. Waitress Sarah remembered our drink order without asking. Will definitely come back next Thursday.",
      metadata: {
        reviewerName: "Maria Garcia",
        reviewerAccountAgeDays: 1250,
        reviewDate: "2024-10-02",
        daysSinceReview: 3,
        reviewerReviewCount: 47,
        reviewerAvgRating: 4.1,
      },
    },
    {
      id: "review_003",
      rating: 5,
      text: "MUST VISIT! Click here for promo code SAVE20. Great experience, 5 stars always!",
      metadata: {
        reviewerName: "Mark S.",
        reviewerAccountAgeDays: 5,
        reviewDate: "2024-10-03",
        daysSinceReview: 2,
        reviewerReviewCount: 3,
        reviewerAvgRating: 5.0,
      },
    },
  ];

  console.log("Analyzing reviews with TypeSafe/Jev...");
  console.log("=".repeat(60));

  const analyses = await analyzeReviewsBatch(sampleReviews);
  const report = generateReport(analyses);

  console.log(JSON.stringify(report, null, 2));
}

main().catch(console.error);
