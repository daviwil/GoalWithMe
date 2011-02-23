from google.appengine.ext import db

class UserProfile(db.Model):
    UserID = db.StringProperty(required=True)
    UserName = db.StringProperty()
    EmailAddress = db.StringProperty()
    FullName = db.StringProperty()
    HomeTown = db.StringProperty()
    DateJoined = db.DateProperty(auto_now_add=True)
    Contexts = db.StringListProperty()

class GoalDirection:
	Increasing = 0
	Decreasing = 1

	Values = [ Increasing, Decreasing ]
	Labels = [ "Increasing", "Decreasing" ]
	Options = zip([str(v) for v in Values], Labels)

class TaskUnits:
	Count = "count"
	Minutes = "mins"

	Values = [ Count, Minutes]
	Labels = [ "Count", "Time (minutes)" ]
	Options = zip(Values, Labels)

class Goal(db.Model):
	# Parent = Owner
	Name = db.StringProperty()
	#Owner = db.ReferenceProperty(UserProfile, required=True)
	Description = db.TextProperty()
	Unit = db.StringProperty(choices=TaskUnits.Values)
	Direction = db.StringProperty(choices=GoalDirection.Values)
	CompletedDuration = db.IntegerProperty()
	RequiredDuration = db.IntegerProperty()
	IsActive = db.BooleanProperty()
	IsPublic = db.BooleanProperty()

class TaskDifficulty:
	VeryEasy = 0
	Easy = 1
	Average = 2
	Hard = 3
	VeryHard = 4

	Values = [ VeryEasy, Easy, Average, Hard, VeryHard ]
	StringValues = ["0", "1", "2", "3", "4"] #map(lambda v: str(v), Values)
	Labels = [ "Very Easy", "Easy", "Average", "Hard", "Very Hard"]
	Options = zip([str(v) for v in Values], Labels)

class Task(db.Model):
	# Parent = Owner
	Name = db.StringProperty()
	#Owner = db.ReferenceProperty(UserProfile, required=True)
	Description = db.TextProperty()
	Unit = db.StringProperty(choices=TaskUnits.Values)	
	Difficulty = db.IntegerProperty(choices=TaskDifficulty.Values)
	IsPublic = db.BooleanProperty()
	Contexts = db.StringListProperty()

	LastUpdated = db.DateTimeProperty(auto_now=True)
	TypicalDuration = db.IntegerProperty()
	TotalDuration = db.IntegerProperty()
	WeekDuration = db.IntegerProperty()

	IsPinned = db.BooleanProperty()
	PinOrder = db.IntegerProperty()

class TaskLink(db.Model):
	# Parent = Goal, Owner is ancestor
	#Owner = db.ReferenceProperty(UserProfile, required=True)
	#Goal = db.ReferenceProperty(Goal, required=True, collection_name="TaskLinks")	
	Task = db.ReferenceProperty(Task, required=True, collection_name="TaskLinks")

	# Count occurrences also?
	LastUpdated = db.DateTimeProperty(auto_now=True)
	TotalDuration = db.IntegerProperty()
	WeekDuration = db.IntegerProperty()

# Logs an entry on a goal with a possible task/duration and message attached
class GoalEntry(db.Model):
	# Parent = Goal, Owner is ancestor
	#Owner = db.ReferenceProperty(UserProfile, required=True)
	#Goal = db.ReferenceProperty(Goal, required=True, collection_name="GoalEntries")	
	Task = db.ReferenceProperty(Task, collection_name="GoalEntries")
	Message = db.TextProperty()
	Type = db.StringProperty() # This defines the type of entry, such as "journal", "task", "review", "details" (for activate/deactivate/details change)
	Quality = db.StringProperty() # This property should be a scale between Needs Improvement to Transcendent Experience
	Duration = db.IntegerProperty()
	DateCreated = db.DateTimeProperty(auto_now_add=True)
	LastModified = db.DateTimeProperty(auto_now=True)

# Potential design of duration manipulation functions
def getTotal(durationArray, index, newValue = None):
	if newValue:
		# Total, Month, Week, Day
		durationArray[index] = newValue
	return durationArray[index]

def monthTotal(durationArray, newValue = None):
	return getTotal(durationArray, 1, newValue)

def monthTotal(durationArray, newValue = None):
	return getTotal(durationArray, 2, newValue)

def dayTotal(durationArray, newValue = None):
	return getTotal(durationArray, 3, newValue)
