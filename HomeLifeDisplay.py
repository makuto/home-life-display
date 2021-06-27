#!/usr/bin/python3
# -*- coding:utf-8 -*-

import datetime
import json
import os
import orgparse

import time
from PIL import Image,ImageDraw,ImageFont
import traceback

"""
Debug settings to avoid overusing hardware/APIs
"""

#debugEnableAPIRequests = True
debugEnableAPIRequests = False

#debugEnableEPaperDisplay = True
debugEnableEPaperDisplay = False

width = 640
height = 384

if debugEnableEPaperDisplay:
    # E-paper includes
    import epd7in5
    width = width
    height = epd7in5.EPD_HEIGHT

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
        epaperDisplay.Clear()

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
Color_EPaper_Red = 1
# 192 < White
Color_EPaper_White = 255

# They changed the API to take two images instead, where even red is 0
def colorToFill(color):
    if color == Color_EPaper_Black:
        return 0
    elif color == Color_EPaper_Red:
        return 0
    elif color == Color_EPaper_White:
        return 255
    return 0

# Useful for testing without wearing out the display
def imageConvertMode1BPPToRGB(image, isZeroRed = False):
    # Colors for non-Epaper display
    Color_RGB_Black = (0, 0, 0)
    Color_RGB_Red = (255, 0, 0)
    Color_RGB_White = (255, 255, 255)

    convertedImage = Image.new("RGB", (width, height), Color_RGB_White)
    convertedData = []
    for y in range(image.height):
        for x in range(image.width):
            value = image.getpixel((x, y))
            if value == 0:
                convertedData.append(Color_RGB_Red if isZeroRed else Color_RGB_Black)
            else:
                convertedData.append(Color_RGB_White)
    convertedImage.putdata(convertedData)
    return convertedImage

# Fonts
# For Japanese
fontJapanese = ImageFont.truetype('/usr/share/fonts/truetype/fonts-japanese-gothic.ttf', 24)
fontJapaneseHuge = ImageFont.truetype('/usr/share/fonts/truetype/fonts-japanese-gothic.ttf', 44)
# For English
fontUbuntuMonoSmall = ImageFont.truetype('ubuntu-font-family-0.83/UbuntuMono-R.ttf', 20)
fontUbuntuMono = ImageFont.truetype('ubuntu-font-family-0.83/UbuntuMono-R.ttf', 24)
fontUbuntuMonoMedium = ImageFont.truetype('ubuntu-font-family-0.83/UbuntuMono-R.ttf', 38)
fontUbuntuMonoHuge = ImageFont.truetype('ubuntu-font-family-0.83/UbuntuMono-R.ttf', 64)
# These are actually chinese fonts, that will support Japanese with some (confusing) variations
# fontMicrohei = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 24)
# fontMicroheiHuge = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 38)

class Layout:
    def __init__(self):
        self.margins = 10
        self.topHeader = 64
        self.topHeaderRightMargin = 10

