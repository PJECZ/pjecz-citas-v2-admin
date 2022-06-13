"""
Clientes, formularios
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Length, Optional


class ClienteSearchForm(FlaskForm):
    """Formulario buscar Clientes"""

    email = StringField("Email", validators=[Optional(), Length(max=256)])
    nombres = StringField("Nombres", validators=[Optional()])
    apellido_primero = StringField("Apellido Primero", validators=[Optional()])
    curp = StringField("CURP", validators=[Optional(), Length(max=18)])
    buscar = SubmitField("Buscar")
