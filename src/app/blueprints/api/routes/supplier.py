import json
from typing import Dict, List, Tuple, Union

from flask import Response
from flask_babel import gettext as g

from app.blueprints.api import bp
from app.cls import ColumnID, ColumnName
from app.extensions.db import db
from app.forms.supplier import AddSupplierForm, UpdateSupplierForm
from app.func import render_td
from app.models.permission import Permission
from app.models.supplier import Supplier
from app.models.user import permission_required

cols: List[Tuple[ColumnID, ColumnName]] = [
    (ColumnID("id"), ColumnName(g("ID_LABEL"))),
    (ColumnID("name"), ColumnName(g("SUPPLIER_NAME_LABEL"))),
    (ColumnID("company_name"), ColumnName(g("COMPANY_NAME_LABEL"))),
    (ColumnID("phone"), ColumnName(g("PHONE_LABEL"))),
    (ColumnID("email"), ColumnName(g("EMAIL_LABEL"))),
    (ColumnID("temp_is_active"), ColumnName(g("STATUS_LABEL"))),
]


@bp.get("/fetch/suppliers")
@permission_required(Permission.get("FETCH_SUPPLIERS"))
def fetch_suppliers() -> Response:

    suppliers = [supplier.to_dict() for supplier in Supplier.query.all()]

    return Response(
        json.dumps(suppliers),
        status=200,
        headers={"Content-Type": "application/json"},
    )


@bp.get("/fetch/rows/suppliers")
@permission_required(Permission.get("FETCH_SUPPLIERS"))
def fetch_suppliers_rows() -> Response:

    suppliers = Supplier.query.all()

    rows = []

    for supplier in suppliers:

        row = [render_td(col_id, supplier) for col_id, _ in cols]

        rows.append(row)

    data = {"cols": [(col_id, g(col_name)) for col_id, col_name in cols], "rows": rows}

    return Response(
        json.dumps(data),
        status=200,
        headers={"Content-Type": "application/json"},
    )


@bp.get("/fetch/row/supplier/<int:id>")
@permission_required(Permission.get("FETCH_SUPPLIER"))
def fetch_supplier_row(id) -> Response:

    supplier = Supplier.query.filter_by(id=id).first()

    if supplier:

        data = {
            key: value
            for key, value in zip(
                [col_id for col_id, _ in cols],
                [render_td(col_id, supplier) for col_id, _ in cols],
            )
        }

        return Response(
            json.dumps(data),
            status=200,
            headers={"Content-Type": "application/json"},
        )

    return Response(
        json.dumps({"message": g("SUPPLIER_NOT_FOUND_MSG"), "category": "error"}),
        status=404,
        headers={"Content-Type": "application/json"},
    )


@bp.get("/fetch/supplier/<int:id>")
@permission_required(Permission.get("FETCH_SUPPLIER"))
def fetch_supplier(id):

    supplier = Supplier.query.filter_by(id=id).first()

    if supplier:

        return Response(
            json.dumps(supplier.to_dict()),
            status=200,
            headers={"Content-Type": "application/json"},
        )

    return Response(
        json.dumps({"message": g("SUPPLIER_NOT_FOUND_MSG"), "category": "error"}),
        status=404,
        headers={"Content-Type": "application/json"},
    )


@bp.post("/add/supplier")
@permission_required(Permission.get("CREATE_SUPPLIER"))
def add_supplier():

    form = AddSupplierForm()

    response: Dict = {}

    if form.validate_on_submit():

        supplier = Supplier()

        supplier.name = form.name.data
        supplier.company_name = form.company_name.data
        supplier.phone = form.phone.data
        supplier.email = form.email.data
        supplier.address = form.address.data
        supplier.is_active = form.is_active.data

        db.session.add(supplier)
        db.session.commit()

        response["title"] = g("SUPPLIER_ADDED_LABEL")

        response["message"] = g("SUPPLIER_ADDED_SUCCESSFULLY_SUCCESS_MSG")

        response["category"] = "success"

        response["id"] = supplier.id

    else:

        response["errors"] = form.errors

    return Response(
        json.dumps(response),
        status=200,
        headers={"Content-Type": "application/json"},
    )


@bp.post("/update/supplier")
@permission_required(Permission.get("UPDATE_SUPPLIER"))
def update_supplier():

    form = UpdateSupplierForm()

    response = {}

    if form.validate_on_submit():

        supplier = Supplier.query.filter_by(id=form.id.data).first()

        if supplier:

            supplier.name = form.name.data
            supplier.company_name = form.company_name.data
            supplier.phone = form.phone.data
            supplier.email = form.email.data
            supplier.address = form.address.data
            supplier.is_active = form.is_active.data

            db.session.commit()

            response["title"] = g("UPDATED_SUCCESSFULLY_LABEL")

            response["message"] = g("SUPPLIER_UPDATED_SUCCESSFULLY_SUCCESS_MSG")

            response["category"] = "success"

    else:

        response["errors"] = form.errors

    return Response(
        json.dumps(response),
        status=200,
        headers={"Content-Type": "application/json"},
    )


@bp.delete("/delete/supplier/<int:id>")
@permission_required(Permission.get("DELETE_SUPPLIER"))
def delete_supplier(id):

    response = {}

    supplier = Supplier.query.filter_by(id=id).first()

    if supplier:

        db.session.delete(supplier)
        db.session.commit()

        response["title"] = g("DELETED_SUCCESS_MSG")

        response["message"] = g("SUPPLIER_DELETED_SUCCESSFULLY_SUCCESS_MSG")

        response["category"] = "success"

        response["status"] = 200

    else:

        response["title"] = g("ERROR_ERROR")

        response["message"] = g("SUPPLIER_NOT_FOUND_MSG")

        response["category"] = "error"

        response["status"] = 404

    return Response(
        json.dumps(response),
        status=response["status"],
        headers={"Content-Type": "application/json"},
    )
