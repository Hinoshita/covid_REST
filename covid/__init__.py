from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import requests_cache


requests_cache.install_cache('covid_api_cache', backend='sqlite', expire_after=36000)
app = Flask(__name__)
app.config["SECRET_KEY"] = "d4a7fbed321f7258a8b607748b458180"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db" # designate where the db is placed
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"


from covid import routes