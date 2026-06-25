"""
Custom integration to integrate daikin_brc1h with Home Assistant.

For more details about this integration, please refer to
https://github.com/ldotlopez/ha-daikin-brc1h
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.loader import async_get_loaded_integration

from .const import (
    COORDINATOR_UPDATE_INTERVAL,
    DOMAIN,
    DOMAIN_LOCK_KEY,
    LOGGER,
)
from .coordinator import KadomaDataUpdateCoordinator, hass_get_unit
from .data import IntegrationKadomaData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import IntegrationKadomaConfigEntry

PLATFORMS: list[Platform] = [Platform.CLIMATE]


def setup_domain_data(hass: HomeAssistant) -> None:
    """Set up shared data for all config entries."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    if DOMAIN_LOCK_KEY not in hass.data[DOMAIN]:
        hass.data[DOMAIN][DOMAIN_LOCK_KEY] = asyncio.Lock()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IntegrationKadomaConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    setup_domain_data(hass)

    unit = await hass_get_unit(hass, entry.data[CONF_ADDRESS], name=entry.title)

    coordinator = KadomaDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=COORDINATOR_UPDATE_INTERVAL,
        integration_lock=hass.data[DOMAIN][DOMAIN_LOCK_KEY],
    )

    entry.runtime_data = IntegrationKadomaData(
        unit=unit,
        lock=hass.data[DOMAIN][DOMAIN_LOCK_KEY],
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
