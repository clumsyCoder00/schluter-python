# schluter-python
A homeassistant integration for Schluter wifi thermostats.

Integrate with HASS by placing climate.py in custom_components/schluter folder.

Include the following entry in configuration.yaml

[...]
  - platform: schluter
    email: <schluter login email>
    password: <schluter login password>
[..]
  Current Limitations
  Only the first thermostat assigned to a group will be recognized by this integration.
