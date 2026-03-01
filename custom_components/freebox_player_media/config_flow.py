"""Config flow for Freebox Player Media."""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol
from freebox_api.exceptions import AuthorizationError, HttpRequestError
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DEFAULT_HOST, DOMAIN, LOGGER

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
    }
)


async def _discover_api(host: str) -> tuple[str, int]:
    """Discover the real API domain and HTTPS port from the Freebox."""
    async with aiohttp.ClientSession() as session:
        # Try HTTPS first (port 443), then HTTP (port 80)
        for url in [f"https://{host}/api_version", f"http://{host}/api_version"]:
            try:
                async with session.get(url, ssl=False, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        api_domain = data.get("api_domain", host)
                        https_port = int(data.get("https_port", 443))
                        return api_domain, https_port
            except Exception:  # noqa: BLE001
                continue
    return host, 443


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

        host = user_input[CONF_HOST]

        # Discover the real API domain and HTTPS port
        api_domain, https_port = await _discover_api(host)
        LOGGER.info(
            "Freebox discovery: %s -> api_domain=%s, https_port=%s",
            host, api_domain, https_port,
        )

        await self.async_set_unique_id(api_domain)
        self._abort_if_unique_id_configured()

        self._data = {CONF_HOST: api_domain, CONF_PORT: https_port}
        return await self.async_step_link()

    async def async_step_link(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the link step: user presses the button on the Freebox."""
        if user_input is None:
            return self.async_show_form(step_id="link")

        errors: dict[str, str] = {}
        try:
            from . import get_api

            fbx = await get_api(self.hass, self._data[CONF_HOST])
            LOGGER.info(
                "Config flow: calling fbx.open(%s, %s)",
                self._data[CONF_HOST], self._data[CONF_PORT],
            )
            await fbx.open(self._data[CONF_HOST], self._data[CONF_PORT])
            LOGGER.info("Config flow: fbx.open() succeeded")
            await fbx.system.get_config()
            await fbx.close()
            return self.async_create_entry(
                title=self._data[CONF_HOST], data=self._data
            )
        except AuthorizationError as err:
            LOGGER.error("Config flow: AuthorizationError: %s", err)
            errors["base"] = "register_failed"
        except HttpRequestError as err:
            LOGGER.error("Config flow: HttpRequestError: %s", err)
            errors["base"] = "cannot_connect"
        except Exception as err:  # noqa: BLE001
            LOGGER.error("Config flow: unexpected error: %s: %s", type(err).__name__, err)
            errors["base"] = "unknown"

        return self.async_show_form(step_id="link", errors=errors)
