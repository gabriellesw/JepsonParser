from flask import Flask
from yaml_pyconf import FlaskConfig
import pathlib

config = FlaskConfig(
    pathlib.Path(__file__).parents[1].join("config.yaml"),
    pathlib.Path(__file__).parents[1].join(".env")
)

from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config.from_object(config)
db = SQLAlchemy(app)

from web_app import routes