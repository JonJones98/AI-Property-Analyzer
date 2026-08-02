import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings
from app.models.buildability import Buildability
from app.models.distances import Distances
from app.models.flood import Flood
from app.models.listing import Listing, ListingStatus
from app.models.parcel import Parcel
from app.models.scores import Scores
from app.models.soil import Soil
from app.models.utilities import Utilities
from app.providers.base import ListingProvider, RawListing, SearchCriteria
from app.schemas.listing import ListingFilterParams
from app.scoring.engine import compute_homestead_score
from app.scoring.schemas import HomesteadScoreInput
from app.services import enrichment


def _listing_relations_options():
    return (
        selectinload(Listing.parcel),
        selectinload(Listing.soil),
        selectinload(Listing.flood),
        selectinload(Listing.buildability),
        selectinload(Listing.utilities),
        selectinload(Listing.distances),
        selectinload(Listing.scores),
    )


async def _get_or_create_listing(db: AsyncSession, raw: RawListing) -> Listing:
    stmt = (
        select(Listing)
        .where(
            Listing.provider == raw.provider,
            Listing.provider_listing_id == raw.provider_listing_id,
        )
        .options(*_listing_relations_options())
    )
    result = await db.execute(stmt)
    listing = result.scalar_one_or_none()

    if listing is None:
        listing = Listing(
            provider=raw.provider,
            provider_listing_id=raw.provider_listing_id,
        )
        db.add(listing)

    listing.address = raw.address
    listing.county = raw.county
    listing.city = raw.city
    listing.zipcode = raw.zipcode
    listing.latitude = raw.latitude
    listing.longitude = raw.longitude
    listing.price = raw.price
    listing.acres = raw.acres
    listing.price_per_acre = raw.price_per_acre
    listing.status = ListingStatus(raw.status)
    listing.url = raw.url

    return listing


async def _upsert_one_to_one(db: AsyncSession, model_cls, listing_id: uuid.UUID, values: dict):
    existing = await db.get(model_cls, listing_id)
    if existing is None:
        existing = model_cls(listing_id=listing_id, **values)
        db.add(existing)
    else:
        for key, value in values.items():
            setattr(existing, key, value)
    return existing


async def enrich_and_score_listing(
    db: AsyncSession, listing: Listing, raw: RawListing, settings: Settings
) -> None:
    await db.flush()  # ensure listing.id is assigned

    distances = enrichment.estimate_distances(raw)
    soil = enrichment.estimate_soil(raw)
    flood_zone = enrichment.estimate_flood_zone(raw)
    buildability = enrichment.estimate_buildability(raw, soil["soil_rating"])
    utilities = enrichment.estimate_utilities(raw)
    parcel = enrichment.estimate_parcel(raw)

    await _upsert_one_to_one(db, Parcel, listing.id, parcel)
    await _upsert_one_to_one(db, Soil, listing.id, soil)
    await _upsert_one_to_one(db, Flood, listing.id, {"flood_zone": flood_zone})
    await _upsert_one_to_one(db, Buildability, listing.id, buildability)
    await _upsert_one_to_one(db, Utilities, listing.id, utilities)
    await _upsert_one_to_one(db, Distances, listing.id, distances)

    score_input = HomesteadScoreInput(
        price=listing.price,
        min_price=settings.default_search_min_price,
        max_price=settings.default_search_max_price,
        stretch_price=settings.default_search_stretch_price,
        acres=listing.acres,
        min_acres=settings.default_search_min_acres,
        max_acres=settings.default_search_max_acres,
        distance_costco=distances["costco"],
        distance_whole_foods=distances["whole_foods"],
        distance_walmart=distances["walmart"],
        distance_cvs=distances["cvs"],
        distance_home_depot=distances["home_depot"],
        distance_lowes=distances["lowes"],
        distance_hospital=distances["hospital"],
        distance_i85=distances["i85"],
        flood_zone=flood_zone,
        electric=utilities["electric"],
        internet=utilities["internet"],
        gas=utilities["gas"],
        soil_rating=soil["soil_rating"],
        perk_possible=soil["perk_possible"],
        estimated_site_cost=buildability["estimated_site_cost"],
        tax_value=parcel["tax_value"],
    )
    result = compute_homestead_score(score_input)

    await _upsert_one_to_one(
        db,
        Scores,
        listing.id,
        {
            "price_score": result.price_score,
            "location_score": result.location_score,
            "build_score": result.build_score,
            "overall_score": result.overall_score,
        },
    )


