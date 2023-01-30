"""
Pagos Pagos, modelos
"""
from collections import OrderedDict
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class PagPago(db.Model, UniversalMixin):
    """PagPago"""

    ESTADOS = OrderedDict(
        [
            ("SOLICITADO", "Solicitado"),  # Cuando se crea el pago en espera de que el banco lo procese
            ("CANCELADO", "Cancelado"),  # Cuando pasa mucho tiempo y no hay respuesta del banco, se cancela
            ("PAGADO", "Pagado"),  # Cuando el banco procesa el pago con exito
            ("FALLIDO", "Fallido"),  # Cuando el banco reporta que falla el pago
        ]
    )

    # Nombre de la tabla
    __tablename__ = "pag_pagos"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Claves foráneas
    cit_cliente_id = db.Column(db.Integer, db.ForeignKey("cit_clientes.id"), index=True, nullable=False)
    cit_cliente = db.relationship("CitCliente", back_populates="pag_pagos")
    pag_tramite_servicio_id = db.Column(db.Integer, db.ForeignKey("pag_tramites_servicios.id"), index=True, nullable=False)
    pag_tramite_servicio = db.relationship("PagTramiteServicio", back_populates="pag_pagos")

    # Columnas
    estado = db.Column(db.Enum(*ESTADOS, name="estados", native_enum=False), nullable=False)
    email = db.Column(db.String(256), nullable=False, default="", server_default="")  # Email opcional si el cliente desea que se le envie el comprobante a otra dirección
    folio = db.Column(db.String(256), nullable=False, default="", server_default="")
    total = db.Column(db.Numeric(precision=8, scale=2, decimal_return_scale=2), nullable=False)
    ya_se_envio_comprobante = db.Column(db.Boolean, nullable=False, default=False, server_default="false")

    def __repr__(self):
        """Representación"""
        return f"<PagPago {self.descripcion} ${self.total}>"
