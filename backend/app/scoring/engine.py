"""Homestead Score engine: turns raw listing + enrichment data into a 0-100
overall score plus the price/location/build sub-scores stored on `Scores`.
"""

from app.scoring import thresholds as t
from app.scoring.schemas import HomesteadScoreInput, HomesteadScoreResult
from app.scoring.weights import (
    BUILD_BUCKET,
    COMPONENT_WEIGHTS,
    LOCATION_BUCKET,
    PRICE_BUCKET,
    TOTAL_WEIGHT,
    ScoreComponent,
    bucket_weighted_average,
)


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _linear_falloff(
    actual: float, target: float, multiplier: float = t.DISTANCE_FALLOFF_MULTIPLIER
) -> float:
    """100 at/under target, 0 at target * multiplier, linear between."""
    if actual <= target:
        return 100.0
    ceiling = target * multiplier
    if actual >= ceiling:
        return 0.0
    return _clamp(100.0 * (ceiling - actual) / (ceiling - target))


def score_price(price: float, min_price: int, max_price: int, stretch_price: int) -> float:
    if price <= min_price:
        return 100.0
    if price <= max_price:
        span = max_price - min_price
        frac = (price - min_price) / span if span else 0
        return _clamp(100.0 - frac * (100.0 - t.PRICE_SCORE_AT_MAX_BUDGET))
    if price <= stretch_price:
        span = stretch_price - max_price
        frac = (price - max_price) / span if span else 0
        return _clamp(
            t.PRICE_SCORE_AT_MAX_BUDGET
            - frac * (t.PRICE_SCORE_AT_MAX_BUDGET - t.PRICE_SCORE_AT_STRETCH_BUDGET)
        )
    return 0.0


def score_acreage(acres: float, min_acres: float, max_acres: float) -> float:
    if min_acres <= acres <= max_acres:
        return 100.0
    span = max_acres - min_acres or 1.0
    if acres < min_acres:
        deficit = min_acres - acres
    else:
        deficit = acres - max_acres
    return _clamp(100.0 - (deficit / span) * 100.0)


def score_shopping(distances: dict[str, float | None]) -> float:
    sub_scores = []
    for store, target in t.DISTANCE_TARGETS_MINUTES.items():
        minutes = distances.get(store)
        if minutes is None:
            continue
        sub_scores.append(_linear_falloff(minutes, target))
    return round(sum(sub_scores) / len(sub_scores), 2) if sub_scores else t.UNKNOWN_COMPONENT_SCORE


def score_healthcare(hospital_minutes: float | None) -> float:
    if hospital_minutes is None:
        return t.UNKNOWN_COMPONENT_SCORE
    return _linear_falloff(hospital_minutes, t.HEALTHCARE_TARGET_MINUTES)


def score_interstate(i85_minutes: float | None) -> float:
    if i85_minutes is None:
        return t.UNKNOWN_COMPONENT_SCORE
    return _linear_falloff(i85_minutes, t.INTERSTATE_TARGET_MINUTES)


def score_flood(flood_zone: str | None) -> float:
    if not flood_zone:
        return t.UNKNOWN_COMPONENT_SCORE
    zone = flood_zone.upper()
    if zone in t.FEMA_HIGH_RISK_ZONES:
        return 0.0
    if zone in t.FEMA_LOW_RISK_ZONES:
        return 100.0
    return t.UNKNOWN_COMPONENT_SCORE


def score_utilities(electric: bool | None, internet: bool | None, gas: bool | None) -> float:
    total = 0.0
    if electric:
        total += t.UTILITY_POINTS_ELECTRIC
    if internet:
        total += t.UTILITY_POINTS_INTERNET
    if gas:
        total += t.UTILITY_POINTS_GAS
    return _clamp(total)


def score_soil(soil_rating: float | None, perk_possible: bool | None) -> float:
    base = soil_rating if soil_rating is not None else t.SOIL_RATING_DEFAULT
    if perk_possible is False:
        return min(base, t.PERK_IMPOSSIBLE_SCORE_CAP)
    return _clamp(base)


