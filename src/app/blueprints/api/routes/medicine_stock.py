import json
from typing import Dict, List, Tuple

from flask import Response
from flask_babel import gettext as g

from app.blueprints.api import bp
from app.cls import ColumnID, ColumnName
from app.extensions.db import db
from app.forms.medicine_stock import AddMedicineStockForm, UpdateMedicineStockForm
from app.func import render_td
from app.models.medicine_stock import MedicineStock
from app.models.permission import Permission
from app.models.user import permission_required

cols: List[Tuple[ColumnID, ColumnName]] = [
    (ColumnID("id"), ColumnName(g("ID_LABEL"))),
    (ColumnID("medicine"), ColumnName(g("MEDICINE_LABEL"))),
    (ColumnID("batch_number"), ColumnName(g("BATCH_NUMBER_LABEL"))),
    (ColumnID("quantity"), ColumnName(g("QUANTITY_LABEL"))),
    (ColumnID("display_expiry_date"), ColumnName(g("EXPIRY_DATE_LABEL"))),
]


@bp.get("/fetch/medicine-stocks")
@permission_required(Permission.get("FETCH_MEDICINE_STOCKS"))
def fetch_medicine_stocks():

    stocks = [
        stock.to_dict()
        for stock in MedicineStock.query.filter(MedicineStock.quantity > 0).all()
    ]

    return Response(
        json.dumps(stocks),
        status=200,
        headers={"Content-Type": "application/json"},
    )


@bp.get("/fetch/medicine-stock/<int:id>")
@permission_required(Permission.get("FETCH_MEDICINE_STOCK"))
def fetch_medicine_stock(id) -> Response:
    stock = MedicineStock.query.filter_by(id=id).first()

    if stock:
        return Response(
            json.dumps(stock.to_dict()),
            status=200,
            headers={"Content-Type": "application/json"},
        )

    return Response(
        json.dumps(
            {
                "message": g("MEDICINE_STOCK_WITH_THE_GIVEN_ID_WAS_NOT_FOUND_MSG"),
                "category": "error",
            }
        ),
        status=404,
        headers={"Content-Type": "application/json"},
    )


@bp.get("/fetch/rows/medicine-stocks")
@permission_required(Permission.get("FETCH_MEDICINE_STOCKS"))
def fetch_medicine_stocks_rows():

    stocks = MedicineStock.query.filter(MedicineStock.quantity > 0).all()

    rows = []

    for stock in stocks:
        rows.append([render_td(col_id, stock) for col_id, _ in cols])

    data = {
        "cols": [(col_id, g(col_name)) for col_id, col_name in cols],
        "rows": rows,
    }

    return Response(
        json.dumps(data),
        status=200,
        headers={"Content-Type": "application/json"},
    )


@bp.get("/fetch/row/medicine-stock/<int:id>")
@permission_required(Permission.get("FETCH_MEDICINE_STOCK"))
def fetch_medicine_stock_row(id) -> Response:
    response = Response()

    stock = MedicineStock.query.filter_by(id=id).first()

    if stock:
        response.response = json.dumps(
            {
                key: value
                for key, value in zip(
                    [col_id for col_id, _ in cols],
                    [render_td(col_id, stock) for col_id, _ in cols],
                )
            }
        )
        response.status_code = 200

    else:
        response.response = json.dumps(
            {
                "message": g("MEDICINE_STOCK_WITH_THE_GIVEN_ID_WAS_NOT_FOUND_MSG"),
                "category": "error",
            }
        )
        response.status_code = 404

    response.headers["Content-Type"] = "application/json"

    return response


@bp.post("/add/medicine-stock")
@permission_required(Permission.get("CREATE_MEDICINE_STOCK"))
def add_medicine_stock():

    form = AddMedicineStockForm()

    response: Dict = {}

    if form.validate_on_submit():

        stock = MedicineStock()

        stock.medicine_id = form.medicine_id.data
        stock.batch_number = form.batch_number.data
        stock.quantity = form.quantity.data
        stock.purchase_price = form.purchase_price.data
        stock.selling_price = form.selling_price.data
        stock.expiry_date = form.expiry_date.data

        db.session.add(stock)
        db.session.commit()

        response["title"] = g("MEDICINE_STOCK_ADDED_LABEL")
        response["message"] = g("MEDICINE_STOCK_ADDED_SUCCESSFULLY_SUCCESS_MSG")
        response["category"] = "success"
        response["id"] = getattr(stock, "id")

    else:
        response["errors"] = form.errors

    return Response(
        json.dumps(response),
        status=200,
        headers={"Content-Type": "application/json"},
    )


@bp.post("/update/medicine-stock")
@permission_required(Permission.get("UPDATE_MEDICINE_STOCK"))
def update_medicine_stock():

    form = UpdateMedicineStockForm()

    response = {}

    if form.validate_on_submit():

        stock = MedicineStock.query.filter_by(id=form.id.data).first()

        if stock:

            stock.medicine_id = form.medicine_id.data
            stock.batch_number = form.batch_number.data
            stock.quantity = form.quantity.data
            stock.purchase_price = form.purchase_price.data
            stock.selling_price = form.selling_price.data
            stock.expiry_date = form.expiry_date.data

            db.session.commit()

            response["title"] = g("GOOD_JOB_LABEL")
            response["message"] = g("MEDICINE_STOCK_UPDATED_SUCCESSFULLY_SUCCESS_MSG")
            response["category"] = "success"

    else:
        response["errors"] = form.errors

    return Response(
        json.dumps(response),
        status=200,
        headers={"Content-Type": "application/json"},
    )


@bp.delete("/delete/medicine-stock/<int:id>")
@permission_required(Permission.get("DELETE_MEDICINE_STOCK"))
def delete_medicine_stock(id):

    response = {}

    stock = MedicineStock.query.filter_by(id=id).first()

    if stock:

        db.session.delete(stock)
        db.session.commit()

        response["title"] = g("DELETED_SUCCESS_MSG")
        response["message"] = g("MEDICINE_STOCK_DELETED_SUCCESSFULLY_SUCCESS_MSG")
        response["category"] = "success"
        response["status"] = 200

    else:

        response["title"] = g("ERROR_ERROR")
        response["message"] = g("MEDICINE_STOCK_NOT_FOUND_MSG")
        response["category"] = "error"
        response["status"] = 404

    return Response(
        json.dumps(response),
        status=response["status"],
        headers={"Content-Type": "application/json"},
    )
