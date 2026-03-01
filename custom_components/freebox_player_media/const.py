"""Constants for freebox_player_media."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)
DOMAIN = "freebox_player_media"

APP_DESC = {
    "app_id": "hass",
    "app_name": "Home Assistant",
    "app_version": "1.0.0",
    "device_name": "homeassistant",
}
API_VERSION = "v6"
STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1
DEFAULT_HOST = "192.168.1.254"
DEFAULT_PORT = 443
SCAN_INTERVAL_SECONDS = 10
