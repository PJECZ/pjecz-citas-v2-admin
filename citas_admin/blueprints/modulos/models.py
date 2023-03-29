"""
Modulos, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class Modulo(db.Model, UniversalMixin):
    """Modulo"""

    # Nombre de la tabla
    __tablename__ = "modulos"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Columnas
    nombre = db.Column(db.String(256), unique=True, nullable=False)
    nombre_corto = db.Column(db.String(64), nullable=False)
    icono = db.Column(db.String(48), nullable=False)
    ruta = db.Column(db.String(64), nullable=False)
    en_navegacion = db.Column(db.Boolean, nullable=False, default=True)

    # Hijos
    bitacoras = db.relationship("Bitacora", back_populates="modulo")
    modulos_favoritos = db.relationship("ModuloFavorito", back_populates="modulo")
    permisos = db.relationship("Permiso", back_populates="modulo")

    def __repr__(self):
        """Representación"""
        return f"<Modulo {self.nombre}>"
