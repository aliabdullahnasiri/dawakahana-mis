import json
from datetime import date
from decimal import Decimal
from typing import Dict, List, Tuple

from flask import Response, render_template
from flask_babel import gettext as g
from flask_login import current_user

from app.blueprints.api import bp
from app.cls import ColumnID, ColumnName
from app.extensions.console import console
from app.extensions.db import db
from app.forms.invoice import AddInvoiceForm, AddInvoiceItemForm, UpdateInvoiceForm
from app.func import render_td
from app.models.invoice import Invoice, InvoiceType
from app.models.invoice_item import InvoiceItem
from app.models.medicine import Medicine
from app.models.medicine_stock import MedicineStock
from app.models.permission import Permission
from app.models.transaction import Transaction, TransactionType
from app.models.user import permission_required

cols: List[Tuple[ColumnID, ColumnName]] = [
    (ColumnID("id"), ColumnName(g("ID_LABEL"))),
    (ColumnID("invoice_number"), ColumnName(g("INVOICE_NUMBER_LABEL"))),
    (ColumnID("display_invoice_type"), ColumnName(g("INVOICE_TYPE_LABEL"))),
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
        try:
            items = json.loads(form.items.data or "{}")
            supplier_id = form.supplier_id.data
            customer_id = form.customer_id.data

            invoice_type = InvoiceType(form.invoice_type.data)
            invoice_num = Invoice.generate_invoice_number(invoice_type)

            invoice = Invoice()

            invoice.invoice_number = invoice_num
            invoice.invoice_type = invoice_type
            invoice.invoice_date = date.today()
            invoice.created_by = current_user.id

            db.session.add(invoice)
            db.session.flush()

            total_amount = Decimal("0")

            for item in items:
                medicine_id = item.get("medicine_id")
                quantity = int(item.get("quantity", 0))
                unit_price = Decimal(str(item.get("unit_price", 0)))

                medicine = Medicine.query.filter_by(id=medicine_id).first()

                if not medicine:
                    break

                item_total = Decimal(quantity) * unit_price

                total_amount += item_total

                match invoice_type:
                    case InvoiceType.PURCHASE:
                        batch_number = item.get("batch_number")
                        expiry_date = item.get("expiry_date")

                        stock = MedicineStock()

                        stock.medicine_id = getattr(medicine, "id")
                        stock.batch_number = batch_number
                        stock.quantity = quantity
                        stock.purchase_price = unit_price
                        stock.expiry_date = expiry_date

                        db.session.add(stock)
                        db.session.flush()

                        invoice_item = InvoiceItem()

                        invoice_item.invoice_id = invoice.id
                        invoice_item.medicine_id = medicine.id
                        invoice_item.quantity = quantity
                        invoice_item.unit_price = unit_price
                        invoice_item.total_price = item_total
                        invoice_item.batch_number = batch_number

                        db.session.add(invoice_item)

                        # !!! ADD STOCK MOVEMENT

                    case InvoiceType.SALE:
                        stock = (
                            MedicineStock.query.filter(
                                MedicineStock.medicine_id == medicine.id,
                                MedicineStock.quantity >= quantity,
                            )
                            .order_by(MedicineStock.expiry_date.asc())
                            .first()
                        )

                        if stock:
                            stock.quantity -= quantity

                            invoice_item = InvoiceItem()

                            invoice_item.invoice_id = invoice.id
                            invoice_item.medicine_id = medicine.id
                            invoice_item.quantity = quantity
                            invoice_item.unit_price = unit_price
                            invoice_item.total_price = item_total
                            invoice_item.batch_number = stock.batch_number

                            db.session.add(invoice_item)

                            # !!! ADD STOCK MOVEMENT

                    case InvoiceType.PURCHASE_RETURN:
                        stock = MedicineStock.query.filter(
                            MedicineStock.medicine_id == medicine.id,
                            MedicineStock.quantity >= quantity,
                            MedicineStock.batch_number == item.get("batch_number"),
                        ).first()

                        if stock:
                            stock.quantity -= quantity

                            invoice_item = InvoiceItem()

                            stock.invoice_id = invoice.id
                            stock.medicine_id = medicine.id
                            stock.quantity = quantity
                            stock.unit_price = unit_price
                            stock.total_price = item_total
                            stock.batch_number = stock.batch_number

                            db.session.add(invoice_item)

                            # !!! ADD STOCK MOVEMENT
                    case InvoiceType.SALE_RETURN:
                        batch_number = item.get("batch_number")

                        stock = MedicineStock.query.filter(
                            MedicineStock.medicine_id == medicine.id,
                            MedicineStock.batch_number == batch_number,
                        ).first()

                        if stock:
                            stock.quantity += quantity
                        else:
                            stock = MedicineStock()

                            stock.medicine_id = medicine.id
                            stock.batch_number = batch_number
                            stock.quantity = quantity
                            stock.purchase_price = unit_price

                            db.session.add(stock)
                            db.session.flush()

                            invoice_item = InvoiceItem()

                            invoice_item.invoice_id = invoice.id
                            invoice_item.medicine_id = medicine.id
                            invoice_item.quantity = quantity
                            invoice_item.unit_price = unit_price
                            invoice_item.total_price = item_total
                            invoice_item.batch_number = batch_number

                            db.session.add(invoice_item)

                            # !!! ADD STOCK MOVEMENT

            paid_amount = Decimal(str(form.paid_amount.data or 0))

            match invoice_type:
                case InvoiceType.PURCHASE:
                    transaction = Transaction()

                    transaction.supplier_id = supplier_id
                    transaction.invoice_id = invoice.id
                    transaction.transaction_type = TransactionType.PURCHASE
                    transaction.created_by = current_user.id
                    transaction.amount = total_amount

                    db.session.add(transaction)

                case InvoiceType.SALE:
                    transaction = Transaction()

                    transaction.customer_id = customer_id
                    transaction.invoice_id = invoice.id
                    transaction.transaction_type = TransactionType.SALE
                    transaction.created_by = current_user.id
                    transaction.amount = total_amount

                    db.session.add(transaction)

                case InvoiceType.PURCHASE_RETURN:
                    transaction = Transaction()

                    transaction.supplier_id = supplier_id
                    transaction.invoice_id = invoice.id
                    transaction.transaction_type = TransactionType.PURCHASE_RETURN
                    transaction.amount = total_amount
                    transaction.created_by = current_user.id

                    db.session.add(transaction)
                case InvoiceType.SALE_RETURN:
                    transaction = Transaction()

                    transaction.customer_id = customer_id
                    transaction.invoice_id = invoice.id
                    transaction.transaction_type = TransactionType.SALE_RETURN
                    transaction.amount = total_amount
                    transaction.created_by = current_user.id

                    db.session.add(transaction)

            if paid_amount > 0:
                if invoice_type in (InvoiceType.SALE, InvoiceType.SALE_RETURN):
                    transaction = Transaction()

                    transaction.customer_id = customer_id
                    transaction.invoice_id = invoice.id
                    transaction.transaction_type = TransactionType.PAYMENT
                    transaction.amount = paid_amount
                    transaction.created_by = current_user.id

                    db.session.add(transaction)

                elif invoice_type in (
                    InvoiceType.PURCHASE,
                    InvoiceType.PURCHASE_RETURN,
                ):
                    transaction = Transaction()

                    transaction.supplier_id = supplier_id
                    transaction.invoice_id = invoice.id
                    transaction.transaction_type = TransactionType.PAYMENT
                    transaction.amount = paid_amount
                    transaction.created_by = current_user.id

                    db.session.add(transaction)

            db.session.commit()

            response["title"] = g("INVOICE_ADDED_LABEL")

            response["message"] = g("INVOICE_ADDED_SUCCESSFULLY_SUCCESS_MSG")

            response["category"] = "success"

            response["id"] = invoice.id

        except (ValueError, KeyError, TypeError) as e:
            print(e)

            db.session.rollback()

            response["title"] = g("ERROR_ERROR")
            response["message"] = str(e)
            response["category"] = "error"

        except Exception as err:
            print(err)

            db.session.rollback()

            response["title"] = g("ERROR_ERROR")
            response["message"] = g("INVOICE_COULD_NOT_BE_CREATED_MSG")
            response["category"] = "error"

    else:

        response["errors"] = form.errors

    return Response(
        json.dumps(response),
        status=200,
    )


@bp.post("/add/invoice-item")
@permission_required(Permission.get("CREATE_INVOICE_ITEM"))
def add_invoice_item():

    response: Dict = {}

    form = AddInvoiceItemForm()
    print(form.data)

    if form.validate_on_submit():

        medicine_id = form.medicine_id.data
        quantity = form.quantity.data
        unit_price = form.unit_price.data

        if isinstance(quantity, int) and isinstance(unit_price, int):
            if medicine := Medicine.query.get(medicine_id):
                # Get stock with nearest expiry first
                stock = (
                    MedicineStock.query.filter(
                        MedicineStock.medicine_id == medicine_id,
                        MedicineStock.quantity > quantity,
                    )
                    .order_by(MedicineStock.expiry_date.asc())
                    .first()
                )

                dct = {}

                if stock:
                    dct["batch_number"] = stock.batch_number

                response["data"] = {
                    "medicine": render_template(
                        "admin/components/tables/td/medicine.html",
                        medicine=medicine,
                    ),
                    "medicine_id": medicine.id,
                    "quantity": quantity,
                    "unit_price": float(unit_price),
                    "total_price": float(quantity * unit_price),
                    **dct,
                }

                response["category"] = "success"

    else:
        response["errors"] = form.errors
        print(form.errors)

    return Response(
        json.dumps(response),
        status=200,
        headers={"Content-Type": "application/json"},
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
