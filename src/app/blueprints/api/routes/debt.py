from flask import jsonify, request

from app.blueprints.api import bp
from app.models.customer import Customer
from app.models.supplier import Supplier


@bp.post("/get/previous/debt")
def get_previous_debt():
    prev_debt = 0

    try:
        data = request.get_json()

        supplier_id = data.get("supplier_id")
        customer_id = data.get("customer_id")

        if isinstance(supplier_id, int):
            if supplier := Supplier.query.get(supplier_id):
                prev_debt = supplier.get_debt()

        elif isinstance(customer_id, int):
            if customer := Customer.query.get(customer_id):
                prev_debt = customer.get_debt()

    except:
        ...

    return (
        jsonify(
            {
                "previous_debt": prev_debt,
            }
        ),
        200,
    )
