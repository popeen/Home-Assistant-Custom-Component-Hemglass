"""Platform for sensor integration."""
import urllib.request, json, asyncio, hashlib, requests
from datetime import timedelta
from urllib import request
from datetime import datetime
from pytz import timezone
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

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=5)

SCAN_INTERVAL = timedelta(minutes=5)

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

    latitude = config[0]
    longitude = config[1]
    name = config[2]
    routeId = config[3]

    async_add_entities([HemglassSensor(name, float(latitude), float(longitude)),HemglassTruckSensor((name + " Truck"), str(routeId))], update_before_add=True)

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

async def get_sales_info(session, stopId):
    url = "https://iceman-prod.azurewebsites.net/api/tracker/getSalesInfoByStop?stopId=" + str(stopId)
    async with session.get(url) as resp:
        data = await resp.json()
        return data['data']

async def get_eta(session, stopId, routeId):
    url = "https://iceman-prod.azurewebsites.net/api/tracker/stopsEta?stopId=" + str(stopId) + "&routeId=" + str(routeId)
    async with session.get(url) as resp:
        data = await resp.json()
        if data['data'] != "":

            date = datetime.now().strftime("%Y-%m-%d")
            date_string = date + " " + data['data'] + " +0000"
            datetime_obj = datetime.strptime(date_string, '%Y-%m-%d %H:%M %z')
            etaStockholmTime = datetime_obj.astimezone(timezone('Europe/Stockholm')).strftime('%H:%M')

            return etaStockholmTime
        else:
            return ""

async def get_depot_info(session, routeId):
    url = "https://iceman-prod.azurewebsites.net/api/tracker/depotInfo/" + str(routeId)
    async with session.get(url) as resp:
        data = await resp.json()

        if data['statusCode'] == 200:
            return data['data']
        else:
            return None

async def get_live_route_info(session, routeId):
    url = "https://iceman-prod.azurewebsites.net/api/tracker/liverouteinfo/" + str(routeId)
    async with session.get(url) as resp:
        data = await resp.json()

        if data['statusCode'] == 200:

            date = datetime.now().strftime("%Y-%m-%d")
            date_string = date + " " + data['data']['indices'][0]['time'] + " +0000"
            datetime_obj = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S %z')
            time = datetime_obj.astimezone(timezone('Europe/Stockholm'))
            data['data']['indices'][0]['time'] = time.strftime('%H:%M:%S')
            return data['data']

        else:
            return None

async def get_route_forecast(session, routeId):
    url = "https://iceman-prod.azurewebsites.net/api/tracker/routeforecast/" + str(routeId)
    async with session.get(url) as resp:
        data = await resp.json()

        if data['statusCode'] == 200:
            return data['data']
        else:
            return None

class HemglassSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, sensor_name, sensor_home_latitude, sensor_home_longitude):
        """Initialize the sensor."""

        self._attr_unique_id = f"{DOMAIN}_{sensor_name}_{sensor_home_latitude}_{sensor_home_longitude}"

        self._state = None
        self._attr_routeId = None
        self._name = sensor_name
        self._homeLat = sensor_home_latitude
        self._homeLong = sensor_home_longitude

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

        nearestStop = await get_nearest_stop(session, self._homeLat, self._homeLong)
        self._attr_stopId = nearestStop['stopId']
        self._attr_stopLat = nearestStop['latitude']
        self._attr_stopLong = nearestStop['longitude']
        self._attr_nextDate = nearestStop['nextDate']
        self._attr_nextTime = nearestStop['nextTime']
        self._attr_routeId = nearestStop['routeId']

        salesInfo = await get_sales_info(session, self._attr_stopId)
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

        etaInfo = await get_eta(session, self._attr_stopId, self._attr_routeId)
        self._attr_eta = etaInfo

        liveRouteInfo = await get_live_route_info(session, self._attr_routeId)
        if liveRouteInfo is not None:
            self._attr_truckIsActiveToday= True

            forecast = await get_route_forecast(session, self._attr_routeId)
            cords = (forecast[(int(liveRouteInfo['indices'][0]['index']) - 1)]).split(",")
            self._attr_truckLatitude = cords[0]
            self._attr_truckLongitude = cords[1]
            self._attr_truckLocationUpdated = liveRouteInfo['indices'][0]['time']

            if "isOffTrack" in liveRouteInfo:
                self._attr_truckIsOffTrack = liveRouteInfo['isOffTrack']
            else:
                self._attr_truckIsOffTrack = ""

        else:
            self._attr_truckIsActiveToday = False
            self._attr_truckLatitude = ""
            self._attr_truckLongitude = ""
            self._attr_truckLocationUpdated = ""
            self._attr_truckIsOffTrack = ""

        nextDateSplit = (self._attr_nextDate).split("T")
        self._state = nextDateSplit[0]


class HemglassTruckSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, sensor_name, routeId):
        """Initialize the sensor."""

        self._attr_unique_id = f"{DOMAIN}_{routeId}"
        self._state = False
        self._name = sensor_name
        self._attr_routeId = routeId

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
    def icon(self):
        """Icon to use in the frontend."""
        return self._icon

    @property
    def extra_state_attributes(self):
        if self._attr_truckLatitude is not None:
            attributes = {
                "latitude" : self._attr_truckLatitude,
                "longitude" : self._attr_truckLongitude,
                "truckIsActiveToday" : self._attr_truckIsActiveToday,
                "truckLocationUpdated" : self._attr_truckLocationUpdated,
                "truckIsOffTrack" : self._attr_truckIsOffTrack,
                "routeID" : self._attr_routeId
            }
        else:
            attributes = {}
        if hasattr(self, "add_state_attributes"):
            attributes = {**attributes, **self.add_state_attributes}
        return attributes

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self) -> None:
        """Get the latest data and updates the states."""

        session = async_get_clientsession(self.hass)

        liveRouteInfo = await get_live_route_info(session, self._attr_routeId)
        if liveRouteInfo is not None:
            self._attr_truckIsActiveToday= True

            forecast = await get_route_forecast(session, self._attr_routeId)
            cords = (forecast[(int(liveRouteInfo['indices'][0]['index']) - 1)]).split(",")
            self._attr_truckLatitude = cords[0]
            self._attr_truckLongitude = cords[1]
            self._attr_truckLocationUpdated = liveRouteInfo['indices'][0]['time']

            if "isOffTrack" in liveRouteInfo:
                self._attr_truckIsOffTrack = liveRouteInfo['isOffTrack']
            else:
                self._attr_truckIsOffTrack = ""

        else:
            self._attr_truckIsActiveToday = False
            self._attr_truckLatitude = ""
            self._attr_truckLongitude = ""
            self._attr_truckLocationUpdated = ""
            self._attr_truckIsOffTrack = ""

        self._state =  self._attr_truckIsActiveToday
