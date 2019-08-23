import requests
from getpass import getpass
import urllib3
import json
import os
import yaml
import jinja2
from datetime import datetime
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

###################Define Global Variables###################
username = 'cvpuser'
password = 'cvppassword'
cvp_server = 'cvpserver'
api_headers = {
    'Content-Type': "application/json",
    'cache-control': "no-cache",
    }
api_root = 'https://%s/cvpservice' % cvp_server
timestamp = str(datetime.now().month) + '_' + str(datetime.now().day) + '_' + str(datetime.now().hour) + '_' + str(datetime.now().minute) + '_' + str(datetime.now().second)
current_directory = os.getcwd()
directory_list = os.listdir(current_directory)
#############################################################

def rename_files():

    if 'builders' or 'static' in directory_list:
        if 'Backup' not in directory_list:
            print('Creating Backup folder')
            os.mkdir('%s\Backup' % current_directory)
        print('Creating backup for current configlets')    
        backup_directory = '%s\Backup\%s' % (current_directory, 'backup_'+timestamp)
        os.mkdir(backup_directory)

        if 'static' in directory_list:
            print('Moving current static configlets to backup folder')
            os.rename('%s\static' % current_directory, '%s\static' % backup_directory)
        
        if 'builders' in directory_list:
            print('Moving current builders to backup folder')
            os.rename(r'%s\builders' % current_directory, '%s\\builders' % backup_directory)

def authenticate():
    url_path = api_root+'/login/authenticate.do'
    payload = { "userId": username,
                "password" : password
            }

    response = requests.request('POST', url_path, data=json.dumps(payload), headers=api_headers, verify=False)
    return(response)
    

def get_configlets_list(auth):
    #Get all configlets
    url_path = api_root+'/configlet/getConfiglets.do?startIndex=0&endIndex=0'
    response = requests.request('GET', url=url_path, headers=api_headers, cookies=auth.cookies, verify=False)
    return (json.loads(response.content)['data'])

def download_configlet(configlet):
    
    if 'static' not in os.listdir(current_directory):
        print('Creating new static configlet directory')
        os.mkdir('%s/static/' % current_directory)
    print('Static: ' + configlet['name'])
    with open('./static/'+configlet['name']+'.txt', 'w') as file:
        file.write(configlet['config'])


def download_builder(configlet, auth):
    url_path = api_root+'/configlet/getConfigletBuilder.do?id='+configlet['key']
    if 'builders' not in os.listdir(current_directory):
        print('Creating new builder directory')
        os.mkdir(r'%s\builders' % current_directory)
    response = requests.request('GET', url=url_path, cookies=auth.cookies, headers=api_headers, verify=False)
    print('Builder: ' + configlet['name'])
    with open('./builders/'+configlet['name']+'.py', 'w') as file:
        file.write(json.loads(response.content)['data']['main_script']['data'])


def main():
    rename_files()
    auth = authenticate()
    configlet_list = get_configlets_list(auth)
    for configlet in configlet_list:
        if configlet['type'] == 'Static':
            download_configlet(configlet)
        elif configlet['type'] == 'Builder':
            download_builder(configlet, auth)

if __name__ == '__main__':
    main()