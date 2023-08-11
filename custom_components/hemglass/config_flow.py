"""Config flow for Hello World integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

DOMAIN = "hemglass"
_LOGGER = logging.getLogger(__name__)


DATA_SCHEMA = vol.Schema(
    {
        vol.Required("name"): str,
        vol.Required("latitude"): str,
        vol.Required("longitude"): str
    }
)


async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input."""

    session = async_get_clientsession(hass)
    
    try:
        latitude = float(data["latitude"])
        longitude = float(data["longitude"])
    except ValueError:
            raise InvalidCoords

    searchRange = 5 * 0.008999
    minLat = latitude - searchRange
    maxLat = latitude + searchRange
    minLong = longitude - searchRange
    maxLong = longitude + searchRange

    url = "https://iceman-prod.azurewebsites.net/api/tracker/getNearestStops?minLong=" + str(minLong) + "&minLat=" + str(minLat) + "&maxLong=" + str(maxLong) + "&maxLat=" + str(maxLat) + "&limit=1"
    async with session.get(url) as resp:
        json = await resp.json()

        try:
            stop = json['data'][0]
        except Exception:
            raise NoStopsFound

    return {"title": data["name"]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hello World."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""

        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                return self.async_create_entry(title=info["title"], data=user_input)
            except NoStopsFound:
                errors["base"] = "no_stops_found"
            except InvalidCoords:
                errors["base"] = "invalid_coordinates"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class NoStopsFound(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidCoords(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""