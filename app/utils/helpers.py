from decimal import Decimal
from datetime import datetime, date # Importar date explícitamente
from typing import Union, List, Tuple # Importar tipos necesarios

# Importar modelos para anotaciones de tipo y acceso a Enum
# Ten cuidado con las importaciones circulares si models.py importa helpers.py
# Si models.py importa helpers.py, importa los modelos dentro de las funciones que los necesiten
# Asumiendo que models.py NO importa helpers.py, la importación a nivel superior está bien para type hints
from app.models import PedidoItem, ProductoAdicional, RolUsuario # Asumiendo que estos modelos existen y RolUsuario es un Enum

def format_currency(value: Union[Decimal, None]) -> str:
    """Formatea un valor Decimal como moneda MXN."""
    if value is None:
        return "$0.00"
    # Formato con separador de miles y 2 decimales
    # Usar f-string formatting: value:,.2f añade separador de miles
    return f"${value:,.2f}"

def format_datetime(dt: Union[datetime, None]) -> str:
    """Formatea un objeto datetime a un string legible."""
    if dt is None:
        return ""
    # Ejemplo de formato: "05/06/2025 14:30"
    return dt.strftime('%d/%m/%Y %H:%M')

def format_date(d: Union[date, None]) -> str: # Usar type hint date
    """Formatea un objeto date a un string legible."""
    if d is None:
        return ""
    # Ejemplo de formato: "05/06/2025"
    return d.strftime('%d/%m/%Y')

def format_pedido_item_description(item: Union[PedidoItem, None]) -> str:
    """Formatea la descripción de un PedidoItem para mostrar en mensajes/tickets."""
    if not item:
        return "Ítem de pedido no válido" # Manejar ítem None

    # Formatear cantidad basado en la unidad (lógica simple para kg vs otros)
    quantity_formatted = str(item.cantidad)
    if item.unidad_medida == 'kg' and item.cantidad is not None:
         # Formatear kg con 3 decimales, eliminar ceros finales y punto si es entero
         quantity_formatted = f"{item.cantidad:.3f}".rstrip('0').rstrip('.')
         if quantity_formatted == '': # Manejar caso como 0.000 -> ''
             quantity_formatted = '0'

    # Usar el helper format_currency para el subtotal
    subtotal_formatted = format_currency(item.subtotal_item)

    # Construir la cadena de descripción
    # Ejemplo: "- 1.50 kg Pechuga Entera, para Asar: $180.00"
    # Ejemplo: "- 2 pz Alas Cortadas en 2: $236.00"
    # Ejemplo: "- 0.500 kg Pulpa de Pechuga Molida: $92.50"
    return f"- {quantity_formatted} {item.unidad_medida} {item.descripcion_item_venta}: {subtotal_formatted}"

def format_producto_adicional_description(pa: Union[ProductoAdicional, None]) -> str:
    """Formatea la descripción de un ProductoAdicional para mostrar en mensajes/tickets."""
    if not pa:
        return "Producto adicional no válido" # Manejar pa None

    # Formatear cantidad basado en la unidad (lógica simple para kg vs otros)
    quantity_formatted = str(pa.cantidad_pa)
    if pa.unidad_medida_pa == 'kg' and pa.cantidad_pa is not None:
         # Formatear kg con 3 decimales, eliminar ceros finales y punto si es entero
         quantity_formatted = f"{pa.cantidad_pa:.3f}".rstrip('0').rstrip('.')
         if quantity_formatted == '': # Manejar caso como 0.000 -> ''
             quantity_formatted = '0'

    # Usar el helper format_currency para el subtotal
    subtotal_formatted = format_currency(pa.subtotal_pa)

    # Construir la cadena de descripción
    # Ejemplo: "- 1 pz Jitomate (PA): $20.00"
    # Ejemplo: "- 0.500 kg Cebolla (PA): $10.00"
    # Ejemplo: "- 1 MONTO Salsa Verde (PA): $35.00"
    return f"- {quantity_formatted} {pa.unidad_medida_pa} {pa.nombre_pa} (PA): {subtotal_formatted}"


def format_pedido_folio(pedido_id: Union[int, None]) -> str:
    """Genera un folio formateado para mostrar al usuario."""
    if pedido_id is None:
        return "N/A"
    # Prefijo y padding hardcodeados para MVP
    prefix = "PM-"
    padding = 6 # ej., PM-000123
    return f"{prefix}{pedido_id:0{padding}d}"

def format_role_name(role_value: Union[str, None]) -> str:
    """Formatea el valor del rol a un nombre legible."""
    if not role_value:
        return "Sin Rol"
    try:
        # Encontrar el miembro del Enum por su valor y formatear su nombre
        # Reemplazar guiones bajos por espacios y capitalizar cada palabra
        role_enum = RolUsuario(role_value)
        return role_enum.name.replace('_', ' ').title()
    except ValueError:
        # Manejar casos donde el role_value no es un miembro válido del enum
        # Aún intentar formatear el valor string como fallback
        return role_value.replace('_', ' ').title()

# Puedes añadir más funciones de ayuda aquí según se necesiten
# Por ejemplo, funciones para generar descripciones de ítems de pedido, etc.
