from flask_babel import gettext as _
from wtforms import (
    DecimalField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, Length, Optional

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

    invoice_number = StringField(
        _("INVOICE_NUMBER_LABEL"),
        validators=[
            DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR")),
            Length(max=100, message=_("THIS_FIELD_CANNOT_EXCEED_100_CHARACTERS_MSG")),
        ],
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


class UpdateInvoiceForm(AddInvoiceForm):

    id = HiddenField(
        _("INVOICE_ID_LABEL"),
        validators=[DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR"))],
    )

    submit = SubmitField(_("UPDATE_LABEL"))
