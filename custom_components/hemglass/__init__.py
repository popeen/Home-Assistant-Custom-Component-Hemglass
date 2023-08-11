"""Hemglass.""" 
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

DOMAIN = "hemglass"

PLATFORMS: list[str] = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = [
        entry.data["latitude"],
        entry.data["longitude"],
        entry.data["name"]
    ]
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True