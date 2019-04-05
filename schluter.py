
# http://docs.python-requests.org/en/master/
import requests
import json
'''
retrieved at 11:17 good at 1:26 expired at 2:50 (2:09)
retrieved at 02:30 good at expired by 4:14
Todo
- need to be able to account for multiple groups / termostats in GET thermostats
- use print(str(result)) to test for good data

# search/account
# confirm/thermostat
# newthermostat
# thermostat
# thermostats
# thermostats/resendconfirmation
# thermostats/assign
# thermostats/delete
# thermostats/unassign
# schedules/copy
# discontinuedthermostats
# unassigned_thermostats
# safetyquestions
# useraccount
# useraccount/changepassword
# useraccount/activeaccount
# useraccount/deactiveaccount
# useraccount/create
# x useraccounts
# x distributers
# distributers/change
# defaults
# notification
# energyusage
# groups/ungroup
# groups/group
# groups/change
# groups/remove
# groups/create
# authenticate/recover
# authenticate/user

- POST to authenticate/user to get sessionid
- GET to thermostat to get SerialNumber
- GET to thermostats to get information at SerialNumber

  SerialNumber            serial number to referred to with thermostat method
  Room                    Name of thermostat
  Temperature             ATTR_CURRENT_TEMPERATURE      Current temperature of floor
  RegulationMode          ATTR_HOLD_MODE
    1 - on schedule
    2 - manual override (with manual selection or "For a Few Hours" is active)
    3 - group away mode ("Away Mode" in user interface is active)
    4 - "Adjust" "For a Few Days" is active VacationEnabled = True, VacationTemperature is set to SetPointTemp
  SetPointTemp            ATTR_TEMPERATURE              (difference between this and ComfortTemperature?)
  VacationEnabled         ATTR_AWAY_MODE                Setback temperature is active (this doesn't appear to work, need to derive from RegulationMode)
  VacationTemperature                                   Setback temperature
  ComfortTemperature      ATTR_TEMPERATURE              Manual set temperature
  Online                                                Thermostat is connect to network
  Heating                 ATTR_OPERATION_MODE           Current is flowing through heating coil
  MaxTemp                 ATTR_MAX_TEMP                 Maximum allowable settable temperature
  MinTemp                 ATTR_MIN_TEMP                 Minimum allowable settable temperature
  
  - SetPointTemp is the active target temperature
  - Comforttemperature is the manually set temperature
    If the manual override is on (RegulationMode = 2), the ComfortTemperature 
    will equal the SetPointTemp.
    When the schedule takes over, the SetPointTemp replaces the ComfortTemperature by the scheduled temperature
  - VacationTemperature is active when away mode on the user interface is
    active (RegulationMode = 3) The schedule will not override this temp.
    When "Adjust" "For a few days" is active, this will be set to the current
    SetPointTemp
'''

# ---- helper ----
def C_to_F(c_temp):
  return round((((c_temp * 9) / 100) / 5) + 32, 0)
  
# ---- authenticate ----
login_url = 'https://ditra-heat-e-wifi.schluter.com/api/authenticate/user'

authenticate_payload = {
  "Email":"nutw07@gmail.com",
  "Password":"Y$1psesc",
  "Application":'7'
  }

result = requests.post(login_url, data = authenticate_payload)
session_id = result.json().get('SessionId')
print("sessionid: " + str(session_id))

# ---- get thermostats ----
request_url = 'https://ditra-heat-e-wifi.schluter.com/api/thermostats'
params = {'sessionid': session_id}
result = requests.get(request_url, params=params) #  timeout=50.000
serialnumber = result.json()['Groups'][0]['Thermostats'][0]['SerialNumber']
print("SerialNumber: " + serialnumber)

# ---- get specific thermostat data ----
request_url = 'https://ditra-heat-e-wifi.schluter.com/api/thermostat'
params = {'sessionid': session_id, 'serialnumber': serialnumber}
result = requests.get(request_url, params=params)
obj_room = result.json()['Room']
obj_temp = result.json()['Temperature']
obj_sche = result.json()['RegulationMode']
obj_temptarget = result.json()['SetPointTemp']
obj_tempcomfor = result.json()['ComfortTemperature']
obj_tempvacati = result.json()['VacationTemperature']
obj_vaca = result.json()['VacationEnabled']

