import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key")

    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL", "sqlite:///dev.db")

    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    SQLALCHEMY_ECHO: bool = False

    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "dev-jwt-secret",
    )

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    BABEL_DEFAULT_LOCALE = "en"

    BABEL_TRANSLATION_DIRECTORIES = "../translations/"

    SUPPORTED_LANGUAGES = ["en"]

    UPLOAD_FOLDER: str = os.path.join("uploads")
