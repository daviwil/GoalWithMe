import logging
from flask import render_template, flash, session, url_for
from goalwithme import app, forms

from functools import wraps
from google.appengine.api import users
from flask import redirect, request

from goalwithme.model import UserProfile, Task, Goal, TaskLink, GoalEntry

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
        newProfile = UserProfile(UserID = user.user_id())
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
@login_required
def dashboard():
    return render_template('views/dashboard.html')

def safeLower(str):
    if str is not None:
        return str.lower()
    return str

def createTask(request, profile):
    form = forms.CreateTaskForm()
    if request.method == 'POST' and form.validate():
        task = Task(parent = profile)
        task.Name = form.Name.data
        task.Description = form.Description.data
        task.Unit = form.Unit.data
        task.Difficulty = int(form.Difficulty.data)
        task.TypicalDuration = form.TypicalDuration.data
        task.IsPublic = form.IsPublic.data
        task.Contexts = []
        task.put()
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
        action = safeLower(action)
        thisTask = Task.get_by_id(int(id), profile)        
        if action is None:
            return render_template('views/task_view.html', task = thisTask)
        elif action == "delete":
            return render_template('views/delete.html', task = thisTask, typeName = "task")
        elif action == "edit":
            return render_template("views/task_edit.html", task = thisTask, typeName = "task")

    elif action is not None:
        action = action.lower()
        if action == "create":
            return createTask(request, profile)

    else:
        if request.method == "GET":
            taskList = Task.all().ancestor(profile)
            if not taskList:
                taskList = []
            return render_template("views/task_list.html", tasks = taskList)
        else:
            return createTask(request, profile)

#----- GOALS -----

def createGoal(request, profile):
    form = forms.CreateGoalForm()
    if request.method == 'POST' and form.validate():
        goal = Goal(parent = profile)
        goal.Name = form.Name.data
        goal.Unit = form.Unit.data
        goal.Description = form.Description.data
        goal.IsPublic = form.IsPublic.data
        goal.Contexts = []
        goal.put()
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
        action = safeLower(action)
        thisGoal = Goal.get_by_id(int(id), profile)
        if action is None:
            links = TaskLink.all().ancestor(thisGoal)
            linkedTasks = [link.Task for link in links]
            return render_template('views/goal_view.html', goal = thisGoal, linkedTasks = linkedTasks)
        elif action == "delete":
            return render_template('views/delete.html', goal = thisGoal, typeName = "goal")
        elif action == "edit":
            return render_template("views/goal_edit.html", goal = thisGoal, typeName = "goal")
        elif action == "tasks":
            return linkTasksToGoal(request, thisGoal, profile)
    elif action is not None:
        action = action.lower()
        if action == "create":
            return createGoal(request, profile)

    else:
        if request.method == "GET":
            goalList = Goal.all().ancestor(profile)
            if not goalList:
                goalList = []
            return render_template("views/goal_list.html", goals = goalList)
        else:
            return createGoal(request, profile)            
