from . import db # Importar la instancia de SQLAlchemy
from .models import ( # Importar todos los modelos necesarios para el seeding
    Usuario, Cliente, Telefono, Direccion,
    Producto, Subproducto, Modificacion, Precio,
    Pedido, PedidoItem, ProductoAdicional,
    MovimientoCaja, MovimientoDenominacion,
    CorteCaja, DenominacionCorteCaja, ConfiguracionSistema,
    RolUsuario # Si tienes un Enum para roles
)
from datetime import datetime, date # Importar datetime y date si se usan en los datos
from werkzeug.security import generate_password_hash # Importar si se crea un usuario admin aquí

# Importar las tablas de asociación si son necesarias para el seeding directo
# from .models import producto_modificacion_association, subproducto_modificacion_association

def seed_initial_data():
    """
    Puebla la base de datos con datos iniciales (productos, tipos cliente, etc.).
    Basado en la Sección 7 del documento de especificaciones.
    """
    print("Iniciando proceso de seeding de la base de datos...")

    # --- 7.2 Tipos de Cliente ---
    # Puedes definir los tipos de cliente aquí o usarlos directamente en los datos de Cliente
    tipos_cliente_validos = [
        'PUBLICO', 'COCINA', 'LEAL', 'ALIADO', 'MAYOREO', 'EMPLEADO', 'GENERICO_MOSTRADOR'
    ]
    # Considera añadir validación o asegurar que estos tipos existen si se usan como FK o Enum

    # --- 7.3 Formas de Pago ---
    # Puedes definir las formas de pago aquí o usarlas directamente en los datos de Pedido/MovimientoCaja
    formas_pago_validas = [
        'EFECTIVO', 'TARJETA_DEBITO', 'TARJETA_CREDITO', 'TRANSFERENCIA_BANCARIA',
        'QR_PAGO', 'CREDITO_INTERNO', 'CORTESIA', 'PAGO_MULTIPLE',
        'GASTO_INTERNO_CAJA', 'AJUSTE_INGRESO_CAJA', 'AJUSTE_EGRESO_CAJA',
        'SALDO_INICIAL_CAJA', 'RETIRO_EFECTIVO_CAJA'
    ]

    # --- 7.4 Estados de Pedido ---
    # Puedes definir los estados de pedido aquí o usarlos directamente en los datos de Pedido
    estados_pedido_validos = [
        'PENDIENTE_CONFIRMACION', 'PENDIENTE_PREPARACION', 'EN_PREPARACION',
        'LISTO_PARA_ENTREGA', 'ASIGNADO_A_REPARTIDOR', 'EN_RUTA',
        'ENTREGADO_PENDIENTE_PAGO', 'ENTREGADO_Y_PAGADO', 'PAGADO',
        'PROBLEMA_EN_ENTREGA', 'REPROGRAMADO', 'CANCELADO_POR_CLIENTE',
        'CANCELADO_POR_NEGOCIO'
    ]

    # --- 7.5 Denominaciones de Moneda (México - MXN) ---
    denominaciones_mxn = [
        0.50, 1.00, 2.00, 5.00, 10.00, 20.00, # Monedas
        20.00, 50.00, 100.00, 200.00, 500.00, 1000.00 # Billetes
    ]
    # Nota: La moneda de $20 y el billete de $20 tienen el mismo valor numérico.
    # Asegúrate de que tu lógica de conteo los maneje correctamente si es necesario diferenciarlos.

    # --- 7.1 Catálogo de Productos, Subproductos, Modificaciones y Precios ---
    # Aquí debes definir los datos estructurados según la Sección 7.1
    # Ejemplo (simplificado):

    # Productos
    productos_data = [
        {'id': 'PECH', 'nombre': 'Pechuga de Pollo', 'categoria': 'POLLO_CRUDO', 'activo': True},
        {'id': 'AL', 'nombre': 'Alas de Pollo', 'categoria': 'POLLO_CRUDO', 'activo': True},
        # ... añadir otros productos
    ]

    # Subproductos
    subproductos_data = [
        {'producto_padre_id': 'PECH', 'codigo_subprod': 'PP', 'nombre': 'Pulpa de Pechuga', 'activo': True},
        # ... añadir otros subproductos
    ]

    # Modificaciones
    modificaciones_data = [
        {'codigo_modif': 'ENT', 'nombre': 'Entera', 'activo': True},
        {'codigo_modif': 'MOLI', 'nombre': 'Molida', 'activo': True},
        # ... añadir otras modificaciones
    ]

    # Precios (ejemplo para PECH)
    precios_data = [
        # Precio Público General para Pechuga Entera
        {'producto_id': 'PECH', 'subproducto_id': None, 'tipo_cliente': 'PUBLICO', 'precio_kg': 120.00, 'cantidad_minima_kg': 0.0, 'etiqueta_promo': None, 'fecha_inicio_vigencia': None, 'fecha_fin_vigencia': None, 'activo': True},
        # Precio Mayoreo para Pechuga Entera
        {'producto_id': 'PECH', 'subproducto_id': None, 'tipo_cliente': 'MAYOREO', 'precio_kg': 100.00, 'cantidad_minima_kg': 10.0, 'etiqueta_promo': 'Precio Mayoreo (desde 10kg)', 'fecha_inicio_vigencia': None, 'fecha_fin_vigencia': None, 'activo': True},
        # ... añadir precios para otros productos/subproductos y tipos de cliente
    ]

    # Tablas de Asociación (Producto <-> Modificacion, Subproducto <-> Modificacion)
    # Debes definir qué modificaciones aplican a qué productos/subproductos.
    # Esto puede ser una lista de tuplas (producto_id, modificacion_id) o (subproducto_id, modificacion_id)
    # y luego iterar para insertar en las tablas de asociación.
    # Ejemplo (requiere obtener los IDs de las modificaciones después de crearlas):
    # producto_modificacion_links = [
    #     ('PECH', 'ENT'), ('PECH', 'MOLI'), # Pechuga puede ser Entera o Molida
    #     ('AL', 'ENT'), # Alas solo Enteras
    #     # ...
    # ]
    # subproducto_modificacion_links = [
    #     ('PP', 'MOLI'), ('PP', 'ASAR'), # Pulpa de Pechuga puede ser Molida o Para Asar
    #     # ...
    # ]


    # --- 3.16 Modelo ConfiguracionSistema ---
    # Crear la configuración inicial si no existe
    config_inicial = ConfiguracionSistema.query.get(1)
    if not config_inicial:
        config_inicial = ConfiguracionSistema(
            id=1, # Asegurar que siempre sea 1 para la fila única
            nombre_negocio='Pollería Montiel',
            direccion_negocio='Dirección de ejemplo #123',
            telefono_negocio='55 1234 5678',
            rfc_negocio=None,
            limite_items_pa_sin_comision=3,
            monto_comision_fija_pa_extra=4.0,
            mensaje_whatsapp_confirmacion='Hola {{cliente_nombre}}! Tu pedido #{{pedido_id}} de Pollería Montiel ha sido confirmado. Total: ${{pedido_total}}. Gracias!',
            porcentaje_iva=16.0,
            permitir_venta_sin_stock=True,
            ultimo_folio_pedido=0
        )
        db.session.add(config_inicial)
        print("Configuración inicial del sistema creada.")
    else:
        print("Configuración del sistema ya existe.")


    # --- Proceso de Inserción ---
    try:
        # Añadir productos
        for prod_data in productos_data:
            if not Producto.query.get(prod_data['id']):
                db.session.add(Producto(**prod_data))
        db.session.commit()
        print(f"Productos insertados/verificados: {len(productos_data)}")

        # Añadir subproductos
        for subprod_data in subproductos_data:
             # Buscar si ya existe un subproducto con el mismo codigo_subprod
            if not Subproducto.query.filter_by(codigo_subprod=subprod_data['codigo_subprod']).first():
                 db.session.add(Subproducto(**subprod_data))
        db.session.commit()
        print(f"Subproductos insertados/verificados: {len(subproductos_data)}")

        # Añadir modificaciones
        for modif_data in modificaciones_data:
            if not Modificacion.query.filter_by(codigo_modif=modif_data['codigo_modif']).first():
                db.session.add(Modificacion(**modif_data))
        db.session.commit()
        print(f"Modificaciones insertadas/verificadas: {len(modificaciones_data)}")

        # Añadir precios
        # Es más complejo manejar duplicados de precios debido a la clave compuesta
        # Una estrategia simple es borrarlos y recrearlos, o verificar cada combinación
        # Para seeding, borrar y recrear puede ser aceptable si no hay datos de producción
        # db.session.query(Precio).delete() # Descomentar con precaución!
        for precio_data in precios_data:
             # Verificar si ya existe un precio con la misma combinación de FKs y cantidad mínima
             existing_price = Precio.query.filter_by(
                 producto_id=precio_data.get('producto_id'),
                 subproducto_id=precio_data.get('subproducto_id'),
                 tipo_cliente=precio_data['tipo_cliente'],
                 cantidad_minima_kg=precio_data['cantidad_minima_kg']
             ).first()
             if not existing_price:
                 db.session.add(Precio(**precio_data))
        db.session.commit()
        print(f"Precios insertados/verificados: {len(precios_data)}")

        # Añadir enlaces de asociación (Many-to-Many)
        # Esto requiere obtener los objetos Producto, Subproducto y Modificacion
        # y añadirlos a las listas de relación.
        # Ejemplo (requiere implementar la lógica de asociación en los modelos):
        # for prod_code, modif_code in producto_modificacion_links:
        #     producto = Producto.query.get(prod_code)
        #     modificacion = Modificacion.query.filter_by(codigo_modif=modif_code).first()
        #     if producto and modificacion and modificacion not in producto.modificaciones_aplicables: # Asumiendo relación definida
        #          producto.modificaciones_aplicables.append(modificacion)
        # db.session.commit()
        # print("Enlaces Producto-Modificacion creados.")

        # for subprod_code, modif_code in subproducto_modificacion_links:
        #     subproducto = Subproducto.query.filter_by(codigo_subprod=subprod_code).first()
        #     modificacion = Modificacion.query.filter_by(codigo_modif=modif_code).first()
        #     if subproducto and modificacion and modificacion not in subproducto.modificaciones_aplicables: # Asumiendo relación definida
        #          subproducto.modificaciones_aplicables.append(modificacion)
        # db.session.commit()
        # print("Enlaces Subproducto-Modificacion creados.")


        # --- Opcional: Crear un usuario administrador por defecto si no existe ---
        # Ya tienes un comando CLI para esto, pero podrías añadir uno aquí también
        # admin_username = 'admin'
        # admin_user = Usuario.query.filter_by(username=admin_username).first()
        # if not admin_user:
        #     admin_user = Usuario(
        #         username=admin_username,
        #         password_hash=generate_password_hash('admin_password_segura'), # ¡Cambia esto en producción!
        #         nombre_completo='Administrador Inicial',
        #         rol=RolUsuario.ADMINISTRADOR.value,
        #         activo=True,
        #         fecha_creacion=datetime.utcnow()
        #     )
        #     db.session.add(admin_user)
        #     db.session.commit()
        #     print(f"Usuario administrador '{admin_username}' creado.")
        # else:
        #     print(f"Usuario administrador '{admin_username}' ya existe.")


        db.session.commit()
        print("Proceso de seeding completado.")

    except Exception as e:
        db.session.rollback()
        print(f"Error durante el seeding: {e}")
        # Considera logging más detallado del error
