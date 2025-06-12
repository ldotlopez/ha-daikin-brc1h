"""Custom types for integration_blueprint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import IntegrationKadomaApiClient
    from .coordinator import KadomaDataUpdateCoordinator


type IntegrationKadomaConfigEntry = ConfigEntry[IntegrationKadomaData]


@dataclass
class IntegrationKadomaData:
    """Data for the Kadoma integration."""

    client: IntegrationKadomaApiClient
    coordinator: KadomaDataUpdateCoordinator
    integration: Integration
