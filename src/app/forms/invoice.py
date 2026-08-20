import json
from json import JSONDecodeError

from flask_babel import gettext as _
from sqlalchemy import func
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    ValidationError,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from app.extensions.db import db
from app.forms import Form, ValidateID
from app.models.invoice import InvoiceType
from app.models.medicine import Medicine
from app.models.medicine_stock import MedicineStock


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
            "data-second-group-id": InvoiceType.PURCHASE_RETURN.value,
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
            "data-second-group-id": InvoiceType.SALE_RETURN.value,
        },
    )

    items = HiddenField(
        _("INVOICE_ITEMS_LABEL"),
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

    is_draft = BooleanField(
        _("SAVE_AS_DRAFT_LABEL"),
        default=False,
    )

    submit = SubmitField(_("ADD_LABEL"))

    def validate_items(self, field):

        try:
            data = json.loads(field.data or "[]")

        except JSONDecodeError:
            raise ValidationError(_("INVALID_INVOICE_ITEMS_MSG"))

        if not isinstance(data, list):
            raise ValidationError(_("INVALID_INVOICE_ITEMS_MSG"))

        if not data:
            raise ValidationError(_("INVOICE_MUST_HAVE_AT_LEAST_ONE_ITEM_MSG"))


class AddInvoiceItemForm(Form):
    invoice_type = HiddenField(
        _("INVOICE_TYPE_LABEL"),
        default=InvoiceType.PURCHASE.value,
        validators=[DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR"))],
        render_kw={"data-group-switcher": "true"},
    )

    return_batch_number = StringField(
        _("BATCH_NUMBER_LABEL"),
        validators=[
            Length(
                max=100,
                message=_("THIS_FIELD_CANNOT_EXCEED_100_CHARACTERS_MSG"),
            ),
        ],
        default=None,
        render_kw={
            "data-auto-complete": "true",
            "data-fetch-api": "api.autocomplete",
            "data-model-name": "MedicineStock",
            "data-select-val": "batch-number",
            "data-search-col": "batch_number",
            "data-template": "medicine_stocks.html",
            "data-group-id": InvoiceType.SALE_RETURN.value,
            "data-second-group-id": InvoiceType.PURCHASE_RETURN.value,
            "data-based-on": "medicine_id",
        },
    )

    purchase_batch_number = StringField(
        _("BATCH_NUMBER_LABEL"),
        validators=[
            Optional(),
            Length(
                max=100,
                message=_("THIS_FIELD_CANNOT_EXCEED_100_CHARACTERS_MSG"),
            ),
        ],
        render_kw={
            "data-group-id": InvoiceType.PURCHASE.value,
        },
    )

    medicine_id = IntegerField(
        _("MEDICINE_ID_LABEL"),
        validators=[
            DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR")),
            ValidateID(Medicine),
        ],
        render_kw={
            "data-auto-complete": "true",
            "data-fetch-api": "api.autocomplete",
            "data-model-name": "Medicine",
            "data-select-val": "id",
            "data-search-col": "name",
            "data-template": "medicines.html",
            "data-get": "/api/fetch/medicine/-1",
            "data-fill-inputs": "unit_price",
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

    selling_price = DecimalField(
        _("SELLING_PRICE_LABEL"),
        validators=[Optional()],
        render_kw={
            "data-group-id": InvoiceType.PURCHASE.value,
        },
    )

    expiry_date = DateField(
        _("EXPIRY_DATE_LABEL"),
        format="%Y-%m-%d",
        validators=[Optional()],
        render_kw={
            "data-group-id": InvoiceType.PURCHASE.value,
        },
    )

    submit = SubmitField(_("ADD_INVOICE_ITEM_LABEL"))

    def validate_return_batch_number(self, field):
        if self.invoice_type.data != InvoiceType.SALE_RETURN.value:
            return

        if not self.return_batch_number.data:
            raise ValidationError(_("THIS_FIELD_IS_REQUIRED_ERROR"))

        medicine_id = self.medicine_id.data

        if not medicine_id:
            return

        stock = MedicineStock.query.filter_by(
            medicine_id=medicine_id,
            batch_number=field.data,
        ).first()

        if not stock:
            raise ValidationError(_("BATCH_NUMBER_NOT_FOUND_MSG"))

    def validate_purchase_batch_number(self, field):
        if self.invoice_type.data != InvoiceType.SALE_RETURN.value:
            return

        if not self.purchase_batch_number.data:
            raise ValidationError(_("THIS_FIELD_IS_REQUIRED_ERROR"))

        medicine_id = self.medicine_id.data

        if not medicine_id:
            return

        stock = MedicineStock.query.filter_by(
            medicine_id=medicine_id,
            batch_number=field.data,
        ).first()

        if not stock:
            raise ValidationError(_("BATCH_NUMBER_NOT_FOUND_MSG"))

    def validate_invoice_type(self, field):
        try:
            InvoiceType(field.data)
        except ValueError:
            raise ValidationError(_("INVALID_INVOICE_TYPE_MSG"))

    def validate_quantity(self, field):

        if self.invoice_type.data != InvoiceType.SALE.value:
            return

        medicine_id = self.medicine_id.data
        quantity = field.data

        if not medicine_id or not quantity:
            return

        available_quantity = (
            db.session.query(
                func.coalesce(
                    func.sum(MedicineStock.quantity),
                    0,
                )
            )
            .filter(
                MedicineStock.medicine_id == medicine_id,
                MedicineStock.quantity > 0,
                MedicineStock.batch_number.isnot(None),
            )
            .scalar()
        )

        if available_quantity < quantity:
            raise ValidationError(_("NOT_ENOUGH_STOCK_AVAILABLE_MSG"))


class UpdateInvoiceForm(AddInvoiceForm):

    id = HiddenField(
        _("INVOICE_ID_LABEL"),
        validators=[DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR"))],
    )

    submit = SubmitField(_("UPDATE_LABEL"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.invoice_type.validators = [Optional()]
