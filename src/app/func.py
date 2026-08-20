import pathlib
import re
from datetime import date

import jdatetime
from flask import render_template, request, session
from jinja2 import TemplateNotFound

from app.const import LANGUAGES


def get_file(id: int):
    from app.models.file import File

    return File.query.filter_by(id=id).first()


def get_file_url(id: int):
    from app.models.file import File

    file = File.query.filter_by(id=id).first()

    if file:
        return file.file_url


def render_td(name: str, obj) -> str:
    dct = {obj.__class__.__name__.lower(): obj}

    value = None

    try:
        return render_template(
            f"admin/components/tables/td/{name}.html",
            **dct
            | ({name: (value := getattr(obj, name))} if hasattr(obj, name) else {}),
        )
    except TemplateNotFound as _:
        pass

    if value is not None:
        return value

    return "N/A"


def __import_all__(path: str) -> None:
    ext = ".py"
    for module in pathlib.Path("src/" + path).glob(f"*{ext}"):
        __import__(
            re.sub(
                re.compile(rf"{ext}$"),
                "",
                f"{path.replace(chr(47), chr(46))}{chr(46)}{module.name}",
            )
        )


def get_locale():
    # 1. Check if the user explicitly requested a language via URL parameter (?lang=es)
    lang = request.args.get("lang")
    if lang in LANGUAGES:
        session["lang"] = lang
        return lang

    # 2. Check if a language is already saved in the user's session
    if "lang" in session:
        return session["lang"]

    # 3. Fall back to the browser's preferred language
    return request.accept_languages.best_match(LANGUAGES)


def convert_to_gregorian(value: date):
    if isinstance(value, date):
        year = value.year

        # Jalali year range (practical check)
        if 1200 <= year <= 1500:
            return jdatetime.date.fromisoformat(
                date.strftime(value, "%Y-%m-%d")
            ).togregorian()

        return value
