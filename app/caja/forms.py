# Archivo: PolleriaMontiel\app\caja\forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, DecimalField, IntegerField
from wtforms.validators import DataRequired, Length, ValidationError, Optional, NumberRange
from wtforms.widgets import NumberInput # Para campos numéricos con flechas
from app.models import TipoMovimientoCaja, FormaPago # Importar los Enums necesarios
from decimal import Decimal # Importar Decimal para manejar valores monetarios

# Lista de denominaciones de MXN para los formularios de conteo (basado en Sección 7.5)
# Usamos tuplas (valor, etiqueta)
DENOMINACIONES_MXN = [
    (1000.00, '$1000'),
    (500.00, '$500'),
    (200.00, '$200'),
    (100.00, '$100'),
    (50.00, '$50'),
    (20.00, '$20 Billete'),
    (20.00, '$20 Moneda'), # Podría requerir manejo especial si se distinguen
    (10.00, '$10'),
    (5.00, '$5'),
    (2.00, '$2'),
    (1.00, '$1'),
    (0.50, '$0.50'),
]

# Ordenar denominaciones de mayor a menor para el conteo
DENOMINACIONES_MXN_ORDENADAS = sorted(DENOMINACIONES_MXN, key=lambda x: x[0], reverse=True)


class MovimientoCajaForm(FlaskForm):
    """
    Formulario para registrar un nuevo movimiento de caja (ingreso o egreso).
    """
    tipo_movimiento = SelectField(
        'Tipo de Movimiento',
        choices=[(choice.value, choice.name.replace('_', ' ').title()) for choice in TipoMovimientoCaja],
        validators=[DataRequired()]
    )
    motivo_movimiento = StringField(
        'Motivo del Movimiento',
        validators=[DataRequired(), Length(max=255)]
        # Considerar autocompletado o SelectField con motivos comunes (Sección 7.6) a futuro
    )
    monto_movimiento = DecimalField(
        'Monto',
        validators=[DataRequired(), NumberRange(min=Decimal('0.01'), message='El monto debe ser positivo.')],
        render_kw={"placeholder": "Ej. 150.75"},
        widget=NumberInput(step='0.01') # Permite decimales en el input HTML
    )
    forma_pago_efectuado = SelectField(
        'Forma de Pago/Egreso',
        # Filtrar las formas de pago que solo aplican a pedidos si es necesario
        choices=[(choice.value, choice.name.replace('_', ' ').title()) for choice in FormaPago],
        validators=[DataRequired()]
    )
    notas_movimiento = TextAreaField(
        'Notas Adicionales',
        validators=[Optional(), Length(max=500)],
        render_kw={"rows": 3, "placeholder": "Detalles adicionales sobre el movimiento"}
    )
    submit = SubmitField('Registrar Movimiento')

    def validate_monto_movimiento(self, monto_movimiento):
        # Asegurar que el monto tenga la precisión correcta si es necesario
        if monto_movimiento.data is not None:
             monto_movimiento.data = round(monto_movimiento.data, 2)


