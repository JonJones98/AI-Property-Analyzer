"""Homestead Score component weights, as specified by the product spec.

The spec's twelve component weights sum to 110 rather than 100. Rather than
silently rescaling (which would misrepresent the spec) or hardcoding a fixup,
`overall_score` is computed as a weighted *average* — `sum(weight * score) /
sum(weight)` — which is mathematically correct regardless of whether the
weights sum to 100, and reproduces the intended relative importance of each
component exactly.
"""

from enum import StrEnum


class ScoreComponent(StrEnum):
    PRICE = "price"
    ACREAGE = "acreage"
    SHOPPING = "shopping"
    HEALTHCARE = "healthcare"
    INTERSTATE = "interstate"
    FLOOD = "flood"
    UTILITIES = "utilities"
    SOIL = "soil"
    BUILDABILITY = "buildability"
    APPRECIATION = "appreciation"
    INTERNET = "internet"
    TAX_RATE = "tax_rate"


COMPONENT_WEIGHTS: dict[ScoreComponent, int] = {
    ScoreComponent.PRICE: 20,
    ScoreComponent.ACREAGE: 15,
    ScoreComponent.SHOPPING: 10,
    ScoreComponent.HEALTHCARE: 5,
    ScoreComponent.INTERSTATE: 10,
    ScoreComponent.FLOOD: 5,
    ScoreComponent.UTILITIES: 10,
    ScoreComponent.SOIL: 10,
    ScoreComponent.BUILDABILITY: 10,
    ScoreComponent.APPRECIATION: 5,
    ScoreComponent.INTERNET: 5,
    ScoreComponent.TAX_RATE: 5,
}

TOTAL_WEIGHT = sum(COMPONENT_WEIGHTS.values())

# How the twelve components roll up into the DB's three sub-scores
# (Listings.scores.price_score / location_score / build_score).
PRICE_BUCKET = (ScoreComponent.PRICE, ScoreComponent.TAX_RATE, ScoreComponent.APPRECIATION)
LOCATION_BUCKET = (
    ScoreComponent.SHOPPING,
    ScoreComponent.HEALTHCARE,
    ScoreComponent.INTERSTATE,
    ScoreComponent.INTERNET,
)
BUILD_BUCKET = (
    ScoreComponent.ACREAGE,
    ScoreComponent.UTILITIES,
    ScoreComponent.SOIL,
    ScoreComponent.BUILDABILITY,
    ScoreComponent.FLOOD,
)


def bucket_weighted_average(
    component_scores: dict[ScoreComponent, float], bucket: tuple[ScoreComponent, ...]
) -> float:
    weight_sum = sum(COMPONENT_WEIGHTS[c] for c in bucket)
    score_sum = sum(COMPONENT_WEIGHTS[c] * component_scores[c] for c in bucket)
    return round(score_sum / weight_sum, 2) if weight_sum else 0.0
