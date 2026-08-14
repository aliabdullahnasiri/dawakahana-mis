import enum

from app.extensions.db import db
from app.models.base import Base


class StockMovementType(enum.Enum):
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    RETURN = "RETURN"
    ADJUSTMENT = "ADJUSTMENT"
    EXPIRED = "EXPIRED"


class StockMovement(Base):

    __tablename__ = "stock_movements"

    medicine_id = db.Column(db.Integer, db.ForeignKey("medicines.id"), nullable=False)

    stock_id = db.Column(db.Integer, db.ForeignKey("medicine_stock.id"), nullable=True)

    movement_type = db.Column(db.Enum(StockMovementType), nullable=False)

    quantity = db.Column(db.Integer, nullable=False)

    reference_id = db.Column(db.Integer)

    note = db.Column(db.Text)

    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    created_at = db.Column(db.DateTime, server_default=db.func.now())

    medicine = db.relationship("Medicine", backref="stock_movements")

    stock = db.relationship("MedicineStock")

    user = db.relationship("User")

    def to_dict(self):

        return {
            "medicine_id": self.medicine_id,
            "stock_id": self.stock_id,
            "movement_type": self.movement_type,
            "quantity": self.quantity,
            "reference_id": self.reference_id,
            "note": self.note,
            "created_at": self.created_at,
            **getattr(super(), "to_dict")(),
        }

    def __repr__(self):

        return (
            f"<StockMovement "
            f"medicine_id='{self.medicine_id}' "
            f"type='{self.movement_type}'>"
        )
