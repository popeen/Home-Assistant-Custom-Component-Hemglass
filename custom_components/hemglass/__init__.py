"""Hemglass.""" 
from __future__ import annotations

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

DOMAIN = "hemglass"

PLATFORMS: list[str] = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)

    stopData = await get_nearest_stop(session, entry.data["latitude"], entry.data["longitude"])
    routeId = stopData['routeId']

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = [
        entry.data["latitude"],
        entry.data["longitude"],
        entry.data["name"],
        routeId
    ]
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def get_nearest_stop(session, latitude, longitude):    
    
    searchRange = 10 * 0.008999
    minLat = float(latitude) - searchRange
    maxLat = float(latitude) + searchRange
    minLong = float(longitude) - searchRange
    maxLong = float(longitude) + searchRange

    url = "https://iceman-prod.azurewebsites.net/api/tracker/getNearestStops?minLong=" + str(minLong) + "&minLat=" + str(minLat) + "&maxLong=" + str(maxLong) + "&maxLat=" + str(maxLat) + "&limit=1"
    async with session.get(url) as resp:
        data = await resp.json()
        return data['data'][0]