async def ingest_raw_listings(
    db: AsyncSession, raw_listings: list[RawListing], settings: Settings
) -> list[Listing]:
    listings: list[Listing] = []
    for raw in raw_listings:
        listing = await _get_or_create_listing(db, raw)
        await enrich_and_score_listing(db, listing, raw, settings)
        listings.append(listing)
    await db.commit()
    return listings


async def run_provider_search(
    db: AsyncSession,
    providers: list[ListingProvider],
    criteria: SearchCriteria,
    settings: Settings,
) -> list[Listing]:
    all_raw: list[RawListing] = []
    for provider in providers:
        all_raw.extend(await provider.search(criteria))
    return await ingest_raw_listings(db, all_raw, settings)


async def run_provider_updates(
    db: AsyncSession,
    providers: list[ListingProvider],
    settings: Settings,
    since: datetime | None = None,
) -> list[Listing]:
    since = since or (datetime.now(UTC) - timedelta(hours=12))
    all_raw: list[RawListing] = []
    for provider in providers:
        all_raw.extend(await provider.get_updates(since))
    return await ingest_raw_listings(db, all_raw, settings)


async def list_listings(db: AsyncSession, filters: ListingFilterParams) -> list[Listing]:
    stmt = select(Listing).options(*_listing_relations_options())

    if filters.county:
        stmt = stmt.where(Listing.county == filters.county)
    if filters.status:
        stmt = stmt.where(Listing.status == filters.status)
    if filters.min_price is not None:
        stmt = stmt.where(Listing.price >= filters.min_price)
    if filters.max_price is not None:
        stmt = stmt.where(Listing.price <= filters.max_price)
    if filters.min_acres is not None:
        stmt = stmt.where(Listing.acres >= filters.min_acres)
    if filters.max_acres is not None:
        stmt = stmt.where(Listing.acres <= filters.max_acres)
    if filters.road_frontage is not None:
        stmt = stmt.join(Listing.parcel).where(Parcel.road_frontage == filters.road_frontage)
    if filters.min_score is not None:
        stmt = stmt.join(Listing.scores).where(Scores.overall_score >= filters.min_score)

    stmt = stmt.order_by(Listing.last_updated.desc()).offset(filters.offset).limit(filters.limit)
    result = await db.execute(stmt)
    return list(result.scalars().unique().all())


async def get_listing(db: AsyncSession, listing_id: uuid.UUID) -> Listing | None:
    stmt = (
        select(Listing).where(Listing.id == listing_id).options(*_listing_relations_options())
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def dashboard_metrics(db: AsyncSession) -> dict:
    total_stmt = select(func.count(Listing.id)).where(Listing.status == ListingStatus.ACTIVE)
    avg_stmt = select(
        func.avg(Listing.price), func.avg(Listing.price_per_acre)
    ).where(Listing.status == ListingStatus.ACTIVE)
    top_score_stmt = (
        select(Listing.id, Scores.overall_score)
        .join(Listing.scores)
        .where(Listing.status == ListingStatus.ACTIVE)
        .order_by(Scores.overall_score.desc())
        .limit(1)
    )
    new_today_stmt = select(func.count(Listing.id)).where(
        Listing.created_at >= datetime.now(UTC) - timedelta(days=1)
    )
    county_stmt = (
        select(Listing.county, func.count(Listing.id), func.avg(Listing.price))
        .where(Listing.status == ListingStatus.ACTIVE)
        .group_by(Listing.county)
    )

    total = (await db.execute(total_stmt)).scalar_one()
    avg_price, avg_ppa = (await db.execute(avg_stmt)).one()
    top_row = (await db.execute(top_score_stmt)).first()
    new_today = (await db.execute(new_today_stmt)).scalar_one()
    county_rows = (await db.execute(county_stmt)).all()

    return {
        "properties_found": total,
        "average_price": round(avg_price or 0, 2),
        "average_price_per_acre": round(avg_ppa or 0, 2),
        "top_homestead_score": top_row[1] if top_row else None,
        "best_deal_listing_id": top_row[0] if top_row else None,
        "new_today": new_today,
        "county_breakdown": [
            {"county": county or "Unknown", "count": count, "avg_price": round(avg or 0, 2)}
            for county, count, avg in county_rows
        ],
    }
