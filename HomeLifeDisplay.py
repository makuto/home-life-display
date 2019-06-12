#!/usr/bin/python3
# -*- coding:utf-8 -*-

import json
import os

# E-paper includes
import epd7in5
import time
from PIL import Image,ImageDraw,ImageFont
import traceback

"""
Debug settings to avoid overusing hardware/APIs
"""

# debugEnableAPIRequests = True
debugEnableAPIRequests = False

# debugEnableEPaperDisplay = True
debugEnableEPaperDisplay = False

"""
Settings
"""

settings = None

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

"""
E-Paper Display
"""

epaperDisplay = None

# Clear the e-paper
def initializeEPaper():
    global epaperDisplay
    
    if not debugEnableEPaperDisplay:
        return
    
    try:
        epaperDisplay = epd7in5.EPD()
        epaperDisplay.init()
        print("E-Paper: Clear")
        epaperDisplay.Clear(0xFF)
        
        epaperDisplay.sleep()
    except:
        print('traceback.format_exc():\n%s', traceback.format_exc())
        exit()
        
def sleepEPaper():
    if epaperDisplay:
        try:
            epaperDisplay.sleep()
        except:
            exit()

"""
Main
"""

# Don't load something which can't be used (importing dropbox takes a while)
if settings["dropbox_token"] and debugEnableAPIRequests:
    print("Importing dropbox API...")
    import dropbox
    print("done.")
else:
    print("No dropbox_token or debugEnableAPIRequests is true. Dropbox is disabled")
    
def main():
    if not debugEnableAPIRequests:
        print("Debug mode: no API requests will occur")
    if not debugEnableEPaperDisplay:
        print("Debug mode: no E-Paper actions will occur")

    print("--------------------------------------\n")
        
    if settings["dropbox_token"] and debugEnableAPIRequests:
        dbx = dropbox.Dropbox(settings["dropbox_token"])
        print(dbx.users_get_current_account())

    if debugEnableEPaperDisplay:
        initializeEPaper()

if __name__ == '__main__':
    print("\nStarted Home Life Display\n")
    try:
        main()
    except:
        # Make sure we put the display to sleep, otherwise it
        # could get damaged
        sleepEPaper()
