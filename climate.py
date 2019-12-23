"""Support for Schluter thermostats."""

"""
Climate structure
https://github.com/home-assistant/home-assistant/blob/dev/homeassistant/components/climate/__init__.py

https://github.com/home-assistant/home-assistant/blob/dev/homeassistant/components/nissan_leaf/__init__.py
https://github.com/jdhorne/pycarwings2/blob/master/pycarwings2/pycarwings2.py
http://dev-docs.home-assistant.io/en/master/api/helpers.html

todo
- add test for token expiration
- account for multiple thermostats
"""
import requests
import json

import logging

import voluptuous as vol

from homeassistant.components.climate import PLATFORM_SCHEMA, ClimateDevice
from homeassistant.components.climate.const import (
    DOMAIN,
    ATTR_PRESET_MODE,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    HVAC_MODE_HEAT,
    HVAC_MODE_AUTO,
    HVAC_MODE_OFF,
    PRESET_AWAY,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    )
    
PRESET_MANUAL = "On Manual"
PRESET_SCHEDULE = "On Schedule"
CONF_PRECISION = 'precision'

from homeassistant.const import (
    ATTR_TEMPERATURE, TEMP_CELSIUS, TEMP_FAHRENHEIT, PRECISION_HALVES,
    PRECISION_TENTHS, PRECISION_WHOLE)
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = "Powered by Schluter Systems"

DEFAULT_PRECISION = PRECISION_WHOLE

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE
                 
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_EMAIL): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_PRECISION, default=DEFAULT_PRECISION): vol.In(
        [PRECISION_TENTHS, PRECISION_HALVES, PRECISION_WHOLE]),
})
def setup_platform(hass, config, add_entities, discovery_info=None):
    _LOGGER.debug("setup_platform: begin")
    """Setup the Schluter platform."""
    email = config.get(CONF_EMAIL)
    password = config.get(CONF_PASSWORD)
    precision = config.get(CONF_PRECISION)
    
    add_entities([SchluterThermostat(hass, email, password, precision)], True)
    _LOGGER.debug("setup_platform: end")
 
class SchluterThermostat(ClimateDevice):
    """Representation of a Schluter thermostat device."""
    
    def __init__(self, hass, email, password, precision):
        """Initialize the thermostat."""
        _LOGGER.debug("__init__: begin")
            
        self.hass = hass
        self._email = email
        self._password = password
        self._precision = precision
        self._support_flags = SUPPORT_FLAGS
        self._hvac_list = [HVAC_MODE_OFF, HVAC_MODE_HEAT, HVAC_MODE_AUTO]
        self._preset_list = [PRESET_AWAY, PRESET_MANUAL, PRESET_SCHEDULE]
        
        # data attributes
        self._location = None               # Group?
        self._name = None                   # Room
        self._target_temperature = None     # ComfortTemperature
        self._temperature = None            # Temperature
        self._temperature_scale = TEMP_CELSIUS
        self._preset_mode = None
        self._hvac_mode = None
        self._min_temperature = None        # MinTemp
        self._max_temperature = None        # MaxTemp
