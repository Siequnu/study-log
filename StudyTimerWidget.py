import appex, ui, os
from imp import reload
import StudyTimer; reload (StudyTimer)
from objc_util import *
import time
import console
from datetime import date
import datetime 

def refreshHistory (sender):
	
	main()

def viewHistory(sender):
	# Get graph data
	csvData = StudyTimer.readCSV()
	
	# Convert UNIXTIME into dd-mm
	dayMonthTimeRegister = StudyTimer.convertUnixTimeToDdMm(csvData)
		
	# Group and add times that are on the same day
	groupedTimes = StudyTimer.groupTimesIntoSameDay(dayMonthTimeRegister)
	
	# Get the latest 7 only
	while (len(groupedTimes) > 6):
		groupedTimes.popitem()
	
	# Calculate height multiplier based on largest time
	maxValue = int(StudyTimer.findMaxValue(groupedTimes))
	heightMultiplier = (75 / maxValue)
	
	xPos = 15
	# Make a bar for each day
	for row in groupedTimes:
		buttonHeight = groupedTimes[row] * heightMultiplier
		barButton, dateLabel = makeButtonAndLabelObj(xPos, buttonHeight, str(row), groupedTimes[row])
		xPos = xPos + 45
		
		try:
			global view
			view.add_subview(barButton)
			view.add_subview(dateLabel)
		except:
			pass

def makeButtonAndLabelObj (xPos, height, dateLabel,totalSeconds):
	name = str('barButton' + str(totalSeconds))
	barButton = ui.Button (name = name, action = StudyTimer.graphAction)
	
	barButton.height = height
	barButton.width = 30
	barButton.corner_radius = 8
	
	barButton.center = (30 + xPos, 50)
	barButton.bg_color = '#106510'
	barButton.tint_color = '#f6f6f6'
	
	dateLabel = makeDateLabelObj (dateLabel, barButton.center, totalSeconds)
	
	return barButton, dateLabel


# Small label in center of bar with date
def makeDateLabelObj (date, center, totalSeconds):
	# Label
	name = str('dateLabel' + str(totalSeconds))
	dateLabel = ui.Label (name = name, action = StudyTimer.graphAction)
	dateLabel.text = date
	dateLabel.font = ('HelveticaNeue-Light', 11)
	dateLabel.text_color='#f6f6f6'
	dateLabel.height = 10
	dateLabel.width = 35
	dateLabel.center = center
	dateLabel.alignment = ui.ALIGN_CENTER
	return dateLabel


def main():
	v = appex.get_widget_view()
	global view
	view = ui.View(frame=(0, 0, 320, 64), name='StudyTimerWidget')
	
	sender = True
	viewHistory(sender)
	
	'''
	label = ui.Label(frame=(0, 0, 320-44, 64), flex='wh', font=('HelveticaNeue-Light', 64), alignment=ui.ALIGN_CENTER, text='')
	label.name = 'timerLabel'
	view.add_subview(label)
	
	global studyButton
	studyButton = ui.Button(name='studyButton', image=ui.Image('iow:ios7_heart_outline_256'), flex='hl', tint_color='#ff2765', action=button_tapped)
	studyButton.frame = (320-100, 0, 64, 64)
	view.add_subview(studyButton)
	

	reset_btn = ui.Button(name='viewHistory', image=ui.Image('iow:ios7_heart_32'), flex='h', tint_color='#ff2765', action=refreshHistory)
	reset_btn.frame = (320-40, 0, 64, 64)
	view.add_subview(reset_btn)
	'''
	
	appex.set_widget_view(view)
	
	

if __name__ == '__main__':
	main()
	
