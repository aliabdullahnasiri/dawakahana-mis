from datetime import datetime, timedelta, timezone
from typing import Any

import jdatetime
from numerize import numerize
from sqlalchemy import Column, Date, DateTime, event, extract, func
from sqlalchemy.ext.declarative import declared_attr

from app.extensions.db import db


class Base(db.Model):
    __abstract__ = True

    @declared_attr
    def id(cls):
        return Column(db.Integer, primary_key=True, autoincrement=True)

    # Timestamps
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __getattribute__(self, name: str, /) -> Any:
        if name.startswith("display_"):
            column_name = name[8:]

            if hasattr(self, column_name):
                column = getattr(self.__class__, column_name, None)
                value = getattr(self, column_name, None)
                if column and value:
                    # check if column is date or datetime
                    if hasattr(column, "type") and isinstance(
                        column.type, (Date, DateTime)
                    ):
                        return jdatetime.date.fromgregorian(date=value).strftime(
                            "%Y/%m/%d"
                        )

                    return str(value)

        return super().__getattribute__(name)

    def update(self):
        self.updated_at = func.now()

    @classmethod
    def yearly_growth(cls):
        current_year = datetime.now().year
        last_year = current_year - 1

        current_count = (
            db.session.query(func.count(cls.created_at))
            .filter(extract("year", cls.created_at) == current_year)
            .scalar()
        )

        previous_count = (
            db.session.query(func.count(cls.created_at))
            .filter(extract("year", cls.created_at) == last_year)
            .scalar()
        )

        return cls._percent_change(current_count, previous_count)

    @classmethod
    def yearly_growth_clr(cls):
        if cls.yearly_growth() > 0:
            return "success"

        return "danger"

    @classmethod
    def yearly_growth_icon(cls):
        if cls.yearly_growth() > 0:
            return "arrow_upward"

        return "arrow_downward"

    @classmethod
    def display_yearly_growth(cls):
        sign = chr(43) if (g := cls.yearly_growth()) > 0 else chr(45)

        if g == 0:
            sign = str()

        return f"{sign}{abs(g)}{chr(37)}"

    @classmethod
    def weekly_growth(cls):
        now = datetime.now(timezone.utc)

        start_of_week = datetime.combine(
            (now - timedelta(days=now.weekday())).date(),
            datetime.min.time(),
            tzinfo=timezone.utc,
        )
        start_of_last_week = start_of_week - timedelta(weeks=1)
        end_of_last_week = start_of_week

        current_week = (
            db.session.query(cls).filter(cls.created_at >= start_of_week).count()
        )

        previous_week = (
            db.session.query(cls)
            .filter(
                cls.created_at >= start_of_last_week, cls.created_at < end_of_last_week
            )
            .count()
        )

        return cls._percent_change(current_week, previous_week)

    @classmethod
    def weekly_growth_clr(cls):
        if cls.weekly_growth() > 0:
            return "success"

        return "danger"

    @classmethod
    def display_weekly_growth(cls):
        sign = chr(43) if (g := cls.weekly_growth()) > 0 else chr(45)

        if g == 0:
            sign = str()

        return f"{sign}{abs(g)}{chr(37)}"

    @classmethod
    def weekly_growth_icon(cls):
        if cls.weekly_growth() > 0:
            return "arrow_upward"

        return "arrow_downward"

    @classmethod
    def monthly_growth(cls):
        current_month = datetime.now().month
        last_month = current_month - 1 if current_month > 1 else 12

        current_count = (
            db.session.query(func.count(cls.created_at))
            .filter(extract("month", cls.created_at) == current_month)
            .scalar()
        )

        previous_count = (
            db.session.query(func.count(cls.created_at))
            .filter(extract("month", cls.created_at) == last_month)
            .scalar()
        )

        return cls._percent_change(current_count, previous_count)

    @classmethod
    def monthly_growth_clr(cls):
        if cls.monthly_growth() > 0:
            return "success"

        return "danger"

    @classmethod
    def display_monthly_growth(cls):
        sign = chr(43) if cls.monthly_growth() >= 0 else chr(45)
        growth = f"{sign}{abs(cls.monthly_growth())}{chr(37)}"

        return growth

    @staticmethod
    def _percent_change(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 2)

    @classmethod
    def count(cls):
        return numerize.numerize(cls.query.count(), 2)

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.display_created_at,
            "updated_at": self.display_updated_at,
        }

    def __setattr__(self, name: str, value: Any, /) -> None:
        if type(value) is str and not value:
            value = None

        return super().__setattr__(name, value)


@event.listens_for(Base, "before_insert", propagate=True)
def before_insert(mapper, connection, target) -> None: ...


@event.listens_for(Base, "after_insert", propagate=True)
def after_insert(mapper, connection, target) -> None: ...


db.Model = Base
