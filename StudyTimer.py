import ui
import time
from datetime import timezone, datetime
import csv
import console
from objc_util import *
import collections
import dialogs

deviceWidth, deviceHeight = ui.get_screen_size()

# Main study button action. Either sends to Pleco and starts new timer or prompts to finish current session
def button_action(sender):
	# Is there currently a temp file? If so, we are studying
	try:
		tempFileContents = readTempCSV()
		
		timeDict = tempFileContents[0]
		timeStarted = timeDict['timeStarted']
		timeStarted = float(timeStarted)
		
		continueOption = dialogs.alert('Finish current session?', 'There is currently a studying session. Would you like to finish this session, or cancel and start a new session?', 'Finish', 'Start New', hide_cancel_button = True)
		
		if continueOption == 1:
			writeNewEntry = True
			finishedStudying(sender, writeNewEntry, timeStarted)
		else:
			startStudying(sender)		
	# Nothing in temp file, start a new study session
	except:
		startStudying(sender)		
		
		
def startStudying (sender):
	writeNewTempCSV()
	sender.superview['studyButton'].image = ui.Image.named('iob:checkmark_round_256')
	try:
		sender.superview['progressButton'].alpha = 0
	except:
		pass
		
	# Open Pleco
	plecoApi = 'plecoapi://x-callback-url/fl?'
	app = UIApplication.sharedApplication()
	app.openURL_(nsurl(plecoApi))


# Triggered by histogram button. Prepares and presents a scroll view with study history bars
def viewHistory (sender):

	# If toggle button hasn’t been selected, default to 0 (Last week)
	if (sender.superview['toggleButton'].selected_index == -1):
		sender.superview['toggleButton'].selected_index = 0
	return finishedStudying(sender, writeNewEntry = False)


def finishedStudying (sender, writeNewEntry = True, timeAtStart = 0):	
	
	# Toggle button is active but invisible, make visible
	sender.superview['toggleButton'].alpha = 1
	if writeNewEntry == True:		
		writeNewTempCSV(deleteTemp=True)
		
		timeNow = int(datetime.now(tz=timezone.utc).timestamp() )
				
		secondsStudied = timeNow - int(timeAtStart)
		
		secondsStudied = format (secondsStudied, '.0f')	
		
		timeStudied = makeSecondsIntoHourMinSec(int(secondsStudied))
		
		writeNewEntryCSV(secondsStudied)
		
		sender.superview['timerLabel'].text = str(timeStudied)
		sender.superview['studyButton'].image = ui.Image.named('iob:ios7_heart_256')
		
		sender.superview['toggleButton'].selected_index = 0
		
	else:
		# If just skipping straight to view stats
			sender.superview['studyButton'].image = ui.Image.named('iob:stats_bars_256')
	
	toggleButtonPosition = sender.superview['toggleButton'].selected_index	
	
	scrollView = makeBarButtons(toggleButtonPosition)	
	view.add_subview(scrollView)	


# Function to write new temporary entry for a study session that has started and is in progress
def writeNewTempCSV (deleteTemp = False):
	with open('studyLogTemp.csv', 'w+') as csvfile:
			fieldnames = ['startTime']
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
			
			if deleteTemp != True:
				timeNow = int(datetime.now(tz=timezone.utc).timestamp())
				writer.writerow({'startTime': str(timeNow)})

				
# Function to read temporary entry CSV for a study session in progress. Returns empty or with read lines. 			
def readTempCSV ():
	with open('studyLogTemp.csv', newline='') as csvfile:
		fieldnames = ['timeStarted']
		reader = csv.DictReader(csvfile, fieldnames=fieldnames)
		readLines = []
		for row in reader:
			readLines.append(row)
		return readLines


# Function to append a finalised study session to the csv record
def writeNewEntryCSV (secondsStudied):
	with open('studyLog.csv', 'a') as csvfile:
			fieldnames = ['unixTime', 'secondsStudied']
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
			writer.writerow({'unixTime': time.time(), 'secondsStudied': secondsStudied})
		
# Function to read study records from csv	
def readCSV ():
	with open('studyLog.csv', newline='') as csvfile:
		fieldnames = ['unixTime', 'secondsStudied']
		reader = csv.DictReader(csvfile, fieldnames=fieldnames)
		readLines = []
		for row in reader:
			readLines.append(row)
		return readLines


# Receives seconds in integer and returns str with m,s or h,m,s
def makeSecondsIntoHourMinSec (seconds):
	m, s = divmod(seconds, 60)
	h, m = divmod(m, 60)
	if h == 0:
		timeLabel = ("%02d:%02d" % (m, s))
	else:
		timeLabel = ("%d:%02d:%02d" % (h, m, s))
	return timeLabel



# Display time in alert when bar is clicked
def graphAction(sender):
	# Sender name gives us the time
	seconds = int(sender.name.replace('barButton',''))
	
	timeLabel = makeSecondsIntoHourMinSec(seconds)
	makePopUpTime(timeLabel)



def makePopUpTime (timeLabel):
	console.hud_alert(str(timeLabel))

																
def findMaxValue(times):
	elapsedTimes = []
	for row in times:
		elapsedTimes.append(int(times[row]))
	elapsedTimes.sort(reverse=True)
	return (elapsedTimes[0])

def convertUnixTimeToDdMm (times):
	dayMonthTimeRegister = []	
	for row in times:
		newDayMonth = str(time.strftime('%d/%m', time.localtime(float(row['unixTime']))))
		
		dayMonthTimeRegister.append([newDayMonth, row['secondsStudied']])		
		
	return dayMonthTimeRegister

