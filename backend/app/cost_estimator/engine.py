from app.cost_estimator import constants as c
from app.cost_estimator.schemas import CostEstimateInput, CostEstimateResult


def _monthly_amortized_payment(principal: float, annual_rate: float, term_years: int) -> float:
    if principal <= 0:
        return 0.0
    monthly_rate = annual_rate / 12
    num_payments = term_years * 12
    if monthly_rate == 0:
        return round(principal / num_payments, 2)
    factor = (1 + monthly_rate) ** num_payments
    return round(principal * monthly_rate * factor / (factor - 1), 2)


def estimate_costs(data: CostEstimateInput) -> CostEstimateResult:
    site_clearing = data.acres * c.COST_PER_ACRE_CLEARING
    grading = data.acres * c.COST_PER_ACRE_GRADING
    driveway = data.driveway_length_feet * c.DRIVEWAY_COST_PER_FOOT
    well = c.WELL_COST_FLAT if data.needs_well else 0.0
    septic = c.SEPTIC_COST_FLAT if data.needs_septic else 0.0
    electrical = c.ELECTRICAL_HOOKUP_COST_FLAT
    survey = c.SURVEY_COST_FLAT
    engineering = c.ENGINEERING_COST_FLAT
    permits = c.PERMITS_COST_FLAT
    construction_cost = data.home_sqft * c.CONSTRUCTION_COST_PER_SQFT
    solar = data.solar_system_kw * c.SOLAR_COST_PER_KW if data.include_solar else 0.0

    total_project_cost = (
        data.land_price
        + site_clearing
        + grading
        + driveway
        + well
        + septic
        + electrical
        + survey
        + engineering
        + permits
        + construction_cost
        + solar
    )

    down_payment = total_project_cost * data.down_payment_pct
    loan_amount = total_project_cost - down_payment

    monthly_mortgage = _monthly_amortized_payment(
        loan_amount, data.annual_interest_rate, data.term_years
    )

    assessed_value = (
        data.assessed_tax_value if data.assessed_tax_value is not None else total_project_cost
    )
    monthly_taxes = round(assessed_value * c.PROPERTY_TAX_ANNUAL_RATE_DEFAULT / 12, 2)
    monthly_insurance = round(
        total_project_cost * c.HOMEOWNERS_INSURANCE_ANNUAL_RATE_DEFAULT / 12, 2
    )
    monthly_pmi = (
        round(loan_amount * c.PMI_ANNUAL_RATE / 12, 2)
        if data.down_payment_pct < 0.20
        else 0.0
    )

    total_monthly_payment = round(
        monthly_mortgage + monthly_taxes + monthly_insurance + monthly_pmi, 2
    )

    return CostEstimateResult(
        land_purchase=round(data.land_price, 2),
        site_clearing=round(site_clearing, 2),
        grading=round(grading, 2),
        driveway=round(driveway, 2),
        well=round(well, 2),
        septic=round(septic, 2),
        electrical=round(electrical, 2),
        survey=round(survey, 2),
        engineering=round(engineering, 2),
        permits=round(permits, 2),
        construction_cost=round(construction_cost, 2),
        solar=round(solar, 2),
        total_project_cost=round(total_project_cost, 2),
        down_payment=round(down_payment, 2),
        loan_amount=round(loan_amount, 2),
        monthly_mortgage=monthly_mortgage,
        monthly_taxes=monthly_taxes,
        monthly_insurance=monthly_insurance,
        monthly_pmi=monthly_pmi,
        total_monthly_payment=total_monthly_payment,
    )
