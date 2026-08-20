import enum
from datetime import datetime
from decimal import Decimal
from typing import Self

from sqlalchemy import func

from app.extensions.db import db
from app.models.base import Base
from app.models.invoice_item import InvoiceItem
from app.models.transaction import Transaction, TransactionType


class InvoiceType(enum.Enum):
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    PURCHASE_RETURN = "PURCHASE_RETURN"
    SALE_RETURN = "SALE_RETURN"


class InvoiceStatus(enum.Enum):
    DRAFT = "DRAFT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Invoice(Base):

    __tablename__ = "invoices"

    invoice_number = db.Column(db.String(100), unique=True, nullable=False, index=True)

    invoice_type = db.Column(db.Enum(InvoiceType), nullable=False)

    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=True)

    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True)

    status = db.Column(
        db.Enum(InvoiceStatus),
        nullable=False,
        default=InvoiceStatus.COMPLETED,
    )

    invoice_date = db.Column(
        db.Date,
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
    )

    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    items = db.relationship(
        "InvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    supplier = db.relationship("Supplier", back_populates="invoices")

    customer = db.relationship("Customer", back_populates="invoices")

    transactions = db.relationship(
        "Transaction",
        foreign_keys="Transaction.invoice_id",
        back_populates="invoice",
        lazy="dynamic",
    )

    source_transactions = db.relationship(
        "Transaction",
        foreign_keys="Transaction.source_invoice_id",
        back_populates="source_invoice",
        lazy="dynamic",
    )

    user = db.relationship("User")

    def to_dict(self):
        readonly = []

        is_return = self.invoice_type in (
            InvoiceType.PURCHASE_RETURN,
            InvoiceType.SALE_RETURN,
        )

        is_normal = self.invoice_type in (
            InvoiceType.PURCHASE,
            InvoiceType.SALE,
        )

        if self.status == InvoiceStatus.COMPLETED:
            readonly.extend(
                [
                    "paid_amount",
                    "supplier_id",
                    "customer_id",
                    "invoice_type",
                    "is_draft",
                    "add_invoice_item",
                    "remove_invoice_item",
                ]
            )

        dct = {
            "invoice_number": self.invoice_number,
            "invoice_type": self.invoice_type.value,
            "invoice_date": self.display_invoice_date,
            "status": self.display_status,
            "is_draft": InvoiceStatus.DRAFT == self.status,
            "customer_id": self.customer_id,
            "supplier_id": self.supplier_id,
            "total_amount": float(self.total_amount),
            "_settled_amount": 0.0,
            "remaining_amount": 0.0,
            "items_count": self.items.count(),
            "readonly": readonly,
            "items": [item.to_dict() for item in self.items.all()],
        }

        if is_normal:
            dct.update(
                {
                    "paid_amount": float(self.paid_amount),
                    "credit_used": float(self.credit_used),
                    "settled_amount": float(self.settled_amount),
                    "remaining_amount": float(self.remaining_amount),
                }
            )

        elif is_return:
            dct.update(
                {
                    "refunded_amount": float(self.refunded_amount),
                    "settled_amount": float(self.settled_amount),
                    "remaining_amount": float(self.remaining_amount),
                }
            )

        dct = {
            **dct,
            **getattr(super(), "to_dict")(),
        }

        return dct

    @staticmethod
    def generate_invoice_number(invoice_type: InvoiceType) -> str:
        prefix = {
            InvoiceType.PURCHASE: "PUR",
            InvoiceType.SALE: "SAL",
            InvoiceType.PURCHASE_RETURN: "PRT",
            InvoiceType.SALE_RETURN: "SRT",
        }[invoice_type]

        date = datetime.now().strftime("%Y%m%d")

        last_invoice = (
            Invoice.query.filter(
                Invoice.invoice_type == invoice_type,
                Invoice.invoice_number.like(f"{prefix}-{date}-%"),
            )
            .order_by(Invoice.id.desc())
            .first()
        )

        if last_invoice:
            sequence = int(last_invoice.invoice_number.rsplit("-", 1)[1]) + 1
        else:
            sequence = 1

        return f"{prefix}-{date}-{sequence:04d}"

    @property
    def total_amount(self):
        return db.session.query(
            func.coalesce(
                func.sum(InvoiceItem.total_price),
                0,
            )
        ).filter(InvoiceItem.invoice_id == self.id,).scalar() or Decimal("0")

    @property
    def paid_amount(self):
        """Actual money paid for a purchase or sale invoice."""
        if self.invoice_type not in (
            InvoiceType.PURCHASE,
            InvoiceType.SALE,
        ):
            return Decimal("0")

        return db.session.query(
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            )
        ).filter(
            Transaction.invoice_id == self.id,
            Transaction.transaction_type == TransactionType.PAYMENT,
        ).scalar() or Decimal("0")

    @property
    def credit_used(self):
        """Existing credit used to settle a purchase or sale invoice."""
        if self.invoice_type not in (
            InvoiceType.PURCHASE,
            InvoiceType.SALE,
        ):
            return Decimal("0")

        return db.session.query(
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            )
        ).filter(
            Transaction.invoice_id == self.id,
            Transaction.transaction_type == TransactionType.CREDIT_USED,
        ).scalar() or Decimal("0")

    @property
    def credit_applied(self):
        """Credit from this return invoice that was applied to other invoices."""
        if self.invoice_type not in (
            InvoiceType.PURCHASE_RETURN,
            InvoiceType.SALE_RETURN,
        ):
            print("Sd")
            return Decimal("0")

        return db.session.query(
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            )
        ).filter(
            Transaction.source_invoice_id == self.id,
            Transaction.transaction_type == TransactionType.CREDIT_USED,
        ).scalar() or Decimal("0")

    @property
    def settled_amount(self):
        """
        Total amount settled for a purchase or sale.

        Actual payment + existing credit used.
        """
        if self.invoice_type in (
            InvoiceType.PURCHASE_RETURN,
            InvoiceType.SALE_RETURN,
        ):
            return self.refunded_amount + self.credit_applied

        return self.paid_amount + self.credit_used

    @property
    def refunded_amount(self):
        """Actual money refunded for a return invoice."""
        if self.invoice_type not in (
            InvoiceType.PURCHASE_RETURN,
            InvoiceType.SALE_RETURN,
        ):
            return Decimal("0")

        return db.session.query(
            func.coalesce(
                func.sum(Transaction.amount),
                0,
            )
        ).filter(
            Transaction.invoice_id == self.id,
            Transaction.transaction_type == TransactionType.REFUND,
        ).scalar() or Decimal("0")

    @property
    def remaining_amount(self):
        """
        Remaining amount for the invoice.

        Purchase/Sale:
            total - paid - credit_used

        Purchase Return/Sale Return:
            total - refunded
        """
        if self.invoice_type in (
            InvoiceType.PURCHASE_RETURN,
            InvoiceType.SALE_RETURN,
        ):
            return max(
                self.total_amount - self.refunded_amount - self.credit_applied,
                Decimal("0"),
            )

        return max(
            self.total_amount - self.paid_amount - self.credit_used,
            Decimal("0"),
        )

    def settle_invoice(
        self: Self,
        invoice: Invoice,
        amount: Decimal,
        customer_id: int | None = None,
        supplier_id: int | None = None,
        user_id: int | None = None,
    ):
        amount = Decimal(str(amount or 0))

        total_amount = Decimal(str(invoice.total_amount or 0))

        match invoice.invoice_type:
            case invoice_type if invoice_type in (
                InvoiceType.SALE,
                InvoiceType.SALE_RETURN,
            ):
                supplier_id = None

            case invoice_type if invoice_type in (
                InvoiceType.PURCHASE,
                InvoiceType.PURCHASE_RETURN,
            ):
                customer_id = None

        if invoice.invoice_type in (
            InvoiceType.PURCHASE_RETURN,
            InvoiceType.SALE_RETURN,
        ):
            return_remaining = Decimal(str(invoice.remaining_amount or 0))

            if return_remaining <= 0:
                return

            # 1. Refund the return first
            refund_amount = min(
                amount,
                return_remaining,
            )

            if refund_amount > 0:
                transaction = Transaction()

                transaction.invoice_id = invoice.id
                transaction.transaction_type = TransactionType.REFUND
                transaction.amount = refund_amount
                transaction.created_by = user_id

                if customer_id is not None:
                    transaction.customer_id = customer_id

                elif supplier_id is not None:
                    transaction.supplier_id = supplier_id

                db.session.add(transaction)

                amount -= refund_amount
                return_remaining -= refund_amount

            if total_amount <= 0:
                return

            if return_remaining <= 0:
                return

            # 2. Remaining return becomes credit
            remaining_credit = return_remaining
            self.use_credit(
                remaining_credit, invoice, supplier_id, customer_id, user_id
            )

        # NORMAL PURCHASE / SALE
        invoice_remaining = Decimal(str(invoice.remaining_amount or 0))

        if invoice_remaining <= 0:
            return

        # 1. USE EXISTING CREDIT
        credit = Decimal("0")

        if supplier_id is not None:
            credit = Decimal(str(invoice.supplier.credit or 0))

        elif customer_id is not None:
            credit = Decimal(str(invoice.customer.credit or 0))

        if credit > 0:
            self.use_credit(credit, invoice, supplier_id, customer_id, user_id)

        # 2. USE ACTUAL PAYMENT
        if amount <= 0:
            return

        payment_amount = min(
            amount,
            invoice_remaining,
        )

        if payment_amount > 0:
            transaction = Transaction()

            transaction.invoice_id = invoice.id
            transaction.transaction_type = TransactionType.PAYMENT
            transaction.amount = payment_amount
            transaction.created_by = user_id

            if customer_id is not None:
                transaction.customer_id = customer_id

            elif supplier_id is not None:
                transaction.supplier_id = supplier_id

            db.session.add(transaction)

            amount -= payment_amount
            invoice_remaining -= payment_amount

        # 3. EXTRA PAYMENT GOES TO OLDER INVOICES
        if amount <= 0:
            return

        remaining_payment = amount

        previous_invoices = []

        if supplier_id is not None:
            previous_invoices.extend(
                Invoice.query.filter(
                    Invoice.supplier_id == supplier_id,
                    Invoice.invoice_type == InvoiceType.PURCHASE,
                    Invoice.status == InvoiceStatus.COMPLETED,
                    Invoice.id != invoice.id,
                )
                .order_by(
                    Invoice.invoice_date.asc(),
                    Invoice.id.asc(),
                )
                .all()
            )

        elif customer_id is not None:
            previous_invoices.extend(
                Invoice.query.filter(
                    Invoice.customer_id == customer_id,
                    Invoice.invoice_type == InvoiceType.SALE,
                    Invoice.status == InvoiceStatus.COMPLETED,
                    Invoice.id != invoice.id,
                )
                .order_by(
                    Invoice.invoice_date.asc(),
                    Invoice.id.asc(),
                )
                .all()
            )

        for previous_invoice in previous_invoices:
            if remaining_payment <= 0:
                break

            previous_remaining = Decimal(str(previous_invoice.remaining_amount or 0))

            if previous_remaining <= 0:
                continue

            payment_amount = min(
                remaining_payment,
                previous_remaining,
            )

            if payment_amount <= 0:
                continue

            transaction = Transaction()

            transaction.invoice_id = previous_invoice.id
            transaction.transaction_type = TransactionType.PAYMENT
            transaction.amount = payment_amount
            transaction.created_by = user_id

            if customer_id is not None:
                transaction.customer_id = customer_id

            elif supplier_id is not None:
                transaction.supplier_id = supplier_id

            db.session.add(transaction)

            remaining_payment -= payment_amount

    def use_credit(self, credit, invoice, supplier_id, customer_id, created_by):
        remaining_credit = credit

        match invoice.invoice_type:
            case invoice_type if invoice_type in (
                InvoiceType.SALE,
                InvoiceType.PURCHASE,
            ):
                remaining_invoice_amount = Decimal(str(invoice.remaining_amount or 0))

                # Find return invoices that generated the available credit.
                if customer_id is not None:
                    source_invoices = (
                        Invoice.query.filter(
                            Invoice.customer_id == customer_id,
                            Invoice.invoice_type == InvoiceType.SALE_RETURN,
                            Invoice.status == InvoiceStatus.COMPLETED,
                            Invoice.id != invoice.id,
                        )
                        .order_by(
                            Invoice.invoice_date.asc(),
                            Invoice.id.asc(),
                        )
                        .all()
                    )

                elif supplier_id is not None:
                    source_invoices = (
                        Invoice.query.filter(
                            Invoice.supplier_id == supplier_id,
                            Invoice.invoice_type == InvoiceType.PURCHASE_RETURN,
                            Invoice.status == InvoiceStatus.COMPLETED,
                            Invoice.id != invoice.id,
                        )
                        .order_by(
                            Invoice.invoice_date.asc(),
                            Invoice.id.asc(),
                        )
                        .all()
                    )

                else:
                    source_invoices = []

                for source_invoice in source_invoices:

                    if remaining_credit <= 0:
                        break

                    # Credit originally created by this return.
                    return_amount = Decimal(str(source_invoice.total_amount or 0))

                    # Amount already refunded from this return.
                    refunded_amount = db.session.query(
                        func.coalesce(
                            func.sum(Transaction.amount),
                            0,
                        )
                    ).filter(
                        Transaction.invoice_id == source_invoice.id,
                        Transaction.transaction_type == TransactionType.REFUND,
                    ).scalar() or Decimal(
                        "0"
                    )

                    # Amount of this return's credit already used.
                    already_used = db.session.query(
                        func.coalesce(
                            func.sum(Transaction.amount),
                            0,
                        )
                    ).filter(
                        Transaction.source_invoice_id == source_invoice.id,
                        Transaction.transaction_type == TransactionType.CREDIT_USED,
                    ).scalar() or Decimal(
                        "0"
                    )

                    available_source_credit = (
                        return_amount
                        - Decimal(str(refunded_amount))
                        - Decimal(str(already_used))
                    )

                    if available_source_credit <= 0:
                        continue

                    credit_used = min(
                        remaining_credit,
                        available_source_credit,
                        remaining_invoice_amount,
                    )

                    if credit_used <= 0:
                        continue

                    transaction = Transaction()

                    # Invoice receiving the credit.
                    transaction.invoice_id = invoice.id

                    # Return invoice that originally generated this credit.
                    transaction.source_invoice_id = source_invoice.id

                    transaction.transaction_type = TransactionType.CREDIT_USED
                    transaction.amount = credit_used
                    transaction.created_by = created_by

                    if customer_id is not None:
                        transaction.customer_id = customer_id

                    elif supplier_id is not None:
                        transaction.supplier_id = supplier_id

                    db.session.add(transaction)

                    remaining_credit -= credit_used
                    remaining_invoice_amount -= credit_used

        # Find old invoices
        if supplier_id is not None:
            previous_invoices = (
                Invoice.query.filter(
                    Invoice.supplier_id == supplier_id,
                    Invoice.invoice_type == InvoiceType.PURCHASE,
                    Invoice.status == InvoiceStatus.COMPLETED,
                    Invoice.id != invoice.id,
                )
                .order_by(
                    Invoice.invoice_date.asc(),
                    Invoice.id.asc(),
                )
                .all()
            )

        elif customer_id is not None:
            previous_invoices = (
                Invoice.query.filter(
                    Invoice.customer_id == customer_id,
                    Invoice.invoice_type == InvoiceType.SALE,
                    Invoice.status == InvoiceStatus.COMPLETED,
                    Invoice.id != invoice.id,
                )
                .order_by(
                    Invoice.invoice_date.asc(),
                    Invoice.id.asc(),
                )
                .all()
            )

        else:
            return

        # Use return credit against old invoices
        for previous_invoice in previous_invoices:
            if remaining_credit <= 0:
                break

            previous_remaining = Decimal(str(previous_invoice.remaining_amount or 0))

            if previous_remaining <= 0:
                continue

            credit_used = min(
                remaining_credit,
                previous_remaining,
            )

            if credit_used <= 0:
                continue

            transaction = Transaction()

            # Invoice receiving the credit
            transaction.invoice_id = previous_invoice.id

            # Return invoice that generated the credit
            transaction.source_invoice_id = invoice.id

            transaction.transaction_type = TransactionType.CREDIT_USED
            transaction.amount = credit_used
            transaction.created_by = created_by

            if customer_id is not None:
                transaction.customer_id = customer_id

            elif supplier_id is not None:
                transaction.supplier_id = supplier_id

            db.session.add(transaction)

            remaining_credit -= credit_used

        return
