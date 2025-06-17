"""DataUpdateCoordinator for daikin_brc1h."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    IntegrationKadomaApiClientAuthenticationError,
    IntegrationKadomaApiClientError,
)

if TYPE_CHECKING:
    from .data import IntegrationKadomaConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class KadomaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: IntegrationKadomaConfigEntry

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            return await self.config_entry.runtime_data.unit.get_status()
        except IntegrationKadomaApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except IntegrationKadomaApiClientError as exception:
            raise UpdateFailed(exception) from exception
