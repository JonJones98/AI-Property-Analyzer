"""Named unit costs and financing assumptions for the cost estimator.

These are reasonable 2026 NC rural-construction ballpark figures, meant to
give a directionally-useful budget rather than a contractor-grade quote.
Centralizing them here means recalibrating the model is a one-file change.
"""

# --- Site development (flat, per-acre, or per-foot as noted) ---
COST_PER_ACRE_CLEARING = 3_000
COST_PER_ACRE_GRADING = 1_500
DRIVEWAY_COST_PER_FOOT = 25
DEFAULT_DRIVEWAY_LENGTH_FEET = 300

WELL_COST_FLAT = 12_000
SEPTIC_COST_FLAT = 15_000
ELECTRICAL_HOOKUP_COST_FLAT = 8_000

SURVEY_COST_FLAT = 2_500
ENGINEERING_COST_FLAT = 4_000
PERMITS_COST_FLAT = 3_500

# --- Home construction ---
CONSTRUCTION_COST_PER_SQFT = 175
DEFAULT_HOME_SQFT = 1_800

# --- Solar ---
SOLAR_COST_PER_KW = 3_000
DEFAULT_SOLAR_SYSTEM_KW = 8

# --- Financing ---
MORTGAGE_DEFAULT_ANNUAL_RATE = 0.0675
MORTGAGE_DEFAULT_TERM_YEARS = 30
MORTGAGE_DEFAULT_DOWN_PAYMENT_PCT = 0.20
PMI_ANNUAL_RATE = 0.005  # applied only when down payment < 20%

# --- Recurring costs ---
PROPERTY_TAX_ANNUAL_RATE_DEFAULT = 0.008  # ~NC statewide rural average
HOMEOWNERS_INSURANCE_ANNUAL_RATE_DEFAULT = 0.0035
