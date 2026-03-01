"""Freebox Player Media integration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from freebox_api import Freepybox
from freebox_api.exceptions import InsufficientPermissionsError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.storage import Store
from slugify import slugify

from .const import APP_DESC, API_VERSION, DOMAIN, LOGGER, STORAGE_KEY, STORAGE_VERSION
from .coordinator import FreeboxPlayerCoordinator

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]

type FreeboxPlayerConfigEntry = ConfigEntry[FreeboxPlayerData]


@dataclass
class FreeboxPlayerData:
    """Runtime data for a Freebox Player config entry."""

    fbx: Freepybox
    players: list[dict[str, Any]]
    channels: dict[str, dict[str, Any]] = field(default_factory=dict)
    coordinators: dict[int, FreeboxPlayerCoordinator] = field(default_factory=dict)


async def get_api(hass: HomeAssistant, host: str) -> Freepybox:
    """Create a Freepybox instance with token stored in HA storage."""
    store_path = Store(hass, STORAGE_VERSION, STORAGE_KEY).path
    if not os.path.exists(store_path):
        await hass.async_add_executor_job(os.makedirs, store_path)
    token_file = Path(f"{store_path}/{slugify(host)}.conf")
    return Freepybox(APP_DESC, token_file, API_VERSION)


async def async_setup_entry(
    hass: HomeAssistant, entry: FreeboxPlayerConfigEntry
) -> bool:
    """Set up Freebox Player Media from a config entry."""
    host: str = entry.data[CONF_HOST]
    port: int = entry.data[CONF_PORT]

    fbx = await get_api(hass, host)
    await fbx.open(host, port)

    try:
        players: list[dict[str, Any]] = await fbx.player.get_players()
    except InsufficientPermissionsError as err:
        await fbx.close()
        LOGGER.error(
            "Permission 'player' manquante pour l'app 'HA Freebox Player'. "
            "Activez-la dans Freebox OS → Paramètres → Gestion des accès → "
            "Applications → HA Freebox Player → cochez 'Player'"
        )
        raise ConfigEntryNotReady(
            "Permission 'player' manquante. Activez-la dans Freebox OS "
            "(Gestion des accès → Applications → HA Freebox Player)."
        ) from err

    # Try to fetch TV channels for metadata (logos, etc.)
    channels: dict[str, dict[str, Any]] = {}
    try:
        raw_channels = await fbx.tv.get_tv_channels()
        LOGGER.warning("Loaded %d TV channels. Sample: %s", len(raw_channels), [{"uuid": ch.get("uuid",""), "name": ch.get("name",""), "logo": ch.get("logo_url","")} for ch in raw_channels[:3]])
        for ch in raw_channels:
            uuid = ch.get("uuid", "")
            channels[uuid] = {
                "name": ch.get("name", ""),
                "number": ch.get("number"),
                "logo_url": ch.get("logo_url", ""),
            }
    except Exception as err:  # noqa: BLE001
        LOGGER.warning("TV channel list unavailable (%s: %s), skipping channel cache", type(err).__name__, err)

    # Create a coordinator per player.
    coordinators: dict[int, FreeboxPlayerCoordinator] = {}
    for player in players:
        player_id: int = player["id"]
        coordinator = FreeboxPlayerCoordinator(hass, fbx, player_id)
        await coordinator.async_config_entry_first_refresh()
        coordinators[player_id] = coordinator

    entry.runtime_data = FreeboxPlayerData(
        fbx=fbx,
        players=players,
        channels=channels,
        coordinators=coordinators,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: FreeboxPlayerConfigEntry
) -> bool:
    """Unload a Freebox Player Media config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.fbx.close()
    return unload_ok
