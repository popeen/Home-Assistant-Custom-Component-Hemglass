"""Platform for sensor integration."""
import urllib.request, json, asyncio, hashlib, requests
from datetime import timedelta
from urllib import request

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_NAME
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle


DOMAIN = "hemglass"

CONF_LAT = "latitude"
CONF_LONG = "longitude"

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=60)

SCAN_INTERVAL = timedelta(minutes=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_LAT): cv.string,
        vol.Required(CONF_LONG): cv.string,
    }
)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    session = async_get_clientsession(hass)
    config = hass.data[DOMAIN][config_entry.entry_id]
    
    latitude = (hass.data[DOMAIN][config_entry.entry_id])[0]
    longitude = (hass.data[DOMAIN][config_entry.entry_id])[1]
    name = (hass.data[DOMAIN][config_entry.entry_id])[2]

    async_add_entities([HemglassSensor(name, float(latitude), float(longitude))], update_before_add=True)

class HemglassSensor(Entity):
    """Representation of a Sensor."""
    
    def __init__(self, sensor_name, sensor_home_latitude, sensor_home_longitude):
        """Initialize the sensor."""
        
        self._attr_unique_id = f"{DOMAIN}_{sensor_name}_{sensor_home_latitude}_{sensor_home_longitude}"

        searchRange = 10 * 0.008999
        self._attr_minLat = sensor_home_latitude - searchRange
        self._attr_maxLat = sensor_home_latitude + searchRange
        self._attr_minLong = sensor_home_longitude - searchRange
        self._attr_maxLong = sensor_home_longitude + searchRange

        self._state = None
        self._name = sensor_name

        self._icon = "mdi:calendar"
        
    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        if self._attr_stopLat is not None:
            attributes = {
                "latitude" : self._attr_stopLat,
                "longitude" : self._attr_stopLong,
                "streetAddress": self._attr_streetAddress,
                "city": self._attr_city,
                "time" : self._attr_nextTime,
                "ETA" : self._attr_eta,
                "salesman" : self._attr_salesMan,
                "depot" : self._attr_depotName,
                "email" : self._attr_depotEmail,
                "comment" : self._attr_comment,
                "canceled" : self._attr_cancelled,
                "canceledMessage" : self._attr_cancelledMessage,
                "truckIsActiveToday" : self._attr_truckIsActiveToday,
                "truckLocationUpdated" : self._attr_truckLocationUpdated,
                "truckLatitude" : self._attr_truckLatitude,
                "truckLongitude" : self._attr_truckLongitude,
                "truckIsOffTrack" : self._attr_truckIsOffTrack,
                "routeID" : self._attr_routeId
            }
        else:
            attributes = {}
        if hasattr(self, "add_state_attributes"):
            attributes = {**attributes, **self.add_state_attributes}
        return attributes

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return self._icon

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self) -> None:
        """Get the latest data and updates the states."""

        session = async_get_clientsession(self.hass)

        nearestStop = await self.get_nearest_stop(session)
        self._attr_stopId = nearestStop['stopId']
        self._attr_stopLat = nearestStop['latitude']
        self._attr_stopLong = nearestStop['longitude']
        self._attr_nextDate = nearestStop['nextDate']
        self._attr_nextTime = nearestStop['nextTime']
        self._attr_routeId = nearestStop['routeId']

        salesInfo = await self.get_sales_info(session )
        self._attr_salesMan = salesInfo['salesmanName']
        self._attr_phoneNumber = salesInfo['phoneNumber']
        self._attr_depotName = salesInfo['depotName'].capitalize()
        self._attr_depotEmail = salesInfo['depotEmail']
        self._attr_streetAddress = salesInfo['streetAddress'].capitalize()
        self._attr_city = salesInfo['city'].capitalize()
        self._attr_comment = salesInfo['comment']
        self._attr_cancelled = salesInfo['cancelled']
        self._attr_cancelledMessage = salesInfo['cancelledMessage']
        if self._attr_cancelledMessage is None:
            self._attr_cancelledMessage = ""

        etaInfo = await self.get_eta(session)
        self._attr_eta = etaInfo
        
        liveRouteInfo = await self.get_live_route_info(session)
        if liveRouteInfo is not None:
            self._attr_truckIsActiveToday= True

            forecast = self.get_route_forecast()
            cords = (forecast[(int(liveRouteInfo['indices'][0]['index']) - 1)]).split(",")
            self._attr_truckLatitude = cords[0]
            self._attr_truckLongitude = cords[1]
            self._attr_truckLocationUpdated = liveRouteInfo['indices'][0]['time']

            if "isOffTrack" in liveRouteInfo:
                self._attr_truckIsOffTrack = liveRouteInfo['isOffTrack']
            else:
                self._attr_truckIsOffTrack = ""

        else:            
            self._attr_truckIsActiveToday= False
            self._attr_truckLatitude = ""
            self._attr_truckLongitude = ""
            self._attr_truckLocationUpdated = ""
            self._attr_truckIsOffTrack = ""

        nextDateSplit = (self._attr_nextDate).split("T")
        self._state = nextDateSplit[0]

    async def get_nearest_stop(self, session):
        url = "https://iceman-prod.azurewebsites.net/api/tracker/getNearestStops?minLong=" + str(self._attr_minLong) + "&minLat=" + str(self._attr_minLat) + "&maxLong=" + str(self._attr_maxLong) + "&maxLat=" + str(self._attr_maxLat) + "&limit=1"
        async with session.get(url) as resp:
            data = await resp.json()
            return data['data'][0]

    async def get_sales_info(self, session):
        url = "https://iceman-prod.azurewebsites.net/api/tracker/getSalesInfoByStop?stopId=" + str(self._attr_stopId)
        async with session.get(url) as resp:
            data = await resp.json()
            return data['data']

    async def get_eta(self, session):
        url = "https://iceman-prod.azurewebsites.net/api/tracker/stopsEta?stopId=" + str(self._attr_stopId) + "&routeId=" + str(self._attr_routeId)
        async with session.get(url) as resp:
            data = await resp.json()
            return data['data']

    async def get_depot_info(self, session):
        url = "https://iceman-prod.azurewebsites.net/api/tracker/depotInfo/" + str(self._attr_routeId)
        async with session.get(url) as resp:
            data = await resp.json()

            if data['statusCode'] == 200:
                return data['data']
            else:
                return None        

    async def get_live_route_info(self, session):
        url = "https://iceman-prod.azurewebsites.net/api/tracker/liverouteinfo/" + str(self._attr_routeId)
        async with session.get(url) as resp:
            data = await resp.json()

            if data['statusCode'] == 200:
                return data['data']
            else:
                return None     

    async def get_route_forecast(self, session):
        url = "https://iceman-prod.azurewebsites.net/api/tracker/routeforecast/" + str(self._attr_routeId)
        async with session.get(url) as resp:
            data = await resp.json()

            if data['statusCode'] == 200:
                return data['data']
            else:
                return None     