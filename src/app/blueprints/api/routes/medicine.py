import json
from typing import Dict, List, Tuple

from flask import Response
from flask_babel import gettext as g

from app.blueprints.api import bp
from app.cls import ColumnID, ColumnName
from app.extensions.db import db
from app.forms.medicine import AddMedicineForm, UpdateMedicineForm
from app.func import render_td
from app.models.medicine import Medicine
from app.models.permission import Permission
from app.models.user import permission_required

cols: List[Tuple[ColumnID, ColumnName]] = [
    (ColumnID("id"), ColumnName(g("ID_LABEL"))),
    (ColumnID("barcode"), ColumnName(g("BARCODE_LABEL"))),
    (ColumnID("name"), ColumnName(g("MEDICINE_NAME_LABEL"))),
    (ColumnID("manufacturer"), ColumnName(g("MANUFACTURER_LABEL"))),
    (ColumnID("strength"), ColumnName(g("STRENGTH_LABEL"))),
]


@bp.get("/fetch/medicines")
@permission_required(Permission.get("FETCH_MEDICINES"))
def fetch_medicines() -> Response:
    medicines: List[Medicine] = [
        medicine.to_dict() for medicine in Medicine.query.all()
    ]

    return Response(
        json.dumps(medicines),
        status=200,
        headers={"Content-Type": "application/json"},
    )


@bp.get("/fetch/rows/medicines")
@permission_required(Permission.get("FETCH_MEDICINES"))
def fetch_medicines_rows() -> Response:
    medicines: List[Medicine] = Medicine.query.all()

    rows: List[List] = []

    for medicine in medicines:
        row = [render_td(col_id, medicine) for col_id, _ in cols]
        rows.append(row)

    data = {
        "cols": [(col_id, g(col_name)) for col_id, col_name in cols],
        "rows": rows,
    }

    return Response(
        json.dumps(data),
        status=200,
        headers={"Content-Type": "application/json"},
    )


@bp.get("/fetch/row/medicine/<int:id>")
@permission_required(Permission.get("FETCH_MEDICINE"))
def fetch_medicine_row(id) -> Response:
    medicine = Medicine.query.filter_by(id=id).first()

    if medicine:
        response = {
            key: value
            for key, value in zip(
                [col_id for col_id, _ in cols],
                [render_td(col_id, medicine) for col_id, _ in cols],
            )
        }

        return Response(
            json.dumps(response),
            status=200,
            headers={"Content-Type": "application/json"},
        )

    return Response(
        json.dumps(
            {
                "message": g("MEDICINE_WITH_THE_GIVEN_ID_WAS_NOT_FOUND_MSG"),
                "category": "error",
            }
        ),
        status=404,
        headers={"Content-Type": "application/json"},
    )


@bp.get("/fetch/medicine/<int:id>")
@permission_required(Permission.get("FETCH_MEDICINE"))
def fetch_medicine(id) -> Response:
    medicine = Medicine.query.filter_by(id=id).first()

    if medicine:
        return Response(
            json.dumps(medicine.to_dict()),
            status=200,
            headers={"Content-Type": "application/json"},
        )

    return Response(
        json.dumps(
            {
                "message": g("MEDICINE_WITH_THE_GIVEN_ID_WAS_NOT_FOUND_MSG"),
                "category": "error",
            }
        ),
        status=404,
        headers={"Content-Type": "application/json"},
    )


@bp.post("/add/medicine")
@permission_required(Permission.get("CREATE_MEDICINE"))
def add_medicine() -> Response:
    form = AddMedicineForm()

    response: Dict = {}

    if form.validate_on_submit():
        medicine = Medicine()
        medicine.barcode = form.barcode.data
        medicine.name = form.name.data
        medicine.generic_name = form.generic_name.data
        medicine.manufacturer = form.manufacturer.data
        medicine.strength = form.strength.data
        medicine.description = form.description.data
        medicine.is_active = form.is_active.data

        db.session.add(medicine)
        db.session.commit()

        response["message"] = g("MEDICINE_ADDED_SUCCESSFULLY_SUCCESS_MSG")
        response["title"] = g("MEDICINE_ADDED_LABEL")
        response["category"] = "success"
        response["id"] = getattr(medicine, "id")

    else:
        response["errors"] = form.errors

    return Response(
        json.dumps(response),
        status=200,
        headers={"Content-Type": "application/json"},
    )


@bp.post("/update/medicine")
@permission_required(
    Permission.get("FETCH_MEDICINE") | Permission.get("UPDATE_MEDICINE")
)
def update_medicine() -> Response:
    form = UpdateMedicineForm()

    response: Dict = {}

    if form.validate_on_submit():
        medicine = Medicine.query.filter_by(id=form.id.data).first()

        if medicine:
            medicine.barcode = form.barcode.data
            medicine.name = form.name.data
            medicine.generic_name = form.generic_name.data
            medicine.manufacturer = form.manufacturer.data
            medicine.strength = form.strength.data
            medicine.description = form.description.data
            medicine.is_active = form.is_active.data

            db.session.commit()

            response["title"] = g("GOOD_JOB_LABEL")
            response["message"] = g("MEDICINE_UPDATED_SUCCESSFULLY_SUCCESS_MSG")
            response["category"] = "success"

    else:
        response["errors"] = form.errors

    return Response(
        json.dumps(response),
        status=200,
        headers={"Content-Type": "application/json"},
    )


@bp.delete("/delete/medicine/<int:id>")
@permission_required(
    Permission.get("FETCH_MEDICINE") | Permission.get("DELETE_MEDICINE")
)
def delete_medicine(id):
    response = {}

    medicine = Medicine.query.filter_by(id=id).first()

    if medicine:
        db.session.delete(medicine)
        db.session.commit()

        response["title"] = g("DELETED_SUCCESS_MSG")
        response["message"] = g("MEDICINE_DELETED_SUCCESSFULLY_SUCCESS_MSG")
        response["category"] = "success"
        response["status"] = 200

    else:
        response["title"] = g("ERROR_ERROR")
        response["message"] = g("MEDICINE_NOT_FOUND_MSG")
        response["category"] = "error"
        response["status"] = 404

    return Response(
        json.dumps(response),
        status=response["status"],
        headers={"Content-Type": "application/json"},
    )
