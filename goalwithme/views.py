import logging
from flask import render_template, flash, session, url_for
from datetime import datetime
from goalwithme import app, forms

from functools import wraps
from google.appengine.api import users
from google.appengine.ext.db import Key
from flask import redirect, request

from goalwithme.model import UserProfile, Task, Goal, TaskLink, GoalEntry, TaskUnits
from goalwithme.stats import AddEntryToStats
from goalwithme.tools import *
from goalwithme.helpers import *

def createInitialUser(user):
    profile = UserProfile(UserID = user.user_id())
    profile.UserName = user.nickname()
    profile.EmailAddress = user.email()
    return profile

def getProfile(user):
    if user:
        if "userProfile" not in session:
            # See if user has a profile
            q = UserProfile.all()
            q.filter("UserID", user.user_id())
            session["userProfile"] = q.get()
        return session["userProfile"]
    return None

def getCurrentProfile():
    return getProfile(users.get_current_user())

def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not getCurrentProfile():
            return redirect("/")
        return func(*args, **kwargs)
    return decorated_view

@app.route('/')
def index():
    user = users.get_current_user()
    profile = getProfile(user)

    nickName = None
    signInUrl = None
    userProfile = None

    if profile:
        userProfile = profile        
    elif user:
        nickName = user.nickname()
    else:
        signInUrl = users.create_login_url("/")

    return render_template('views/start.html', signInUrl = signInUrl, nickName = nickName, userProfile = profile)

@app.route
@app.route('/createUser/', methods=['GET', 'POST'])
def user():
    # If the user isn't authenticated through Google, redirect to landing page
    user = users.get_current_user()
    if not user:
        return redirect("/")
    elif getProfile(user):
        return redirect(url_for('dashboard'))

    form = forms.CreateUserForm(UserName=user.nickname(), EmailAddress=user.email(), HomeTown=user.user_id())
    if request.method == 'POST' and form.validate():

        q = UserProfile.all()
        q.filter("UserName", form.UserName.data)
        existingProfile = q.get()
        # TODO: Make sure username doesn't exist!

        # Create the new profile for the user and save it
        newProfile = UserProfile(key_name = form.UserName.data, UserID = user.user_id())
        newProfile.UserName = form.UserName.data
        newProfile.EmailAddress = form.EmailAddress.data
        newProfile.FullName = form.FullName.data
        newProfile.HomeTown = form.HomeTown.data         
        newProfile.put()
               
        # Store the profile in the session and head to the dashboard
        session["userProfile"] = newProfile
        return redirect(url_for('dashboard'))

    return render_template('views/createUser.html', form = form)

@app.route('/logout/')
def logout():
    # Clear session state and sign out
    session.pop('userProfile', None)
    return redirect(users.create_logout_url("/"))

@app.route('/dashboard/')
@app.route('/dashboard/<action>/')
@login_required
def dashboard(action = None):
    profile = getCurrentProfile()    
    settings = GetDashboardSettings(profile, createIfNotFound=False)
    dayStats = None
    weekStats = None
    weekChartData = None
    pinnedItems = []
    if settings:
        today = datetime.now()
        thisWeek = GetFirstDayOfWeek(today)
        #recentEntries = GoalEntry.all().ancestor(profile).filter("CompletedTask =", thisTask).fetch(5)
        weekStats = WeekStats.get_by_key_name(DayKey(thisWeek), parent=settings)
        dayStats = DayStats.get_by_key_name(DayKey(today), parent=settings)
        weekChartData = GetWeekChartData(thisWeek.day, DayStats.all().ancestor(settings).filter("WeekBeginDate =", thisWeek.date()).order("DayOfMonth"))
        pinnedItems = db.get(settings.PinnedItems)

    return render_template('views/dashboard.html', 
        dayStats = dayStats, weekStats = weekStats, currentDate = datetime.now(),
        weekChartData = weekChartData, pinnedItems = pinnedItems)

def showCreateTask(request, profile):
    form = forms.CreateTaskForm()
    if request.method == 'POST' and form.validate():
        taskKey = CreateTask(
            form.Name.data, form.Description.data, form.Unit.data,
            form.Difficulty.data, form.TypicalDuration.data, 
            form.IsPublic.Data, [])
        return redirect(url_for('task', id = task.key().id()))
    return render_template(
        "views/task_edit.html", 
        typeName = "task", actionName = "Create", 
        formMethod = "POST", formUrl = "/tasks/",
        form = form)

@app.route('/tasks/', methods=['GET', 'POST'])
@app.route('/tasks/<action>/')
@app.route('/tasks/<int:id>/', methods=['GET', 'PUT', 'DELETE'])
@app.route('/tasks/<int:id>/<action>/')
@login_required
def task(id = None, action = None):
    profile = getCurrentProfile()
    if id is not None:
        # Make the action name lowercase
        action = SafeLower(action)
        thisTask = Task.get_by_id(int(id), profile)

        if action is None:
            # TODO: Make this more efficient!
            statsDict = LoadObjectStats(thisTask, datetime.now())
            statsDict["task"] = thisTask
            statsDict["recentEntries"] = GoalEntry.all().ancestor(profile).filter("CompletedTask =", thisTask).fetch(5)
            return render_template('views/task_view.html', **statsDict)                
        elif action == "delete":
            return render_template('views/delete.html', task = thisTask, typeName = "task")
        elif action == "edit":
            return render_template("views/task_edit.html", task = thisTask, typeName = "task")

    elif action is not None:
        action = action.lower()
        if action == "create":
            return showCreateTask(request, profile)

    else:
        if request.method == "GET":
            taskList = Task.all().ancestor(profile)
            if not taskList:
                taskList = []
            return render_template("views/task_list.html", tasks = taskList)
        else:
            return showCreateTask(request, profile)