def drawLayout1BPPImage(agendaList):
    layout = Layout()

    # Clear the frame
    # 1 = 1 byte per pixel mode
    imageBlack = Image.new('1', (width, height), Color_EPaper_White)
    imageRed = Image.new('1', (width, height), Color_EPaper_White)
    drawBlack = ImageDraw.Draw(imageBlack)
    drawRed = ImageDraw.Draw(imageRed)

    #
    # Large date
    #
    # Circle background
    timeNow = datetime.date.today()
    dateString = timeNow.strftime("%b\n%d")
    # Right align by getting text size
    dateTextSize = drawBlack.multiline_textsize(dateString, font = fontUbuntuMonoHuge)
    dateTextHorizontalOffset = layout.topHeader - 15
    circleOffset = (-23, 34 + dateTextHorizontalOffset)
    # drawBlack.arc((width - (dateTextSize[0]) + circleOffset[0],
    #           -dateTextSize[1] + circleOffset[1],
    #           width + (dateTextSize[0]) + circleOffset[0],
    #           dateTextSize[1] + circleOffset[1]),
    #          0, 360,
    #          fill = Color_EPaper_Black, width = 5)

    # Outer
    drawBlack.ellipse((width - (dateTextSize[0]) + circleOffset[0],
                       -dateTextSize[1] + circleOffset[1],
                       width + (dateTextSize[0]) + circleOffset[0],
                       dateTextSize[1] + circleOffset[1]),
                      fill = Color_EPaper_Black)
    # Inner
    drawBlack.ellipse((width - (dateTextSize[0]) + circleOffset[0] - 5,
                       -dateTextSize[1] + circleOffset[1] - 5,
                       width + (dateTextSize[0]) + circleOffset[0] - 5,
                       dateTextSize[1] + circleOffset[1] - 5),
                      fill = Color_EPaper_White)
    drawRed.multiline_text((width - dateTextSize[0] - layout.margins,
                            layout.margins + dateTextHorizontalOffset),
                           dateString,
                           font = fontUbuntuMonoHuge, fill = colorToFill(Color_EPaper_Red), align = "right")

    #
    # Header
    #
    headerLabel = u'日本語'
    headerLabel = u'漢字'
    drawRed.text((layout.margins, layout.margins), headerLabel, font = fontJapaneseHuge,
                 fill = colorToFill(Color_EPaper_Red))
    headerLabelSize = drawBlack.textsize(headerLabel, font = fontJapaneseHuge)

    # Study review schedule
    # Interval:days
    # kanjiScheduleIntervals = [('T', 3), ('W', 7), ('BM', 15), ('M', 30), ('2M', 60), ('4M', 120), ('6M', 180)]
    # kanjiScheduleIntervalsJapanese = [(u'半週', 3) ,(u'一週', 7), (u'半月', 15),
    #                                   (u'一月', 30), (u'二月', 2 * 30), (u'四月', 4 * 30), (u'六月', 6 * 30), (u'十月', 10 * 30)]
    kanjiScheduleIntervalsJapanese = [(u'半月', 15), (u'一月', 30), (u'二月', 2 * 30), (u'四月', 4 * 30),
                                      (u'六月', 6 * 30), (u'十月', 10 * 30), (u'長年', 18 * 30)]

    # Keeping the labels only as comments, effectively
    kanjiScheduleStartDates = [
        # ('T', datetime.date(2019, 6, 15)),
        # ('W', datetime.date(2019, 6, 1)),
        ('BM', datetime.date(2019, 6, 15)),
        ('M', datetime.date(2019, 6, 1)),
        ('2M', datetime.date(2019, 5, 31)),
        ('4M', datetime.date(2019, 5, 31)),
        ('6M', datetime.date(2019, 5, 31)),
        ('10M', datetime.date(2019, 11, 24)),
        ('1.5Y', datetime.date(2020, 9, 22))]
    # Interval countdowns
    # TODO These don't match up to my actual schedule quite right yet
    for i in range(len(kanjiScheduleIntervalsJapanese)):
        label = kanjiScheduleIntervalsJapanese[i][0]
        labelSize = drawBlack.textsize(label, fontJapanese)
        labelWithSpaceSize = drawBlack.textsize(label + u"     ", fontJapanese)

        date = kanjiScheduleStartDates[i]
        countdownDays = ((kanjiScheduleIntervalsJapanese[i][1] -
                          (timeNow - date[1]).days) % kanjiScheduleIntervalsJapanese[i][1])
        countdownDaysText = "{}".format(str(countdownDays))
        # Star for shuffling
        if countdownDays == 0:
            countdownDaysText = str(kanjiScheduleIntervalsJapanese[i][1])
            countdownDaysText += "*"

        countdownSize = drawBlack.textsize(countdownDaysText, fontUbuntuMono)

        scheduleMargin = layout.margins + headerLabelSize[0] + 5
        intervalOffset = labelWithSpaceSize[0] * i
        countdownCenterAlign = (labelSize[0] - countdownSize[0]) / 2
        # countdownRightAlign = (labelSize[0] - countdownSize[0])
        countdownColor = Color_EPaper_Red if countdownDays <= 3 else Color_EPaper_Black

        print("{}\t{}".format(label, countdownDaysText))

        drawBlack.text((scheduleMargin + intervalOffset, layout.margins),
                       label, font = fontJapanese, fill = colorToFill(Color_EPaper_Black))
        if countdownColor == Color_EPaper_Red:
            drawRed.text((scheduleMargin + intervalOffset + countdownCenterAlign, layout.margins + labelSize[1]),
                         countdownDaysText, font = fontUbuntuMono, fill = colorToFill(countdownColor), align = "right")
        else:
            drawBlack.text((scheduleMargin + intervalOffset + countdownCenterAlign, layout.margins + labelSize[1]),
                           countdownDaysText, font = fontUbuntuMono, fill = colorToFill(countdownColor), align = "right")

    # Divider
    drawBlack.line((layout.margins, layout.topHeader,
                    width - layout.margins, layout.topHeader),
                   fill = colorToFill(Color_EPaper_Black))

    #
    # Agenda
    #
    agendaHeaderSize = drawBlack.textsize('Agenda', font = fontUbuntuMonoMedium)
    drawRed.text((layout.margins, layout.topHeader),
                 'Agenda',
                 font = fontUbuntuMonoMedium, fill = colorToFill(Color_EPaper_Red))
    timeRangeSize = drawBlack.textsize('(30 Days)', font = fontUbuntuMonoSmall)
    drawBlack.text((layout.margins + agendaHeaderSize[0], layout.topHeader + (agendaHeaderSize[1] - timeRangeSize[1]) - 4),
                   " (30 Days)",
                   font = fontUbuntuMonoSmall, fill = colorToFill(Color_EPaper_Black))

    taskY = 0

    today = datetime.datetime.today()
    # This is a hack because descenders are taller
    taskMaxTextSize = drawBlack.textsize("Ty", font = fontUbuntuMono)
    lastTextSize = 0
    for i in range(len(agendaList)):
        taskStr = ""
        dateTaskPair = agendaList[i]
        daysFromToday = (dateTaskPair[0] - today).days
        taskColor = Color_EPaper_Red if daysFromToday < 0 else Color_EPaper_Black

        # Stop at 30 days from now
        if daysFromToday > 30:
            break

        onSameDay = (i > 0
                     and (dateTaskPair[0] - agendaList[i - 1][0]).days == 0
                     and dateTaskPair[0].day == agendaList[i - 1][0].day)
        inSameMonth = (i > 0
                       and dateTaskPair[0].month == agendaList[i - 1][0].month)

        if onSameDay:
            # Continue the date
            taskStr = '       {}'.format(dateTaskPair[1])
        elif inSameMonth:
            # Leave off the month string
            taskStr = '    {} {}'.format(dateTaskPair[0].strftime('%d'), dateTaskPair[1])
        else:
            taskStr = '{} {}'.format(dateTaskPair[0].strftime('%b %d'), dateTaskPair[1])

        if taskColor == Color_EPaper_Red:
            drawRed.text((layout.margins, layout.topHeader + agendaHeaderSize[1] + (taskMaxTextSize[1] * taskY)),
                         taskStr,
                         font = fontUbuntuMono, fill = colorToFill(taskColor))
        else:
            drawBlack.text((layout.margins, layout.topHeader + agendaHeaderSize[1] + (taskMaxTextSize[1] * taskY)),
                           taskStr,
                           font = fontUbuntuMono, fill = colorToFill(taskColor))

        taskY += 1

    # draw.multiline_text((layout.margins, layout.topHeader + 20), agendaStr,
    # font = fontUbuntuMono, fill = Color_EPaper_Black)
    # draw.text((layout.margins, layout.topHeader + 20), 'TODO Make agenda work', font = fontUbuntuMono, fill = Color_EPaper_Black)
    # draw.text((layout.margins, layout.topHeader + 40), u'食べて太鼓をしたいだ。', font = fontJapanese, fill = Color_EPaper_Black)

    # draw.line((70, 50, 20, 100), fill = 0)
    # draw.rectangle((20, 50, 70, 100), outline = 0)
    # draw.line((165, 50, 165, 100), fill = 0)
    # draw.line((140, 75, 190, 75), fill = 0)
    # draw.arc((140, 50, 190, 100), 0, 360, fill = 0)
    # draw.rectangle((80, 50, 130, 100), fill = 0)
    # draw.chord((200, 50, 250, 100), 0, 360, fill = 0)

    return (imageBlack, imageRed)

