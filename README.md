# schluter-python
A [home-assistant] integration for [Schluter][] Ditra Heat Floor Warming System Wifi Thermostat
[Schluter®-DITRA-HEAT-E-WiFi]

Integrate with HASS by copying the `schluter` folder into the  `custom_components` folder.

Include the following entry in configuration.yaml

    climate:
      - platform: schluter
        email: <schluter login email>
        password: <schluter login password>
        
        (optional)
        precision: 1.0, 0.5 or 0.1

# Current Limitations
  Only the first thermostat assigned to a group will be recognized by this integration.
  
# Todo
- add test for token expiration
- move schluter functions to separate file
- make async
- implement aiohttp
- make (more) object oriented
- account for multiple thermostats

# Implementation
- Integration utilizes the API interfaced by the [Schluter thermostat website].

[home-assistant]: https://github.com/home-assistant/home-assistant
[Schluter]: https://www.schluter.com/schluter-us/en_US/
[Schluter®-DITRA-HEAT-E-WiFi]: https://www.schluter.com/schluter-us/en_US/Floor-Warming/c/FW
[Schluter thermostat website]: https://ditra-heat-e-wifi.schluter.com/
