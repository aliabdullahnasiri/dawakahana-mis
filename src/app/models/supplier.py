from decimal import Decimal

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

    @property
    def balance(self):
        debt = db.session.query(
            func.coalesce(
                func.sum(
                    case(
                        (
                            Transaction.transaction_type == TransactionType.PURCHASE,
                            Transaction.amount,
                        ),
                        (
                            Transaction.transaction_type == TransactionType.PAYMENT,
                            -Transaction.amount,
                        ),
                        (
                            Transaction.transaction_type == TransactionType.CREDIT_USED,
                            -Transaction.amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            )
        ).filter(
            Transaction.supplier_id == self.id,
            Transaction.transaction_type.in_(
                (
                    TransactionType.PURCHASE,
                    TransactionType.PAYMENT,
                    TransactionType.CREDIT_USED,
                )
            ),
        ).scalar() or Decimal(
            "0"
        )

        return_credit = db.session.query(
            func.coalesce(
                func.sum(
                    case(
                        (
                            Transaction.transaction_type
                            == TransactionType.PURCHASE_RETURN,
                            Transaction.amount,
                        ),
                        (
                            Transaction.transaction_type == TransactionType.REFUND,
                            -Transaction.amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            )
        ).filter(Transaction.supplier_id == self.id,).scalar() or Decimal("0")

        credit_used = db.session.query(
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            )
        ).filter(
            Transaction.supplier_id == self.id,
            Transaction.transaction_type == TransactionType.CREDIT_USED,
            Transaction.source_invoice_id.isnot(None),
        ).scalar() or Decimal(
            "0"
        )

        return (
            Decimal(str(debt)) - Decimal(str(return_credit)) + Decimal(str(credit_used))
        )

    @property
    def debt(self):
        """
        Amount your organization owes the supplier.
        """
        return max(self.balance, 0)

    @property
    def credit(self):
        """
        Amount the supplier owes your organization.
        """
        return max(-self.balance, 0)

    @property
    def is_debtor(self):
        """
        True when your organization owes the supplier.
        """
        return self.balance > 0

    @property
    def is_creditor(self):
        """
        True when the supplier owes your organization.
        """
        return self.balance < 0

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
