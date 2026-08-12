from flask import current_app, request, session


def get_locale():
    # 1. Check if the user explicitly requested a language via URL parameter (?lang=es)
    lang = request.args.get("lang")
    if lang in current_app.config["SUPPORTED_LANGUAGES"]:
        session["lang"] = lang
        return lang

    # 2. Check if a language is already saved in the user's session
    if "lang" in session:
        return session["lang"]

    # 3. Fall back to the browser's preferred language
    return request.accept_languages.best_match(
        current_app.config["SUPPORTED_LANGUAGES"]
    )
