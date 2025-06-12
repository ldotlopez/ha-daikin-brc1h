"""Climate platform for integration_blueprint."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.climate import ClimateEntity, ClimateEntityDescription

from .entity import IntegrationKadomaEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import KadomaDataUpdateCoordinator
    from .data import IntegrationKadomaConfigEntry

ENTITY_DESCRIPTIONS = (
    ClimateEntityDescription(
        key="integration_blueprint",
        name="Integration Climate",
        icon="mdi:format-quote-close",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: IntegrationKadomaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    async_add_entities(
        IntegrationKadomaClimate(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class IntegrationKadomaClimate(IntegrationKadomaEntity, ClimateEntity):
    """integration_blueprint switch class."""

    def __init__(
        self,
        coordinator: KadomaDataUpdateCoordinator,
        entity_description: ClimateEntityDescription,
    ) -> None:
        """Initialize the switch class."""
        super().__init__(coordinator)
        self.entity_description = entity_description

    # @property
    # def is_on(self) -> bool:
    #     """Return true if the switch is on."""
    #     return self.coordinator.data.get("title", "") == "foo"

    # async def async_turn_on(self, **_: Any) -> None:
    #     """Turn on the switch."""
    #     await self.coordinator.config_entry.runtime_data.client.async_set_title("bar")
    #     await self.coordinator.async_request_refresh()

    # async def async_turn_off(self, **_: Any) -> None:
    #     """Turn off the switch."""
    #     await self.coordinator.config_entry.runtime_data.client.async_set_title("foo")
    #     await self.coordinator.async_request_refresh()
