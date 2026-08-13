from flask_babel import gettext as _
from wtforms import (
    DateField,
    DecimalField,
    HiddenField,
    PasswordField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from app.forms.user import AddUserForm, UpdateUserForm


class AddEmployeeForm(AddUserForm):
    job_id = StringField(
        _("JOB_ID_LABEL"),
        validators=[
            Optional(),
            Length(min=8, max=8, message=_("THIS_FIELD_MUST_BE_8_CHARACTERS_MSG")),
        ],
        render_kw={
            "data-auto-complete": "true",
            "data-fetch-api": "api.autocomplete",
            "data-model-name": "Job",
            "data-select-val": "id",
            "data-search-col": "job_title",
            "data-template": "jobs.html",
        },
    )

    address = StringField(
        _("ADDRESS_LABEL"),
        validators=[
            Length(max=255, message=_("THIS_FIELD_CANNOT_EXCEED_255_CHARACTERS_MSG"))
        ],
    )
    salary = DecimalField(
        _("SALARY_LABEL"),
        places=2,
        validators=[
            Optional(),
            NumberRange(min=0, message=_("VALUE_MUST_BE_AT_LEAST_MIN_S_MSG")),
        ],
    )
    hire_date = DateField(_("HIRE_DATE_LABEL"), format="%Y-%m-%d")
    submit = SubmitField(_("ADD_LABEL"))


class UpdateEmployeeForm(UpdateUserForm, AddEmployeeForm):
    id = HiddenField(
        _("EMPLOYEE_ID_LABEL"),
        validators=[
            DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR")),
        ],
    )
    user_id = HiddenField(
        _("USER_ID_LABEL"),
        validators=[
            DataRequired(message=_("THIS_FIELD_IS_REQUIRED_ERROR")),
        ],
    )
    password = PasswordField(_("PASSWORD_LABEL"))
    submit = SubmitField(_("UPDATE_LABEL"))
