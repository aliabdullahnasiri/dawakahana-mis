from flask import render_template
from flask_babel import gettext as _

from app.blueprints.admin import bp
from app.forms.supplier import AddSupplierForm, UpdateSupplierForm
from app.models.permission import Permission
from app.models.user import permission_required


@bp.get("/suppliers")
@permission_required(
    Permission.get("FETCH_SUPPLIERS") | Permission.get("FETCH_SUPPLIER")
)
def suppliers():

    return render_template(
        "admin/pages/suppliers.html",
        title=_("SUPPLIERS_LABEL"),
        form={"a": AddSupplierForm(), "u": UpdateSupplierForm()},
    )