def groupTimesIntoSameDay (dayMonthTimeRegister):
	dayMonthTimeRegister.reverse()
	
	groupedTimes = collections.OrderedDict()
	for row in dayMonthTimeRegister:
		try:	
			groupedTimes[row[0]] += int(row[1])
		except:
			groupedTimes[row[0]] = int(row[1])
	
	return groupedTimes

def makeBarButtons (toggleBarPosition):
	
	times = readCSV()
	xPos = 10
	
	# Convert UNIXTIME into dd-mm
	dayMonthTimeRegister = convertUnixTimeToDdMm(times)
	
	# Group and add times that are on the same day
	groupedTimes = groupTimesIntoSameDay(dayMonthTimeRegister)
	
	# If toggle bar set to this week only, limit to the last 7 days
	if (toggleBarPosition==0):
		newGroupedItems = collections.OrderedDict()
		i = 0
		for row in groupedTimes:
			if i < 7:
				newGroupedItems[row] = int(groupedTimes[row])				
				i = i + 1
		groupedTimes = newGroupedItems
	
	# Calculate height multiplier based on largest time
	maxValue = int(findMaxValue(groupedTimes))
	heightMultiplier = (250 / maxValue)
	
	contentSizeWidth = (len(groupedTimes)) * 45

	# Create results view
	scrollView = ui.ScrollView(name = 'Study Results')
	scrollView.content_size = (contentSizeWidth, 250)
	scrollView.bounds = 0, 0, deviceWidth, 300
	scrollView.background_color='#f6f6f6'
	scrollView.center = (deviceWidth/2, deviceHeight/7*5)
	
	# Make a bar for each day
	for row in groupedTimes:
		buttonHeight = groupedTimes[row] * heightMultiplier
		barButton, dateLabel = makeButtonAndLabelObj(xPos, buttonHeight, str(row), groupedTimes[row])
		xPos = xPos + 45
		scrollView.add_subview(barButton)
		scrollView.add_subview(dateLabel)
	
	return scrollView


def makeButtonAndLabelObj (xPos, height, dateLabel,totalSeconds):
	name = str('barButton' + str(totalSeconds))
	barButton = ui.Button (name = name, action = graphAction)
	
	barButton.height = height
	barButton.width = 35
	barButton.corner_radius = 8
	
	barButton.center = (deviceWidth/10 + xPos, deviceHeight/5)
	barButton.bg_color = '#034c03'
	barButton.tint_color = '#f6f6f6'
	
	dateLabel = makeDateLabelObj (dateLabel, barButton.center, totalSeconds)
	
	return barButton, dateLabel

# Small label in center of bar with date
def makeDateLabelObj (date, center, totalSeconds):
	# Label
	name = str('dateLabel' + str(totalSeconds))
	dateLabel = ui.Label (name = name, action = graphAction)
	dateLabel.text = date
	dateLabel.font = ('HelveticaNeue-Light', 11)
	dateLabel.text_color='#f6f6f6'
	dateLabel.height = 10
	dateLabel.width = 35
	dateLabel.center = center
	dateLabel.alignment = ui.ALIGN_CENTER
	return dateLabel
	
def makeLabelObj ():
	# Label
	timerLabel = ui.Label (name = 'timerLabel')
	timerLabel.text = ('')
	timerLabel.height = 85
	timerLabel.width = 200
	timerLabel.center = (deviceWidth/2, deviceHeight/7*2.5)
	timerLabel.alignment = ui.ALIGN_CENTER
	return timerLabel

def makeSearchButtonObj ():
	# Search Button
	searchButton = ui.Button (name = 'studyButton', action = button_action)
	searchButton.height = 85
	searchButton.width = 85
	searchButton.corner_radius = 6
	searchButton.center = (deviceWidth/2, deviceHeight/7*1.5)
	searchIcon = ui.Image.named('iob:heart_256')
	searchButton.image = searchIcon
	searchButton.bg_color = '#f6f6f6'
	searchButton.tint_color = '#ff2765'
	return searchButton
	
def makeViewProgressButtonObj ():
	# Progress Button
	searchButton = ui.Button (name = 'progressButton', action = viewHistory)
	searchButton.height = 50
	searchButton.width = 50
	searchButton.corner_radius = 6
	searchButton.center = (deviceWidth/2, deviceHeight/7*4)
	searchIcon = ui.Image.named('iob:stats_bars_256')
	searchButton.image = searchIcon
	searchButton.bg_color = '#f6f6f6'
	searchButton.tint_color = '#ff2765'
	return searchButton

def makeHistoryToggleButtonObj ():
	# Progress Button
	toggleButton = ui.SegmentedControl (name = 'toggleButton', action = viewHistory )
	#toggleButton.height = 50
	toggleButton.width = 150
	#searchButton.corner_radius = 6
	toggleButton.segments =['Last week', 'All time']
	toggleButton.center = (deviceWidth/2, deviceHeight/7*3)
	toggleButton.bg_color = '#f6f6f6'
	toggleButton.tint_color = '#ff2765'
	toggleButton.alpha = 0
	return toggleButton

# Main entry to program
def main ():
	# Create the UI and view
	global view
	view = ui.View()
	view.name = 'Study Aid'
	view.background_color = '#f6f6f6'
	
	# Create buttons and views and add to view
	view.add_subview(makeSearchButtonObj())
	view.add_subview(makeLabelObj())
	view.add_subview(makeViewProgressButtonObj())
	view.add_subview(makeHistoryToggleButtonObj())
	
	# Present view
	view.present(hide_title_bar = False, animated = True, style= 'full_screen')

if __name__ == '__main__':
	main()
