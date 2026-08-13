from flask import render_template
from flask_babel import gettext as _

from app.blueprints.admin import bp
from app.forms.medicine import AddMedicineForm, UpdateMedicineForm
from app.models.permission import Permission
from app.models.user import permission_required


@bp.get("/medicines")
@permission_required(
    Permission.get("FETCH_MEDICINES") | Permission.get("FETCH_MEDICINE")
)
def medicines():
    return render_template(
        "admin/pages/medicines.html",
        title=_("MEDICINES_LABEL"),
        form={"a": AddMedicineForm(), "u": UpdateMedicineForm()},
    )
