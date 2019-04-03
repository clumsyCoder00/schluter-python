"""Support for Schluter thermostats."""

"""
Climate structure
https://github.com/home-assistant/home-assistant/blob/dev/homeassistant/components/climate/__init__.py

https://github.com/home-assistant/home-assistant/blob/dev/homeassistant/components/nissan_leaf/__init__.py
https://github.com/jdhorne/pycarwings2/blob/master/pycarwings2/pycarwings2.py
http://dev-docs.home-assistant.io/en/master/api/helpers.html

todo
- add test for token expiration
- move schluter functions to separate file
- make async
- implement aiohttp
- make object oriented
- account for multiple thermostats
"""
import requests
import json

#import asyncio
import logging

import voluptuous as vol

#from homeassistant.core import callback
from homeassistant.components.climate import ClimateDevice, PLATFORM_SCHEMA
from homeassistant.components.climate.const import (
    DOMAIN,
    STATE_HEAT,
    STATE_IDLE,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_OPERATION_MODE,
    SUPPORT_AWAY_MODE,
    SUPPORT_HOLD_MODE,
    STATE_AUTO,
    STATE_MANUAL
    )
from homeassistant.const import (
    ATTR_TEMPERATURE, TEMP_CELSIUS, TEMP_FAHRENHEIT,
    CONF_SCAN_INTERVAL, STATE_ON, STATE_OFF, PRECISION_HALVES,
    PRECISION_TENTHS, PRECISION_WHOLE)
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
import homeassistant.helpers.config_validation as cv
#from homeassistant.helpers.dispatcher import (async_dispatcher_connect,
#                                              async_dispatcher_send)

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = (
    SUPPORT_TARGET_TEMPERATURE |
    SUPPORT_OPERATION_MODE |
    SUPPORT_AWAY_MODE |
    SUPPORT_HOLD_MODE
    )
                 
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_EMAIL): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
})
def setup_platform(hass, config, add_entities, discovery_info=None):
#async def async_setup_platform(hass, config, async_add_entities,
#                                discovery_info=None):
    """Setup the Schluter platform."""
    email = config.get(CONF_EMAIL)
    password = config.get(CONF_PASSWORD)
    
    add_entities([SchluterThermostat(hass, email, password)], True)
#    async_add_entities([SchluterThermostat(hass, email, password)])
 
