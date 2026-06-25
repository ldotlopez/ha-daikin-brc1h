"""DataUpdateCoordinator for daikin_brc1h."""

from __future__ import annotations

import asyncio
from logging import getLogger
from typing import TYPE_CHECKING

import bleak.exc
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from homeassistant.components import bluetooth
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from kadoma import Unit, UnitInfo
from kadoma.transport import Transport

from .const import (
    MAX_UNIT_RESET_ATTEMPS,
    RECOVER_DELAY,
)
from .retry import GiveUpError, await_with_retry

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import IntegrationKadomaConfigEntry


LOGGER = getLogger(__name__)


class UnitNotAvailableError(Exception):
    """Raised when a Kadoma unit is not available."""


async def hass_get_unit(
    hass: HomeAssistant, address: str, *, name: str | None = None
) -> Unit:
    """Get a Kadoma unit from Home Assistant by its Bluetooth address."""
    device = bluetooth.async_ble_device_from_address(hass, address, connectable=True)
    if device is None:
        raise ValueError(address)

    name = name or device.name or address

    client = await establish_connection(
        BleakClientWithServiceCache,
        device,
        name or device.name or address,
        max_attempts=3,
    )
    # 2026-06-23 14:18:15.389 DEBUG (MainThread) [custom_components.daikin_brc1h] F4:93:1C:97:84:A5: got client=<HaBleakClientWithServiceCache, F4:93:1C:97:84:A5, <class 'bleak.backends.bluezdbus.client.BleakClientBlueZDBus'>>
    LOGGER.debug(f"{name}: got client={client!r}")

    # try:
    #     await await_with_retry(
    #         transport.start,
    #         catch_exceptions=(TimeoutError, bleak.exc.BleakError),
    #         log_prefix=f"{name}: transport.start ",
    #     )
    # except GiveUpError as e:
    #     LOGGER.error(
    #         f"{name}: Unable to start unit '{address}': TimeoutError ({e!r})"
    #     )
    #     return False
    transport = Transport(client)
    await transport.start()
    # LOGGER.debug(f"{name}: transport ready ({transport!r})")

    unit = Unit(transport)
    await unit.start()
    # LOGGER.debug(f"{name}: unit ready ({unit!r})")

    return unit


async def unit_get_status_safe(unit: Unit) -> dict:
    """Safely query the status of a Kadoma unit."""
    knobs = {
        "clean_filter_indicator": unit.clean_filter_indicator,
        "fan_speed": unit.fan_speed,
        "operation_mode": unit.operation_mode,
        "power_state": unit.power_state,
        "sensors": unit.sensors,
        "set_point": unit.set_point,
    }

    ret = {}
    for k, knob in knobs.items():
        try:
            value = await knob.query()
        except Exception as e:
            LOGGER.exception(
                f"unknow exception '{e.__class__.__module__}.{e.__class__.__name__}' "
                f"while querying '{k}'"
            )
            value = None

        ret[k] = value

        await unit._delay()

    if all(v is None for v in ret.values()):
        raise UnitNotAvailableError

    return ret


async def unit_recover(unit: Unit) -> None:
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
                LOGGER.debug(f"{addr}: recover #{step} stopped successfully")

            await unit.start()
            LOGGER.debug(f"{addr}: recover #{step} started successfully")
            LOGGER.debug(f"{addr}: recover #{step} unit recovered")
            return

        except (TimeoutError, bleak.exc.BleakError) as e:
            LOGGER.debug(f"{addr}: recover #{step} failed with {e!r}")
            await asyncio.sleep(RECOVER_DELAY)

        except Exception as e:
            LOGGER.debug(
                f"{addr}: recover #{step} got unhandled exception"
                f" {e.__class__.__name__}"
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

    async def _async_update_data(self) -> UnitInfo | None:
        # TODO:
        # Add a random delay if there's more than one integration in this domain
        # to decouple this call from the others.
        #
        # if there_is_more_than_one:
        #     await asyncio.sleep(self.update_interval.total_seconds() * 0.1)

        async with self.integration_lock:
            addr = self.config_entry.runtime_data.unit.transport.client.address
            info = None
            try:
                info = await await_with_retry(
                    self._get_unit_status_safe,
                    catch_exceptions=(
                        asyncio.TimeoutError,
                        bleak.exc.BleakError,
                        UnitNotAvailableError,
                    ),
                    recover=self._recover_unit,
                    log_prefix=f"{addr}: get_status() ",
                )
            except GiveUpError:
                LOGGER.warning(f"{addr}: is not available")
                return info

            else:
                # await asyncio.sleep(random.range(0, 30) / 10)
                return info

    async def _get_unit_status_safe(self) -> dict:
        """Safely query the status of the unit."""
        return await unit_get_status_safe(self.config_entry.runtime_data.unit)

    async def _recover_unit(self) -> None:
        """Recover the unit."""
        await unit_recover(self.config_entry.runtime_data.unit)


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
