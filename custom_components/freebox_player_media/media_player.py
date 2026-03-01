"""Media player entity for Freebox Player."""

from __future__ import annotations

from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGGER

APP_NAMES = {
    "com.sony.dtv.tvx": "TV",
    "com.google.android.youtube.tv": "YouTube",
    "com.netflix.ninja": "Netflix",
    "com.disney.disneyplus": "Disney+",
    "com.amazon.amazonvideo.livingroom": "Prime Video",
    "com.plexapp.android": "Plex",
    "org.xbmc.kodi": "Kodi",
    "com.spotify.tv.android": "Spotify",
    "com.google.android.apps.tv.launcherx": "Launcher",
    "com.google.android.tvlauncher": "Accueil",
    "com.sony.dtv.ceb": "Navigateur",
    "com.arte.android.tv": "Arte",
    "fr.francetv.pluzz": "France TV",
    "fr.freebox.player": "Freebox Player",
    "com.molotov.tv": "Molotov",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Freebox Player media_player entities from a config entry."""
    data = entry.runtime_data
    entities: list[FreeboxPlayerMediaPlayer] = []
    for player in data.players:
        player_id = player["id"]
        coordinator = data.coordinators[player_id]
        entities.append(
            FreeboxPlayerMediaPlayer(
                coordinator=coordinator,
                player=player,
                entry_id=entry.entry_id,
                channels=data.channels,
            )
        )
    async_add_entities(entities)


class FreeboxPlayerMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Representation of a Freebox Player as a media player."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        coordinator,
        player: dict[str, Any],
        entry_id: str,
        channels: dict[str, dict[str, Any]],
    ) -> None:
        """Initialize the Freebox Player media player."""
        super().__init__(coordinator)
        self._player_id = player["id"]
        self._player_name = player.get(
            "device_name", player.get("name", "Freebox Player")
        )
        self._channels = channels
        self._attr_unique_id = f"{entry_id}_player_{player['id']}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry_id}_{player['id']}")},
            name=self._player_name,
            manufacturer="Freebox",
            model=player.get("device_model", "Freebox Player"),
        )
        self._attr_supported_features = (
            MediaPlayerEntityFeature.PAUSE
            | MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.VOLUME_STEP
            | MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.TURN_OFF
            | MediaPlayerEntityFeature.PREVIOUS_TRACK
            | MediaPlayerEntityFeature.NEXT_TRACK
        )

    @property
    def state(self) -> MediaPlayerState | None:
        """Return the current state of the player."""
        if not self.coordinator.data:
            return None
        power = self.coordinator.data.get("power_state")
        if power != "running":
            return MediaPlayerState.OFF
        fg = self.coordinator.data.get("foreground_app", {})
        media_info = fg.get("media_info", {})
        playback = media_info.get("playback_state", "")
        if playback == "playing":
            return MediaPlayerState.PLAYING
        if playback == "paused":
            return MediaPlayerState.PAUSED
        return MediaPlayerState.ON

    @property
    def media_title(self) -> str | None:
        """Return the title of the current media (channel name)."""
        if (
            not self.coordinator.data
            or self.coordinator.data.get("power_state") != "running"
        ):
            return None
        channel = self.coordinator.data.get("current_channel", {})
        if channel and channel.get("name"):
            return channel["name"]
        # Fallback: parse cur_url for channel UUID and look up in cache
        fg = self.coordinator.data.get("foreground_app", {})
        cur_url = fg.get("cur_url", "")
        if cur_url.startswith("tv://"):
            uuid = cur_url.replace("tv://", "")
            cached = self._channels.get(uuid, {})
            if cached.get("name"):
                return cached["name"]
        return None

    @property
    def app_id(self) -> str | None:
        """Return the package name of the foreground app."""
        if (
            not self.coordinator.data
            or self.coordinator.data.get("power_state") != "running"
        ):
            return None
        fg = self.coordinator.data.get("foreground_app", {})
        return fg.get("package")

    @property
    def app_name(self) -> str | None:
        """Return a human-readable name for the foreground app."""
        pkg = self.app_id
        if not pkg:
            return None
        return APP_NAMES.get(pkg, pkg.split(".")[-1] if "." in pkg else pkg)

    @property
    def volume_level(self) -> float | None:
        """Return the volume level (0.0 to 1.0)."""
        if not self.coordinator.data:
            return None
        vol = self.coordinator.data.get("volume", {})
        level = vol.get("level")
        if level is not None:
            return level / 100.0
        return None

    @property
    def is_volume_muted(self) -> bool | None:
        """Return whether the player is muted."""
        if not self.coordinator.data:
            return None
        vol = self.coordinator.data.get("volume", {})
        return vol.get("muted")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs: dict[str, Any] = {}
        if self.app_id:
            attrs["app_id"] = self.app_id
        if self.app_name:
            attrs["app_name"] = self.app_name
        if self.coordinator.data:
            channel = self.coordinator.data.get("current_channel", {})
            uuid = channel.get("uuid", "")
            cached = self._channels.get(uuid, {})
            if cached.get("number"):
                attrs["channel_number"] = cached["number"]
            if channel.get("logo_url"):
                attrs["channel_logo"] = channel["logo_url"]
        return attrs

    # -- Control methods (stubs) -----------------------------------------------

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the player."""
        # TODO: needs remote_code support
        LOGGER.warning("Control not yet implemented: turn_on")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the player."""
        # TODO: needs remote_code support
        LOGGER.warning("Control not yet implemented: turn_off")

    async def async_volume_up(self) -> None:
        """Increase volume."""
        # TODO: needs remote_code support
        LOGGER.warning("Control not yet implemented: volume_up")

    async def async_volume_down(self) -> None:
        """Decrease volume."""
        # TODO: needs remote_code support
        LOGGER.warning("Control not yet implemented: volume_down")

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute or unmute the player."""
        # TODO: needs remote_code support
        LOGGER.warning("Control not yet implemented: mute_volume")

    async def async_media_play(self) -> None:
        """Play media."""
        # TODO: needs remote_code support
        LOGGER.warning("Control not yet implemented: media_play")

    async def async_media_pause(self) -> None:
        """Pause media."""
        # TODO: needs remote_code support
        LOGGER.warning("Control not yet implemented: media_pause")

    async def async_media_previous_track(self) -> None:
        """Switch to previous channel."""
        # TODO: needs remote_code support
        LOGGER.warning("Control not yet implemented: media_previous_track")

    async def async_media_next_track(self) -> None:
        """Switch to next channel."""
        # TODO: needs remote_code support
        LOGGER.warning("Control not yet implemented: media_next_track")
