"""Climate platform for daikin_brc1h."""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

import kadoma
from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityDescription,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import PRECISION_WHOLE, UnitOfTemperature

from .const import LOGGER, MAX_TEMP, MIN_TEMP, TEMP_STEP
from .entity import IntegrationKadomaEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import KadomaDataUpdateCoordinator
    from .data import IntegrationKadomaConfigEntry

ENTITY_DESCRIPTIONS = (
    ClimateEntityDescription(
        key="daikin_brc1h",
        name="Daikin BRC1H thermostat",
        icon="mdi:air-conditioner",
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
    """daikin_brc1h climate class."""

    # For update entity after an update. The safer (but slow) strategy is to call
    # await self.coordinator.async_request_refresh()
    # ... but we don't do it.

    def __init__(
        self,
        coordinator: KadomaDataUpdateCoordinator,
        entity_description: ClimateEntityDescription,
    ) -> None:
        """Initialize the climate class."""
        super().__init__(coordinator)

        self.entity_description = entity_description

        self._attr_has_name = True
        self._attr_name = None
        self._attr_unique_id = self.unit.transport.client.address

        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_max_temp = MAX_TEMP
        self._attr_min_temp = MIN_TEMP
        self._attr_target_temperature_step = TEMP_STEP
        self._attr_precision = PRECISION_WHOLE
        self._attr_supported_features = (
            ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON
        )

        self._attr_hvac_modes = [
            HVACMode.AUTO,
            HVACMode.COOL,
            HVACMode.DRY,
            HVACMode.FAN_ONLY,
            HVACMode.HEAT,
            HVACMode.OFF,
        ]

        self._attr_fan_modes = [
            "auto",
            "low",
            "medium_low",
            "medium",
            "medium_high",
            "high",
        ]

    async def async_turn_on(self) -> None:
        await self.unit.power_state.update(state=True)
        self.coordinator.data["power_state"] = True
        self.async_write_ha_state()

    async def async_turn_off(self) -> None:
        await self.unit.power_state.update(state=False)
        self.coordinator.data["power_state"] = False
        self.async_write_ha_state()

    @cached_property
    def unit(self) -> kadoma.Unit:
        return self.coordinator.config_entry.runtime_data.unit

    @property
    def available(self) -> bool:
        return self.coordinator.data["operation_mode"] is not None

    @property
    def hvac_mode(self) -> HVACMode | None:
        if self.coordinator.data["power_state"] is False:
            return HVACMode.OFF

        m = {
            kadoma.OperationModeValue.AUTO: HVACMode.AUTO,
            kadoma.OperationModeValue.COOL: HVACMode.COOL,
            kadoma.OperationModeValue.DRY: HVACMode.DRY,
            kadoma.OperationModeValue.FAN: HVACMode.FAN_ONLY,
            kadoma.OperationModeValue.HEAT: HVACMode.HEAT,
        }

        operation_mode = self.coordinator.data["operation_mode"]
        if operation_mode is None:
            LOGGER.error("operation mode is unavailable")
            return None

        try:
            return m[operation_mode]
        except KeyError:
            LOGGER.warning(f"unsupported operation mode '{operation_mode}'")
            return None

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode is HVACMode.OFF:
            await self.unit.power_state.update(state=False)
            self.coordinator.data["power_state"] = False
            self.async_write_ha_state()
            return

        m = {
            HVACMode.AUTO: kadoma.OperationModeValue.AUTO,
            HVACMode.COOL: kadoma.OperationModeValue.COOL,
            HVACMode.DRY: kadoma.OperationModeValue.DRY,
            HVACMode.FAN_ONLY: kadoma.OperationModeValue.FAN,
            HVACMode.HEAT: kadoma.OperationModeValue.HEAT,
        }

        try:
            unit_mode = m[hvac_mode]
        except KeyError:
            LOGGER.warning(f"unsupported HVAC mode '{hvac_mode}'")
            return

        if self.coordinator.data["power_state"] is False:
            await self.unit.power_state.update(state=True)
            self.coordinator.data["power_state"] = True

        await self.unit.operation_mode.update(unit_mode)
        self.coordinator.data["operation_mode"] = unit_mode
        self.async_write_ha_state()

    @property
    def fan_mode(self) -> str | None:
        m = {
            kadoma.FanSpeedValue.AUTO: "auto",
            kadoma.FanSpeedValue.HIGH: "high",
            kadoma.FanSpeedValue.MID_HIGH: "medium_high",
            kadoma.FanSpeedValue.MID: "medium",
            kadoma.FanSpeedValue.MID_LOW: "medium_low",
            kadoma.FanSpeedValue.LOW: "low",
        }
        if self.coordinator.data["fan_speed"] is None:
            LOGGER.error("fan mode is unavailable")
            return None

        cooling_fan_speed, heating_fan_speed = self.coordinator.data["fan_speed"]

        operation_mode = self.coordinator.data["operation_mode"]
        if operation_mode is kadoma.OperationModeValue.HEAT:
            fan_speed = heating_fan_speed
        elif operation_mode is kadoma.OperationModeValue.COOL:
            fan_speed = cooling_fan_speed
        else:
            if cooling_fan_speed != heating_fan_speed:
                LOGGER.warning(
                    f"Fan speeds for"
                    f" cooling ({cooling_fan_speed.name})"
                    f" and heating ({heating_fan_speed.name})"
                    f" missmatch."
                )
            LOGGER.info(
                f"Using cooling fan speed for mode '{operation_mode.name}'"
                " but it may be incorrect"
            )
            fan_speed = cooling_fan_speed

        try:
            return m[fan_speed]
        except KeyError:
            LOGGER.warning(f"unsupported fan speed '{fan_speed}'")
            return None

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        m = {
            "auto": kadoma.FanSpeedValue.AUTO,
            "high": kadoma.FanSpeedValue.HIGH,
            "medium_high": kadoma.FanSpeedValue.MID_HIGH,
            "medium": kadoma.FanSpeedValue.MID,
            "medium_low": kadoma.FanSpeedValue.MID_LOW,
            "low": kadoma.FanSpeedValue.LOW,
        }

        try:
            fan_speed = m[fan_mode]
        except KeyError:
            LOGGER.warning(f"unsupported fan mode '{fan_mode}'")
            return

        await self.unit.fan_speed.update(cooling=fan_speed, heating=fan_speed)
        self.coordinator.data["fan_speed"] = (fan_speed, fan_speed)
        self.async_write_ha_state()

    @property
    def target_temperature(self) -> float | None:
        if self.coordinator.data["set_point"] is None:
            LOGGER.error("fan mode is unavailable")
            return None

        operation_mode = self.coordinator.data["operation_mode"]
        set_point = self.coordinator.data.get("set_point", {})

        if operation_mode is kadoma.OperationModeValue.HEAT:
            temp = set_point.get("heating_set_point")

        elif operation_mode is kadoma.OperationModeValue.COOL:
            temp = set_point.get("cooling_set_point")

        elif operation_mode is kadoma.OperationModeValue.FAN:
            # FAN has no temperature
            return None

        else:  # AUTO ?
            cooling = set_point.get("cooling_set_point")
            heating = set_point.get("heating_set_point")

            if cooling is None or heating is None:
                temp = None
            else:
                LOGGER.warning(
                    f"guessing temperature in mode '{operation_mode.name}' as the mean"
                    f" of cooling ({cooling}) and heating ({heating})"
                )
                temp = round((heating + cooling) / 2)

        if temp is None:
            LOGGER.error("set point temperatures are unavailable")
            return None

        return temp

    async def async_set_temperature(self, *, temperature: float, **kwargs) -> None:
        temperature = round(temperature)

        await self.unit.set_point.update(cooling=temperature, heating=temperature)
        self.coordinator.data["set_point"].update(
            {"cooling_set_point": temperature, "heating_set_point": temperature}
        )
        self.async_write_ha_state()
