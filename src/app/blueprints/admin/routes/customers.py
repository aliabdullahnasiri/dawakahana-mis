from flask import render_template

from app.blueprints.admin import bp
from app.forms.customer import AddCustomerForm, UpdateCustomerForm
from app.models.permission import Permission
from app.models.user import permission_required


@bp.get("/customers")
@permission_required(Permission.get("FETCH_CUSTOMERS"))
def customers():

    return render_template(
        "admin/pages/customers.html",
        title="CUSTOMERS_LABEL",
        form={
            "a": AddCustomerForm(),
            "u": UpdateCustomerForm(),
        },
    )
