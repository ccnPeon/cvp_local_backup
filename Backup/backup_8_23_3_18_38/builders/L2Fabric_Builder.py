#TODO make MLAG autobuild, management build, and potentially turn this into a leaf builder too.
import requests
from getpass import getpass
import urllib3
import json
import yaml
import jinja2
from cvplibrary import CVPGlobalVariables, Form, GlobalVariableNames, device
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

###################Define Global Variables###################
username = CVPGlobalVariables.getValue(GlobalVariableNames.CVP_USERNAME)
password = CVPGlobalVariables.getValue(GlobalVariableNames.CVP_PASSWORD)
cvpserver = '10.0.0.14'
apiHeaders = {
    'Content-Type': "application/json",
    'cache-control': "no-cache",
    }
deviceIp = CVPGlobalVariables.getValue(GlobalVariableNames.CVP_IP)
apiRoot = 'https://{0}/web'.format(cvpserver)
#############################################################

def authenticate():

    urlPath = apiRoot+'/login/authenticate.do'
    payload = { "userId": username,
                "password" : password
    }

    response = requests.request('POST', urlPath, data=json.dumps(payload), headers=apiHeaders, verify=False)
    return(response)

def getAcl(auth, acl):
  urlPath = apiRoot+'/configlet/getConfigletByName.do?name='+acl+'.acl'
  response = requests.request('GET', url=urlPath, headers=apiHeaders, cookies=auth.cookies, verify=False)
  return(json.loads(response.content)['config'])

def getJinjaTemplate(auth, deviceType):
    if deviceType == 'spine':
        templatePath = 'L2Fabric_Builder_SpineBuilder.j2'
    elif deviceType == 'leaf':
        templatePath = 'L2Fabric_Builder_LeafBuilder.j2'
    urlPath = apiRoot+"/configlet/getConfigletByName.do?name=%s" % templatePath
    response = requests.request('GET', urlPath, headers=apiHeaders, cookies=auth.cookies, verify=False)
    template = json.loads(response.content)['config']
    return(template)

def getVariables(auth):
    varsPath = 'L2Fabric_Builder_varsfile.yaml'
    urlPath = apiRoot+"/configlet/getConfigletByName.do?name=%s" % varsPath
    response = requests.request('GET', urlPath, headers=apiHeaders, cookies=auth.cookies, verify=False)
    configVars = yaml.safe_load(json.loads(response.content)['config'])
    
    for environment in configVars:
      if deviceIp in configVars[environment]['spines']['devices']:
        templateVars = configVars[environment]
        templateVars['deviceType'] = 'spine'
        templateVars['hostname'] = configVars[environment]['spines']['devices'][deviceIp]
        templateVars['mgmtIp'] = deviceIp
        charChecker = templateVars['spines']['devices'][deviceIp][-1]
        #variable to be changed to intended last character
        #of hostnames Example: change to A,B if devices are
        #named "deviceA" and "deviceB", or 1,2  if devices
        #are named "device1" and "device2")
        charCheckerType = ["a","b"]
        #variable to define what the device's last octet for IPs will be for L3 configuration
        lastOctet = ["2","3"]
        
        if 'aclList' in templateVars:
          if templateVars['aclList'] != None:
            for acl in templateVars['aclList']:
              templateVars['aclList'][acl] = getAcl(auth, acl)
          
    
        if charChecker == charCheckerType[0]:
            templateVars['lastOctet'] = lastOctet[0]
            templateVars['mlagOctet'] = '254'
            return(templateVars)
        elif charChecker == charCheckerType[1]:
            templateVars['lastOctet'] = lastOctet[1]
            templateVars['mlagOctet'] = '255'
            return(templateVars)
        else:
            print('Error: Hostname must end with %s or %s' % (charCheckerType[0],charCheckerType[1]))
            return(None)

      elif deviceIp in configVars[environment]['leafs']['devices']:
        templateVars = configVars[environment]
        templateVars['deviceType'] = 'leaf'
        templateVars['hostname'] = configVars[environment]['leafs']['devices'][deviceIp]
        templateVars['mgmtIp'] = deviceIp
        charChecker = templateVars['leafs']['devices'][deviceIp][-1]
        for domainId in templateVars['leafs']['mlag']['domainIds']:
          if deviceIp in templateVars['leafs']['mlag']['domainIds'][domainId]:
            templateVars['mlagDomain'] = domainId
        #variable to be changed to intended last character
        #of hostnames Example: change to A,B if devices are
        #named "deviceA" and "deviceB", or 1,2  if devices
        #are named "device1" and "device2")
        charCheckerType = ["a","b"]
    
        if charChecker == charCheckerType[0]:
            templateVars['mlagOctet'] = '254'
            return(templateVars)
        elif charChecker == charCheckerType[1]:
            templateVars['mlagOctet'] = '255'
            return(templateVars)
        else:
            print('Error: Hostname must end with %s or %s' % (charCheckerType[0],charCheckerType[1]))
            return(None)
    

def render_config_template(varsDict, auth):
    template = getJinjaTemplate(auth, varsDict['deviceType'])
    env = jinja2.Environment(
        loader=jinja2.BaseLoader(),
        trim_blocks=True,
        extensions=['jinja2.ext.do'])
    templategen = env.from_string(template)
    if templategen:
        config = templategen.render(varsDict)
        return(config)
    return(None)
    
def main():
    authInfo = authenticate()
    configVariables = getVariables(authInfo)
    configuration = render_config_template(configVariables, authInfo)
    print(configuration)


if __name__ == '__main__':
    main()