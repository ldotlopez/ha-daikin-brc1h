"""DataUpdateCoordinator for daikin_brc1h."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import LOGGER

if TYPE_CHECKING:
    from .data import IntegrationKadomaConfigEntry


class KadomaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the unit."""

    config_entry: IntegrationKadomaConfigEntry

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            return await self.config_entry.runtime_data.unit.get_status()
        except Exception as exception:
            LOGGER.warning(
                "Generic exception catched while updating unit status: "
                f"{exception.__class__.__module__}.{exception.__class__.__name__}"
            )
            LOGGER.exception(exception)
