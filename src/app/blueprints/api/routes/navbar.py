from typing import Dict, List

from flask import jsonify, url_for
from flask_babel import _
from flask_login import current_user, login_required

from app.blueprints.api import bp
from app.models.permission import Permission

ITEMS: List[Dict] = [
    {
        "type": "item",
        "title": _("DASHBOARD_LABEL"),
        "icon": "dashboard",
        "endpoint": "admin.dashboard",
        "permissions": Permission.get("VIEW_DASHBOARD"),
    },
    {
        "type": "item",
        "title": _("USERS_LABEL"),
        "icon": "groups",
        "endpoint": "admin.users",
        "permissions": Permission.get("FETCH_USERS") | Permission.get("FETCH_USER"),
    },
    {
        "type": "item",
        "title": _("PERMISSIONS_LABEL"),
        "icon": "lock_open_circle",
        "endpoint": "admin.permissions",
        "permissions": Permission.get("FETCH_PERMISSIONS")
        | Permission.get("FETCH_PERMISSION"),
    },
    {
        "type": "item",
        "title": _("ROLES_LABEL"),
        "icon": "supervised_user_circle",
        "endpoint": "admin.roles",
        "permissions": Permission.get("FETCH_ROLES") | Permission.get("FETCH_ROLE"),
    },
    {
        "type": "section",
        "title": _("MANAGEMENT_LABEL"),
        "items": [
            {
                "type": "item",
                "title": _("MEDICINES_LABEL"),
                "icon": None,
                "endpoint": "admin.medicines",
                "permissions": Permission.get("FETCH_MEDICINES")
                | Permission.get("FETCH_MEDICINE"),
            },
            {
                "type": "item",
                "title": _("MEDICINE_STOCKS_LABEL"),
                "icon": None,
                "endpoint": "admin.medicine_stocks",
                "permissions": Permission.get("FETCH_MEDICINE_STOCKS")
                | Permission.get("FETCH_MEDICINE_STOCK"),
            },
            {
                "type": "item",
                "title": _("JOBS_LABEL"),
                "icon": None,
                "endpoint": "admin.jobs",
                "permissions": Permission.get("FETCH_JOBS")
                | Permission.get("FETCH_JOB"),
            },
            {
                "type": "item",
                "title": _("EMPLOYEES_LABEL"),
                "icon": None,
                "endpoint": "admin.employees",
                "permissions": Permission.get("FETCH_EMPLOYEES")
                | Permission.get("FETCH_EMPLOYEE"),
            },
        ],
    },
    {
        "type": "section",
        "title": _("ACCOUNT_TITLE"),
        "items": [
            {
                "type": "item",
                "title": _("PROFILE_TITLE"),
                "icon": "person",
                "endpoint": "admin.profile",
            },
        ],
    },
]


def build_navbar(current_user) -> List:
    return list(
        filter(
            lambda f_item: (
                type(f_item["for"]) is str if f_item and f_item.get("for") else True
            ),
            [
                (
                    {
                        "type": item.get("type"),
                        "title": item.get("title"),
                        "for": item.get("for"),
                        "icon": item.get("icon"),
                        "items": list(
                            map(
                                lambda m_item: {
                                    "type": m_item.get("type"),
                                    "title": m_item.get("title"),
                                    "icon": m_item.get("icon"),
                                    "url": url_for(m_item.get("endpoint")),
                                    "for": item.get("for"),
                                },
                                filter(
                                    lambda i: current_user.can(i.get("permissions", 0)),
                                    item.get("items", []),
                                ),
                            )
                        ),
                    }
                    if item.get("type") == "section"
                    else (
                        {
                            "type": item.get("type"),
                            "title": item.get("title"),
                            "for": item.get("for"),
                            "icon": item.get("icon"),
                            "url": url_for(item["endpoint"]),
                        }
                        if current_user.can(item.get("permissions", 0))
                        else None
                    )
                )
                for item in ITEMS
            ],
        )
    )


@bp.route("/navbar")
@login_required
def navbar():
    return jsonify(build_navbar(current_user))
