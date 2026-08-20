from flask import render_template, request
from flask_login import login_required

from app.blueprints.api import bp
from app.models.base import Base


@bp.get("/autocomplete")
@login_required
def autocomplete() -> str:

    query = request.args.get("query")
    model_name = request.args.get("model-name")
    search_col = request.args.get("search-col")
    limit = int(request.args.get("limit", 10))
    template = request.args.get("template")
    where = request.args.get("where")

    for cls in Base.__subclasses__():

        if cls.__name__ != model_name:
            continue

        if not search_col:
            return ""

        search_column = getattr(cls, search_col, None)

        if search_column is None:
            return ""

        query_builder = cls.query

        # Search condition
        if query:
            query_builder = query_builder.filter(search_column.ilike(f"%{query}%"))

        # WHERE conditions
        if where:
            for condition in where.split(";"):

                condition = condition.strip()

                if not condition:
                    continue

                # Supported operators
                operator = None

                for op in ("!=", ">=", "<=", "=", ">", "<"):
                    if op in condition:
                        operator = op
                        break

                if not operator:
                    continue

                field_name, value = condition.split(
                    operator,
                    1,
                )

                field_name = field_name.strip()
                value = value.strip()

                field = getattr(
                    cls,
                    field_name,
                    None,
                )

                if field is None:
                    continue

                # Convert common values
                if value.lower() == "null":
                    if operator == "=":
                        query_builder = query_builder.filter(field.is_(None))
                    elif operator == "!=":
                        query_builder = query_builder.filter(field.is_not(None))

                    continue

                if value.lower() == "true":
                    value = True

                elif value.lower() == "false":
                    value = False

                else:
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            pass

                match operator:
                    case "=":
                        query_builder = query_builder.filter(field == value)

                    case "!=":
                        query_builder = query_builder.filter(field != value)

                    case ">":
                        query_builder = query_builder.filter(field > value)

                    case "<":
                        query_builder = query_builder.filter(field < value)

                    case ">=":
                        query_builder = query_builder.filter(field >= value)

                    case "<=":
                        query_builder = query_builder.filter(field <= value)

        rows = query_builder.limit(limit).all()

        return render_template(
            f"admin/autocomplete/{template}",
            rows=rows,
        )

    return ""
