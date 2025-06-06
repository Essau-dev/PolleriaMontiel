from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, BooleanField, DecimalField, DateField
from wtforms.validators import DataRequired, Length, Optional, ValidationError, NumberRange, Regexp
from wtforms.widgets import NumberInput
from app.models import Producto, Subproducto, Modificacion, Precio, TipoCliente # Importar modelos y Enums
from decimal import Decimal
from datetime import date # Para el default de DateField

# Definir categorías de productos (basado en Sección 7.1)
CATEGORIAS_PRODUCTO = [
    ('POLLO_CRUDO', 'Pollo Crudo'),
    ('MENUDENCIA', 'Menudencia'),
    # Añadir otras categorías si es necesario
]

class ProductoForm(FlaskForm):
    """
    Formulario para crear o editar un Producto principal.
    """
    # El ID (código) puede ser editable en creación, pero no en edición
    id = StringField(
        'Código del Producto',
        validators=[
            DataRequired(),
            Length(min=2, max=10),
            Regexp(r'^[A-Z0-9]+$', message="El código debe contener solo letras mayúsculas y números.")
        ],
        render_kw={"placeholder": "Ej. PECH, AL"}
    )
    nombre = StringField(
        'Nombre del Producto',
        validators=[DataRequired(), Length(max=100)],
        render_kw={"placeholder": "Ej. Pechuga de Pollo"}
    )
    descripcion = TextAreaField(
        'Descripción',
        validators=[Optional(), Length(max=500)],
        render_kw={"rows": 3, "placeholder": "Descripción detallada (opcional)"}
    )
    categoria = SelectField(
        'Categoría',
        choices=[(code, name) for code, name in CATEGORIAS_PRODUCTO],
        validators=[DataRequired()]
    )
    activo = BooleanField('Producto Activo', default=True)
    submit = SubmitField('Guardar Producto')

    # Validación de unicidad para el ID y nombre (se puede hacer aquí o en la ruta)
    # def validate_id(self, id):
    #     producto = Producto.query.get(id.data)
    #     if producto and (not hasattr(self, '_obj') or producto.id != self._obj.id):
    #         raise ValidationError('Este código de producto ya está en uso.')

    # def validate_nombre(self, nombre):
    #     producto = Producto.query.filter_by(nombre=nombre.data).first()
    #     if producto and (not hasattr(self, '_obj') or producto.id != self._obj.id):
    #         raise ValidationError('Este nombre de producto ya está en uso.')


class SubproductoForm(FlaskForm):
    """
    Formulario para crear o editar un Subproducto.
    """
    # Campo para seleccionar el Producto padre (se poblará dinámicamente)
    producto_padre_id = SelectField(
        'Producto Padre',
        coerce=str, # El ID del Producto es String
        validators=[DataRequired()],
        # Las choices se poblarán dinámicamente en la ruta con Productos activos
        choices=[('', 'Seleccionar Producto Padre')] # Opción por defecto
    )
    codigo_subprod = StringField(
        'Código del Subproducto',
        validators=[
            DataRequired(),
            Length(min=2, max=15),
            Regexp(r'^[A-Z0-9\-]+$', message="El código debe contener solo letras mayúsculas, números y guiones.")
        ],
        render_kw={"placeholder": "Ej. PP, CD, M-PM"}
    )
    nombre = StringField(
        'Nombre del Subproducto',
        validators=[DataRequired(), Length(max=100)],
        render_kw={"placeholder": "Ej. Pulpa de Pechuga"}
    )
    descripcion = TextAreaField(
        'Descripción',
        validators=[Optional(), Length(max=500)],
        render_kw={"rows": 3, "placeholder": "Descripción detallada (opcional)"}
    )
    activo = BooleanField('Subproducto Activo', default=True)
    submit = SubmitField('Guardar Subproducto')

    # Validación de unicidad para el código (se puede hacer aquí o en la ruta)
    # def validate_codigo_subprod(self, codigo_subprod):
    #     subproducto = Subproducto.query.filter_by(codigo_subprod=codigo_subprod.data).first()
    #     if subproducto and (not hasattr(self, '_obj') or subproducto.id != self._obj.id):
    #         raise ValidationError('Este código de subproducto ya está en uso.')


class ModificacionForm(FlaskForm):
    """
    Formulario para crear o editar una Modificación.
    """
    codigo_modif = StringField(
        'Código de Modificación',
        validators=[
            DataRequired(),
            Length(min=2, max=20),
            Regexp(r'^[A-Z0-9\_]+$', message="El código debe contener solo letras mayúsculas, números y guiones bajos.")
        ],
        render_kw={"placeholder": "Ej. MOLI, ASAR_PECH"}
    )
    nombre = StringField(
        'Nombre de Modificación',
        validators=[DataRequired(), Length(max=100)],
        render_kw={"placeholder": "Ej. Molida, Para Asar (Pechuga)"}
    )
    descripcion = TextAreaField(
        'Descripción',
        validators=[Optional(), Length(max=500)],
        render_kw={"rows": 3, "placeholder": "Descripción detallada (opcional)"}
    )
    activo = BooleanField('Modificación Activa', default=True)
    submit = SubmitField('Guardar Modificación')

    # Validación de unicidad para el código (se puede hacer aquí o en la ruta)
    # def validate_codigo_modif(self, codigo_modif):
    #     modificacion = Modificacion.query.filter_by(codigo_modif=codigo_modif.data).first()
    #     if modificacion and (not hasattr(self, '_obj') or modificacion.id != self._obj.id):
    #         raise ValidationError('Este código de modificación ya está en uso.')


