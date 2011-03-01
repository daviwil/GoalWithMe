from google.appengine.ext import db

class UserProfile(db.Model):
    UserID = db.StringProperty(required=True)
    UserName = db.StringProperty()
    EmailAddress = db.StringProperty()
    FullName = db.StringProperty()
    HomeTown = db.StringProperty()
    DateJoined = db.DateProperty(auto_now_add=True)
    Contexts = db.StringListProperty()

# Parent is a UserProfile, key_name is UserName
class DashboardSettings(db.Model):
	PinnedItems = db.ListProperty(db.Key)

class GoalDirection:
	Increasing = 0
	Decreasing = 1

	Options = {
		Increasing: "Increasing",
		Decreasing: "Decreasing"
	}
	Values = [val for val, label in Options.items()]

class TaskUnits:
	Count = 0
	Minutes = 1

	Options = {
		Count: "Count",
		Minutes: "Time (minutes)"
	}
	Values = [val for val, label in Options.items()]

	# Used for cases where you have a text entry field 
	# and want to put the units beside it
	FieldLabels = {
		Count: "times",
		Minutes: "minutes"
	}

class Goal(db.Model):
	# Parent = Owner
	Name = db.StringProperty()
	Description = db.TextProperty()
	Unit = db.IntegerProperty(choices=TaskUnits.Values)
	Direction = db.StringProperty(choices=GoalDirection.Values)
	CompletedDuration = db.IntegerProperty()
	RequiredDuration = db.IntegerProperty()
	IsActive = db.BooleanProperty()
	IsPublic = db.BooleanProperty()
	DateCreated = db.DateProperty(auto_now_add=True)

class TaskDifficulty:
	VeryEasy = 1
	Easy = 2
	Average = 3
	Hard = 4
	VeryHard = 5

	Options = {
		VeryEasy: "Very Easy",
		Easy: "Easy",
		Average: "Average",
		Hard: "Hard",
		VeryHard: "Very Hard"
	}
	Values = [val for val, label in Options.items()]

class Task(db.Model):
	# Parent = Owner
	Name = db.StringProperty()
	Description = db.TextProperty()
	Unit = db.IntegerProperty(choices=TaskUnits.Values)	
	Difficulty = db.IntegerProperty(choices=TaskDifficulty.Values)
	IsPublic = db.BooleanProperty()
	Contexts = db.StringListProperty()

	DateCreated = db.DateProperty(auto_now_add=True)
	LastUpdated = db.DateTimeProperty(auto_now=True)
	TypicalDuration = db.IntegerProperty()
	TotalDuration = db.IntegerProperty()
	WeekDuration = db.IntegerProperty()

class TaskLink(db.Model):
	# Parent = Goal, Owner is ancestor
	Task = db.ReferenceProperty(Task, required=True, collection_name="TaskLinks")

	# Count occurrences also?
	LastUpdated = db.DateTimeProperty(auto_now=True)
	TotalDuration = db.IntegerProperty()
	WeekDuration = db.IntegerProperty()

class GoalEntryType:
	Note = 0
	Task = 1
	Review = 2
	ChangeDetails = 3
	ChangeQuantity = 4

	Options = {
		Note: "Note",
		Task: "Completed Task",
		Review: "Weekly Review",
		ChangeDetails: "Goal Details Changed",
		ChangeQuantity: "Goal Quantity Changed"
	}
	Values = Values = [val for val, label in Options.items()]

class GoalEntryQuality:
	NeedsImprovement = 1
	SlowlyImproving = 2
	Maintaining = 3
	WorkingHard = 4
	Excellent = 5

	Options = {
		NeedsImprovement: "Needs Improvement",
		SlowlyImproving: "Slowly Improving",
		Maintaining: "Maintaining Good Progress",
		WorkingHard: "Working Hard",
		Excellent: "Excellent Progress"
	}
	Values = [val for val, label in Options.items()]

# Logs an entry on a goal with a possible task/duration and message attached
class GoalEntry(db.Model):
	# Parent = Goal, Owner is ancestor
	Type = db.IntegerProperty(choices=GoalEntryType.Values) # This defines the type of entry, such as "journal", "task", "review", "details" (for activate/deactivate/details change)	
	CompletedTask = db.ReferenceProperty(Task, collection_name="GoalEntries")
	CompletesGoal = db.BooleanProperty() # Set to true if this entry completes the user's goal for this week
	Notes = db.TextProperty()
	Quality = db.IntegerProperty(choices=GoalEntryQuality.Values) # This property should be a scale between Needs Improvement to Transcendent Experience
	Quantity = db.IntegerProperty()
	Difficulty = db.IntegerProperty(choices=TaskDifficulty.Values)
	Unit = db.IntegerProperty(choices=TaskUnits.Values)
	DateCreated = db.DateTimeProperty(auto_now_add=True)

# All of these stats objects will have their parent set to the
# goal or task that they are related to.
# Key format: [year] (e.g. '2011')
class YearStats(db.Model):
	Year = db.IntegerProperty()

	TotalEntries = db.IntegerProperty()
	TotalQuality = db.IntegerProperty()
	TotalDifficulty = db.IntegerProperty()
	QualityCounters = db.StringListProperty(indexed=False)	
	DifficultyCounters = db.StringListProperty(indexed=False)	
	TotalCount = db.IntegerProperty()
	TotalMinutes = db.IntegerProperty()	

# Key format: [year]-[month]  (e.g. '2011-2')
class MonthStats(db.Model):
	Month = db.IntegerProperty()
	Year = db.IntegerProperty()

	TotalEntries = db.IntegerProperty()
	TotalQuality = db.IntegerProperty()
	TotalDifficulty = db.IntegerProperty()	
	QualityCounters = db.StringListProperty(indexed=False)	
	DifficultyCounters = db.StringListProperty(indexed=False)
	TotalCount = db.IntegerProperty()
	TotalMinutes = db.IntegerProperty()	

# Key format: [year]-[month]-[mondayofweek]  (e.g. '2011-2-21')
class WeekStats(db.Model):
	WeekBeginDate = db.DateProperty()
	Month = db.IntegerProperty()	
	Year = db.IntegerProperty()

	TotalEntries = db.IntegerProperty()
	TotalQuality = db.IntegerProperty()
	TotalDifficulty = db.IntegerProperty()
	QualityCounters = db.StringListProperty(indexed=False)	
	DifficultyCounters = db.StringListProperty(indexed=False)	
	TotalCount = db.IntegerProperty()
	TotalMinutes = db.IntegerProperty()	

# Key format: [year]-[month]-[day]  (e.g. '2011-2-24')
class DayStats(db.Model):
	Date = db.DateProperty()
	DayOfMonth = db.IntegerProperty()
	WeekBeginDate = db.DateProperty()
	Month = db.IntegerProperty()	
	Year = db.IntegerProperty()

	TotalEntries = db.IntegerProperty()
	TotalQuality = db.IntegerProperty()
	TotalDifficulty = db.IntegerProperty()
	QualityCounters = db.StringListProperty(indexed=False)	
	DifficultyCounters = db.StringListProperty(indexed=False)
	TotalCount = db.IntegerProperty()
	TotalMinutes = db.IntegerProperty()
