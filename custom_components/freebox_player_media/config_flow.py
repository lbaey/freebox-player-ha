"""Config flow for Freebox Player Media."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from freebox_api.exceptions import AuthorizationError, HttpRequestError
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DEFAULT_HOST, DEFAULT_PORT, DOMAIN


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
    }
)


class FreeboxPlayerMediaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Freebox Player Media."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step to enter host and port."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        await self.async_set_unique_id(user_input[CONF_HOST])
        self._abort_if_unique_id_configured()

        self._data = user_input
        return await self.async_step_link()

    async def async_step_link(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the link step: user presses the button on the Freebox."""
        if user_input is None:
            return self.async_show_form(step_id="link")

        errors: dict[str, str] = {}
        try:
            # Import here to avoid circular imports.
            from . import get_api

            fbx = await get_api(self.hass, self._data[CONF_HOST])
            await fbx.open(self._data[CONF_HOST], self._data[CONF_PORT])
            await fbx.system.get_config()
            await fbx.close()
            return self.async_create_entry(
                title=self._data[CONF_HOST], data=self._data
            )
        except AuthorizationError:
            errors["base"] = "register_failed"
        except HttpRequestError:
            errors["base"] = "cannot_connect"
        except Exception:  # noqa: BLE001
            errors["base"] = "unknown"

        return self.async_show_form(step_id="link", errors=errors)