# print(result.text)
print('Room:' + obj_room)
print('Temperature:' + str(C_to_F(obj_temp)))
print('RegulationMode: ' + str(obj_sche))
print('SetPointTemp: ' + str(C_to_F(obj_temptarget)))
print('ComfortTemperature: ' + str(C_to_F(obj_tempcomfor)))
print('VacationTemperature: ' + str(C_to_F(obj_tempvacati)))
print('VacationEnabled: ' + str(obj_vaca))


# ---- set specific thermostat data ----
# values are degree celcius * 100
request_payload = {
#  'ComfortEndTime': '"26/03/2019 03:00:00"',
#  'ComfortTemperature': '1500',
#  'RegulationMode': '1',
  'VacationEnabled': 'false'
    }

result = requests.post(request_url,
  data=json.dumps(request_payload),
  headers={'Content-Type': 'application/json; charset=UTF-8'},
  params=params)
print(result.text)



  
'''
http://docs.python-requests.org/en/master/user/quickstart/#response-content
str(result)
#print("result.ok: " + str(result.ok))
#print("result.status_code: " + str(result.status_code))
#print("result.headers: " + str(result.headers))

#print("login result: " + str(result))
#print("login result.ok: " + str(result.ok))
#print("login result.status_code: " + str(result.status_code))

# ---- set temp ----
# set temp headers

# POST /api/thermostat?sessionid=kWxsFkimIE2rhGALrwIWXQ&serialnumber=660714 HTTP/1.1
#Host: ditra-heat-e-wifi.schluter.com
#Connection: keep-alive
#Content-Length: 111
#Accept: application/json, text/javascript, */*; q=0.01
#Origin: https://ditra-heat-e-wifi.schluter.com
#User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
#DNT: 1
#Content-Type: application/json; charset=UTF-8
#Referer: https://ditra-heat-e-wifi.schluter.com/
#Accept-Encoding: gzip, deflate, br
#Accept-Language: en-US,en;q=0.9

#result = session_requests.get(
#	url, 
#	headers = dict(referer = url)
#)

#print(session_requests.cookies.get_dict())
#print(str(session_requests.cookies._cookies))
#print(session_requests.cookies)
# current floor temp
# //*[@id="thermostat_setpoint_temperature_660714"]

# current air? temperature
# //*[@id="thermostat_current_temp_660714"]

#tree = html.fromstring(result.content)
#bucket_names = tree.xpath('//*[@id="thermostat_current_temp_660714"]')
#print("result: " + str(result))
#print("result.ok: " + str(result.ok))
#print("result.status_code: " + str(result.status_code))
#print("result.headers: " + str(result.headers))

#soup = BeautifulSoup(result.content, 'html.parser')

#print(soup.prettify())

#print(bucket_names)

#print(etree.tostring(tree, pretty_print=True))

#print(result.text)
#print(str(result.content))# >> '/home/nuthanael/Desktop/content.txt'
#print(result.content == result.text)

#with open('/home/nuthanael/Desktop/content.txt', "wb") as file:
#  file.write(result.content)
#  file.close()

#def download(url, file_name):
    # open in binary mode
#    with open(file_name, "wb") as file:
#        # get request
#        response = get(url)
#        # write to file
#        file.write(response.content)

# -------------
#try:
#  result = session_requests.post(request_url + 'sessionid=' + session_id + '&serialnumber=' + serial_number,
#    data=json.dumps(request_payload),
#    headers=request_headers)

# If the response was successful, no Exception will be raised

#  result.raise_for_status()
#except HTTPError as http_err:
#  print(f'HTTP error occurred: {http_err}')  # Python 3.6
#except Exception as err:
#  print(f'Other error occurred: {err}')  # Python 3.6
#else:
#  print('Success!')

#print(result.text)
'''
