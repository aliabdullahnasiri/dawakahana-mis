from flask_babel import gettext as _
from wtforms import (
    DateField,
    DecimalField,
    HiddenField,
    IntegerField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from app.forms import Form


class AddMedicineStockForm(Form):
    medicine_id = IntegerField(
        _("MEDICINE_ID_LABEL"),
        validators=[DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR"))],
        render_kw={
            "data-auto-complete": "true",
            "data-fetch-api": "api.autocomplete",
            "data-model-name": "Medicine",
            "data-select-val": "id",
            "data-search-col": "name",
            "data-template": "medicines.html",
        },
    )

    batch_number = StringField(
        _("BATCH_NUMBER_LABEL"),
        validators=[
            Optional(),
            Length(
                max=100,
                message=_("THIS_FIELD_CANNOT_EXCEED_100_CHARACTERS_MSG"),
            ),
        ],
    )

    quantity = IntegerField(
        _("QUANTITY_LABEL"),
        validators=[
            DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR")),
            NumberRange(
                min=0,
                message=_("VALUE_MUST_BE_GREATER_THAN_ZERO_MSG"),
            ),
        ],
    )

    purchase_price = DecimalField(
        _("PURCHASE_PRICE_LABEL"),
        validators=[
            DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR")),
        ],
    )

    selling_price = DecimalField(
        _("SELLING_PRICE_LABEL"),
        validators=[
            DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR")),
        ],
    )

    expiry_date = DateField(
        _("EXPIRY_DATE_LABEL"),
        format="%Y-%m-%d",
        validators=[Optional()],
    )

    submit = SubmitField(_("ADD_LABEL"))


class UpdateMedicineStockForm(AddMedicineStockForm):

    id = HiddenField(
        _("ID_LABEL"),
        validators=[DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR"))],
    )

    submit = SubmitField(_("UPDATE_LABEL"))