class SchluterThermostat(ClimateDevice):
    """Representation of a Schluter thermostat device."""
    
    def __init__(self, hass, email, password):
        """Initialize the thermostat."""
            
        #async def async_handle_update():
        #    _LOGGER.debug("async_handle_update")
        #    await self._update()
            
        self.hass = hass
        self._email = email
        self._password = password
        self._support_flags = SUPPORT_FLAGS
        self._operation_list = [STATE_IDLE, STATE_HEAT]
        
        # data attributes
        self._away = None                   # RegulationMode
        self._hold = None
        self._location = None               # Group?
        self._name = None                   # Room
        self._target_temperature = None     # ComfortTemperature
        self._temperature = None            # Temperature
        self._temperature_scale = TEMP_CELSIUS
        self._mode = None                   # Heating
        self._is_locked = None              # VacationEnabled
        self._locked_temperature = None     # VacationTemperature
        self._min_temperature = None        # MinTemp
        self._max_temperature = None        # MaxTemp
        
        self._session_id = None
        self._serial = None
        self._thermostat_data = None
        
        # is this a platform or thermostat instance. This should be in the platform instance?
        self._session_id = self._get_session_id(self._email, self._password)
        self._serial = self._get_thermostat_serial(self._session_id)
        self.update()

        #hass.services.register(DOMAIN, 'Schluter_update', async_handle_update, PLATFORM_SCHEMA)
                
    #async def async_added_to_hass(self):
    #    """Device added to hass."""
    #    _LOGGER.warning("async_added_to_hass")
    #    async_dispatcher_connect(self.hass, 'Schluter_update',
    #                             self._update_callback)             

    #@callback
    #def _update_callback(self):
    #    """Update the state."""
    #    _LOGGER.warning("_update_callback")
    #    self.async_schedule_update_ha_state(True)

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._support_flags
                
    @property
    def current_operation(self):
        """Return the current state."""
        return self._mode        
        
    @property
    def name(self):
        """Return the name of the thermostat."""
        return self._name
        
    @property
    def precision(self):
        """Return the precision of the system."""
        # PRECISION_WHOLE
        # PRECISION_TENTHS
        return PRECISION_TENTHS

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._temperature_scale
        
    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._temperature
                
    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        self._target_temp = temperature
        self._set_termostat_data(self._session_id, self._serial, {
            'ComfortTemperature': str(int(round(temperature*100,0))),
            'RegulationMode': 2})

    @property
    def operation_list(self):
        """List of available operation modes."""
        return [STATE_HEAT, STATE_IDLE, STATE_AUTO]

    def set_operation_mode(self, operation_mode):
        """Set operation mode."""
        if operation_mode == STATE_AUTO:
            self._set_termostat_data(self._session_id, self._serial, {'RegulationMode': 1})

    @property
    def min_temp(self):
        """Identify min_temp in Nest API or defaults if not available."""
        return self._min_temperature

    @property
    def max_temp(self):
        """Identify max_temp in Nest API or defaults if not available."""
        return self._max_temperature

    @property
    def is_away_mode_on(self):
        """Return true if away mode is on."""
        return self._away
        
    # should probably do this through the group/change url the way that the webpage does
    def turn_away_mode_on(self):
        """Turn away mode on."""
        self._set_termostat_data(self._session_id, self._serial, {
            'ManualTemperature': str(int(round(self._min_temperature*100,0))),
            'RegulationMode': 3})

    def turn_away_mode_off(self):
        """Turn away mode off."""
        self._set_termostat_data(self._session_id, self._serial, {'RegulationMode': 1})
                                                
    @property
    def current_hold_mode(self):
        """Return the current hold mode, e.g., home, away, temp."""
        return self._hold
        
    def _get_session_id(self, email, password):
        """Get Session ID"""
        login_url = 'https://ditra-heat-e-wifi.schluter.com/api/authenticate/user'
        authenticate_payload = {
          "Email":email,
          "Password":password,
          "Application":'7'
          }
        result = requests.post(login_url, data = authenticate_payload)
        return result.json().get('SessionId')

    def _get_thermostat_serial(self, session_id):
        request_url = 'https://ditra-heat-e-wifi.schluter.com/api/thermostats'
        params = {'sessionid': session_id}
        result = requests.get(request_url, params=params) #  timeout=50.000
        return result.json()['Groups'][0]['Thermostats'][0]['SerialNumber']

    # ---- get data of specific thermostat ----
    def _get_thermostat_data(self, session_id, serialnumber):
        request_url = 'https://ditra-heat-e-wifi.schluter.com/api/thermostat'
        params = {'sessionid': session_id, 'serialnumber': serialnumber}
        return requests.get(request_url, params=params)  

    # ---- set data of specific thermostat ----    
    def _set_termostat_data(self, session_id, serialnumber, request_payload):
        request_url = 'https://ditra-heat-e-wifi.schluter.com/api/thermostat'
        params = {'sessionid': session_id, 'serialnumber': serialnumber}
        result = requests.post(request_url,
          data=json.dumps(request_payload),
          headers={'Content-Type': 'application/json; charset=UTF-8'},
          params=params)
      
    def update(self):
        self._thermostat_data = self._get_thermostat_data(self._session_id, self._serial)
        self._name = self._thermostat_data.json()['Room']
        self._temperature = self._thermostat_data.json()['Temperature'] / 100
        self._target_temperature = self._thermostat_data.json()['SetPointTemp'] / 100
        self._min_temperature = self._thermostat_data.json()['MinTemp'] / 100
        self._max_temperature = self._thermostat_data.json()['MaxTemp'] / 100
        self._away = self._thermostat_data.json()['RegulationMode'] == 3
        
        if self._thermostat_data.json()['Heating'] == False:
            self._mode = STATE_IDLE
        else:
            self._mode = STATE_HEAT

        if self._thermostat_data.json()['RegulationMode'] == 1:
            self._hold = STATE_AUTO
        else:
            self._hold = STATE_MANUAL
        
#    async def async_get_something(self):
#        await self.hass.async_add_executor_job(
#                    self.leaf.get_latest_hvac_status)