def imageDisplayOnEPaper(imageBlack, imageRed):
    if not epaperDisplay:
        print("No epaper display!")
        return

    print("Home Life Display drawing...")

    epaperDisplay.display(epaperDisplay.getbuffer(imageBlack), epaperDisplay.getbuffer(imageRed))
    time.sleep(2)
    epaperDisplay.sleep()

def getAllOrgScheduledTasks_Recursive(root, tasks = None):
    if not tasks:
        # Use dictionary for uniqueness
        tasks = {}
    for node in root[1:]:
        if node.scheduled and not node.closed and not node.todo == 'DONE':
            # Key with the heading and date to not conflict with same-name tasks on different days
            tasks[node.heading + str(node.scheduled)] = (node.heading, node.scheduled)

        # TODO: Fix duplicate entries
        if node.children:
            getAllOrgScheduledTasks_Recursive(node.children, tasks = tasks)

    return tasks

# Convert dates to datetimes so they can be compared
def convertDateDateTime(key):
    if type(key) == datetime.date:
        return datetime.datetime(key.year, key.month, key.day, 0, 0)
    else:
        return key

def getAgenda():
    taskList = []

    for orgAgendaFile in settings["org_agenda_files"]:
        # Parse org file for any scheduled tasks
        orgRoot = orgparse.load(orgAgendaFile)
        scheduledTasks = getAllOrgScheduledTasks_Recursive(orgRoot)

        for taskKey, taskDatePair in scheduledTasks.items():
            taskList.append((convertDateDateTime(taskDatePair[1].start), taskDatePair[0]))

    sortedTaskList = sorted(taskList, key = lambda task: task[0])
    return sortedTaskList

def main():
    if not debugEnableAPIRequests:
        print("Debug mode: no API requests will occur")
    if not debugEnableEPaperDisplay:
        print("Debug mode: no E-Paper actions will occur")

    print("--------------------------------------\n")

    print("Getting agenda")
    agendaList = getAgenda()

    print("Drawing image")
    images = drawLayout1BPPImage(agendaList)

    # Output image
    print("Output images")
    imageConvertMode1BPPToRGB(images[0]).save("outputBlack.png", isZeroRed = False)
    imageConvertMode1BPPToRGB(images[1]).save("outputRed.png", isZeroRed = True)
    print("Saved to {}".format("output[Black|red].png"))

    # Output to e-Paper
    if debugEnableEPaperDisplay:
        print("Output images to E-paper")
        initializeEPaper()
        imageDisplayOnEPaper(images[0], images[1])

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
