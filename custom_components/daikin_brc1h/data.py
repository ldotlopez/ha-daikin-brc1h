"""Custom types for daikin_brc1h."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import kadoma
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .coordinator import KadomaDataUpdateCoordinator


type IntegrationKadomaConfigEntry = ConfigEntry[IntegrationKadomaData]


@dataclass
class IntegrationKadomaData:
    """Data for the Kadoma integration."""

    unit: kadoma.Unit
    coordinator: KadomaDataUpdateCoordinator
    integration: Integration
