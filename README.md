# Freebox Player Media for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![HA](https://img.shields.io/badge/Home%20Assistant-2024.1+-blue.svg)](https://www.home-assistant.io/)

A Home Assistant custom integration that exposes your **Freebox Player** (Delta, Pop, Revolution) as a `media_player` entity.

## Features

- **Power state** -- detects whether the player is on or off
- **Current TV channel** -- displays the channel name being watched
- **Active app** -- shows the foreground application (YouTube, Netflix, Disney+, etc.)
- **Volume level** -- reports the current volume and mute state
- **Channel metadata** -- channel number and logo via extra attributes

## Installation

### HACS (recommended)

1. Open **HACS** in Home Assistant
2. Go to **Integrations** and click the three-dot menu
3. Select **Custom repositories**
4. Add this repository URL and choose category **Integration**
5. Install **Freebox Player Media**
6. Restart Home Assistant

### Manual

Copy the `custom_components/freebox_player_media` folder into your Home Assistant `config/custom_components/` directory and restart.

## Configuration

1. Go to **Settings > Devices & Services > Add Integration**
2. Search for **Freebox Player Media**
3. Enter the IP address of your Freebox Server (default: `192.168.1.254`)
4. Press the link button on the front of your Freebox Server when prompted
5. Submit the form to complete pairing

The integration communicates with the **Freebox Server** API, which relays player status from all connected Freebox Players on your local network.

## Entities

One `media_player` entity is created per Freebox Player detected on your network. Each entity reports:

| Attribute | Description |
|---|---|
| `state` | `off`, `on`, `playing`, or `paused` |
| `media_title` | Current TV channel name |
| `app_id` | Android package of the foreground app |
| `app_name` | Human-readable app name |
| `volume_level` | Volume (0.0 -- 1.0) |
| `is_volume_muted` | Mute state |
| `channel_number` | Channel number (extra attribute) |
| `channel_logo` | Channel logo URL (extra attribute) |

## Credits

- Uses the [freebox-api](https://pypi.org/project/freebox-api/) Python library
- Inspired by [freebox_homexa](https://github.com/music-assistant/freebox_homexa)
