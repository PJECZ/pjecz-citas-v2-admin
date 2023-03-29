"""
Modulos Favoritos, vistas
"""
import json

from flask import Blueprint, render_template, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from citas_admin.blueprints.usuarios.decorators import permission_required

from citas_admin.blueprints.modulos_favoritos.models import ModuloFavorito
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso

MODULO = "MODULOS"

modulos_favoritos = Blueprint("modulos_favoritos", __name__, template_folder="templates")


@modulos_favoritos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@modulos_favoritos.route("/modulos_favoritos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON de todos los modulos en navegación"""
    # Tomar parámetros de DataTables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultamos los modulos favoritos
    modulos_favoritos = {}
    consulta = ModuloFavorito.query.filter(ModuloFavorito.usuario == current_user).all()
    for modulo in consulta:
        modulos_favoritos[modulo.modulo.id] = modulo.estatus
    # Consultamos los modulos del usuario actual
    modulos = []
    for modulo in current_user.modulos_menu_principal:
        if modulo.id in modulos_favoritos:
            if modulos_favoritos[modulo.id] == "B":
                modulo.estatus = "B"
        else:
            modulo.estatus = "B"
        modulos.append(modulo)
    modulos = modulos[start : start + rows_per_page]
    total = len(current_user.modulos_menu_principal)
    # Elaborar datos para DataTable
    data = []
    for resultado in modulos:
        data.append(
            {
                "detalle": {
                    "nombre": resultado.nombre,
                    "url": url_for("modulos.detail", modulo_id=resultado.id),
                },
                "icono": resultado.icono,
                "nombre_corto": resultado.nombre_corto,
                "toggle_estatus": {
                    "id": resultado.id,
                    "estatus": resultado.estatus,
                    "url": url_for("modulos_favoritos.toggle_estatus_json", modulo_id=resultado.id),
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@modulos_favoritos.route("/modulos_favoritos")
def list_active():
    """Listado de Módulos Favoritos activos"""
    return render_template(
        "modulos_favoritos/list.jinja2",
        filtros=json.dumps({}),
        titulo="Módulos Favoritos",
        estatus="A",
    )


@modulos_favoritos.route("/modulos_favoritos/toggle_estatus_json/<int:modulo_id>", methods=["GET", "POST"])
def toggle_estatus_json(modulo_id):
    """Cambiar el estatus de un usuario-rol"""

    # Consultar ModuloFavorito
    modulo = Modulo.query.get_or_404(modulo_id)
    if modulo is None:
        return {"success": False, "message": "No encontrado"}

    # Buscar si ya está en favoritos
    modulo_favorito = ModuloFavorito.query.filter_by(usuario=current_user).filter_by(modulo=modulo).first()

    if modulo_favorito:
        # Cambiar estatus a su opuesto
        if modulo_favorito.estatus == "A":
            modulo_favorito.estatus = "B"
        else:
            modulo_favorito.estatus = "A"
    else:
        modulo_favorito = ModuloFavorito(
            modulo=modulo,
            usuario=current_user,
        )

    # Guardar
    modulo_favorito.save()

    # Entregar JSON
    return {
        "success": True,
        "message": "Activo" if modulo_favorito.estatus == "A" else "Inactivo",
        "estatus": modulo_favorito.estatus,
        "id": modulo_favorito.id,
    }
