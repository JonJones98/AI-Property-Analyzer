from app.cost_estimator.engine import estimate_costs
from app.cost_estimator.schemas import CostEstimateInput


def test_total_project_cost_includes_every_line_item():
    result = estimate_costs(CostEstimateInput(land_price=100_000, acres=15))

    line_items = [
        result.land_purchase,
        result.site_clearing,
        result.grading,
        result.driveway,
        result.well,
        result.septic,
        result.electrical,
        result.survey,
        result.engineering,
        result.permits,
        result.construction_cost,
        result.solar,
    ]
    assert result.total_project_cost == round(sum(line_items), 2)


def test_skipping_well_and_septic_reduces_total():
    with_utilities = estimate_costs(CostEstimateInput(land_price=100_000, acres=15))
    without_utilities = estimate_costs(
        CostEstimateInput(land_price=100_000, acres=15, needs_well=False, needs_septic=False)
    )
    assert without_utilities.total_project_cost < with_utilities.total_project_cost
    assert without_utilities.well == 0
    assert without_utilities.septic == 0


def test_pmi_applies_only_below_twenty_percent_down():
    low_down = estimate_costs(
        CostEstimateInput(land_price=100_000, acres=15, down_payment_pct=0.10)
    )
    full_down = estimate_costs(
        CostEstimateInput(land_price=100_000, acres=15, down_payment_pct=0.20)
    )
    assert low_down.monthly_pmi > 0
    assert full_down.monthly_pmi == 0


def test_monthly_payment_is_sum_of_components():
    result = estimate_costs(CostEstimateInput(land_price=100_000, acres=15))
    components = [
        result.monthly_mortgage,
        result.monthly_taxes,
        result.monthly_insurance,
        result.monthly_pmi,
    ]
    expected = round(sum(components), 2)
    assert result.total_monthly_payment == expected
