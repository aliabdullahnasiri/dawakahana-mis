from flask_babel import gettext as _
from wtforms import BooleanField, HiddenField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.forms import Form, MustBeUnique
from app.models.medicine import Medicine


class AddMedicineForm(Form):
    barcode = StringField(
        _("BARCODE_LABEL"),
        validators=[
            Optional(),
            Length(max=100, message=_("THIS_FIELD_CANNOT_EXCEED_100_CHARACTERS_MSG")),
            MustBeUnique(
                Medicine,
                "barcode",
                _("BARCODE_ALREADY_EXISTS_MSG"),
            ),
        ],
    )

    name = StringField(
        _("MEDICINE_NAME_LABEL"),
        validators=[
            DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR")),
            Length(max=255, message=_("THIS_FIELD_CANNOT_EXCEED_255_CHARACTERS_MSG")),
        ],
    )

    generic_name = StringField(
        _("GENERIC_NAME_LABEL"),
        validators=[
            Optional(),
            Length(max=255, message=_("THIS_FIELD_CANNOT_EXCEED_255_CHARACTERS_MSG")),
        ],
    )

    manufacturer = StringField(
        _("MANUFACTURER_LABEL"),
        validators=[
            Optional(),
            Length(max=255, message=_("THIS_FIELD_CANNOT_EXCEED_255_CHARACTERS_MSG")),
        ],
    )

    strength = StringField(
        _("STRENGTH_LABEL"),
        validators=[
            Optional(),
            Length(max=100, message=_("THIS_FIELD_CANNOT_EXCEED_100_CHARACTERS_MSG")),
        ],
    )

    description = TextAreaField(
        _("DESCRIPTION_LABEL"),
        validators=[Optional()],
    )

    is_active = BooleanField(
        _("ACTIVE_LABEL"),
        default=True,
    )

    submit = SubmitField(_("ADD_LABEL"))


class UpdateMedicineForm(AddMedicineForm):
    id = HiddenField(
        _("ID_LABEL"),
        validators=[DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR"))],
    )

    barcode = StringField(
        _("BARCODE_LABEL"),
        validators=[
            Optional(),
            Length(max=100, message=_("THIS_FIELD_CANNOT_EXCEED_100_CHARACTERS_MSG")),
        ],
    )

    submit = SubmitField(_("UPDATE_LABEL"))
