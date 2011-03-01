from flaskext import wtf
from flaskext.wtf import validators

from goalwithme.model import UserProfile, Task, TaskDifficulty, TaskUnits, GoalEntryQuality

# This method provides a widget for displaying a SelectMultipleField
# as a list of checkboxes
def SelectMultiCheckboxWidget(field, **kwargs):
    kwargs.setdefault('type', 'checkbox')
    field_id = kwargs.pop('id', field.id)
    html = u'<div data-role="fieldcontain"><fieldset data-role="controlgroup">'  # [u'<div %s>' % html_params(id=field_id, class_=ul_class)]
    html.append(u'<legend>%s</legend' % field.label)
    for value, label, checked in field.iter_choices():
        choice_id = u'%s-%s' % (field_id, value)
        options = dict(kwargs, name=field.name, value=value, id=choice_id)
        if checked:
            options['checked'] = 'checked'
        html.append(u'<input %s /> ' % html_options(**options))
    html.append(u'</fieldset></div>')
    return u''.join(html)

class CreateUserForm(wtf.Form):
    UserName = wtf.TextField('Username', validators=[validators.Required(), validators.Length(min=3, max=10)])
    EmailAddress = wtf.TextField("E-mail Address", validators=[validators.Required(), validators.Length(min=6, max=35), validators.Email()])
    FullName = wtf.TextField('Full Name', validators=[validators.Length(max=20)])
    HomeTown = wtf.TextField('City', validators=[validators.Length(max=25)])
    AcceptTos = wtf.BooleanField('I accept the Terms of Service', [validators.Required()])

class CreateTaskForm(wtf.Form):
    Name = wtf.TextField('Name', validators=[validators.Required()])
    Description = wtf.TextAreaField('Description')
    Unit = wtf.SelectField('Unit of Measure', default=0, coerce=int, choices=TaskUnits.Options.items())    
    TypicalDuration = wtf.IntegerField('Typical Duration (minutes)')
    Difficulty = wtf.SelectField('Difficulty', default=2, coerce=int, choices=TaskDifficulty.Options.items())    
    Contexts = wtf.TextField('Contexts (comma delimited)')
    IsPublic = wtf.BooleanField('Visible to other users', default=False)

class CreateGoalForm(wtf.Form):
    Name = wtf.TextField('Name', validators=[validators.Required()])
    Description = wtf.TextAreaField('Description')    
    Unit = wtf.SelectField('Unit of Measure', default=0, coerce=int, choices=TaskUnits.Options.items())
    Contexts = wtf.TextField('Contexts (comma delimited)')
    IsPublic = wtf.BooleanField('Visible to other users', default=False)    
    IsPublic = wtf.BooleanField('Visible to other users', default=False)    
    IsActive = wtf.BooleanField('Make this goal active', default=True)

class GoalTaskLinkForm(wtf.Form):
    TaskList = wtf.SelectMultipleField(
        'Select any relevant tasks:',
        coerce = int,
        option_widget=SelectMultiCheckboxWidget) # Choices defined at runtime

class CreateGoalEntryForm(wtf.Form):
    Notes = wtf.TextAreaField('Notes')
    Goal = wtf.SelectField('Goal')
    CompletedTask = wtf.SelectField('Task')
    Quantity = wtf.IntegerField('How much did you complete?', default=0)
    Quality = wtf.SelectField('How was the quality of your effort', coerce=int, choices=GoalEntryQuality.Options.items())
    Difficulty = wtf.SelectField('Difficulty of the task', coerce=int, choices=TaskDifficulty.Options.items())
