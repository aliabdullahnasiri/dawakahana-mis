from flask_babel import gettext as _


def dummy_navbar_strings():
    """
    This function is never executed. It only exists so pybabel extract
    can find dynamic database strings and add them to the .pot file.
    """

    _("Ali Abdullah Nasiri")

    _("PS_LABEL")
    _("FA_LABEL")
    _("EN_LABEL")
