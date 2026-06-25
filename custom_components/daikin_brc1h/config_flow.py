"""Adds config flow for Kadoma."""

from __future__ import annotations

import bleak.exc
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS
from homeassistant.helpers import selector
from slugify import slugify

from .const import BLUETOOTH_DISCOVERY_TIMEOUT, DOMAIN, LOGGER, REPOSITORY_URL
from .coordinator import hass_get_unit


class KadomaFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Config flow for Kadoma."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        _errors: dict[str, str] = {}

        if user_input is not None:
            try:
                unit = await hass_get_unit(self.hass, user_input[CONF_ADDRESS])
                info = await unit.get_info()
                title = f"BRC1H {user_input[CONF_ADDRESS][-8:]}"
                # {'Device Information': {'Firmware Revision String': 'BL C0',
                #                         'Hardware Revision String': 'UEIS-15288',
                #                         'IEEE 11073-20601 Regulatory Cert. Data List': '3\x00\x00\x00\x00\x00',
                #                         'Manufacturer Name String': 'Universal Electronics, '
                #                                                     'Inc.',
                #                         'Model Number String': '0.1',
                #                         'PnP ID': '02:e7:06:31:70:10:01',
                #                         'Serial Number String': '1.2.3.4.5.6',
                #                         'Software Revision String': '7031.05.17',
                #                         'System ID': 'f4:93:1c:ff:fe:97:84:a5'},
                #  'Generic Access Profile': {'Appearance': '\x00\x00',
                #                             'Central Address Resolution': '\x00',
                #                             'Device Name': 'UE878 RF MODULE'},
                #  'Generic Attribute Profile': {},
                #  'Unknown': {}}

                # 2026-06-23 14:18:16.916 INFO (MainThread) [custom_components.daikin_brc1h] Successfully connected to 'F4:93:1C:97:84:A5': {'Generic Access Profile': {'Device Name': 'UE878 RF MODULE', 'Appearance': '\x00\x00', 'Central Address Resolution': '\x00'}, 'Unknown': {}, 'Generic Attribute Profile': {}, 'Device Information': {'Software Revision String': '7031.05.17', 'System ID': 'f4:93:1c:ff:fe:97:84:a5', 'Hardware Revision String': 'UEIS-15288', 'Serial Number String': '1.2.3.4.5.6', 'Model Number String': '0.1', 'Firmware Revision String': 'BL C0', 'PnP ID': '02:e7:06:31:70:10:01', 'IEEE 11073-20601 Regulatory Cert. Data List': '3\x00\x00\x00\x00\x00', 'Manufacturer Name String': 'Universal Electronics, Inc.'}}
                LOGGER.info(
                    f"Successfully connected to '{user_input[CONF_ADDRESS]}': {info!r}"
                )

            except bleak.exc.BleakError as e:
                LOGGER.warning(
                    f"Exception caught: {e.__class__.__module__}.{e.__class__.__name__}"
                )
                LOGGER.exception(e)
                _errors["generic"] = str(e)

            else:
                await self.async_set_unique_id(unique_id=slugify(title))
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=title,
                    data=user_input,
                )

            opts = [user_input[CONF_ADDRESS]]

        else:
            scanner = bluetooth.async_get_scanner(self.hass)
            devices = await scanner.discover(timeout=BLUETOOTH_DISCOVERY_TIMEOUT)
            # opts = ["{} ({})".format(d.name or d.address, d.address) for d in devices]
            opts = sorted([d.address for d in devices])

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ADDRESS,
                        default=(user_input or {}).get(CONF_ADDRESS, vol.UNDEFINED),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(multiple=False, options=opts)
                    )
                }
            ),
            description_placeholders={"repository_url": REPOSITORY_URL},
            errors=_errors,
        )
