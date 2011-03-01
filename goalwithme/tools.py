from google.appengine.ext import db
from datetime import datetime, timedelta

from goalwithme import app
from goalwithme.model import *
from goalwithme.helpers import *
from goalwithme.stats import *

@app.template_filter('format_difficulty')
def FormatTaskDifficulty(difficulty):
	return TaskDifficulty.Options[int(difficulty)]

@app.template_filter('avgdifficulty')
def CalculateAverageDifficulty(stats):
	return TaskDifficulty.Options[int((float(stats.TotalDifficulty) / (stats.TotalEntries * 5)) * 5 )]

@app.template_filter('avgquality')
def CalculateAverageQuality(stats):
	return GoalEntryQuality.Options[int((float(stats.TotalQuality) / (stats.TotalEntries * 5)) * 5 )]

def DeleteUserData(userProfile, alsoDeleteProfile = False):
	userObjects = db.Query().ancestor(userProfile)
	if not alsoDeleteProfile:
		userObjects = filter(lambda x: type(x) != UserProfile, userObjects)

	db.delete(userObjects)

def CreateTask(profile, name, description, unit, difficulty, quantity, visibility, contexts):
    task = Task(parent = profile)
    task.Name = name
    task.Description = description
    task.Unit = unit
    task.Difficulty = difficulty
    task.TypicalDuration = quantity
    task.IsPublic = visibility
    task.Contexts = contexts
    task.put()
    return task	

def CreateGoal(profile, name, unit, description, visibility, contexts):
    goal = Goal(parent = profile)
    goal.Name = name
    goal.Unit = unit
    goal.Description = description
    goal.IsPublic = visibility
    goal.Contexts = contexts
    goal.put()
    # TODO: Create goal entry! 
    return goal

def CreateGoalEntry(profile, goal, taskKey, date, notes, quantity, quality, difficulty):
    entry = GoalEntry(parent = goal)
    entry.CompletedTask = taskKey
    entry.Notes = notes
    entry.Unit = goal.Unit
    entry.Quantity = quantity
    entry.Quality = quality
    entry.Difficulty = difficulty
    entry.DateCreated = date
    # TODO: Update CompletesGoal
    entry.put()

    # Update stats for the goal and task
    AddEntryToStats(profile, goal, entry, entry.DateCreated, addToDashboard=True)
    AddEntryToStats(profile, taskKey, entry, entry.DateCreated)
    return entry

# Generates some fake data for the given user
def GenerateFakeData(userProfile, seedDate):
	monday = GetFirstDayOfWeek(seedDate)
	tuesday = monday + timedelta(1)
	wednesday = tuesday + timedelta(1)
	thursday = wednesday + timedelta(1)
	friday = thursday + timedelta(1)

	# Create 4 goals
	goal1 = CreateGoal(userProfile, "Goal 1", 0, "Count goal", False, [])
	goal2 = CreateGoal(userProfile, "Goal 2", 1, "Time goal", False, [])
	goal3 = CreateGoal(userProfile, "Goal 3", 0, "Count goal", False, [])
	goal4 = CreateGoal(userProfile, "Goal 4", 1, "Time goal", False, [])

	# Create 4 tasks
	task1 = CreateTask(userProfile, "Task 1", "Count task", 0, 2, 0, False, [])
	task2 = CreateTask(userProfile, "Task 2", "Time task", 1, 2, 10, False, [])
	task3 = CreateTask(userProfile, "Task 3", "Count task", 0, 2, 0, False, [])
	task4 = CreateTask(userProfile, "Task 4", "Time task", 1, 2, 10, False, [])

	# TODO Set up task links

	# Create some entries across a few days
	CreateGoalEntry(userProfile, goal1, task1.key(), monday, "Test", 1, 1, 4)
	CreateGoalEntry(userProfile, goal3, task1.key(), tuesday, "Test", 1, 3, 2)
	CreateGoalEntry(userProfile, goal1, task3.key(), monday, "Test", 2, 4, 5)
	CreateGoalEntry(userProfile, goal3, task3.key(), thursday, "Test", 3, 4, 2)

	CreateGoalEntry(userProfile, goal2, task2.key(), tuesday, "Test", 10, 4, 3)
	CreateGoalEntry(userProfile, goal4, task2.key(), friday, "Test", 30, 1, 1)
	CreateGoalEntry(userProfile, goal2, task4.key(), monday, "Test", 20, 5, 2)
	CreateGoalEntry(userProfile, goal4, task4.key(), wednesday, "Test", 40, 4, 5)

	print "Done."

def LoadObjectStats(obj, fullDate):
	thisWeek = GetFirstDayOfWeek(fullDate)
	return {
		"dayStats": DayStats.get_by_key_name(DayKey(fullDate), parent=obj),
		"weekChartData": GetWeekChartData(thisWeek.day, DayStats.all().ancestor(obj).filter("WeekBeginDate =", thisWeek.date()).order("DayOfMonth")),
		"weekStats": WeekStats.get_by_key_name(DayKey(thisWeek), parent=obj),
		"monthStats": MonthStats.get_by_key_name(MonthKey(fullDate), parent=obj),
		"monthChartData": GetMonthChartData(fullDate.year, fullDate.month, DayStats.all().ancestor(obj).filter("Month =", thisWeek.month).order("DayOfMonth")),
		"yearStats": YearStats.get_by_key_name(YearKey(fullDate), parent=obj),
		"yearChartData": GetYearChartData(MonthStats.all().ancestor(obj).filter("Year =", thisWeek.year).order("Month"))		
	}


