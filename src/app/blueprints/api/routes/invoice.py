import json
from decimal import Decimal
from typing import Dict, List, Tuple

from flask import Response
from flask_babel import gettext as g

from app.blueprints.api import bp
from app.cls import ColumnID, ColumnName
from app.extensions.db import db
from app.forms.invoice import AddInvoiceForm, UpdateInvoiceForm
from app.func import render_td
from app.models.invoice import Invoice, InvoiceType
from app.models.invoice_item import InvoiceItem
from app.models.medicine import Medicine
from app.models.medicine_stock import MedicineStock
from app.models.permission import Permission
from app.models.user import permission_required

cols: List[Tuple[ColumnID, ColumnName]] = [
    (ColumnID("id"), ColumnName(g("ID_LABEL"))),
    (ColumnID("invoice_number"), ColumnName(g("INVOICE_NUMBER_LABEL"))),
    (ColumnID("invoice_type"), ColumnName(g("INVOICE_TYPE_LABEL"))),
    (ColumnID("total_amount"), ColumnName(g("TOTAL_AMOUNT_LABEL"))),
    (ColumnID("paid_amount"), ColumnName(g("PAID_AMOUNT_LABEL"))),
    (ColumnID("remaining_amount"), ColumnName(g("REMAINING_AMOUNT_LABEL"))),
    (ColumnID("invoice_date"), ColumnName(g("DATE_LABEL"))),
]


@bp.get("/fetch/invoices")
@permission_required(Permission.get("FETCH_INVOICES"))
def fetch_invoices():

    invoices = [invoice.to_dict() for invoice in Invoice.query.all()]

    return Response(
        json.dumps(invoices),
        status=200,
        headers={"Content-Type": "application/json"},
    )


@bp.get("/fetch/rows/invoices")
@permission_required(Permission.get("FETCH_INVOICES"))
def fetch_invoice_rows():

    invoices = Invoice.query.all()

    rows = []

    for invoice in invoices:
        rows.append([render_td(col_id, invoice) for col_id, _ in cols])

    data = {
        "cols": [(col_id, g(col_name)) for col_id, col_name in cols],
        "rows": rows,
    }

    return Response(
        json.dumps(data),
        status=200,
        headers={"Content-Type": "application/json"},
    )


@bp.get("/fetch/invoice/<int:id>")
@permission_required(Permission.get("FETCH_INVOICE"))
def fetch_invoice(id):

    invoice = Invoice.query.filter_by(id=id).first()

    if invoice:

        return Response(
            json.dumps(invoice.to_dict()),
            status=200,
            headers={"Content-Type": "application/json"},
        )

    return Response(
        json.dumps(
            {
                "message": g("INVOICE_NOT_FOUND_MSG"),
                "category": "error",
            }
        ),
        status=404,
    )


@bp.get("/fetch/row/invoice/<int:id>")
@permission_required(Permission.get("FETCH_INVOICE"))
def fetch_invoice_row(id):

    invoice = Invoice.query.filter_by(id=id).first()

    if invoice:

        return Response(
            json.dumps(
                {
                    key: value
                    for key, value in zip(
                        [col_id for col_id, _ in cols],
                        [render_td(col_id, invoice) for col_id, _ in cols],
                    )
                }
            ),
            status=200,
        )

    return Response(
        json.dumps(
            {
                "message": g("INVOICE_NOT_FOUND_MSG"),
                "category": "error",
            }
        ),
        status=404,
    )


@bp.post("/add/invoice")
@permission_required(Permission.get("CREATE_INVOICE"))
def add_invoice():

    form = AddInvoiceForm()

    response: Dict = {}

    if form.validate_on_submit():
        pass

    else:

        response["errors"] = form.errors

    return Response(
        json.dumps(response),
        status=200,
    )


@bp.post("/update/invoice")
@permission_required(Permission.get("UPDATE_INVOICE"))
def update_invoice():

    form = UpdateInvoiceForm()

    response: Dict = {}

    if form.validate_on_submit():
        pass

    else:

        response["errors"] = form.errors

    return Response(
        json.dumps(response),
        status=200,
    )


@bp.delete("/delete/invoice/<int:id>")
@permission_required(Permission.get("DELETE_INVOICE"))
def delete_invoice(id):

    invoice = Invoice.query.filter_by(id=id).first()

    if invoice:

        db.session.delete(invoice)

        db.session.commit()

        return Response(
            json.dumps(
                {
                    "title": g("DELETED_SUCCESS_MSG"),
                    "message": g("INVOICE_DELETED_SUCCESSFULLY_MSG"),
                    "category": "success",
                }
            ),
            status=200,
        )

    return Response(
        json.dumps(
            {
                "message": g("INVOICE_NOT_FOUND_MSG"),
                "category": "error",
            }
        ),
        status=404,
    )
