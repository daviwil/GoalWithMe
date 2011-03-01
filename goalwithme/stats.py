from datetime import timedelta
from goalwithme.model import *
from goalwithme.helpers import *

# NOTES:
# - Don't let user log more time today than they're supposed to, or at least don't 
#	let it count to goal completion.  Maybe cap off completion and let them log whatever?

def GetUnitTotal(key_name, parent, unit, statsKey):
	unitTotal = UnitTotal.get_by_key_name(key_name, parent=parent)
	if not unitTotal:
		unitTotal = UnitTotal(key_name=key_name, parent=parent, Unit=unit)
	return unitTotal

def IncrementCounterList(counterList, index, length=5):
	if counterList == None or len(counterList) == 0:
		counterList = ["0"] * length
	if index < len(counterList):
		counterList[index] = str(int(counterList[index]) + 1)
	return counterList

# Take one new entry for the user profile and
# add it into the stats for all time periods.
# Returns True if this entry completes the goal.
def AddEntryToStats(profile, parent, entry, fullDate, addToDashboard = False):
	# Quick calculations
	shortDate = fullDate.date()
	weekBeginDate = GetFirstDayOfWeek(fullDate).date()

	# Get all stats objects starting with week because old day stats might
	# be deleted for dashboard data, so new day stats should be created after that.
	key_name = DayKey(weekBeginDate)
	week = WeekStats.get_by_key_name(key_name, parent=parent)
	if not week:
		week = WeekStats(key_name=key_name, parent=parent)
		week.WeekBeginDate = weekBeginDate
		week.Month = fullDate.month
		week.Year = fullDate.year

	userWeek = None
	if addToDashboard and weekBeginDate != GetFirstDayOfWeek(datetime.now()).date():
		settings = GetDashboardSettings(profile, True)
		userWeek = WeekStats.get_by_key_name(key_name, parent=settings)
		if not userWeek:
			# Delete any previous week and day stats
			dayData = db.Query(DayStats, keys_only=True).ancestor(settings)
			db.delete(dayData)			
			weekData = db.Query(WeekStats, keys_only=True).ancestor(settings)
			db.delete(weekData)

			# Create the new week stats object for the dashboard
			userWeek = WeekStats(key_name=key_name, parent=settings)
			userWeek.WeekBeginDate = weekBeginDate

	key_name = DayKey(fullDate)
	day = DayStats.get_by_key_name(key_name, parent=parent)
	if not day:
		day = DayStats(key_name=key_name, parent=parent)
		day.Date = shortDate
		day.DayOfMonth = fullDate.day
		day.WeekBeginDate = weekBeginDate
		day.Month = fullDate.month
		day.Year = fullDate.year

	# Only create dashboard info for the day if one for the week was
	# created.  We know that any day occurring in the current week
	# is valid for dashboard data.
	userDay = None
	if addToDashboard and userWeek:
		userDay = DayStats.get_by_key_name(key_name, parent=settings)
		if not userDay:
			# Create the new day stats object for the dashboard
			userDay = DayStats(key_name=key_name, parent=settings)
			userDay.Date = shortDate
			userDay.WeekBeginDate = weekBeginDate

	key_name = MonthKey(shortDate)
	month = MonthStats.get_by_key_name(key_name, parent=parent)
	if not month:
		month = MonthStats(key_name=key_name, parent=parent)	
		month.Month = fullDate.month
		month.Year = fullDate.year

	key_name = YearKey(shortDate)
	year = YearStats.get_by_key_name(key_name, parent=parent)
	if not year:
		year = YearStats(key_name=key_name, parent=parent)	
		year.Year = fullDate.year

	def AddAndCommitStats(stats, entry):
		stats.TotalEntries = (stats.TotalEntries or 0) + 1
		stats.TotalQuality = (stats.TotalQuality or 0) + entry.Quality
		stats.TotalDifficulty = (stats.TotalDifficulty or 0) + entry.Difficulty	
		if entry.Unit == 0: # Count
			stats.TotalCount = (stats.TotalCount or 0) + entry.Quantity
		elif entry.Unit == 1: # Minutes
			stats.TotalMinutes = (stats.TotalMinutes or 0) + entry.Quantity
		stats.DifficultyCounters = IncrementCounterList(stats.DifficultyCounters, entry.Difficulty - 1)
		stats.QualityCounters = IncrementCounterList(stats.QualityCounters, entry.Quality - 1)
		stats.put()

	# Update all stats entries
	AddAndCommitStats(day, entry)
	AddAndCommitStats(week, entry)
	AddAndCommitStats(month, entry)
	AddAndCommitStats(year, entry)
	if userDay:
		AddAndCommitStats(userDay, entry)
	if userWeek:
		AddAndCommitStats(userWeek, entry)

	# TODO: Finish this!
	return False

# Remove an entry from a user's stats
def RemoveEntryFromStats(profile, entry):
	pass