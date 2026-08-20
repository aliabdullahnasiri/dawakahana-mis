from flask import jsonify, request
from flask_login import login_required

from app.blueprints.api import bp
from app.models.customer import Customer
from app.models.supplier import Supplier


@bp.post("/get/previous/balance")
@login_required
def get_previous_balance():

    balance = 0
    debt = 0
    credit = 0

    data = request.get_json() or {}

    supplier_id = data.get("supplier_id")
    customer_id = data.get("customer_id")

    if isinstance(supplier_id, int):
        supplier = Supplier.query.get(supplier_id)

        if supplier:
            balance = supplier.balance
            debt = supplier.debt
            credit = supplier.credit

    elif isinstance(customer_id, int):
        customer = Customer.query.get(customer_id)

        if customer:
            balance = customer.balance
            debt = customer.debt
            credit = customer.credit

    return (
        jsonify(
            {
                "previous_balance": float(balance),
                "previous_debt": float(debt),
                "previous_credit": float(credit),
            }
        ),
        200,
    )
