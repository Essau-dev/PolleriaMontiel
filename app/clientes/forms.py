from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, BooleanField, DecimalField, HiddenField
from wtforms.validators import DataRequired, Length, Optional, ValidationError, Regexp
from wtforms.widgets import NumberInput # Importar NumberInput
from app.models import Cliente, TipoCliente, TipoTelefono, Direccion, TipoDireccion, Telefono # Importar modelos y Enums
from decimal import Decimal # Importar Decimal para manejar valores monetarios

class ClienteForm(FlaskForm):
    """
    Formulario para crear o editar un cliente.
    """
    nombre = StringField(
        'Nombre(s)',
        validators=[DataRequired(), Length(max=100)],
        render_kw={"placeholder": "Nombre(s) del cliente"}
    )
    apellidos = StringField(
        'Apellidos',
        validators=[Optional(), Length(max=150)],
        render_kw={"placeholder": "Apellidos del cliente (opcional)"}
    )
    alias = StringField(
        'Alias',
        validators=[Optional(), Length(max=80)],
        render_kw={"placeholder": "Apodo o nombre corto (opcional)"}
    )
    tipo_cliente = SelectField(
        'Tipo de Cliente',
        choices=[(choice.value, choice.name.replace('_', ' ').title()) for choice in TipoCliente],
        validators=[DataRequired()]
    )
    notas_cliente = TextAreaField(
        'Notas del Cliente',
        validators=[Optional(), Length(max=500)],
        render_kw={"rows": 3, "placeholder": "Preferencias, historial relevante, etc. (opcional)"}
    )
    activo = BooleanField('Cliente Activo', default=True)
    submit = SubmitField('Guardar Cliente')

    # Validación para asegurar que el alias, si se proporciona, sea único (opcional, dependiendo de la regla de negocio)
    # def validate_alias(self, alias):
    #     if alias.data:
    #         cliente = Cliente.query.filter_by(alias=alias.data).first()
    #         if cliente and (not hasattr(self, '_obj') or cliente.id != self._obj.id): # Permite editar el mismo cliente
    #             raise ValidationError('Ese alias ya está en uso. Por favor, elige otro.')


class TelefonoForm(FlaskForm):
    """
    Formulario para añadir o editar un número de teléfono para un cliente.
    """
    # cliente_id = HiddenField() # Podría ser útil si se usa en un formulario principal de cliente
    numero_telefono = StringField(
        'Número de Teléfono',
        validators=[
            DataRequired(),
            Length(max=20),
            # Añadir validación de formato básica (permite + al inicio y solo dígitos)
            Regexp(r'^\+?\d+$', message="Formato de teléfono inválido. Use solo números y opcionalmente '+' al inicio.")
        ],
        render_kw={"placeholder": "Ej. 5512345678"}
    )
    tipo_telefono = SelectField(
        'Tipo de Teléfono',
        choices=[(choice.value, choice.name.replace('_', ' ').title()) for choice in TipoTelefono],
        validators=[DataRequired()]
    )
    es_principal = BooleanField('Marcar como Teléfono Principal', default=False)
    submit = SubmitField('Guardar Teléfono')

    # Validación para asegurar que el número de teléfono sea único para este cliente (si aplica)
    # La lógica para asegurar un solo teléfono principal por cliente se manejaría en las rutas/lógica de negocio.
    # Añadir validación de unicidad a nivel de formulario para mejor UX
    def validate_numero_telefono(self, numero_telefono):
        # Esta validación asume que el formulario se usa en un contexto donde se conoce el cliente_id
        # Si el formulario se usa de forma independiente, esta validación necesitaría el cliente_id
        # Para un formulario anidado o usado en una ruta de edición/creación de cliente, se puede acceder al cliente
        # a través del objeto padre o pasándolo al formulario.
        # Ejemplo básico (requiere que el formulario tenga acceso al objeto cliente, ej. form = TelefonoForm(obj=telefono_existente)):
        # if hasattr(self, '_obj') and self._obj.cliente_id:
        #     existing_phone = Telefono.query.filter(
        #         Telefono.cliente_id == self._obj.cliente_id,
        #         Telefono.numero_telefono == numero_telefono.data,
        #         Telefono.id != self._obj.id # Excluir el teléfono actual si estamos editando
        #     ).first()
        #     if existing_phone:
        #         raise ValidationError('Este número de teléfono ya está registrado para este cliente.')
        pass # Mantener pass por ahora, la lógica de unicidad por cliente_id es más compleja sin el contexto del cliente


class DireccionForm(FlaskForm):
    """
    Formulario para añadir o editar una dirección para un cliente.
    """
    # cliente_id = HiddenField() # Podría ser útil si se usa en un formulario principal de cliente
    calle_numero = StringField(
        'Calle y Número',
        validators=[DataRequired(), Length(max=200)],
        render_kw={"placeholder": "Ej. Calle Falsa 123, Int A"}
    )
    colonia = StringField(
        'Colonia',
        validators=[Optional(), Length(max=100)],
        render_kw={"placeholder": "Ej. Centro (opcional)"}
    )
    ciudad = StringField(
        'Ciudad',
        validators=[DataRequired(), Length(max=100)],
        render_kw={"placeholder": "Ej. Ciudad Ejemplo"}
    )
    codigo_postal = StringField(
        'Código Postal',
        validators=[Optional(), Length(max=10)],
        render_kw={"placeholder": "Ej. 12345 (opcional)"}
    )
    referencias = TextAreaField(
        'Referencias',
        validators=[Optional(), Length(max=500)],
        render_kw={"rows": 3, "placeholder": "Indicaciones adicionales para la entrega (opcional)"}
    )
    tipo_direccion = SelectField(
        'Tipo de Dirección',
        choices=[(choice.value, choice.name.replace('_', ' ').title()) for choice in TipoDireccion],
        validators=[DataRequired()]
    )
    latitud = DecimalField(
        'Latitud',
        validators=[Optional()], # Considerar NumberRange si se validan rangos geográficos
        render_kw={"placeholder": "Opcional"},
        widget=NumberInput(step='0.0000001') # Permite decimales para coordenadas
    )
    longitud = DecimalField(
        'Longitud',
        validators=[Optional()], # Considerar NumberRange si se validan rangos geográficos
        render_kw={"placeholder": "Opcional"},
        widget=NumberInput(step='0.0000001') # Permite decimales para coordenadas
    )
    es_principal = BooleanField('Marcar como Dirección Principal de Entrega', default=False)
    submit = SubmitField('Guardar Dirección')

    # La lógica para asegurar una sola dirección principal por cliente se manejaría en las rutas/lógica de negocio.
