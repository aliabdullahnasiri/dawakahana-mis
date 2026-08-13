from flask import render_template
from flask_babel import gettext as _

from app.blueprints.admin import bp
from app.forms.medicine_stock import AddMedicineStockForm, UpdateMedicineStockForm
from app.models.permission import Permission
from app.models.user import permission_required


@bp.get("/medicine-stocks")
@permission_required(
    Permission.get("FETCH_MEDICINE_STOCKS") | Permission.get("FETCH_MEDICINE_STOCK")
)
def medicine_stocks():
    return render_template(
        "admin/pages/medicine-stocks.html",
        title=_("MEDICINE_STOCKS_LABEL"),
        form={
            "a": AddMedicineStockForm(),
            "u": UpdateMedicineStockForm(),
        },
    )
