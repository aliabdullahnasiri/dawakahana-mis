import os
import sys

from flask import Flask

from app.config import Config
from app.extensions import babel, bcrypt, db, migrate
from app.func import get_locale


def create_app(config_class: type[Config] | None = None) -> Flask:
    app: Flask = Flask(__name__, instance_relative_config=False)

    app.config.from_object(config_class or Config())

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    babel.init_app(app, locale_selector=get_locale)

    if "db" not in sys.argv:
        with app.app_context():
            ...

    return app
