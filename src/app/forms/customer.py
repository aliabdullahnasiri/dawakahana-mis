from flask_babel import gettext as _
from wtforms import BooleanField, HiddenField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional

from app.forms import Form, MustBeUnique
from app.models.customer import Customer


class AddCustomerForm(Form):

    name = StringField(
        _("CUSTOMER_NAME_LABEL"),
        validators=[
            DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR")),
            Length(max=255),
            MustBeUnique(Customer, "name"),
        ],
    )

    phone = StringField(
        _("PHONE_NUMBER_LABEL"),
        validators=[
            Optional(),
            Length(max=50),
        ],
    )

    email = StringField(
        _("EMAIL_LABEL"),
        validators=[
            Optional(),
            Email(message=_("INVALID_EMAIL_ERROR")),
            Length(max=255),
        ],
    )

    address = StringField(
        _("ADDRESS_LABEL"),
        validators=[
            Optional(),
        ],
    )

    is_active = BooleanField(
        _("ACTIVE_LABEL"),
        default=True,
    )

    submit = SubmitField(_("ADD_CUSTOMER_LABEL"))


class UpdateCustomerForm(AddCustomerForm):

    id = HiddenField(
        _("CUSTOMER_UID_LABEL"),
        validators=[
            DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR")),
        ],
    )

    submit = SubmitField(_("UPDATE_CUSTOMER_LABEL"))
