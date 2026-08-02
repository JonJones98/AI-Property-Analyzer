from app.scoring.engine import (
    compute_homestead_score,
    score_acreage,
    score_color,
    score_flood,
    score_price,
    score_utilities,
)
from app.scoring.schemas import HomesteadScoreInput


def test_score_price_at_or_below_min_is_perfect():
    score = score_price(price=70_000, min_price=80_000, max_price=125_000, stretch_price=150_000)
    assert score == 100.0


def test_score_price_at_max_budget_matches_band():
    score = score_price(
        price=125_000, min_price=80_000, max_price=125_000, stretch_price=150_000
    )
    assert score == 60.0


def test_score_price_above_stretch_is_zero():
    score = score_price(
        price=200_000, min_price=80_000, max_price=125_000, stretch_price=150_000
    )
    assert score == 0.0


def test_score_acreage_within_range_is_perfect():
    assert score_acreage(acres=15, min_acres=10, max_acres=20) == 100.0


def test_score_acreage_outside_range_decays():
    below = score_acreage(acres=5, min_acres=10, max_acres=20)
    above = score_acreage(acres=25, min_acres=10, max_acres=20)
    assert 0 <= below < 100
    assert 0 <= above < 100


def test_score_flood_zone_bands():
    assert score_flood("X") == 100.0
    assert score_flood("AE") == 0.0
    assert score_flood(None) == 50.0


def test_score_utilities_full_house():
    assert score_utilities(electric=True, internet=True, gas=True) == 100.0
    assert score_utilities(electric=False, internet=False, gas=False) == 0.0


def test_score_color_bands():
    assert score_color(95) == "green"
    assert score_color(85) == "blue"
    assert score_color(75) == "yellow"
    assert score_color(50) == "red"


def test_compute_homestead_score_end_to_end_ideal_listing():
    data = HomesteadScoreInput(
        price=100_000,
        min_price=80_000,
        max_price=125_000,
        stretch_price=150_000,
        acres=15,
        min_acres=10,
        max_acres=20,
        distance_costco=20,
        distance_whole_foods=20,
        distance_walmart=10,
        distance_cvs=10,
        distance_home_depot=15,
        distance_lowes=15,
        distance_hospital=20,
        distance_i85=5,
        flood_zone="X",
        electric=True,
        internet=True,
        gas=True,
        soil_rating=90,
        perk_possible=True,
        estimated_site_cost=3_000,
        tax_value=1_500,
    )
    result = compute_homestead_score(data)
    assert result.overall_score > 90
    assert result.color == "green"
    assert set(result.components) == {
        "price",
        "acreage",
        "shopping",
        "healthcare",
        "interstate",
        "flood",
        "utilities",
        "soil",
        "buildability",
        "appreciation",
        "internet",
        "tax_rate",
    }


def test_compute_homestead_score_poor_listing_scores_low():
    data = HomesteadScoreInput(
        price=180_000,
        min_price=80_000,
        max_price=125_000,
        stretch_price=150_000,
        acres=2,
        min_acres=10,
        max_acres=20,
        distance_costco=90,
        distance_whole_foods=90,
        distance_walmart=60,
        distance_cvs=60,
        distance_home_depot=90,
        distance_lowes=90,
        distance_hospital=90,
        distance_i85=60,
        flood_zone="AE",
        electric=False,
        internet=False,
        gas=False,
        soil_rating=10,
        perk_possible=False,
        estimated_site_cost=60_000,
        tax_value=50_000,
    )
    result = compute_homestead_score(data)
    assert result.overall_score < 30
    assert result.color == "red"