class PrecioForm(FlaskForm):
    """
    Formulario para crear o editar un registro de Precio.
    Define el precio para un Producto O un Subproducto.
    """
    # Campos para seleccionar el Producto o Subproducto (se poblarán dinámicamente)
    # Usamos SelectField con Optional para permitir que uno sea None
    producto_id = SelectField(
        'Producto Base',
        coerce=str, # El ID del Producto es String
        validators=[Optional()],
        # Las choices se poblarán dinámicamente en la ruta con Productos activos
        choices=[('', 'Seleccionar Producto')] # Opción por defecto
    )
    subproducto_id = SelectField(
        'Subproducto Base',
        coerce=int, # El ID del Subproducto es Integer
        validators=[Optional()],
        # Las choices se poblarán dinámicamente en la ruta con Subproductos activos
        choices=[(0, 'Seleccionar Subproducto')] # Opción por defecto (0 para Integer)
    )

    tipo_cliente = SelectField(
        'Tipo de Cliente',
        choices=[(choice.value, choice.name.replace('_', ' ').title()) for choice in TipoCliente],
        validators=[DataRequired()]
    )

    precio_kg = DecimalField(
        'Precio por Kg',
        validators=[DataRequired(), NumberRange(min=Decimal('0.00'), message='El precio no puede ser negativo.')],
        render_kw={"placeholder": "Ej. 120.50"},
        widget=NumberInput(step='0.01')
    )

    cantidad_minima_kg = DecimalField(
        'Cantidad Mínima (Kg)',
        validators=[DataRequired(), NumberRange(min=Decimal('0.00'), message='La cantidad mínima no puede ser negativa.')],
        default=Decimal('0.00'),
        render_kw={"placeholder": "Ej. 2.000 (0 para precio general)"},
        widget=NumberInput(step='0.001')
    )

    etiqueta_promo = StringField(
        'Etiqueta de Promoción',
        validators=[Optional(), Length(max=100)],
        render_kw={"placeholder": "Ej. Promo 2kg (opcional)"}
    )

    fecha_inicio_vigencia = DateField(
        'Fecha Inicio Vigencia',
        validators=[Optional()],
        format='%Y-%m-%d', # Formato compatible con input type="date"
        render_kw={"placeholder": "AAAA-MM-DD"}
    )

    fecha_fin_vigencia = DateField(
        'Fecha Fin Vigencia',
        validators=[Optional()],
        format='%Y-%m-%d', # Formato compatible con input type="date"
        render_kw={"placeholder": "AAAA-MM-DD"}
    )

    activo = BooleanField('Precio Activo', default=True)

    submit = SubmitField('Guardar Precio')

    # Validación personalizada para asegurar que se selecciona UN Producto O UN Subproducto
    def validate(self):
        if not FlaskForm.validate(self):
            return False

        producto_selected = self.producto_id.data and self.producto_id.data != ''
        subproducto_selected = self.subproducto_id.data and self.subproducto_id.data != 0 # 0 es el valor por defecto para SelectField con coerce=int

        if not producto_selected and not subproducto_selected:
            self.producto_id.errors.append('Debe seleccionar un Producto o un Subproducto.')
            self.subproducto_id.errors.append('Debe seleccionar un Producto o un Subproducto.')
            return False

        if producto_selected and subproducto_selected:
            self.producto_id.errors.append('No puede seleccionar un Producto y un Subproducto al mismo tiempo.')
            self.subproducto_id.errors.append('No puede seleccionar un Producto y un Subproducto al mismo tiempo.')
            return False

        # Opcional: Validar que los IDs seleccionados existan en la BD
        # if producto_selected:
        #     producto = Producto.query.get(self.producto_id.data)
        #     if not producto:
        #          self.producto_id.errors.append('Producto seleccionado no válido.')
        #          return False
        # if subproducto_selected:
        #     subproducto = Subproducto.query.get(self.subproducto_id.data)
        #     if not subproducto:
        #          self.subproducto_id.errors.append('Subproducto seleccionado no válido.')
        #          return False

        return True

    # Validación de unicidad para la combinación producto/subproducto, tipo_cliente y cantidad_minima_kg
    # Esta validación es más compleja y se manejaría mejor en la lógica de negocio/ruta
    # def validate_cantidad_minima_kg(self, cantidad_minima_kg):
    #     query = Precio.query.filter_by(
    #         tipo_cliente=self.tipo_cliente.data,
    #         cantidad_minima_kg=cantidad_minima_kg.data
    #     )
    #     if self.producto_id.data and self.producto_id.data != '':
    #         query = query.filter_by(producto_id=self.producto_id.data)
    #     elif self.subproducto_id.data and self.subproducto_id.data != 0:
    #         query = query.filter_by(subproducto_id=self.subproducto_id.data)
    #     else:
    #         # Esto no debería pasar si validate() funciona, pero por seguridad
    #         return

    #     existing_price = query.first()
    #     if existing_price and (not hasattr(self, '_obj') or existing_price.id != self._obj.id):
    #         raise ValidationError('Ya existe un precio para esta combinación de producto/subproducto, tipo de cliente y cantidad mínima.')
