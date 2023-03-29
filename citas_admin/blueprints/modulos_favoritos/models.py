"""
Modulos Favoritos, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class ModuloFavorito(db.Model, UniversalMixin):
    """Modulo"""

    # Nombre de la tabla
    __tablename__ = "modulos_favoritos"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Clave foránea
    modulo_id = db.Column(db.Integer, db.ForeignKey("modulos.id"), index=True, nullable=False)
    modulo = db.relationship("Modulo", back_populates="modulos_favoritos")
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), index=True, nullable=False)
    usuario = db.relationship("Usuario", back_populates="modulos_favoritos")

    def __repr__(self):
        """Representación"""
        return f"<Módulo Favorito {self.nombre}>"
