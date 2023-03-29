"""
Flask App
"""
from flask import Flask
from redis import Redis
import rq
from citas_admin.extensions import csrf, db, login_manager, moment

from citas_admin.blueprints.autoridades.views import autoridades
from citas_admin.blueprints.bitacoras.views import bitacoras
from citas_admin.blueprints.boletines.views import boletines
from citas_admin.blueprints.cit_categorias.views import cit_categorias
from citas_admin.blueprints.cit_citas.views import cit_citas
from citas_admin.blueprints.cit_citas_stats.views import cit_citas_stats
from citas_admin.blueprints.cit_citas_documentos.views import cit_citas_documentos
from citas_admin.blueprints.cit_clientes.views import cit_clientes
from citas_admin.blueprints.cit_clientes_recuperaciones.views import cit_clientes_recuperaciones
from citas_admin.blueprints.cit_clientes_registros.views import cit_clientes_registros
from citas_admin.blueprints.cit_dias_inhabiles.views import cit_dias_inhabiles
from citas_admin.blueprints.cit_horas_bloqueadas.views import cit_horas_bloqueadas
from citas_admin.blueprints.cit_oficinas_servicios.views import cit_oficinas_servicios
from citas_admin.blueprints.cit_servicios.views import cit_servicios
from citas_admin.blueprints.distritos.views import distritos
from citas_admin.blueprints.domicilios.views import domicilios
from citas_admin.blueprints.enc_encuestas.views import enc_encuestas
from citas_admin.blueprints.enc_servicios.views import enc_servicios
from citas_admin.blueprints.enc_sistemas.views import enc_sistemas
from citas_admin.blueprints.entradas_salidas.views import entradas_salidas
from citas_admin.blueprints.materias.views import materias
from citas_admin.blueprints.modulos.views import modulos
from citas_admin.blueprints.modulos_favoritos.views import modulos_favoritos
from citas_admin.blueprints.municipios.views import municipios
from citas_admin.blueprints.oficinas.views import oficinas
from citas_admin.blueprints.pag_pagos.views import pag_pagos
from citas_admin.blueprints.pag_tramites_servicios.views import pag_tramites_servicios
from citas_admin.blueprints.permisos.views import permisos
from citas_admin.blueprints.ppa_solicitudes.views import ppa_solicitudes
from citas_admin.blueprints.roles.views import roles
from citas_admin.blueprints.sistemas.views import sistemas
from citas_admin.blueprints.tareas.views import tareas
from citas_admin.blueprints.tdt_partidos.views import tdt_partidos
from citas_admin.blueprints.tdt_solicitudes.views import tdt_solicitudes
from citas_admin.blueprints.usuarios.views import usuarios
from citas_admin.blueprints.usuarios_oficinas.views import usuarios_oficinas
from citas_admin.blueprints.usuarios_roles.views import usuarios_roles

from citas_admin.blueprints.usuarios.models import Usuario


def create_app():
    """Crear app"""
    # Definir app
    app = Flask(__name__, instance_relative_config=True)
    # Cargar la configuración para producción en config/settings.py
    app.config.from_object("config.settings")
    # Cargar la configuración para desarrollo en instance/settings.py
    app.config.from_pyfile("settings.py", silent=True)
    # Redis
    app.redis = Redis.from_url(app.config["REDIS_URL"])
    app.task_queue = rq.Queue(app.config["TASK_QUEUE"], connection=app.redis, default_timeout=1920)
    # Cargar los blueprints
    app.register_blueprint(autoridades)
    app.register_blueprint(bitacoras)
    app.register_blueprint(boletines)
    app.register_blueprint(cit_categorias)
    app.register_blueprint(cit_citas)
    app.register_blueprint(cit_citas_stats)
    app.register_blueprint(cit_citas_documentos)
    app.register_blueprint(cit_clientes)
    app.register_blueprint(cit_clientes_recuperaciones)
    app.register_blueprint(cit_clientes_registros)
    app.register_blueprint(cit_dias_inhabiles)
    app.register_blueprint(cit_horas_bloqueadas)
    app.register_blueprint(cit_oficinas_servicios)
    app.register_blueprint(cit_servicios)
    app.register_blueprint(distritos)
    app.register_blueprint(domicilios)
    app.register_blueprint(enc_servicios)
    app.register_blueprint(enc_encuestas)
    app.register_blueprint(enc_sistemas)
    app.register_blueprint(entradas_salidas)
    app.register_blueprint(materias)
    app.register_blueprint(modulos)
    app.register_blueprint(modulos_favoritos)
    app.register_blueprint(municipios)
    app.register_blueprint(oficinas)
    app.register_blueprint(pag_pagos)
    app.register_blueprint(pag_tramites_servicios)
    app.register_blueprint(permisos)
    app.register_blueprint(ppa_solicitudes)
    app.register_blueprint(roles)
    app.register_blueprint(sistemas)
    app.register_blueprint(tareas)
    app.register_blueprint(tdt_partidos)
    app.register_blueprint(tdt_solicitudes)
    app.register_blueprint(usuarios)
    app.register_blueprint(usuarios_oficinas)
    app.register_blueprint(usuarios_roles)
    # Cargar las extensiones
    extensions(app)
    authentication(Usuario)
    # Entregar app
    return app


def extensions(app):
    """Incorporar las extensiones"""
    csrf.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    moment.init_app(app)


def authentication(user_model):
    """Inicializar Flask-Login"""
    login_manager.login_view = "usuarios.login"

    @login_manager.user_loader
    def load_user(uid):
        return user_model.query.get(uid)
