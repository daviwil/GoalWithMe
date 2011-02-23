from flask import Flask
import settings

app = Flask('goalwithme')
app.config.from_object('goalwithme.settings')

import views

