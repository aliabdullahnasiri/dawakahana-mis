from flask_babel import gettext as _
from wtforms import BooleanField, HiddenField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.forms import Form


class AddSupplierForm(Form):

    name = StringField(
        _("SUPPLIER_NAME_LABEL"),
        validators=[
            DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR")),
            Length(max=255, message=_("THIS_FIELD_CANNOT_EXCEED_255_CHARACTERS_MSG")),
        ],
    )

    company_name = StringField(_("COMPANY_NAME_LABEL"), validators=[Optional()])

    phone = StringField(_("PHONE_LABEL"), validators=[Optional()])

    email = StringField(_("EMAIL_LABEL"), validators=[Optional()])

    address = TextAreaField(_("ADDRESS_LABEL"), validators=[Optional()])

    is_active = BooleanField(_("ACTIVE_LABEL"), default=True)

    submit = SubmitField(_("ADD_LABEL"))


class UpdateSupplierForm(AddSupplierForm):

    id = HiddenField(
        _("ID_LABEL"),
        validators=[DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR"))],
    )

    submit = SubmitField(_("UPDATE_LABEL"))
