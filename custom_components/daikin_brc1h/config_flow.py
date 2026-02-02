"""Adds config flow for Kadoma."""

from __future__ import annotations

import bleak.exc
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS
from homeassistant.helpers import selector
from kadoma import Unit
from kadoma.transport import get_transport
from slugify import slugify

from .const import BLUETOOTH_DISCOVERY_TIMEOUT, DOMAIN, LOGGER, REPOSITORY_URL


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
                await self._test_device(user_input[CONF_ADDRESS])

            except bleak.exc.BleakError as e:
                LOGGER.warning(
                    "Exception catched: "
                    f"{e.__class__.__module__}.{e.__class__.__name__}"
                )
                LOGGER.exception(e)
                _errors["generic"] = str(e)

            else:
                await self.async_set_unique_id(
                    unique_id=slugify(user_input[CONF_ADDRESS])
                )
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_ADDRESS],
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

    # async def async_step_user(
    #     self,
    #     user_input: dict | None = None,
    # ) -> config_entries.ConfigFlowResult:
    #     """Handle a flow initialized by the user."""
    #     _errors = {}
    #     if user_input is not None:
    #         try:
    #             await self._test_credentials(
    #                 username=user_input[CONF_USERNAME],
    #                 password=user_input[CONF_PASSWORD],
    #             )
    #         except IntegrationKadomaApiClientAuthenticationError as exception:
    #             LOGGER.warning(exception)
    #             _errors["base"] = "auth"
    #         except IntegrationKadomaApiClientCommunicationError as exception:
    #             LOGGER.error(exception)
    #             _errors["base"] = "connection"
    #         except IntegrationKadomaApiClientError as exception:
    #             LOGGER.exception(exception)
    #             _errors["base"] = "unknown"
    #         else:
    #             await self.async_set_unique_id(
    #                 ## Do NOT use this in production code
    #                 ## The unique_id should never be something that can change
    #                 ## https://developers.home-assistant.io/docs/config_entries_config_flow_handler#unique-ids
    #                 unique_id=slugify(user_input[CONF_USERNAME])
    #             )
    #             self._abort_if_unique_id_configured()
    #             return self.async_create_entry(
    #                 title=user_input[CONF_USERNAME],
    #                 data=user_input,
    #             )
    #
    #     return self.async_show_form(
    #         step_id="user",
    #         data_schema=vol.Schema(
    #             {
    #                 vol.Required(
    #                     CONF_USERNAME,
    #                     default=(user_input or {}).get(CONF_USERNAME, vol.UNDEFINED),
    #                 ): selector.TextSelector(
    #                     selector.TextSelectorConfig(
    #                         type=selector.TextSelectorType.TEXT,
    #                     ),
    #                 ),
    #                 vol.Required(CONF_PASSWORD): selector.TextSelector(
    #                     selector.TextSelectorConfig(
    #                         type=selector.TextSelectorType.PASSWORD,
    #                     ),
    #                 ),
    #             },
    #         ),
    #         errors=_errors,
    #     )

    async def _test_device(self, address: str) -> None:
        device = bluetooth.async_ble_device_from_address(
            self.hass, address, connectable=True
        )
        if device is None:
            raise ValueError(address)

        async with get_transport(device) as transport:
            unit = Unit(transport)
            info = await unit.get_info()
            LOGGER.info(f"Successfully connected to '{address}': {info!r}")