#----- GOALS -----

def showCreateGoal(request, profile):
    form = forms.CreateGoalForm()
    if request.method == 'POST' and form.validate():
        # TODO: Contexts!
        goalKey = CreateGoal(
            profile, form.Name.data, form.Unit.data, 
            form.Description.data, form.IsPublic.data, [])
        return redirect(url_for('goal', id = goal.key().id()))
    return render_template(
        "views/goal_edit.html", 
        typeName = "goal", actionName = "Create", 
        formMethod = "POST", formUrl = "/goals/",
        form = form)

def linkTasksToGoal(request, goal, profile):
    # Create the form and calculate the choices
    form = forms.GoalTaskLinkForm()
    taskList = Task.all().ancestor(profile).filter('Unit =', goal.Unit)
    form.TaskList.choices = [(t.key().id(), t.Name) for t in taskList]
    taskLinks = TaskLink.all().ancestor(goal)
    selectedTasks = set([link.Task.key().id() for link in taskLinks])

    if request.method == 'POST' and form.validate():
        for value, label, selected in form.TaskList.iter_choices():
            task = Task.get_by_id(value, profile)
            if value in selectedTasks:
                if not selected:
                    # Delete the task link
                    oldLink = TaskLink.all().ancestor(goal).filter('Task =', task).get()
                    if oldLink:
                        oldLink.delete()
            else:
                if selected:
                    # Create the task link
                    newLink = TaskLink(parent = goal, Task = task)
                    newLink.put()

        return redirect(url_for('goal', id = goal.key().id()))
    else:
        form.TaskList.data = selectedTasks

    return render_template("views/goal_link.html", goal = goal, form = form)

@app.route('/goals/', methods=['GET', 'POST'])
@app.route('/goals/<action>/')
@app.route('/goals/<int:id>/', methods=['GET', 'PUT', 'DELETE'])
@app.route('/goals/<int:id>/<action>/', methods=['GET', 'POST'])
@login_required
def goal(id = None, action = None):
    profile = getCurrentProfile()
    if id is not None:
        # Make the action name lowercase
        action = SafeLower(action)
        thisGoal = Goal.get_by_id(int(id), profile)
        if action is None:
            links = TaskLink.all().ancestor(thisGoal)
            statsDict = LoadObjectStats(thisGoal, datetime.now())
            statsDict["goal"] = thisGoal
            statsDict["linkedTasks"] = [link.Task for link in links]
            statsDict["recentEntries"] = GoalEntry.all().ancestor(profile).fetch(5)
            return render_template('views/goal_view.html', **statsDict)
        elif action == "delete":
            return render_template('views/delete.html', goal = thisGoal, typeName = "goal")
        elif action == "edit":
            return render_template("views/goal_edit.html", goal = thisGoal, typeName = "goal")
        elif action == "tasks":
            return linkTasksToGoal(request, thisGoal, profile)
        elif action == "entires":
            return 
    elif action is not None:
        action = action.lower()
        if action == "create":
            return showCreateGoal(request, profile)

    else:
        if request.method == "GET":
            goalList = Goal.all().ancestor(profile)
            if not goalList:
                goalList = []
            return render_template("views/goal_list.html", goals = goalList)
        else:
            return showCreateGoal(request, profile)

def showCreateGoalEntry(request, profile):
    form = forms.CreateGoalEntryForm()
    goalId = request.args["goal"]
    goal = Goal.get_by_id(int(goalId), profile)    
    # TODO: Error if goal ID not found
        
    if request.method == 'POST': #and form.validate():    
        taskKey = Key.from_path('Task', int(form.CompletedTask.data), parent=profile.key()) # = Task.get_by_id(int(form.CompletedTask.data), profile)
        CreateGoalEntry(
            profile, goal, taskKey, datetime.now(), form.Notes.data, 
            form.Quantity.data, form.Quality.data, form.Difficulty.data)
        return redirect(url_for('goal', id = goal.key().id()))

    taskLinks = TaskLink.all().ancestor(goal)
    tasks = [(link.Task.key().id(), link.Task.Name) for link in taskLinks] 
    form.CompletedTask.choices = tasks
    return render_template(
        "views/entry_edit.html", 
        typeName = "goal", actionName = "Create", 
        formMethod = "POST", formUrl = "/entries/?goal=%s" % goalId,
        form = form, unitLabel = TaskUnits.FieldLabels[goal.Unit])

@app.route('/entries/', methods=['GET', 'POST'])
@app.route('/entries/<action>/')
@app.route('/entries/<int:id>/', methods=['GET', 'DELETE'])
def goal_entry(id = None, action = None):
    # Can create and delete entries, but not edit?
    action = SafeLower(action)
    profile = getCurrentProfile()
    if id is not None:
        if action is None:
            # Show entry details
            pass
    elif action is not None:
        if action == "create":
            # Show creation page for entry, use query params to pre-populate
            return showCreateGoalEntry(request, profile)
    else:
        if request.method == "POST":
            return showCreateGoalEntry(request, profile)
        # List all entries for user
        pass
