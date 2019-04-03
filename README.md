# schluter-python
A homeassistant integration for [Schluter][] wifi thermostat [Schluter®-DITRA-HEAT-E-WiFi]

Integrate with HASS by placing climate.py in 'custom_components/schluter' folder.

Include the following entry in configuration.yaml

    climate:
      - platform: schluter
        email: <schluter login email>
        password: <schluter login password>

# Current Limitations
  Only the first thermostat assigned to a group will be recognized by this integration.
  
# Todo
- add test for token expiration
- move schluter functions to separate file
- make async
- implement aiohttp
- make object oriented
- account for multiple thermostats

[Schluter]: https://www.schluter.com/schluter-us/en_US/
[Schluter®-DITRA-HEAT-E-WiFi]: https://www.schluter.com/schluter-us/en_US/Floor-Warming/c/FW
