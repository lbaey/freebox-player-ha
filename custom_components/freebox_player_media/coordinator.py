"""DataUpdateCoordinator for freebox_player_media."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from freebox_api import Freepybox
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import LOGGER, SCAN_INTERVAL_SECONDS


class FreeboxPlayerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to poll a single Freebox Player's status."""

    def __init__(
        self,
        hass: HomeAssistant,
        fbx: Freepybox,
        player_id: int,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            name=f"Freebox Player {player_id}",
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.fbx = fbx
        self.player_id = player_id

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch player status from the Freebox API."""
        try:
            data = await self.fbx.player.get_player_status(self.player_id)
            # Temporary debug: log structure keys
            fg = data.get("foreground_app", {})
            ctx = fg.get("context", {})
            ch = ctx.get("channel", {})
            ch_keys = {k: type(v).__name__ for k, v in ch.items()}
            LOGGER.warning(
                "Player %s keys: top=%s | fg=%s | ctx=%s | channel=%s | channel.name=%s | channel.number=%s",
                self.player_id,
                list(data.keys()),
                list(fg.keys()),
                list(ctx.keys()),
                ch_keys,
                ch.get("name"),
                ch.get("number"),
            )
            return data
        except Exception as exception:
            raise UpdateFailed(exception) from exception
