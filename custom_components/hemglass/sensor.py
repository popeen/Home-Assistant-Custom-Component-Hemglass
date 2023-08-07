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

def setup_platform(hass, config, add_entities, discovery_info=None) -> None:
    """Set up the Hemglass sensor platform."""

    sensor_name = config[CONF_NAME]
    sensor_home_latitude = float(config[CONF_LAT])
    sensor_home_longitude = float(config[CONF_LONG])

    add_entities([HemglassSensor(sensor_name, sensor_home_latitude, sensor_home_longitude)])


class HemglassSensor(Entity):
    """Representation of a Sensor."""
    
    def __init__(self, sensor_name, sensor_home_latitude, sensor_home_longitude):
        """Initialize the sensor."""
        
        self._attr_unique_id = f"{DOMAIN}_{sensor_name}_{sensor_home_latitude}_{sensor_home_longitude}"

        searchRange = 5 * 0.008999
        self._attr_minLat = sensor_home_latitude - searchRange
        self._attr_maxLat = sensor_home_latitude + searchRange
        self._attr_minLong = sensor_home_longitude - searchRange
        self._attr_maxLong = sensor_home_longitude + searchRange

        self._state = self.update_hemglass_data()
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
            "canceledMessage" : self._attr_cancelledMessage 
        }
        if hasattr(self, "add_state_attributes"):
            attributes = {**attributes, **self.add_state_attributes}
        return attributes

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return self._icon

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self) -> None:
        """Get the latest data and updates the states."""
        self._state = update_hemglass_data()
    

    def update_hemglass_data(self):
        nearestStop = self.get_nearest_stop()
        self._attr_stopId = nearestStop['stopId']
        self._attr_stopLat = nearestStop['latitude']
        self._attr_stopLong = nearestStop['longitude']
        self._attr_nextDate = nearestStop['nextDate']
        self._attr_nextTime = nearestStop['nextTime']
        self._attr_routeId = nearestStop['routeId']

        salesInfo = self.get_sales_info()
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

        etaInfo = self.get_eta()
        self._attr_eta = etaInfo

        nextDateSplit = (self._attr_nextDate).split("T")
        return nextDateSplit[0]

    def get_nearest_stop(self):
        return requests.get(url="https://iceman-prod.azurewebsites.net/api/tracker/getNearestStops?minLong=" + str(self._attr_minLong) + "&minLat=" + str(self._attr_minLat) + "&maxLong=" + str(self._attr_maxLong) + "&maxLat=" + str(self._attr_maxLat) + "&limit=1", headers={
                'user-agent': 'www.Home-Assistant.io - Add-On for Hemglass'
            }).json()['data'][0]

    def get_sales_info(self):
        return requests.get(url="https://iceman-prod.azurewebsites.net/api/tracker/getSalesInfoByStop?stopId=" + str(self._attr_stopId), headers={
                'user-agent': 'www.Home-Assistant.io - Add-On for Hemglass'
            }).json()['data']

    def get_eta(self):
        return requests.get(url="https://iceman-prod.azurewebsites.net/api/tracker/stopsEta?stopId=" + str(self._attr_stopId) + "&routeId=" + str(self._attr_routeId), headers={
                'user-agent': 'www.Home-Assistant.io - Add-On for Hemglass'
            }).json()['data']