def score_buildability(estimated_site_cost: float | None, price: float) -> float:
    if estimated_site_cost is None or price <= 0:
        return t.UNKNOWN_COMPONENT_SCORE
    ratio = estimated_site_cost / price
    if ratio <= t.SITE_COST_RATIO_EXCELLENT:
        return 100.0
    if ratio >= t.SITE_COST_RATIO_POOR:
        return 0.0
    span = t.SITE_COST_RATIO_POOR - t.SITE_COST_RATIO_EXCELLENT
    frac = (ratio - t.SITE_COST_RATIO_EXCELLENT) / span
    return _clamp(100.0 - frac * 100.0)


def score_appreciation(i85_minutes: float | None) -> float:
    """Placeholder proxy using interstate access; replace with real
    Census/BLS county growth-rate data (see README roadmap)."""
    if i85_minutes is None:
        return t.UNKNOWN_COMPONENT_SCORE
    capped = min(i85_minutes, t.APPRECIATION_INTERSTATE_CAP_MINUTES)
    return _clamp(100.0 - (capped / t.APPRECIATION_INTERSTATE_CAP_MINUTES) * 100.0)


def score_internet(internet: bool | None) -> float:
    return 100.0 if internet else 20.0


def score_tax_rate(tax_value: float | None, price: float) -> float:
    if tax_value is None or price <= 0:
        return t.UNKNOWN_COMPONENT_SCORE
    ratio = tax_value / price
    return _clamp(100.0 - min(ratio / t.TAX_RATIO_HIGH, 1.0) * 100.0)


def score_color(overall_score: float) -> str:
    for threshold, color in t.SCORE_COLOR_BANDS:
        if overall_score >= threshold:
            return color
    return "red"


def compute_homestead_score(data: HomesteadScoreInput) -> HomesteadScoreResult:
    components: dict[ScoreComponent, float] = {
        ScoreComponent.PRICE: score_price(
            data.price, data.min_price, data.max_price, data.stretch_price
        ),
        ScoreComponent.ACREAGE: score_acreage(data.acres, data.min_acres, data.max_acres),
        ScoreComponent.SHOPPING: score_shopping(
            {
                "costco": data.distance_costco,
                "whole_foods": data.distance_whole_foods,
                "walmart": data.distance_walmart,
                "cvs": data.distance_cvs,
                "home_depot": data.distance_home_depot,
                "lowes": data.distance_lowes,
            }
        ),
        ScoreComponent.HEALTHCARE: score_healthcare(data.distance_hospital),
        ScoreComponent.INTERSTATE: score_interstate(data.distance_i85),
        ScoreComponent.FLOOD: score_flood(data.flood_zone),
        ScoreComponent.UTILITIES: score_utilities(data.electric, data.internet, data.gas),
        ScoreComponent.SOIL: score_soil(data.soil_rating, data.perk_possible),
        ScoreComponent.BUILDABILITY: score_buildability(data.estimated_site_cost, data.price),
        ScoreComponent.APPRECIATION: score_appreciation(data.distance_i85),
        ScoreComponent.INTERNET: score_internet(data.internet),
        ScoreComponent.TAX_RATE: score_tax_rate(data.tax_value, data.price),
    }

    price_score = bucket_weighted_average(components, PRICE_BUCKET)
    location_score = bucket_weighted_average(components, LOCATION_BUCKET)
    build_score = bucket_weighted_average(components, BUILD_BUCKET)

    overall = sum(COMPONENT_WEIGHTS[c] * s for c, s in components.items()) / TOTAL_WEIGHT
    overall = round(overall, 2)

    return HomesteadScoreResult(
        price_score=price_score,
        location_score=location_score,
        build_score=build_score,
        overall_score=overall,
        color=score_color(overall),
        components={c.value: v for c, v in components.items()},
    )
