"""
Cit Tramites Servicios, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class CitTramiteServicio(db.Model, UniversalMixin):
    """CitTramiteServicio"""

    # Nombre de la tabla
    __tablename__ = "cit_tramites_servicios"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Columnas
    nombre = db.Column(db.String(256), nullable=False, unique=True)
    costo = db.Column(db.Numeric(12, 2), nullable=False)
    url = db.Column(db.String(512), nullable=False)

    # Hijos
    cit_pagos = db.relationship("CitPago", back_populates="cit_tramite_servicio")

    def __repr__(self):
        """Representación"""
        return f"<CitTramiteServicio> {self.id}"
