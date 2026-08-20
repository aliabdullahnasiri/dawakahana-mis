from flask import render_template

from app.extensions.db import db
from app.models.base import Base


class InvoiceItem(Base):

    __tablename__ = "invoice_items"

    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=False)

    medicine_id = db.Column(db.Integer, db.ForeignKey("medicines.id"), nullable=False)

    quantity = db.Column(db.Integer, nullable=False)

    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    total_price = db.Column(db.Numeric(10, 2), nullable=False)

    batch_number = db.Column(db.String(100))

    invoice = db.relationship("Invoice", back_populates="items")

    medicine = db.relationship("Medicine")

    def to_dict(self) -> dict:
        return {
            "medicine_id": self.medicine_id,
            "medicine": render_template(
                "admin/components/tables/td/medicine.html",
                medicine=self.medicine,
            ),
            "batch_number": self.batch_number,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price or 0),
            "total_price": float(self.total_price or 0),
            "is_deletable": self.invoice.status.value != "COMPLETED",
            **getattr(super(), "to_dict")(),
        }
