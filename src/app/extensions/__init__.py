from app.extensions.babel import babel
from app.extensions.bcrypt import bcrypt
from app.extensions.console import console
from app.extensions.db import db
from app.extensions.migrate import migrate

__all__ = [
    "babel",
    "bcrypt",
    "console",
    "db",
    "migrate",
]
