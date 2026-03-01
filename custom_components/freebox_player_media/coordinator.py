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
            LOGGER.warning("Player %s raw data: %s", self.player_id, data)
            return data
        except Exception as exception:
            raise UpdateFailed(exception) from exception
