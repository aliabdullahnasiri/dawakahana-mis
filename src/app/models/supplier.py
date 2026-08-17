from sqlalchemy import case, func

from app.extensions.db import db
from app.models.base import Base
from app.models.transaction import Transaction, TransactionType


class Supplier(Base):

    __tablename__ = "suppliers"

    name = db.Column(db.String(255), nullable=False)

    company_name = db.Column(db.String(255))

    phone = db.Column(db.String(50))

    email = db.Column(db.String(255))

    address = db.Column(db.Text)

    is_active = db.Column(db.Boolean, default=True)

    invoices = db.relationship("Invoice", back_populates="supplier", lazy="dynamic")

    transactions = db.relationship(
        "Transaction", back_populates="supplier", lazy="dynamic"
    )

    def get_debt(self):
        debt = (
            db.session.query(
                func.coalesce(
                    func.sum(
                        case(
                            (
                                Transaction.transaction_type
                                == TransactionType.PURCHASE,
                                Transaction.amount,
                            ),
                            (
                                Transaction.transaction_type == TransactionType.PAYMENT,
                                -Transaction.amount,
                            ),
                            (
                                Transaction.transaction_type
                                == TransactionType.PURCHASE_RETURN,
                                -Transaction.amount,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                )
            )
            .filter(
                Transaction.supplier_id == self.id,
            )
            .scalar()
        )

        return debt or 0

    def to_dict(self):

        return {
            "name": self.name,
            "company_name": self.company_name,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "is_active": self.is_active,
            **getattr(super(), "to_dict")(),
        }
