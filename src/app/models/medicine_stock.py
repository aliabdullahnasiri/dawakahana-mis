from app.extensions.db import db
from app.models.base import Base


class MedicineStock(Base):

    __tablename__ = "medicine_stock"

    medicine_id = db.Column(db.Integer, db.ForeignKey("medicines.id"))

    batch_number = db.Column(db.String(100))

    quantity = db.Column(db.Integer, default=0)

    purchase_price = db.Column(db.Numeric(10, 2))

    selling_price = db.Column(db.Numeric(10, 2))

    expiry_date = db.Column(db.Date)

    medicine = db.relationship("Medicine", back_populates="stocks")

    def to_dict(self) -> dict:
        return {
            "medicine_id": self.medicine_id,
            "batch_number": self.batch_number,
            "quantity": self.quantity,
            "expiry_date": self.display_expiry_date,
            "purchase_price": self.display_purchase_price,
            "selling_price": self.display_selling_price,
            **getattr(super(), "to_dict")(),
        }

    def __repr__(self):
        return (
            f"<MedicineStock medicine_id='{self.medicine_id}' "
            f"batch='{self.batch_number}'>"
        )
