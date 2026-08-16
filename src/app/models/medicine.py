from app.extensions.db import db
from app.models.base import Base
from app.models.medicine_stock import MedicineStock


class Medicine(Base):
    __tablename__ = "medicines"

    barcode = db.Column(db.String(100), unique=True, index=True)

    name = db.Column(db.String(255), nullable=False)

    generic_name = db.Column(db.String(255))

    manufacturer = db.Column(db.String(255))

    strength = db.Column(db.String(100))

    description = db.Column(db.Text)

    is_active = db.Column(db.Boolean, default=True)

    stocks = db.relationship("MedicineStock", back_populates="medicine", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "barcode": self.barcode,
            "name": self.name,
            "generic_name": self.generic_name,
            "manufacturer": self.manufacturer,
            "strength": self.strength,
            "description": self.description,
            "unit_price": self.unit_price,
            "is_active": self.is_active,
            **getattr(super(), "to_dict")(),
        }

    @property
    def unit_price(self):
        stock = (
            self.stocks.filter(MedicineStock.selling_price.isnot(None))
            .order_by(MedicineStock.created_at.desc())
            .first()
        )

        if stock:
            return float(stock.selling_price)

    def __repr__(self):
        return f"<Medicine name='{self.name!r}' barcode='{self.barcode!r}'>"
