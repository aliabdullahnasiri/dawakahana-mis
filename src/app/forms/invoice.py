from flask_babel import gettext as _
from wtforms import (
    DecimalField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from app.forms import Form
from app.models.invoice import InvoiceType


class AddInvoiceForm(Form):

    invoice_type = SelectField(
        _("INVOICE_TYPE_LABEL"),
        validators=[DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR"))],
        choices=[
            (InvoiceType.PURCHASE.value, _("PURCHASE_LABEL")),
            (InvoiceType.SALE.value, _("SALE_LABEL")),
            (InvoiceType.PURCHASE_RETURN.value, _("PURCHASE_RETURN_LABEL")),
            (InvoiceType.SALE_RETURN.value, _("SALE_RETURN_LABEL")),
        ],
        render_kw={"data-group-switcher": "true"},
    )

    supplier_id = IntegerField(
        _("SUPPLIER_LABEL"),
        validators=[
            Optional(),
        ],
        render_kw={
            "data-auto-complete": "true",
            "data-fetch-api": "api.autocomplete",
            "data-model-name": "Supplier",
            "data-select-val": "id",
            "data-search-col": "name",
            "data-template": "suppliers.html",
            "data-group-id": InvoiceType.PURCHASE.value,
        },
    )

    customer_id = IntegerField(
        _("CUSTOMER_LABEL"),
        validators=[
            Optional(),
        ],
        render_kw={
            "data-auto-complete": "true",
            "data-fetch-api": "api.autocomplete",
            "data-model-name": "Customer",
            "data-select-val": "id",
            "data-search-col": "name",
            "data-template": "customers.html",
            "data-group-id": InvoiceType.SALE.value,
        },
    )

    items = HiddenField(
        _("INVOICE_ITEMS_LABEL"),
        validators=[DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR"))],
    )

    paid_amount = DecimalField(
        _("PAID_AMOUNT_LABEL"),
        validators=[Optional()],
    )

    payment_method = SelectField(
        _("PAYMENT_METHOD_LABEL"),
        choices=[
            ("CASH", _("CASH_LABEL")),
        ],
        default="CASH",
    )

    note = StringField(
        _("NOTE_LABEL"),
        validators=[
            Optional(),
            Length(max=255),
        ],
    )

    submit = SubmitField(_("ADD_LABEL"))


class AddInvoiceItemForm(Form):
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

    unit_price = IntegerField(
        _("UNIT_PRICE_LABEL"),
        validators=[
            DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR")),
            NumberRange(
                min=0,
                message=_("VALUE_MUST_BE_GREATER_THAN_ZERO_MSG"),
            ),
        ],
    )

    submit = SubmitField(_("ADD_INVOICE_ITEM_LABEL"))


class UpdateInvoiceForm(AddInvoiceForm):

    id = HiddenField(
        _("INVOICE_ID_LABEL"),
        validators=[DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR"))],
    )

    submit = SubmitField(_("UPDATE_LABEL"))
