import yaml
import requests
import json
from cvplibrary import CVPGlobalVariables, GlobalVariableNames
from cvplibrary import Device

#Revision 0.6

device_ip = CVPGlobalVariables.getValue(GlobalVariableNames.CVP_IP)
dev_user = CVPGlobalVariables.getValue(GlobalVariableNames.CVP_USERNAME)
dev_pass = CVPGlobalVariables.getValue(GlobalVariableNames.CVP_PASSWORD)

def authenticate():
  #Send username and password via API and get session ID in cookies in order to use for future API calls.
  
  #Login API Url
  authUrl = "https://localhost/web/login/authenticate.do"
  
  #Create JSON object with username and password.
  authPayload = '''{
    "userId": \"%s\",
    "password": \"%s\"
    }''' % (dev_user, dev_pass)
    
  #Establish connection headers                  
  headers = {
      'Content-Type': "application/json",
      'cache-control': "no-cache",
      }
  
  #Perform API call for authentication and log response as a variable.
  response = requests.request("POST", authUrl, data=authPayload, headers=headers, verify=False)
  
  #Pull coookies out of response that contains session ID.
  connectionCookies = response.cookies
  
  #Return cookies to main for use with other functions.
  return(connectionCookies)

def buildVlan(connectionCookies):
  #Get Device name and IP for SVIs based on Device Hostname
  deviceCollect = getDeviceNAMEID()
  device_name = deviceCollect[0]
  svi_ip = deviceCollect[1]
  #Create Vlan Dictionary
  vlanDict = {}
  #Route Target Dictionary
  tarDict = {}

  #Get vlans from a specified configlet that will be in YAML format.
  
    #Get Configlet API URL
  url = "https://localhost/cvpservice/configlet/getConfigletByName.do"
  
  #Establish connection headers
  headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
  
  #Query string to specify the name of the configlet.
  querystring = {"name":"VLAN-CB.yml"}
  
  #Perform API call to get the configlet by name based on the URL and Query String and save response to a
  #variable.
  response = requests.request("GET", url, cookies=connectionCookies, headers=headers, params=querystring, verify=False)
  
  #Load the JSON object from the 'config' output in the response, read it as YAML, and save it to a variable
  deviceInfo = yaml.safe_load(json.loads(response.text)['config'])

#Loop through DEVICEs and print vlan and SVI
  if "agg" in device_name:
    for device in deviceInfo['devices']:
      if device['deviceName'] == device_name:
        for v1 in device['appliedVlans']:
          for vlan in deviceInfo['vlans']:
            if str(vlan['vlanId']) == str(v1):
              print('vlan ' + str(vlan['vlanId']))
              print('name ' + vlan['name'])
              print "!"
              print('interface vlan ' + str(vlan['vlanId']))
              print('description ') + vlan['name']
              print('ip address ' + vlan['subnet'][:-1] + svi_ip + vlan['mask'])
              print('ip virtual-router address ' + vlan['subnet'][:-1] + "1")
              print "!"
  else:
    if "dci" in device_name:
      #build vxlan interface based on applied vlans
      print "interface vxlan1"
      for device in deviceInfo['devices']:
        if device['deviceName'] == device_name:
          for v2 in device['appliedVlans']:
            for vxlan in deviceInfo['vlans']:
              if str(vxlan['vlanId']) == str(v2):
                print ('vxlan vlan ' + str(vxlan['vlanId']) + ' vni ' + vxlan['vlanVni'])
      for device in deviceInfo['devices']:
        if device['deviceName'] == device_name:
          for v1 in device['appliedVlans']:
            for vlan in deviceInfo['vlans']:
              if str(vlan['vlanId']) == str(v1):
                print('vlan ' + str(vlan['vlanId']))
                print('name ' + vlan['name'])
                print "!"
    else:
      for device in deviceInfo['devices']:
        if device['deviceName'] == device_name:
          for v1 in device['appliedVlans']:
            for vlan in deviceInfo['vlans']:
              if str(vlan['vlanId']) == str(v1):
                print('vlan ' + str(vlan['vlanId']))
                print('name ' + vlan['name'])
                print "!"

def getDeviceNAMEID():
  #Get device name to determine SVI IP
  cmdList = ['show hostname']
  device = Device(device_ip,dev_user,dev_pass)

  dict_resp = device.runCmds(cmdList)
  device_hostname = dict_resp[0]['response']['hostname']
  if "gdc" in device_hostname:
    svi_id = 2
  else:
    svi_id = 4
  if device_hostname.endswith('2'):
    svi_id = svi_id + 1
  return device_hostname, str(svi_id)

def main():
  #Main function
  connectionCookies = authenticate()
  buildVlan(connectionCookies)
  
if __name__ == '__main__':
    main()
    