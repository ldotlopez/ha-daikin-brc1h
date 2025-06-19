"""
Custom integration to integrate daikin_brc1h with Home Assistant.

For more details about this integration, please refer to
https://github.com/ldotlopez/ha-daikin-brc1h
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import kadoma
from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.loader import async_get_loaded_integration

from .const import COORDINATOR_UPDATE_INTERVAL, DOMAIN, LOGGER
from .coordinator import KadomaDataUpdateCoordinator
from .data import IntegrationKadomaData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import IntegrationKadomaConfigEntry

PLATFORMS: list[Platform] = [Platform.CLIMATE]


def setup_domain_data(hass: HomeAssistant) -> None:
    """Set up shared data for all config entries."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    if "lock" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["lock"] = asyncio.Lock()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IntegrationKadomaConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    setup_domain_data(hass)

    coordinator = KadomaDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=COORDINATOR_UPDATE_INTERVAL,
        lock=hass.data[DOMAIN]["lock"],
    )

    device = bluetooth.async_ble_device_from_address(
        hass, entry.data[CONF_ADDRESS], connectable=True
    )
    if device is None:
        LOGGER.error(f"Unable to get BLE device for '{entry.data[CONF_ADDRESS]}'")
        return False

    unit = kadoma.Unit(device)
    await unit.start()

    entry.runtime_data = IntegrationKadomaData(
        unit=unit,
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: IntegrationKadomaConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    await entry.runtime_data.unit.stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: IntegrationKadomaConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
