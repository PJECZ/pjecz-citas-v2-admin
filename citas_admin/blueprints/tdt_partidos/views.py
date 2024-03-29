"""
Tres de Tres - Partidos, vistas
"""
import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required
from citas_admin.blueprints.tdt_partidos.models import TdtPartido

MODULO = "TDT PARTIDOS"

tdt_partidos = Blueprint("tdt_partidos", __name__, template_folder="templates")


@tdt_partidos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@tdt_partidos.route("/tdt_partidos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de partidos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = TdtPartido.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    registros = consulta.order_by(TdtPartido.siglas).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "siglas": resultado.siglas,
                    "url": url_for("tdt_partidos.detail", tdt_partido_id=resultado.id),
                },
                "nombre": resultado.nombre,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@tdt_partidos.route("/tdt_partidos")
def list_active():
    """Listado de partidos activos"""
    return render_template(
        "tdt_partidos/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Partidos",
        estatus="A",
    )


@tdt_partidos.route("/tdt_partidos/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Partidos inactivos"""
    return render_template(
        "tdt_partidos/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Partidos inactivos",
        estatus="B",
    )


@tdt_partidos.route("/tdt_partidos/<int:tdt_partido_id>")
def detail(tdt_partido_id):
    """Detalle de un Partido"""
    tdt_partido = TdtPartido.query.get_or_404(tdt_partido_id)
    return render_template("tdt_partidos/detail.jinja2", tdt_partido=tdt_partido)
