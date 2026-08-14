import json
from typing import Dict, List, Tuple, Union

from flask import Response
from flask_babel import gettext as g

from app.blueprints.api import bp
from app.cls import ColumnID, ColumnName
from app.extensions.db import db
from app.forms.customer import AddCustomerForm, UpdateCustomerForm
from app.func import render_td
from app.models.customer import Customer
from app.models.permission import Permission
from app.models.user import permission_required

cols: List[Tuple[ColumnID, ColumnName]] = [
    (ColumnID("id"), ColumnName(g("ID_LABEL"))),
    (ColumnID("name"), ColumnName(g("CUSTOMER_NAME_LABEL"))),
    (ColumnID("phone"), ColumnName(g("PHONE_NUMBER_LABEL"))),
    (ColumnID("email"), ColumnName(g("EMAIL_LABEL"))),
    (ColumnID("is_active"), ColumnName(g("STATUS_LABEL"))),
]


@bp.get("/fetch/customers")
@permission_required(Permission.get("FETCH_CUSTOMERS"))
def fetch_customers() -> Response:

    customers: List[Dict] = [customer.to_dict() for customer in Customer.query.all()]

    return Response(
        json.dumps(customers),
        status=200,
        headers={"Content-Type": "application/json"},
    )


@bp.get("/fetch/rows/customers")
@permission_required(Permission.get("FETCH_CUSTOMERS"))
def fetch_customer_rows() -> Response:

    response = Response(
        headers={"Content-Type": "application/json"},
    )

    customers: List[Customer] = Customer.query.all()

    rows = []

    for customer in customers:

        row = [render_td(col_id, customer) for col_id, _ in cols]

        rows.append(row)

    data = {
        "cols": [(col_id, g(col_name)) for col_id, col_name in cols],
        "rows": rows,
    }

    response.response = json.dumps(data)
    response.status_code = 200

    return response


@bp.get("/fetch/row/customer/<int:id>")
@permission_required(Permission.get("FETCH_CUSTOMER"))
def fetch_customer_row(id: int) -> Response:

    customer = Customer.query.filter_by(id=id).first()

    if customer:

        return Response(
            json.dumps(
                {
                    key: value
                    for key, value in zip(
                        [col_id for col_id, _ in cols],
                        [render_td(col_id, customer) for col_id, _ in cols],
                    )
                }
            ),
            status=200,
            headers={"Content-Type": "application/json"},
        )

    return Response(
        json.dumps(
            {
                "message": g("CUSTOMER_WITH_THE_GIVEN_ID_WAS_NOT_FOUND_MSG"),
                "category": "error",
            }
        ),
        status=404,
        headers={"Content-Type": "application/json"},
    )


@bp.get("/fetch/customer/<int:id>")
@permission_required(Permission.get("FETCH_CUSTOMER"))
def fetch_customer(id: int) -> Response:

    customer = Customer.query.filter_by(id=id).first()

    if customer:

        return Response(
            json.dumps(customer.to_dict()),
            status=200,
            headers={"Content-Type": "application/json"},
        )

    return Response(
        json.dumps(
            {
                "message": g("CUSTOMER_WITH_THE_GIVEN_ID_WAS_NOT_FOUND_MSG"),
                "category": "error",
            }
        ),
        status=404,
        headers={"Content-Type": "application/json"},
    )


@bp.post("/add/customer")
@permission_required(Permission.get("CREATE_CUSTOMER"))
def add_customer() -> Response:

    response: Dict = {}

    form = AddCustomerForm()

    if form.validate_on_submit():

        customer = Customer()

        customer.name = form.name.data
        customer.phone = form.phone.data
        customer.email = form.email.data
        customer.address = form.address.data
        customer.is_active = form.is_active.data

        db.session.add(customer)
        db.session.commit()

        response["title"] = g("CUSTOMER_ADDED_LABEL")
        response["message"] = g("CUSTOMER_ADDED_SUCCESSFULLY_SUCCESS_MSG")
        response["category"] = "success"
        response["id"] = customer.id

    else:

        response["errors"] = form.errors

    return Response(
        json.dumps(response),
        status=200,
        headers={"Content-Type": "application/json"},
    )


@bp.post("/update/customer")
@permission_required(Permission.get("UPDATE_CUSTOMER"))
def update_customer() -> Response:

    response: Dict = {}

    form = UpdateCustomerForm()

    if form.validate_on_submit():

        customer = Customer.query.filter_by(id=form.id.data).first()

        if customer:

            customer.name = form.name.data
            customer.phone = form.phone.data
            customer.email = form.email.data
            customer.address = form.address.data
            customer.is_active = form.is_active.data

            db.session.commit()

            response["title"] = g("UPDATED_SUCCESS_MSG")
            response["message"] = g("CUSTOMER_UPDATED_SUCCESSFULLY_SUCCESS_MSG")
            response["category"] = "success"

        else:

            response["title"] = g("NOT_FOUND_LABEL")
            response["message"] = g("CUSTOMER_RECORD_NOT_FOUND_MSG")
            response["category"] = "error"

    else:

        response["errors"] = form.errors

    return Response(
        json.dumps(response),
        status=200,
        headers={"Content-Type": "application/json"},
    )


@bp.delete("/delete/customer/<int:id>")
@permission_required(Permission.get("DELETE_CUSTOMER"))
def delete_customer(id: int) -> Response:

    response: Dict = {}

    customer = Customer.query.filter_by(id=id).first()

    if customer:

        db.session.delete(customer)
        db.session.commit()

        response["title"] = g("DELETED_SUCCESS_MSG")
        response["message"] = g("CUSTOMER_DELETED_SUCCESSFULLY_SUCCESS_MSG")
        response["category"] = "success"
        response["status"] = 200

    else:

        response["title"] = g("ERROR_ERROR")
        response["message"] = g("CUSTOMER_NOT_FOUND_MSG")
        response["category"] = "error"
        response["status"] = 404

    return Response(
        json.dumps(response),
        status=response["status"],
        headers={"Content-Type": "application/json"},
    )
