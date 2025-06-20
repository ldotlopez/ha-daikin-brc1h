"""DataUpdateCoordinator for daikin_brc1h."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, cast

import bleak.exc
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import LOGGER
from .retry import awaitable_retriable_ctx

if TYPE_CHECKING:
    import kadoma

    from .data import IntegrationKadomaConfigEntry


class KadomaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the unit."""

    config_entry: IntegrationKadomaConfigEntry

    def __init__(self, *args, lock: asyncio.Lock, **kwargs) -> None:
        """Initialize the coordinator."""
        super().__init__(*args, **kwargs)
        self.lock = lock

    async def _async_update_data(self) -> kadoma.UnitInfo:
        """Update data."""
        # TODO: # noqa: FIX002
        # Add a random delay if there's more than one integration in this domain
        # to decouple this call from the others.
        #
        # if there_is_more_than_one:
        #     await asyncio.sleep(self.update_interval.total_seconds() * 0.1)

        async def recover_unit(unit: kadoma.Unit) -> None:
            LOGGER.info(f"Resetting unit {unit}")
            await unit.reset()

        async with self.lock:
            try:
                with awaitable_retriable_ctx(
                    self.config_entry.runtime_data.unit.get_status,
                    allowed_exceptions=[asyncio.TimeoutError, bleak.exc.BleakError],
                    recover_awaitable=recover_unit,
                ) as get_status:
                    return await get_status()

            except Exception as exception:
                LOGGER.warning(
                    "Generic exception catched while updating unit status: "
                    f"{exception.__class__.__module__}.{exception.__class__.__name__}"
                )
                LOGGER.exception(exception)

                return cast(
                    "kadoma.UnitInfo", {"power_state": None, "operation_mode": None}
                )
