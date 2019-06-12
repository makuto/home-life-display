#!/usr/bin/python3

import json
import os

settings = None

# debugEnableAPIRequests = True
debugEnableAPIRequests = False

def loadSettings():
    global settings
    
    settingsFilename = "settings.json"
    # Load git ignored settings, if it exists (so I don't check in my API tokens)
    if os.path.isfile("LOCAL_settings.json"):
        settingsFilename = "LOCAL_settings.json"
        
    print("Loading settings from {}".format(settingsFilename))
        
    settingsFile = open(settingsFilename, "r")
    settingsLines = settingsFile.readlines()
    settingsFile.close()

    settings = json.loads("".join(settingsLines))
    print(settings)
    
loadSettings()

# Don't load something which can't be used
if settings["dropbox_token"] and debugEnableAPIRequests:
    import dropbox
    
def main():
    if not debugEnableAPIRequests:
        print("Debug mode: no API requests will occur")
        
    if settings["dropbox_token"] and debugEnableAPIRequests:
        dbx = dropbox.Dropbox(settings["dropbox_token"])
        print(dbx.users_get_current_account())
    else:
        print("No dropbox_token. Dropbox is disabled")

if __name__ == '__main__':
    print("Started Home Life Display")
    main()
