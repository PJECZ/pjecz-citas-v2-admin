"""
Cit Citas, vistas
"""
from datetime import datetime, timedelta
import json
from flask import Blueprint, flash, redirect, render_template, request, url_for, abort
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string, safe_email, safe_text

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.cit_citas.models import CitCita
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.cit_clientes.models import CitCliente
from citas_admin.blueprints.usuarios.decorators import permission_required
from citas_admin.blueprints.distritos.models import Distrito
from citas_admin.blueprints.oficinas.models import Oficina

from citas_admin.blueprints.cit_citas.forms import CitCitaSearchForm

MODULO = "CIT CITAS"

cit_citas = Blueprint("cit_citas", __name__, template_folder="templates")


@cit_citas.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_citas.route("/cit_citas/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de citas"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitCita.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "cit_cliente_id" in request.form:
        consulta = consulta.filter_by(cit_cliente_id=request.form["cit_cliente_id"])
    if "cit_cliente" in request.form:
        consulta = consulta.join(CitCliente)
        consulta = consulta.filter(CitCliente.nombres.contains(request.form["cit_cliente"]))
    if "cit_cliente_email" in request.form:
        consulta = consulta.join(CitCliente)
        consulta = consulta.filter(CitCliente.email.contains(request.form["cit_cliente_email"]))
    if "cit_servicio_id" in request.form:
        consulta = consulta.filter_by(cit_servicio_id=request.form["cit_servicio_id"])
    if "oficina_id" in request.form:
        consulta = consulta.filter_by(oficina_id=request.form["oficina_id"])
    if "fecha" in request.form and request.form["fecha"] != "":
        fecha = datetime.strptime(request.form["fecha"], "%Y-%m-%d")
        inicio_dt = datetime(year=fecha.year, month=fecha.month, day=fecha.day, hour=0, minute=0, second=0)
        termino_dt = datetime(year=fecha.year, month=fecha.month, day=fecha.day, hour=23, minute=59, second=59)
        consulta = consulta.filter(CitCita.inicio >= inicio_dt).filter(CitCita.inicio <= termino_dt)
    # Si es admin, ordenar por id, si es juzgado ordenar por fecha
    if current_user.can_admin(MODULO):
        registros = consulta.order_by(CitCita.id.desc()).offset(start).limit(rows_per_page).all()
    else:
        registros = consulta.order_by(CitCita.inicio).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for cita in registros:
        data.append(
            {
                "detalle": {
                    "id": cita.id,
                    "url": url_for("cit_citas.detail", cit_cita_id=cita.id),
                },
                "cit_cliente": {
                    "nombre": cita.cit_cliente.nombre,
                    "url": url_for("cit_clientes.detail", cit_cliente_id=cita.cit_cliente.id) if current_user.can_view("CIT CLIENTES") else "",
                },
                "cit_servicio": {
                    "clave": cita.cit_servicio.clave,
                    "url": url_for("cit_servicios.detail", cit_servicio_id=cita.cit_servicio.id) if current_user.can_view("CIT SERVICIOS") else "",
                    "descripcion": cita.cit_servicio.descripcion,
                },
                "oficina": {
                    "clave": cita.oficina.clave,
                    "url": url_for("oficinas.detail", oficina_id=cita.oficina.id) if current_user.can_view("OFICINAS") else "",
                    "descripcion": cita.oficina.descripcion,
                },
                "creado": cita.creado.strftime("%Y-%m-%d %H:%M"),
                "fecha": cita.inicio.strftime("%Y-%m-%d %H:%M"),
                "inicio": cita.inicio.strftime("%H:%M"),
                "termino": cita.termino.strftime("%H:%M"),
                "estado": cita.estado,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_citas.route("/cit_citas", methods=["POST", "GET"])
def list_active():
    """Listado de Citas activas"""
    fecha = None
    fecha_str = ""
    fecha_anterior_str = ""
    fecha_siguiente_str = ""
    # La fecha puede venir como argumento
    fecha_str = request.args.get("fecha", "")
    # Si no es administrador y no viene la fecha, se impone la fecha de hoy
    if fecha_str == "" and not current_user.can_admin(MODULO):
        fecha = datetime.now()
        fecha_str = fecha.strftime("%Y-%m-%d")
    # Al tener la fecha, se calcula la fecha anterior y siguiente
    if fecha_str != "":
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
        fecha_anterior_str = (fecha - timedelta(days=1)).strftime("%Y-%m-%d")
        fecha_siguiente_str = (fecha + timedelta(days=1)).strftime("%Y-%m-%d")
    # Si es administrador, puede ver las citas de todas las oficinas
    if current_user.can_admin(MODULO):
        return render_template(
            "cit_citas/list_admin.jinja2",
            filtros=json.dumps({"estatus": "A", "fecha": fecha_str}),
            titulo="Todas las Citas" if fecha is None else f"Todas las citas del {fecha_str}",
            estatus="A",
            fecha_actual=fecha_str,
            fecha_anterior=fecha_anterior_str,
            fecha_siguiente=fecha_siguiente_str,
        )
    # NO es administrador, entonces se filtra por su propia oficina
    return render_template(
        "cit_citas/list.jinja2",
        filtros=json.dumps({"estatus": "A", "oficina_id": current_user.oficina_id, "fecha": fecha_str}),
        titulo=f"Citas del {current_user.oficina.descripcion_corta}",
        estatus="A",
        fecha_actual=fecha_str,
        fecha_anterior=fecha_anterior_str,
        fecha_siguiente=fecha_siguiente_str,
    )


@cit_citas.route("/cit_citas/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Citas inactivas"""
    fecha = None
    fecha_str = ""
    fecha_anterior_str = ""
    fecha_siguiente_str = ""
    # La fecha puede venir como argumento
    fecha_str = request.args.get("fecha", "")
    # Si no es administrador y no viene la fecha, se impone la fecha de hoy
    if fecha_str == "" and not current_user.can_admin(MODULO):
        fecha = datetime.now()
        fecha_str = fecha.strftime("%Y-%m-%d")
    # Al tener la fecha, se calcula la fecha anterior y siguiente
    if fecha_str != "":
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
        fecha_anterior_str = (fecha - timedelta(days=1)).strftime("%Y-%m-%d")
        fecha_siguiente_str = (fecha + timedelta(days=1)).strftime("%Y-%m-%d")
    # Si es administrador, puede ver las citas de todas las oficinas
    if current_user.can_admin(MODULO):
        return render_template(
            "cit_citas/list_admin.jinja2",
            filtros=json.dumps({"estatus": "B", "fecha": fecha_str}),
            titulo="Todas las Citas eliminadas" if fecha is None else f"Todas las citas del {fecha_str}",
            estatus="B",
            fecha_anterior=fecha_anterior_str,
            fecha_siguiente=fecha_siguiente_str,
        )
    # NO es administrador, entonces se filtra por su propia oficina
    return render_template(
        "cit_citas/list.jinja2",
        filtros=json.dumps({"estatus": "B", "oficina_id": current_user.oficina_id, "fecha": fecha_str}),
        titulo=f"Citas eliminadas del {current_user.oficina.descripcion_corta}",
        estatus="B",
        fecha_actual=fecha_str,
        fecha_anterior=fecha_anterior_str,
        fecha_siguiente=fecha_siguiente_str,
    )


@cit_citas.route("/cit_citas/<int:cit_cita_id>")
def detail(cit_cita_id):
    """Detalle de una Cita"""
    cit_cita = CitCita.query.get_or_404(cit_cita_id)
    # Si es administrador, ve todas las citas
    if current_user.can_admin(MODULO):
        return render_template("cit_citas/detail.jinja2", cit_cita=cit_cita)
    # Si no es administrador, solo puede ver los detalles de una cita de su propia oficina
    if cit_cita.oficina == current_user.oficina:
        return render_template("cit_citas/detail.jinja2", cit_cita=cit_cita)
    # Si no es administrador, no puede ver los detalles de una cita de otra oficina, lo reenviamos al listado
    abort(403)


@cit_citas.route("/cit_citas/eliminar/<int:cit_cita_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(cit_cita_id):
    """Eliminar Cita"""
    cit_cita = CitCita.query.get_or_404(cit_cita_id)
    # Si no es administrador, no puede eliminar un cita de otra oficina
    if not current_user.can_admin(MODULO) and cit_cita.oficina != current_user.oficina:
        abort(403)

    if cit_cita.estatus == "A":
        cit_cita.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Cita {cit_cita.id}"),
            url=url_for("cit_citas.detail", cit_cita_id=cit_cita.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_citas.detail", cit_cita_id=cit_cita.id))


@cit_citas.route("/cit_citas/recuperar/<int:cit_cita_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(cit_cita_id):
    """Recuperar Cita"""
    cit_cita = CitCita.query.get_or_404(cit_cita_id)
    # Si no es administrador, no puede eliminar un cita de otra oficina
    if not current_user.can_admin(MODULO) and cit_cita.oficina != current_user.oficina:
        abort(403)

    if cit_cita.estatus == "B":
        cit_cita.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Cita {cit_cita.id}"),
            url=url_for("cit_citas.detail", cit_cita_id=cit_cita.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_citas.detail", cit_cita_id=cit_cita.id))


@cit_citas.route("/cit_citas/aistencia/<int:cit_cita_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def assistance(cit_cita_id):
    """Marcar Asistencia a una Cita"""
    cit_cita = CitCita.query.get_or_404(cit_cita_id)
    # Si no es administrador, no puede eliminar un cita de otra oficina
    if not current_user.can_admin(MODULO) and cit_cita.oficina != current_user.oficina:
        abort(403)

    if cit_cita.estatus == "A":
        cit_cita.estado = "ASISTIO"
        cit_cita.asistencia = True
        cit_cita.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Agregadó Asistencia a la Cita {cit_cita.id}"),
            url=url_for("cit_citas.detail", cit_cita_id=cit_cita.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_citas.detail", cit_cita_id=cit_cita.id))


@cit_citas.route("/cit_citas/pendiente/<int:cit_cita_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def pending(cit_cita_id):
    """Marcar la Cita como Pendiente"""
    cit_cita = CitCita.query.get_or_404(cit_cita_id)
    # Si no es administrador, no puede eliminar un cita de otra oficina
    if not current_user.can_admin(MODULO) and cit_cita.oficina != current_user.oficina:
        abort(403)

    if cit_cita.estatus == "A":
        cit_cita.estado = "PENDIENTE"
        cit_cita.asistencia = False
        cit_cita.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Cambiado estado de la Cita {cit_cita.id} a Pendiente"),
            url=url_for("cit_citas.detail", cit_cita_id=cit_cita.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_citas.detail", cit_cita_id=cit_cita.id))


@cit_citas.route("/cit_citas/buscar", methods=["GET", "POST"])
def search():
    """Buscar cit_citas"""
    form_search = CitCitaSearchForm()
    if form_search.validate_on_submit():
        busqueda = {"estatus": "A"}
        titulos = []

        if form_search.cliente.data:
            cliente = safe_string(form_search.cliente.data)
            if cliente != "":
                busqueda["cit_cliente"] = cliente
                titulos.append("cit_cliente " + cliente)
        if form_search.email.data:
            email = safe_text(form_search.email.data, to_uppercase=False)
            if email != "":
                busqueda["cit_cliente_email"] = email
                titulos.append("email " + email)

        return render_template(
            "cit_citas/list_search.jinja2",
            filtros=json.dumps(busqueda),
            titulo="Citas con " + ", ".join(titulos),
            estatus="A",
        )
    return render_template("cit_citas/search.jinja2", form=form_search)


@cit_citas.route("/cit_citas/distritos")
def list_distritos():
    """Listado de Distritos"""
    return render_template(
        "cit_citas/list_distritos.jinja2",
        distritos=Distrito.query.filter_by(es_distrito_judicial=True).filter_by(estatus="A").order_by(Distrito.nombre).all(),
    )


@cit_citas.route("/cit_citas/distrito/<int:distrito_id>")
def list_oficinas(distrito_id):
    """Listado de Oficinas de un distrito"""
    distrito = Distrito.query.get_or_404(distrito_id)
    return render_template(
        "cit_citas/list_oficinas.jinja2",
        distrito=distrito,
        oficinas=Oficina.query.filter(Oficina.distrito == distrito).filter_by(estatus="A").filter_by(puede_agendar_citas=True).order_by(Oficina.clave).all(),
    )


@cit_citas.route("/cit_citas/oficina/<int:oficina_id>")
def list_oficina_cit_citas(oficina_id):
    """Listado de Citas activas de una Oficina"""
    oficina = Oficina.query.get_or_404(oficina_id)
    busqueda = {"estatus": "A"}
    busqueda["oficina_id"] = oficina.id
    return render_template(
        "cit_citas/list_admin.jinja2",
        filtros=json.dumps(busqueda),
        titulo="Citas de la Oficina: " + oficina.clave,
        estatus="A",
    )