class AperturaCajaForm(FlaskForm):
    """
    Formulario para registrar el saldo inicial al abrir la caja.
    Incluye campos para contar efectivo por denominaciones.
    """
    # Campos para la cantidad de cada denominación
    # Se generan dinámicamente basados en la lista DENOMINACIONES_MXN_ORDENADAS
    # Usamos un prefijo 'cantidad_' y reemplazamos el punto por guion bajo para el nombre del campo
    for valor, etiqueta in DENOMINACIONES_MXN_ORDENADAS:
        field_name = f'cantidad_{str(valor).replace(".", "_")}'
        setattr(
            FlaskForm,
            field_name,
            IntegerField(
                f'Cantidad de {etiqueta}',
                validators=[Optional(), NumberRange(min=0, message='La cantidad no puede ser negativa.')],
                default=0,
                widget=NumberInput(min=0)
            )
        )

    notas_apertura = TextAreaField(
        'Notas de Apertura',
        validators=[Optional(), Length(max=500)],
        render_kw={"rows": 3, "placeholder": "Observaciones sobre el estado inicial de la caja"}
    )

    submit = SubmitField('Realizar Apertura de Caja')

    def get_denominaciones_contadas(self):
        """
        Recopila las cantidades ingresadas por denominación en un diccionario.
        Retorna un diccionario {valor_denominacion: cantidad}.
        """
        contado = {}
        for valor, etiqueta in DENOMINACIONES_MXN_ORDENADAS:
            field_name = f'cantidad_{str(valor).replace(".", "_")}'
            field = getattr(self, field_name)
            if field.data is not None and field.data > 0:
                contado[Decimal(str(valor))] = field.data # Usar Decimal para el valor
        return contado

    def validate_submit(self, submit):
        """
        Validación personalizada para asegurar que se ingresó alguna cantidad de efectivo.
        """
        total_contado = Decimal('0.00')
        for valor, cantidad in self.get_denominaciones_contadas().items():
             total_contado += valor * Decimal(str(cantidad))

        if total_contado <= Decimal('0.00'):
             # Buscar un campo para asociar el error, por ejemplo, el primer campo de cantidad
             first_quantity_field_name = f'cantidad_{str(DENOMINACIONES_MXN_ORDENADAS[0][0]).replace(".", "_")}'
             first_quantity_field = getattr(self, first_quantity_field_name)
             raise ValidationError('Debe ingresar al menos una cantidad de efectivo para la apertura.')


class CierreCajaForm(FlaskForm):
    """
    Formulario para registrar el conteo final al cerrar la caja.
    Incluye campos para contar efectivo por denominaciones y notas.
    """
    # Campos para la cantidad de cada denominación (igual que Apertura)
    for valor, etiqueta in DENOMINACIONES_MXN_ORDENADAS:
        field_name = f'cantidad_{str(valor).replace(".", "_")}'
        setattr(
            FlaskForm,
            field_name,
            IntegerField(
                f'Cantidad Contada de {etiqueta}',
                validators=[Optional(), NumberRange(min=0, message='La cantidad no puede ser negativa.')],
                default=0,
                widget=NumberInput(min=0)
            )
        )

    notas_cierre = TextAreaField(
        'Notas del Corte',
        validators=[Optional(), Length(max=500)],
        render_kw={"rows": 3, "placeholder": "Observaciones sobre el corte, justificación de diferencias, etc."}
    )

    submit = SubmitField('Finalizar y Cerrar Corte')

    def get_denominaciones_contadas(self):
        """
        Recopila las cantidades ingresadas por denominación en un diccionario.
        Retorna un diccionario {valor_denominacion: cantidad}.
        """
        contado = {}
        for valor, etiqueta in DENOMINACIONES_MXN_ORDENADAS:
            field_name = f'cantidad_{str(valor).replace(".", "_")}'
            field = getattr(self, field_name)
            if field.data is not None and field.data > 0:
                contado[Decimal(str(valor))] = field.data # Usar Decimal para el valor
        return contado

    def validate_submit(self, submit):
        """
        Validación personalizada para asegurar que se ingresó alguna cantidad de efectivo.
        """
        total_contado = Decimal('0.00')
        for valor, cantidad in self.get_denominaciones_contadas().items():
             total_contado += valor * Decimal(str(cantidad))

        if total_contado <= Decimal('0.00'):
             # Buscar un campo para asociar el error, por ejemplo, el primer campo de cantidad
             first_quantity_field_name = f'cantidad_{str(DENOMINACIONES_MXN_ORDENADAS[0][0]).replace(".", "_")}'
             first_quantity_field = getattr(self, first_quantity_field_name)
             raise ValidationError('Debe ingresar al menos una cantidad de efectivo para el cierre.')
