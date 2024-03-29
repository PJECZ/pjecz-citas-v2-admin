"""
Autoridades, formularios
"""
from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, SelectField, StringField, SubmitField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from citas_admin.blueprints.autoridades.models import Autoridad
from citas_admin.blueprints.distritos.models import Distrito
from citas_admin.blueprints.materias.models import Materia


def distritos_opciones():
    """Distrito: opciones para select"""
    return Distrito.query.filter_by(estatus="A").order_by(Distrito.nombre).all()


def materias_opciones():
    """Materias: opciones para select"""
    return Materia.query.filter_by(estatus="A").order_by(Materia.nombre).all()


class AutoridadNewForm(FlaskForm):
    """Formulario nueva Autoridad"""

    distrito = QuerySelectField("Departamento", query_factory=distritos_opciones, get_label="nombre", validators=[DataRequired()])
    descripcion = StringField("Descripción", validators=[DataRequired(), Length(max=256)])
    descripcion_corta = StringField("Descripción corta (máximo 64 caracteres)", validators=[DataRequired(), Length(max=64)])
    clave = StringField("Clave (única, máximo 16 caracteres)", validators=[DataRequired(), Length(max=16)])
    es_jurisdiccional = BooleanField("Es Jurisdiccional", validators=[Optional()])
    es_notaria = BooleanField("Es Notaría", validators=[Optional()])
    es_organo_especializado = BooleanField("Es Órgano Especializado", validators=[Optional()])
    organo_jurisdiccional = SelectField("Órgano Jurisdiccional", choices=Autoridad.ORGANOS_JURISDICCIONALES, validators=[DataRequired()])
    materia = QuerySelectField("Materia (si es de Primera Instancia)", query_factory=materias_opciones, get_label="nombre", validators=[DataRequired()])
    guardar = SubmitField("Guardar")


class AutoridadEditForm(FlaskForm):
    """Formulario modificar Autoridad"""

    distrito = QuerySelectField("Departamento", query_factory=distritos_opciones, get_label="nombre", validators=[DataRequired()])
    descripcion = StringField("Descripción", validators=[DataRequired(), Length(max=256)])
    descripcion_corta = StringField("Descripción corta (máximo 64 caracteres)", validators=[DataRequired(), Length(max=64)])
    clave = StringField("Clave (única, máximo 16 caracteres)", validators=[DataRequired(), Length(max=16)])
    es_jurisdiccional = BooleanField("Es Jurisdiccional", validators=[Optional()])
    es_notaria = BooleanField("Es Notaría", validators=[Optional()])
    es_organo_especializado = BooleanField("Es Órgano Especializado", validators=[Optional()])
    organo_jurisdiccional = SelectField("Órgano Jurisdiccional", choices=Autoridad.ORGANOS_JURISDICCIONALES, validators=[DataRequired()])
    materia = QuerySelectField("Materia (si es de Primera Instancia)", query_factory=materias_opciones, get_label="nombre", validators=[DataRequired()])
    guardar = SubmitField("Guardar")


class AutoridadSearchForm(FlaskForm):
    """Formulario buscar autoridades"""

    descripcion = StringField("Descripción", validators=[Optional(), Length(max=256)])
    clave = StringField("Clave (máximo 16 caracteres)", validators=[Optional(), Length(max=16)])
    organo_jurisdiccional = SelectField("Órgano Jurisdiccional", choices=Autoridad.ORGANOS_JURISDICCIONALES, validators=[Optional()])
    buscar = SubmitField("Buscar")
