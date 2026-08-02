import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import DbSession
from app.cost_estimator.engine import estimate_costs
from app.cost_estimator.schemas import CostEstimateInput, CostEstimateResult
from app.services.listing_service import get_listing

router = APIRouter()


@router.post("/cost-estimator", response_model=CostEstimateResult)
async def post_cost_estimate(data: CostEstimateInput) -> CostEstimateResult:
    """Ad-hoc project cost estimate for arbitrary land price / acreage inputs."""
    return estimate_costs(data)


@router.get("/cost-estimator/{listing_id}", response_model=CostEstimateResult)
async def get_cost_estimate_for_listing(
    listing_id: uuid.UUID, db: DbSession
) -> CostEstimateResult:
    """Project cost estimate seeded from a specific listing's price/acreage/tax data."""
    listing = await get_listing(db, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")

    data = CostEstimateInput(
        land_price=listing.price,
        acres=listing.acres,
        needs_well=bool(listing.buildability and listing.buildability.well_required),
        needs_septic=bool(listing.buildability and listing.buildability.septic_required),
        assessed_tax_value=listing.parcel.tax_value if listing.parcel else None,
    )
    return estimate_costs(data)
