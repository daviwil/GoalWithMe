import calendar
from datetime import datetime, timedelta
from goalwithme import app
from goalwithme.model import DashboardSettings

def SafeLower(str):
    if str is not None:
        return str.lower()
    return str

@app.template_filter('dateformat')
def DateTimeFormat(value, format='%m/%d/%Y'):
    return value.strftime(format).lstrip('0')

@app.template_filter('monthname')
def DateTimeFormat(monthNum):
	return calendar.month_name[int(monthNum)]

def GetFirstDayOfWeek(fullDate):
	return (fullDate + timedelta(-fullDate.weekday()))

def DayKey(date, unit = None):
	return "%d-%d-%d_%d" % (date.year, date.month, date.day, unit) if unit else \
		"%d-%d-%d" % (date.year, date.month, date.day)

def MonthKey(date, unit = None):
	return "%d-%d_%d" % (date.year, date.month, unit) if unit else \
		"%d-%d" % (date.year, date.month)

def YearKey(date, unit = None):
	return "%d_%d" % (date.year, unit) if unit else \
		"%d" % date.year

def GetUnitKey(dateKey, unitId):
	return "%s_%d" % (dateKey, unitId)

def GetWeekChartData(startDay, dayList):
    i = 0
    num = dayList.count()
    # TODO: limit this by month
    for day in range(startDay, startDay + 7):
        if i >= num or day != dayList[i].DayOfMonth:
            yield 0
        else:
            yield dayList[i].TotalEntries
            i += 1

import random
def GetMonthChartData(year, month, dayList):
#	for i in range(1, 30):
#		yield random.randint(0, 10)
    i = 0
    num = dayList.count()
    for day in range(1, calendar.monthrange(year, month)[1]):
        if i >= num or day != dayList[i].DayOfMonth:
            yield 0
        else:
            yield dayList[i].TotalEntries
            i += 1

def GetYearChartData(monthList):
    i = 0
    num = monthList.count()
    for month in range(1, 12):
        if i >= num or month != monthList[i].Month:
            yield 0
        else:
            yield monthList[i].TotalEntries
            i += 1

def GetDashboardSettings(profile, createIfNotFound=True, commitOnCreate=False):
	settings = DashboardSettings.get_by_key_name(profile.UserName, parent=profile)
	if not settings and createIfNotFound:
		settings = DashboardSettings(parent=profile, key_name=profile.UserName)
		if commitOnCreate:
			settings.put()
	return settings
