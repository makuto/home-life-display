#!/usr/bin/python3
# -*- coding:utf-8 -*-

import datetime
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

# TODO: *important* Blank display during the night time to prevent burn in (look up best practices there)

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

        # If you sleep here, it won't respond to commands
        # epaperDisplay.sleep()
    except:
        print('traceback.format_exc():\n%s', traceback.format_exc())
        exit()

    print("E-paper initialized")
        
def sleepEPaper():
    if epaperDisplay:
        try:
            epaperDisplay.sleep()
        except:
            exit()

"""
Main
"""

# Black < 64
Color_EPaper_Black = 0
# 64 < Red < 192
Color_EPaper_Red = 180
# 192 < White
Color_EPaper_White = 255

# Colors for non-Epaper display
Color_RGB_Black = (0, 0, 0)
Color_RGB_Red = (255, 0, 0)
Color_RGB_White = (255, 255, 255)

convertEPaperColorToRGB = {
    Color_EPaper_Black:Color_RGB_Black,
    Color_EPaper_Red:Color_RGB_Red,
    Color_EPaper_White:Color_RGB_White}

# Useful for testing without wearing out the display
def imageConvertMode1BPPToRGB(image):
    convertedImage = Image.new("RGB", (epd7in5.EPD_WIDTH, epd7in5.EPD_HEIGHT), Color_RGB_White)
    convertedData = []
    for y in range(image.height):
        for x in range(image.width):
            value = image.getpixel((x, y))
            convertedData.append(convertEPaperColorToRGB[value])
    convertedImage.putdata(convertedData)
    return convertedImage

# Fonts
# For Japanese
fontMicrohei = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 24)
fontMicroheiHuge = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 36)
# For English
fontUbuntuMono = ImageFont.truetype('ubuntu-font-family-0.83/UbuntuMono-R.ttf', 24)
fontUbuntuMonoHuge = ImageFont.truetype('ubuntu-font-family-0.83/UbuntuMono-R.ttf', 64)

class Layout:
    def __init__(self):
        self.margins = 10
        self.topHeader = 64