#        self._is_device_active = None
        self._session_id = None
        self._serial = None
        self._thermostat_data = None
    
        # is this a platform or thermostat instance. This should be in the platform instance?
        self._get_session_id(self._email, self._password, self._session_id)
        self._serial = self._get_thermostat_serial(self._session_id)
        self.update()
        
        _LOGGER.debug("__init__: end")

    @property
    def attribution(self):
        """Return the attribution."""
        return ATTRIBUTION
                
    @property
    def name(self):
        """Return the name of the thermostat."""
        return self._name

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self._precision
                
    @property
    def precision(self):
        """Return the precision of the system."""
        return self._precision
        
    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._temperature_scale
                
    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._temperature

    @property
    def preset_mode(self):
        """Return current preset mode."""
        return self._preset_mode
        
    @property
    def preset_modes(self):
        """List of available operation modes."""
        return self._preset_list

    def set_preset_mode(self, preset_mode):
        """Set new target preset mode."""
        if preset_mode == self.preset_mode:
            return
        if preset_mode == PRESET_SCHEDULE:
            self._preset_mode = PRESET_SCHEDULE
            self._set_termostat_data(self._session_id, self._serial, {
                'RegulationMode': 1, # set to schedule mode
                'VacationEnabled': False})
        elif preset_mode == PRESET_MANUAL:
            self._preset_mode = PRESET_MANUAL
            self._set_termostat_data(self._session_id, self._serial, {
                'RegulationMode': 2, # set to manual mode
                'VacationEnabled': False})
        elif preset_mode == PRESET_AWAY:
            self._preset_mode = PRESET_AWAY
            self._set_termostat_data(self._session_id, self._serial, {
                'RegulationMode': 3, # set to away mode
                'VacationEnabled': False})

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def hvac_mode(self):
        """Return the current state."""
        return self._hvac_mode   

    @property
    def hvac_modes(self):
        """List of available operation modes."""
        return self._hvac_list

    def set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        if hvac_mode == self.hvac_mode:
            return
        if hvac_mode == HVAC_MODE_AUTO:
            self._hvac_mode = HVAC_MODE_AUTO
            self._set_termostat_data(self._session_id, self._serial, {
                'RegulationMode': 1, # set to schedule mode
                'VacationEnabled': False})
        elif hvac_mode == HVAC_MODE_HEAT:
            self._hvac_mode = HVAC_MODE_HEAT
            self._set_termostat_data(self._session_id, self._serial, {
                'ComfortTemperature': str(int(round(self._temperature*100,0))),
                'RegulationMode': 2})
        elif hvac_mode == HVAC_MODE_OFF:
            self._hvac_mode = HVAC_MODE_OFF
            self._set_termostat_data(self._session_id, self._serial, {
                'RegulationMode': 3, # set to away mode
                'VacationEnabled': False})
        
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
    def min_temp(self):
        """Identify min_temp in Nest API or defaults if not available."""
        return self._min_temperature

    @property
    def max_temp(self):
        """Identify max_temp in Nest API or defaults if not available."""
        return self._max_temperature
        
    def _get_session_id(self, email, password, session_id):
        """Get Session ID"""
        request_url = 'https://ditra-heat-e-wifi.schluter.com/api/thermostats'
        params = {'sessionid': session_id}
        result = requests.get(request_url, params=params)
        
        if result.ok == False:
            _LOGGER.info("renewing session_id")
            login_url = 'https://ditra-heat-e-wifi.schluter.com/api/authenticate/user'
            authenticate_payload = {
              "Email":email,
              "Password":password,
              "Application":'7'
              }
            result = requests.post(login_url, data = authenticate_payload)
            self._session_id = result.json().get('SessionId')

    def _get_thermostat_serial(self, session_id):
        request_url = 'https://ditra-heat-e-wifi.schluter.com/api/thermostats'
        params = {'sessionid': session_id}
        result = requests.get(request_url, params=params) #  timeout=50.000
        return result.json()['Groups'][0]['Thermostats'][0]['SerialNumber']

    # ---- get data of specific thermostat ----
    def _get_thermostat_data(self, session_id, serialnumber):
        request_url = 'https://ditra-heat-e-wifi.schluter.com/api/thermostat'
        params = {'sessionid': session_id, 'serialnumber': serialnumber}
        self._thermostat_data = requests.get(request_url, params=params)
        _LOGGER.debug("\nget_thermostat_data" + 
            "\n\tsession_id: " + session_id + 
            '\n\tserialnumber: ' + serialnumber + 
            '\n\trequest_payload:\n' + 
#            json.dumps(self._thermostat_data.json(), indent=4, sort_keys=True, skipkeys=True)
            '\n'.join("\t\t{!r}: {!r},".format(k, v) for k, v in self._thermostat_data.json().items() if k is not "'Schedules'")
            )
        return self._thermostat_data.ok 

    # ---- set data of specific thermostat ----    
    def _set_termostat_data(self, session_id, serialnumber, request_payload):
        _LOGGER.debug("\nset_thermostat_data" + 
            "\n\tsession_id: " + session_id + 
            '\n\tserailnumber: ' + serialnumber + 
            '\n\trequest_payload:\n' + "\n".join("\t\t{!r}: {!r},".format(k, v) for k, v in request_payload.items()))
        request_url = 'https://ditra-heat-e-wifi.schluter.com/api/thermostat'
        params = {'sessionid': session_id, 'serialnumber': serialnumber}
        result = requests.post(request_url,
          data=json.dumps(request_payload),
          headers={'Content-Type': 'application/json; charset=UTF-8'},
          params=params)
      
    def update(self):
        self._get_session_id(self._email, self._password, self._session_id)
        
        if self._get_thermostat_data(self._session_id, self._serial):
            self._name = self._thermostat_data.json()['Room']
        
            raw_temperature = self._thermostat_data.json()['Temperature']
            if type(raw_temperature) is int:
                self._temperature = raw_temperature / 100
            elif raw_temperature is None:
                _LOGGER.warning("invalid raw_temperature type: None")
            else:
                _LOGGER.warning("invalid raw_temperature type: " + str(type(raw_temperature)))
            
            self._target_temperature = self._thermostat_data.json()['SetPointTemp'] / 100
            self._min_temperature = self._thermostat_data.json()['MinTemp'] / 100
            self._max_temperature = self._thermostat_data.json()['MaxTemp'] / 100

            if self._thermostat_data.json()['RegulationMode'] == 1:
               self._preset_mode = PRESET_SCHEDULE
               self._hvac_mode = HVAC_MODE_AUTO
            elif self._thermostat_data.json()['RegulationMode'] == 2:
               self._preset_mode = PRESET_MANUAL
               self._hvac_mode = HVAC_MODE_HEAT
            elif self._thermostat_data.json()['RegulationMode'] == 3:
               self._preset_mode = PRESET_AWAY
               self._hvac_mode = HVAC_MODE_OFF

            if self._thermostat_data.json()['Heating'] == False:
#                self._is_device_active = False
                self._is_heating = False
            else:
#                self._is_device_active = True
                self._is_heating = True
        else:
            _LOGGER.warning("could not get thermostat data")

    @property
    def device_info(self):
        """Return device info for this device."""
        return {
            "name": self._name,
            "serial": self._serial,
            "manufacturer": "Schluter Systems",
            "model": "DITRA-HEAT-E-WiFi Thermostat",
        }
        
    @property
    def hvac_action(self):
        """Return the current running hvac operation if supported.
        Need to be one of CURRENT_HVAC_*.
        """
        if not self._is_heating:
            return CURRENT_HVAC_IDLE
        return CURRENT_HVAC_HEAT
        
    @property
    def _is_device_active(self):
        """If the toggleable device is currently active."""
        return self._is_heating

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._support_flags
