import json
from datetime import date
from decimal import Decimal
from typing import Dict, List, Tuple

from flask import Response, render_template
from flask_babel import gettext as g
from flask_login import current_user

from app.blueprints.api import bp
from app.cls import ColumnID, ColumnName
from app.extensions.db import db
from app.forms.invoice import AddInvoiceForm, AddInvoiceItemForm, UpdateInvoiceForm
from app.func import render_td
from app.models.invoice import Invoice, InvoiceStatus, InvoiceType
from app.models.invoice_item import InvoiceItem
from app.models.medicine import Medicine
from app.models.medicine_stock import MedicineStock
from app.models.permission import Permission
from app.models.transaction import Transaction, TransactionType
from app.models.user import permission_required

cols: List[Tuple[ColumnID, ColumnName]] = [
    (ColumnID("id"), ColumnName(g("ID_LABEL"))),
    (ColumnID("invoice_number"), ColumnName(g("INVOICE_NUMBER_LABEL"))),
    (ColumnID("invoice_type"), ColumnName(g("INVOICE_TYPE_LABEL"))),
    (ColumnID("display_total_amount"), ColumnName(g("TOTAL_AMOUNT_LABEL"))),
    (ColumnID("display_settled_amount"), ColumnName(g("SETTLED_AMOUNT_LABEL"))),
    (ColumnID("display_remaining_amount"), ColumnName(g("REMAINING_AMOUNT_LABEL"))),
    (ColumnID("display_invoice_date"), ColumnName(g("DATE_LABEL"))),
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
            invoice.status = (
                InvoiceStatus.DRAFT if form.is_draft.data else InvoiceStatus.COMPLETED
            )

            if invoice_type in (InvoiceType.PURCHASE, InvoiceType.PURCHASE_RETURN):
                invoice.supplier_id = supplier_id
            elif invoice_type in (InvoiceType.SALE, InvoiceType.SALE_RETURN):
                invoice.customer_id = customer_id

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

                invoice_item = InvoiceItem()

                invoice_item.invoice_id = invoice.id
                invoice_item.medicine_id = medicine.id
                invoice_item.quantity = quantity
                invoice_item.unit_price = unit_price
                invoice_item.total_price = item_total

                if not form.is_draft.data:
                    match invoice_type:
                        case InvoiceType.PURCHASE:
                            batch_number = item.get("purchase_batch_number")
                            expiry_date = item.get("expiry_date")

                            stock = MedicineStock()

                            stock.medicine_id = getattr(medicine, "id")
                            stock.batch_number = batch_number
                            stock.quantity = quantity
                            stock.purchase_price = unit_price
                            stock.expiry_date = expiry_date

                            db.session.add(stock)
                            db.session.flush()

                            invoice_item.batch_number = batch_number

                        case InvoiceType.SALE:
                            if stock := (
                                MedicineStock.query.filter(
                                    MedicineStock.medicine_id == medicine.id,
                                    MedicineStock.quantity >= quantity,
                                    MedicineStock.batch_number.isnot(None),
                                )
                                .order_by(MedicineStock.expiry_date.asc())
                                .first()
                            ):
                                stock.quantity -= quantity
                                invoice_item.batch_number = stock.batch_number

                        case InvoiceType.PURCHASE_RETURN:
                            if stock := MedicineStock.query.filter(
                                MedicineStock.medicine_id == medicine.id,
                                MedicineStock.quantity >= quantity,
                                MedicineStock.batch_number
                                == item.get("return_batch_number"),
                            ).first():
                                stock.quantity -= quantity
                                invoice_item.batch_number = stock.batch_number

                        case InvoiceType.SALE_RETURN:
                            batch_number = item.get("return_batch_number")

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

                            invoice_item.batch_number = batch_number
                else:
                    invoice_item.batch_number = (
                        item.get("batch_number")
                        or item.get("purchase_batch_number")
                        or item.get("return_batch_number")
                    )

                db.session.add(invoice_item)

            if not form.is_draft.data:
                paid_amount = Decimal(str(form.paid_amount.data or 0))

                transaction = Transaction()

                transaction.invoice_id = invoice.id
                transaction.created_by = current_user.id
                transaction.amount = total_amount

                match invoice_type:
                    case InvoiceType.PURCHASE:
                        transaction.supplier_id = supplier_id
                        transaction.transaction_type = TransactionType.PURCHASE

                    case InvoiceType.SALE:
                        transaction.customer_id = customer_id
                        transaction.transaction_type = TransactionType.SALE

                    case InvoiceType.PURCHASE_RETURN:
                        transaction.supplier_id = supplier_id
                        transaction.transaction_type = TransactionType.PURCHASE_RETURN

                        db.session.add(transaction)
                    case InvoiceType.SALE_RETURN:
                        transaction.customer_id = customer_id
                        transaction.transaction_type = TransactionType.SALE_RETURN

                invoice.settle_invoice(
                    invoice,
                    paid_amount,
                    customer_id,
                    supplier_id,
                    current_user.id,
                )

                db.session.add(transaction)

            db.session.commit()

            response["title"] = g("INVOICE_ADDED_LABEL")

            response["message"] = g("INVOICE_ADDED_SUCCESSFULLY_SUCCESS_MSG")

            response["category"] = "success"

            response["id"] = invoice.id

        except (ValueError, KeyError, TypeError) as e:
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

    if not form.validate_on_submit():
        response["errors"] = form.errors

        return Response(
            json.dumps(response),
            status=200,
            headers={"Content-Type": "application/json"},
        )

    medicine_id = form.medicine_id.data
    quantity = form.quantity.data
    unit_price = form.unit_price.data
    invoice_type = InvoiceType(form.invoice_type.data)

    medicine = Medicine.query.get(medicine_id)

    if not medicine:
        response["title"] = g("ERROR_ERROR")
        response["message"] = g("MEDICINE_NOT_FOUND_MSG")
        response["category"] = "error"

        return Response(
            json.dumps(response),
            status=404,
            headers={"Content-Type": "application/json"},
        )

    quantity = int(quantity or 0)
    unit_price = Decimal(str(unit_price or 0))

    if quantity <= 0:
        response["title"] = g("ERROR_ERROR")
        response["message"] = g("QUANTITY_MUST_BE_GREATER_THAN_ZERO_MSG")
        response["category"] = "error"

        return Response(
            json.dumps(response),
            status=422,
            headers={"Content-Type": "application/json"},
        )

    if unit_price < 0:
        response["title"] = g("ERROR_ERROR")
        response["message"] = g("UNIT_PRICE_CANNOT_BE_NEGATIVE_MSG")
        response["category"] = "error"

        return Response(
            json.dumps(response),
            status=422,
            headers={"Content-Type": "application/json"},
        )

    items = []

    if invoice_type == InvoiceType.PURCHASE:

        batch_number = form.purchase_batch_number.data
        expiry_date = form.expiry_date.data

        if not batch_number:
            response["title"] = g("ERROR_ERROR")
            response["message"] = g("BATCH_NUMBER_IS_REQUIRED_MSG")
            response["category"] = "error"

            return Response(
                json.dumps(response),
                status=422,
                headers={"Content-Type": "application/json"},
            )

        if not expiry_date:
            response["title"] = g("ERROR_ERROR")
            response["message"] = g("EXPIRY_DATE_IS_REQUIRED_MSG")
            response["category"] = "error"

            return Response(
                json.dumps(response),
                status=422,
                headers={"Content-Type": "application/json"},
            )

        # Check whether this exact batch already exists.
        existing_stock = MedicineStock.query.filter(
            MedicineStock.medicine_id == medicine_id,
            MedicineStock.batch_number == batch_number,
        ).first()

        if existing_stock:
            response["title"] = g("ERROR_ERROR")
            response["message"] = g("BATCH_NUMBER_ALREADY_EXISTS_MSG")
            response["category"] = "error"

            return Response(
                json.dumps(response),
                status=422,
                headers={"Content-Type": "application/json"},
            )

        items.append(
            {
                "stock_id": None,
                "batch_number": batch_number,
                "quantity": quantity,
                "available_quantity": 0,
                "expiry_date": expiry_date.isoformat(),
            }
        )

    elif invoice_type == InvoiceType.PURCHASE_RETURN:

        batch_number = form.return_batch_number.data

        if not batch_number:
            response["title"] = g("ERROR_ERROR")
            response["message"] = g("BATCH_NUMBER_IS_REQUIRED_MSG")
            response["category"] = "error"

            return Response(
                json.dumps(response),
                status=422,
                headers={"Content-Type": "application/json"},
            )

        stock = MedicineStock.query.filter(
            MedicineStock.medicine_id == medicine_id,
            MedicineStock.batch_number == batch_number,
            MedicineStock.quantity > 0,
        ).first()

        if not stock:
            response["title"] = g("ERROR_ERROR")
            response["message"] = g("BATCH_NOT_FOUND_MSG")
            response["category"] = "error"

            return Response(
                json.dumps(response),
                status=422,
                headers={"Content-Type": "application/json"},
            )

        if stock.quantity < quantity:
            response["title"] = g("ERROR_ERROR")
            response["message"] = g("NOT_ENOUGH_STOCK_AVAILABLE_MSG")
            response["category"] = "error"

            response["data"] = {
                "requested_quantity": quantity,
                "available_quantity": stock.quantity,
            }

            return Response(
                json.dumps(response),
                status=422,
                headers={"Content-Type": "application/json"},
            )

        items.append(
            {
                "stock_id": stock.id,
                "batch_number": stock.batch_number,
                "quantity": quantity,
                "available_quantity": stock.quantity,
                "expiry_date": (
                    stock.expiry_date.isoformat() if stock.expiry_date else None
                ),
            }
        )

    elif invoice_type == InvoiceType.SALE_RETURN:

        batch_number = form.return_batch_number.data

        if not batch_number:
            response["title"] = g("ERROR_ERROR")
            response["message"] = g("BATCH_NUMBER_IS_REQUIRED_MSG")
            response["category"] = "error"

            return Response(
                json.dumps(response),
                status=422,
                headers={"Content-Type": "application/json"},
            )

        stock = MedicineStock.query.filter(
            MedicineStock.medicine_id == medicine_id,
            MedicineStock.batch_number == batch_number,
        ).first()

        if not stock:
            response["title"] = g("ERROR_ERROR")
            response["message"] = g("BATCH_NOT_FOUND_MSG")
            response["category"] = "error"

            return Response(
                json.dumps(response),
                status=422,
                headers={"Content-Type": "application/json"},
            )

        items.append(
            {
                "stock_id": stock.id,
                "batch_number": stock.batch_number,
                "quantity": quantity,
                "available_quantity": stock.quantity,
                "expiry_date": (
                    stock.expiry_date.isoformat() if stock.expiry_date else None
                ),
            }
        )

    elif invoice_type == InvoiceType.SALE:

        stocks = (
            MedicineStock.query.filter(
                MedicineStock.medicine_id == medicine_id,
                MedicineStock.quantity > 0,
                MedicineStock.batch_number.isnot(None),
            )
            .order_by(
                MedicineStock.expiry_date.asc(),
                MedicineStock.id.asc(),
            )
            .all()
        )

        remaining_quantity = quantity

        for stock in stocks:

            if remaining_quantity <= 0:
                break

            allocated_quantity = min(
                remaining_quantity,
                stock.quantity,
            )

            items.append(
                {
                    "stock_id": stock.id,
                    "batch_number": stock.batch_number,
                    "quantity": allocated_quantity,
                    "available_quantity": stock.quantity,
                    "expiry_date": (
                        stock.expiry_date.isoformat() if stock.expiry_date else None
                    ),
                }
            )

            remaining_quantity -= allocated_quantity

        if remaining_quantity > 0:

            available_quantity = quantity - remaining_quantity

            response["title"] = g("ERROR_ERROR")
            response["message"] = g("NOT_ENOUGH_STOCK_AVAILABLE_MSG")
            response["category"] = "error"

            response["data"] = {
                "requested_quantity": quantity,
                "available_quantity": available_quantity,
            }

            return Response(
                json.dumps(response),
                status=422,
                headers={"Content-Type": "application/json"},
            )

    total_price = Decimal(quantity) * unit_price

    response["data"] = {
        "medicine": render_template(
            "admin/components/tables/td/medicine.html",
            medicine=medicine,
        ),
        "medicine_id": medicine.id,
        "quantity": quantity,
        "unit_price": float(unit_price),
        "total_price": float(total_price),
        "items": items,
    }

    response["category"] = "success"

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

    if not form.validate_on_submit():
        response["errors"] = form.errors

        return Response(
            json.dumps(response),
            status=200,
            headers={"Content-Type": "application/json"},
        )

    try:
        invoice = Invoice.query.get(form.id.data)

        if not invoice:
            response["title"] = g("ERROR_ERROR")
            response["message"] = g("INVOICE_NOT_FOUND_MSG")
            response["category"] = "error"

            return Response(
                json.dumps(response),
                status=404,
                headers={"Content-Type": "application/json"},
            )

        items = json.loads(form.items.data or "[]")

        if not isinstance(items, list):
            raise ValueError(g("INVALID_INVOICE_ITEMS_MSG"))

        supplier_id = form.supplier_id.data
        customer_id = form.customer_id.data

        invoice_type = InvoiceType(form.invoice_type.data)

        is_draft = bool(form.is_draft.data)

        if invoice.status == InvoiceStatus.COMPLETED:

            if invoice_type != invoice.invoice_type:
                raise ValueError(g("CANNOT_CHANGE_COMPLETED_INVOICE_TYPE_MSG"))

            if invoice_type in (
                InvoiceType.SALE,
                InvoiceType.SALE_RETURN,
            ):
                if customer_id != invoice.customer_id:
                    raise ValueError(g("CANNOT_CHANGE_COMPLETED_INVOICE_CUSTOMER_MSG"))

            elif invoice_type in (
                InvoiceType.PURCHASE,
                InvoiceType.PURCHASE_RETURN,
            ):
                if supplier_id != invoice.supplier_id:
                    raise ValueError(g("CANNOT_CHANGE_COMPLETED_INVOICE_SUPPLIER_MSG"))

            if is_draft:
                raise ValueError(g("COMPLETED_INVOICE_CANNOT_BE_DRAFT_MSG"))

            if hasattr(form, "note") and hasattr(invoice, "note"):
                invoice.note = form.note.data

            db.session.commit()

            response["title"] = g("INVOICE_UPDATED_LABEL")
            response["message"] = g("INVOICE_UPDATED_SUCCESSFULLY_MSG")
            response["category"] = "success"
            response["id"] = invoice.id

            return Response(
                json.dumps(response),
                status=200,
                headers={"Content-Type": "application/json"},
            )

        if invoice.status != InvoiceStatus.DRAFT:
            raise ValueError(g("INVALID_INVOICE_STATUS_MSG"))

        invoice.invoice_type = invoice_type

        if hasattr(form, "note") and hasattr(invoice, "note"):
            invoice.note = form.note.data

        invoice.status = InvoiceStatus.DRAFT if is_draft else InvoiceStatus.COMPLETED

        invoice.supplier_id = None
        invoice.customer_id = None

        if invoice_type in (
            InvoiceType.PURCHASE,
            InvoiceType.PURCHASE_RETURN,
        ):
            invoice.supplier_id = supplier_id

        elif invoice_type in (
            InvoiceType.SALE,
            InvoiceType.SALE_RETURN,
        ):
            invoice.customer_id = customer_id

        InvoiceItem.query.filter(InvoiceItem.invoice_id == invoice.id).delete(
            synchronize_session=False
        )

        db.session.flush()

        total_amount = Decimal("0")

        for item in items:

            medicine_id = item.get("medicine_id")

            quantity = int(item.get("quantity", 0))

            unit_price = Decimal(str(item.get("unit_price", 0)))

            if quantity <= 0:
                raise ValueError(g("QUANTITY_MUST_BE_GREATER_THAN_ZERO_MSG"))

            if unit_price < 0:
                raise ValueError(g("UNIT_PRICE_CANNOT_BE_NEGATIVE_MSG"))

            medicine = Medicine.query.filter_by(id=medicine_id).first()

            if not medicine:
                raise ValueError(g("MEDICINE_NOT_FOUND_MSG"))

            item_total = Decimal(quantity) * unit_price

            total_amount += item_total

            invoice_item = InvoiceItem()
            invoice_item.invoice_id = invoice.id
            invoice_item.medicine_id = medicine.id
            invoice_item.quantity = quantity
            invoice_item.unit_price = unit_price
            invoice_item.total_price = item_total

            if is_draft:
                invoice_item.batch_number = (
                    item.get("batch_number")
                    or item.get("purchase_batch_number")
                    or item.get("return_batch_number")
                )

            else:

                match invoice_type:

                    case InvoiceType.PURCHASE:

                        batch_number = item.get("purchase_batch_number") or item.get(
                            "batch_number"
                        )

                        expiry_date = item.get("expiry_date")

                        if not batch_number:
                            raise ValueError(g("BATCH_NUMBER_IS_REQUIRED_MSG"))

                        stock = MedicineStock()
                        stock.medicine_id = medicine.id
                        stock.batch_number = batch_number
                        stock.quantity = quantity
                        stock.purchase_price = unit_price
                        stock.expiry_date = expiry_date

                        db.session.add(stock)

                        invoice_item.batch_number = batch_number

                    case InvoiceType.SALE:

                        stock = (
                            MedicineStock.query.filter(
                                MedicineStock.medicine_id == medicine.id,
                                MedicineStock.quantity >= quantity,
                                MedicineStock.batch_number.isnot(None),
                            )
                            .order_by(
                                MedicineStock.expiry_date.asc(),
                                MedicineStock.id.asc(),
                            )
                            .first()
                        )

                        if not stock:
                            raise ValueError(g("NOT_ENOUGH_STOCK_AVAILABLE_MSG"))

                        stock.quantity -= quantity

                        invoice_item.batch_number = stock.batch_number

                    case InvoiceType.PURCHASE_RETURN:

                        batch_number = item.get("return_batch_number") or item.get(
                            "batch_number"
                        )

                        if not batch_number:
                            raise ValueError(g("BATCH_NUMBER_IS_REQUIRED_MSG"))

                        stock = MedicineStock.query.filter(
                            MedicineStock.medicine_id == medicine.id,
                            MedicineStock.batch_number == batch_number,
                            MedicineStock.quantity >= quantity,
                        ).first()

                        if not stock:
                            raise ValueError(g("NOT_ENOUGH_STOCK_AVAILABLE_MSG"))

                        stock.quantity -= quantity

                        invoice_item.batch_number = batch_number

                    case InvoiceType.SALE_RETURN:

                        batch_number = item.get("return_batch_number") or item.get(
                            "batch_number"
                        )

                        if not batch_number:
                            raise ValueError(g("BATCH_NUMBER_IS_REQUIRED_MSG"))

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

                        invoice_item.batch_number = batch_number

            db.session.add(invoice_item)

        if is_draft:

            db.session.commit()

            response["title"] = g("INVOICE_UPDATED_LABEL")

            response["message"] = g("INVOICE_SAVED_AS_DRAFT_SUCCESSFULLY_MSG")

            response["category"] = "success"
            response["id"] = invoice.id

            return Response(
                json.dumps(response),
                status=200,
                headers={"Content-Type": "application/json"},
            )

        paid_amount = Decimal(str(form.paid_amount.data or 0))

        # Create invoice financial transaction
        transaction = Transaction()
        transaction.invoice_id = invoice.id
        transaction.created_by = current_user.id
        transaction.amount = total_amount

        match invoice_type:

            case InvoiceType.PURCHASE:

                transaction.supplier_id = supplier_id
                transaction.transaction_type = TransactionType.PURCHASE

            case InvoiceType.SALE:

                transaction.customer_id = customer_id
                transaction.transaction_type = TransactionType.SALE

            case InvoiceType.PURCHASE_RETURN:

                transaction.supplier_id = supplier_id
                transaction.transaction_type = TransactionType.PURCHASE_RETURN

            case InvoiceType.SALE_RETURN:

                transaction.customer_id = customer_id
                transaction.transaction_type = TransactionType.SALE_RETURN

        db.session.add(transaction)

        if paid_amount > 0:

            invoice.allocate_payment(
                invoice,
                paid_amount,
                customer_id,
                supplier_id,
                current_user.id,
            )

        db.session.commit()

        response["title"] = g("INVOICE_UPDATED_LABEL")

        response["message"] = g("INVOICE_UPDATED_SUCCESSFULLY_MSG")

        response["category"] = "success"
        response["id"] = invoice.id

    except (ValueError, KeyError, TypeError) as e:

        db.session.rollback()

        response["title"] = g("ERROR_ERROR")
        response["message"] = str(e)
        response["category"] = "error"

    except Exception as e:

        db.session.rollback()

        response["title"] = g("ERROR_ERROR")
        response["message"] = g("INVOICE_COULD_NOT_BE_UPDATED_MSG")
        response["category"] = "error"

    return Response(
        json.dumps(response),
        status=200,
        headers={"Content-Type": "application/json"},
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
