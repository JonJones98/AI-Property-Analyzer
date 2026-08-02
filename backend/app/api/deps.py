from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db as _get_db
from app.providers.base import ListingProvider
from app.providers.registry import get_active_providers


async def get_db() -> AsyncGenerator[AsyncSession]:
    async for session in _get_db():
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def get_providers(settings: AppSettings) -> list[ListingProvider]:
    return get_active_providers(settings.active_provider_keys)


Providers = Annotated[list[ListingProvider], Depends(get_providers)]
