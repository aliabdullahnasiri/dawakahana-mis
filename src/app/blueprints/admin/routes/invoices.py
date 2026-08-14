from flask import render_template
from flask_babel import gettext as _

from app.blueprints.admin import bp
from app.forms.invoice import AddInvoiceForm, UpdateInvoiceForm
from app.models.permission import Permission
from app.models.user import permission_required


@bp.get("/invoices")
@permission_required(Permission.get("FETCH_INVOICES") | Permission.get("FETCH_INVOICE"))
def invoices():

    return render_template(
        "admin/pages/invoices.html",
        title=_("INVOICES_LABEL"),
        form={
            "a": AddInvoiceForm(),
            "u": UpdateInvoiceForm(),
        },
    )
