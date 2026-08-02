from app.providers.base import ListingProvider
from app.providers.mock_nc_land import MockNCLandProvider

#: Register every available provider here. Adding a real provider (e.g. an
#: MLS/RESO feed, a licensed land-listing API) means writing one class that
#: implements `ListingProvider` and adding one line below — nothing else in
#: the app needs to change since routes/jobs depend only on the interface.
PROVIDER_REGISTRY: dict[str, type[ListingProvider]] = {
    "mock_nc_land": MockNCLandProvider,
}


def get_active_providers(provider_keys: list[str]) -> list[ListingProvider]:
    providers: list[ListingProvider] = []
    for key in provider_keys:
        provider_cls = PROVIDER_REGISTRY.get(key)
        if provider_cls is None:
            raise ValueError(
                f"Unknown listing provider '{key}'. Registered providers: "
                f"{list(PROVIDER_REGISTRY)}"
            )
        providers.append(provider_cls())
    return providers