def drawLayout1BPPImage():
    layout = Layout()
    
    # Clear the frame
    # 1 = 1 byte per pixel mode
    image = Image.new('1', (epd7in5.EPD_WIDTH, epd7in5.EPD_HEIGHT), Color_EPaper_White)
    draw = ImageDraw.Draw(image)
    
    # Large date
    timeNow = datetime.date.today()
    dateString = timeNow.strftime("%b\n%d")
    # Right align by getting text size
    dateTextSize = draw.multiline_textsize(dateString, font = fontUbuntuMonoHuge)
    draw.multiline_text((epd7in5.EPD_WIDTH - dateTextSize[0] - layout.margins, layout.margins), dateString,
                        font = fontUbuntuMonoHuge, fill = Color_EPaper_Red, align = "right")

    #
    # Header
    #
    headerLabel = u'日本語'
    draw.text((layout.margins, layout.margins), headerLabel, font = fontMicroheiHuge, fill = Color_EPaper_Red)
    headerLabelSize = draw.textsize(headerLabel, font = fontMicroheiHuge)

    # Study review schedule
    # Interval:days
    # kanjiScheduleIntervals = [('T', 3), ('W', 7), ('BM', 15), ('M', 30), ('2M', 60), ('4M', 120), ('6M', 180)]
    kanjiScheduleIntervalsJapanese = [(u'半週', 3) ,(u'一週', 7), (u'半月', 15),
                                      (u'一月', 30), (u'二月', 2 * 30), (u'四月', 4 * 30), (u'六月', 6 * 30)]
    # Keeping the labels only as comments, effectively
    kanjiScheduleStartDates = [('T', datetime.date(2019, 6, 15)),
                               ('W', datetime.date(2019, 6, 1)),
                               ('BM', datetime.date(2019, 6, 15)),
                               ('M', datetime.date(2019, 6, 1)),
                               ('2M', datetime.date(2019, 5, 31)),
                               ('4M', datetime.date(2019, 5, 31)),
                               ('6M', datetime.date(2019, 5, 31))]
    # Interval countdowns
    # TODO These don't match up to my actual schedule quite right yet
    for i in range(len(kanjiScheduleIntervalsJapanese)):
        label = kanjiScheduleIntervalsJapanese[i][0]
        labelSize = draw.textsize(label, fontMicrohei)
        labelWithSpaceSize = draw.textsize(label + u"  ", fontMicrohei) 

        date = kanjiScheduleStartDates[i]
        oneDayDelta = datetime.timedelta(days=-1);
        countdownDays = ((kanjiScheduleIntervalsJapanese[i][1] -
            (timeNow - date[1] + oneDayDelta).days) % kanjiScheduleIntervalsJapanese[i][1])
        countdownDaysText = "{}".format(str(countdownDays))
        # Star for shuffling
        if countdownDays == 0:
            countdownDaysText += "*"
        countdownSize = draw.textsize(countdownDaysText, fontUbuntuMono)
        
        scheduleMargin = layout.margins + headerLabelSize[0] + 5
        intervalOffset = labelWithSpaceSize[0] * i
        countdownRightAlign = labelSize[0] - countdownSize[0]
        countdownColor = Color_EPaper_Red if countdownDays <= 3 else Color_EPaper_Black
        
        draw.text((scheduleMargin + intervalOffset, layout.margins),
                  label, font = fontMicrohei, fill = Color_EPaper_Black)
        draw.text((scheduleMargin + intervalOffset + countdownRightAlign, layout.margins + labelSize[1]),
                  countdownDaysText, font = fontUbuntuMono, fill = countdownColor, align = "right")
            
    # Divider
    draw.line((layout.margins, layout.topHeader, epd7in5.EPD_WIDTH - dateTextSize[0] - layout.margins, layout.topHeader),
              fill = Color_EPaper_Black)

    #
    # Body
    #
    draw.text((layout.margins, layout.topHeader), 'Agenda', font = fontUbuntuMono, fill = Color_EPaper_Red)
    draw.text((layout.margins, layout.topHeader + 20), 'TODO Make agenda work', font = fontUbuntuMono, fill = Color_EPaper_Black)
    draw.text((layout.margins, layout.topHeader + 40), u'食べて太鼓をしたいだ。', font = fontMicrohei, fill = Color_EPaper_Black)
    
    # draw.line((70, 50, 20, 100), fill = 0)
    # draw.rectangle((20, 50, 70, 100), outline = 0)
    # draw.line((165, 50, 165, 100), fill = 0)
    # draw.line((140, 75, 190, 75), fill = 0)
    # draw.arc((140, 50, 190, 100), 0, 360, fill = 0)
    # draw.rectangle((80, 50, 130, 100), fill = 0)
    # draw.chord((200, 50, 250, 100), 0, 360, fill = 0)
    
    return image

def imageDisplayOnEPaper(image):
    if not epaperDisplay:
        print("No epaper display!")
        return

    print("Home Life Display drawing...")

    epaperDisplay.display(epaperDisplay.getbuffer(image))
    time.sleep(2)
    epaperDisplay.sleep()

# Import dropbox, if usable
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

    image = drawLayout1BPPImage()
        
    if debugEnableEPaperDisplay:
        initializeEPaper()
        imageDisplayOnEPaper(image)

    # Output image
    image = drawLayout1BPPImage()
    outputFilename = "output.png"
    imageConvertMode1BPPToRGB(image).save(outputFilename)
    print("Saved to {}".format(outputFilename))

if __name__ == '__main__':
    print("\nStarted Home Life Display\n")
    try:
        main()
    except Exception as e:
        print('[ERROR] Exception:\n\t {}'
              .format(e))
    finally:
        # Make sure we put the display to sleep, otherwise it
        # could get damaged
        print("Putting E-Paper to sleep (sweet dreams~~)")
        sleepEPaper()

# Local Variables:
# compile-command: "./HomeLifeDisplay.py"
# End:
