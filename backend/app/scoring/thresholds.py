"""Named thresholds used by the scoring engine.

Centralized here (rather than as inline literals) so tuning the model means
editing one file, not hunting through engine.py.
"""

# --- Distance targets (minutes), from the product spec's "Distance
# Requirements" section. A component scores 100 at or under its target and
# decays linearly to 0 at `target * FALLOFF_MULTIPLIER`.
DISTANCE_TARGETS_MINUTES: dict[str, int] = {
    "costco": 30,
    "whole_foods": 30,
    "walmart": 15,
    "cvs": 15,
    "home_depot": 20,
    "lowes": 20,
}
HEALTHCARE_TARGET_MINUTES = 30
INTERSTATE_TARGET_MINUTES = 10
DISTANCE_FALLOFF_MULTIPLIER = 2.0

# --- Flood zones considered high-risk (FEMA Special Flood Hazard Areas).
FEMA_HIGH_RISK_ZONES = {"A", "AE", "AH", "AO", "AR", "A99", "V", "VE"}
FEMA_LOW_RISK_ZONES = {"X", "X500", "C", "B"}

# --- Utilities scoring weights (must sum to 100).
UTILITY_POINTS_ELECTRIC = 50
UTILITY_POINTS_INTERNET = 35
UTILITY_POINTS_GAS = 15

# --- Fallback used by any component when its underlying data is missing.
UNKNOWN_COMPONENT_SCORE = 50.0

# --- Soil / perc.
SOIL_RATING_DEFAULT = UNKNOWN_COMPONENT_SCORE
PERK_IMPOSSIBLE_SCORE_CAP = 30.0

# --- Buildability: estimated site-development cost as a fraction of price.
SITE_COST_RATIO_EXCELLENT = 0.05  # site cost <= 5% of price -> 100
SITE_COST_RATIO_POOR = 0.30  # site cost >= 30% of price -> 0

# --- Price scoring bands relative to budget / stretch budget.
PRICE_SCORE_AT_MAX_BUDGET = 60.0
PRICE_SCORE_AT_STRETCH_BUDGET = 20.0

# --- Appreciation proxy: interstate access as a stand-in until real
# Census/BLS growth-rate data is integrated (see README roadmap).
APPRECIATION_INTERSTATE_CAP_MINUTES = 60

# --- Tax rate: effective tax_value/price ratio considered "high".
TAX_RATIO_HIGH = 0.02

# --- Overall score color banding.
SCORE_COLOR_BANDS: list[tuple[float, str]] = [
    (90, "green"),
    (80, "blue"),
    (70, "yellow"),
    (0, "red"),
]
