from pydantic import BaseModel

from app.cost_estimator import constants as c


class CostEstimateInput(BaseModel):
    land_price: float
    acres: float

    needs_well: bool = True
    needs_septic: bool = True
    driveway_length_feet: float = c.DEFAULT_DRIVEWAY_LENGTH_FEET
    home_sqft: float = c.DEFAULT_HOME_SQFT
    solar_system_kw: float = c.DEFAULT_SOLAR_SYSTEM_KW
    include_solar: bool = True

    down_payment_pct: float = c.MORTGAGE_DEFAULT_DOWN_PAYMENT_PCT
    annual_interest_rate: float = c.MORTGAGE_DEFAULT_ANNUAL_RATE
    term_years: int = c.MORTGAGE_DEFAULT_TERM_YEARS

    assessed_tax_value: float | None = None


class CostEstimateResult(BaseModel):
    land_purchase: float
    site_clearing: float
    grading: float
    driveway: float
    well: float
    septic: float
    electrical: float
    survey: float
    engineering: float
    permits: float
    construction_cost: float
    solar: float
    total_project_cost: float

    down_payment: float
    loan_amount: float
    monthly_mortgage: float
    monthly_taxes: float
    monthly_insurance: float
    monthly_pmi: float
    total_monthly_payment: float
