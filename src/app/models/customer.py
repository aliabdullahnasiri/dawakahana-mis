from decimal import Decimal

from sqlalchemy import case, func

from app.extensions.db import db
from app.models.base import Base
from app.models.transaction import Transaction, TransactionType


class Customer(Base):

    __tablename__ = "customers"

    name = db.Column(db.String(100), nullable=False)

    phone = db.Column(db.String(50), unique=True, index=True)

    email = db.Column(db.String(120))

    address = db.Column(db.String(255))

    notes = db.Column(db.Text)

    is_active = db.Column(db.Boolean, default=True)

    invoices = db.relationship("Invoice", back_populates="customer", lazy="dynamic")

    transactions = db.relationship(
        "Transaction", back_populates="customer", lazy="dynamic"
    )

    invoices = db.relationship("Invoice", back_populates="customer", lazy="dynamic")

    @property
    def balance(self):
        debt = db.session.query(
            func.coalesce(
                func.sum(
                    case(
                        (
                            Transaction.transaction_type == TransactionType.SALE,
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
            Transaction.customer_id == self.id,
            Transaction.transaction_type.in_(
                (
                    TransactionType.SALE,
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
                            Transaction.transaction_type == TransactionType.SALE_RETURN,
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
        ).filter(Transaction.customer_id == self.id).scalar() or Decimal("0")

        credit_used = db.session.query(
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            )
        ).filter(
            Transaction.customer_id == self.id,
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
        Amount the customer owes us.
        """
        return max(
            self.balance,
            Decimal("0"),
        )

    @property
    def credit(self):
        """
        Amount we owe the customer.
        """
        return max(
            -self.balance,
            Decimal("0"),
        )

    @property
    def is_debtor(self):
        """
        True when the customer owes us.
        """
        return self.balance > 0

    @property
    def is_creditor(self):
        """
        True when we owe the customer.
        """
        return self.balance < 0

    def to_dict(self) -> dict:

        return {
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "notes": self.notes,
            "is_active": self.is_active,
            **getattr(super(), "to_dict")(),
        }

    def __repr__(self):
        return f"<Customer name={self.name!r} " f"phone={self.phone!r}>"
