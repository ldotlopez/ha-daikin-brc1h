"""DataUpdateCoordinator for daikin_brc1h."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import bleak.exc
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import LOGGER, MAX_UNIT_RESET_ATTEMPS, RECOVER_DELAY
from .retry import GiveUpError, await_with_retry

if TYPE_CHECKING:
    import kadoma

    from .data import IntegrationKadomaConfigEntry


async def unit_recover(unit: kadoma.Unit) -> None:
    """
    Attempt to recover a unit by stopping and starting it with retries.

    This function tries to re-establish a working connection with the unit
    by first attempting to stop it (if connected) and then starting it.
    It performs multiple attempts, logging progress and failures.

    Args:
        unit: The `kadoma.Unit` instance to attempt recovery on.
              It is expected to have `transport.client.address`,
              `transport.client.is_connected`, `stop()`, and `start()` methods.

    Raises:
        GiveUpError: If all `MAX_UNIT_RESET_ATTEMPS` fail to recover the unit,
                     or if an unexpected exception occurs during any attempt.

    """
    for attempt in range(MAX_UNIT_RESET_ATTEMPS):
        addr = unit.transport.client.address
        step = f"{attempt + 1}/{MAX_UNIT_RESET_ATTEMPS}"

        LOGGER.debug(f"{addr}: Recovering unit #{step}")

        try:
            # By-pass any possible configured or unconfigured unit delay
            if unit.transport.client.is_connected:
                await unit.stop()
                await asyncio.sleep(RECOVER_DELAY)
                LOGGER.debug(f"{addr}: recover #{step} stop successfully ")

            await unit.start()
            LOGGER.debug(f"{addr}: recover #{step} start successfully")
            LOGGER.debug(f"{addr}: recover #{step} unit recovered!")
            return

        except (TimeoutError, bleak.exc.BleakError) as e:
            LOGGER.debug(f"{addr}: recover #{step} failed with {e!r}")
            await asyncio.sleep(RECOVER_DELAY)

        except Exception as e:
            LOGGER.debug(
                f"{addr}: recover #{step} got unhandled exception {e.__class__}"
            )
            raise

    raise GiveUpError


class KadomaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the unit."""

    config_entry: IntegrationKadomaConfigEntry

    def __init__(self, *args, integration_lock: asyncio.Lock, **kwargs) -> None:
        """Initialize the coordinator."""
        super().__init__(*args, **kwargs)
        self.integration_lock = integration_lock

    async def _async_update_data(self) -> kadoma.UnitInfo:
        # TODO:
        # Add a random delay if there's more than one integration in this domain
        # to decouple this call from the others.
        #
        # if there_is_more_than_one:
        #     await asyncio.sleep(self.update_interval.total_seconds() * 0.1)

        addr = self.config_entry.runtime_data.unit.transport.client.address
        return await await_with_retry(
            lambda: self.config_entry.runtime_data.unit.get_status(),
            catch_exceptions=(asyncio.TimeoutError, bleak.exc.BleakError),
            recover=lambda: unit_recover(self.config_entry.runtime_data.unit),
            log_prefix=f"{addr}: get_status() ",
        )

    # async def _async_update_data(self) -> kadoma.UnitInfo:
    #     async with self.integration_lock:
    #         while True:
    #             try:
    #                 return await self.config_entry.runtime_data.unit.get_status()
    #             except (TimeoutError, bleak.exc.BleakError):
    #                 await try_unit_reset(self.config_entry.runtime_data.unit)

    # async def _async_update_data_(self) -> kadoma.UnitInfo:
    #     """Update data."""
    #     async def recover_unit() -> None:
    #         LOGGER.info(f"Resetting unit {self.config_entry.runtime_data.unit}")
    #         await self.config_entry.runtime_data.unit.reset()

    #     async with self.integration_lock:
    #         try:
    #             with awaitable_retriable_ctx(
    #                 self.config_entry.runtime_data.unit.get_status,
    #                 allowed_exceptions=[asyncio.TimeoutError, bleak.exc.BleakError],
    #                 recover_awaitable=recover_unit,
    #             ) as get_status:
    #                 return await get_status()

    #         except Exception as exception:
    #             LOGGER.warning(
    #                 "Generic exception catched while updating unit status: "
    #                 f"{exception.__class__.__module__}.{exception.__class__.__name__}"
    #             )
    #             LOGGER.exception(exception)

    #             return cast(
    #                 kadoma.UnitInfo, {"power_state": None, "operation_mode": None}
    #             )
