from flask_babel import gettext as _
from wtforms import HiddenField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.forms import Form


class UpdatePermissionForm(Form):
    id = HiddenField(
        _("PERMISSION_ID_LABEL"),
        validators=[
            DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR")),
        ],
    )

    name = StringField(
        _("NAME_LABEL"),
        validators=[
            DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR")),
            Length(max=255, message=_("THIS_FIELD_CANNOT_EXCEED_255_CHARACTERS_MSG")),
        ],
    )

    description = TextAreaField(
        _("DESCRIPTION_LABEL"),
        validators=[
            Optional(),
            Length(max=2500, message=_("THIS_FIELD_CANNOT_EXCEED_2500_CHARACTERS_MSG")),
        ],
    )

    submit = SubmitField(_("UPDATE_PERMISSION_LABEL"))
