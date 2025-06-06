---
applyTo: '**'
---
## 1. Introducción y Propósito

Este documento sirve como la **guía central y única fuente de verdad (Single Source of Truth - SSoT)** para el desarrollo del **Sistema de Gestión para Pollería Montiel (SGPM)**, en su fase de **Producto Mínimo Viable (MVP)**. Su propósito es detallar de manera exhaustiva los requisitos funcionales, la lógica de negocio específica de Pollería Montiel, los modelos de datos precisos, los flujos de usuario críticos y las directrices de interfaz y experiencia de usuario. El objetivo final es asegurar un desarrollo consistente, de alta calidad y perfectamente alineado con las necesidades operativas y estratégicas del negocio.

# Idioma
Manten la interaccion con el usuario en español.

**Objetivos Principales del Sistema MVP (SGPM):**

El SGPM MVP se centrará en digitalizar y optimizar las operaciones diarias clave de Pollería Montiel, buscando:

1.  **Agilizar la Toma y Gestión de Pedidos:**
    *   Capturar eficientemente pedidos tanto en **mostrador** (venta rápida) como para **reparto a domicilio**.
    *   Permitir la selección detallada de productos, incluyendo **subproductos** (ej. Pulpa de Pechuga) y **modificaciones** (ej. "para asar", "molida").
    *   Facilitar la inclusión de **Productos Adicionales (PAs)** (ej. refrescos, verduras compradas al momento) con cálculo de comisión si aplica.
2.  **Optimizar la Gestión de Clientes:**
    *   Mantener una base de datos de clientes con información de contacto (múltiples teléfonos y direcciones).
    *   Identificar **tipos de cliente** para aplicar precios y promociones diferenciadas (ej. Público, Cocina, Leal).
    *   (Futuro MVP+) Rastrear historial de pedidos por cliente.
3.  **Controlar el Catálogo de Productos y Precios:**
    *   Administrar un catálogo detallado de productos de pollo, subproductos y modificaciones permitidas.
    *   Gestionar una estructura de **precios dinámica** basada en el tipo de cliente y, opcionalmente, en cantidades mínimas (promociones).
    *   Utilizar una **simbología interna** (ej. PECH, AL, PP) para una rápida identificación.
4.  **Fortalecer el Control de Caja y Flujo de Efectivo:**
    *   Registrar de forma precisa todos los **ingresos** (ventas, otros) y **egresos** (compra de PAs, cambio para repartidores, gastos operativos menores).
    *   Implementar un sistema de **apertura de caja** con saldo inicial detallado por denominaciones.
    *   Facilitar **cortes de caja** diarios, comparando el saldo teórico con el conteo físico de efectivo (desglosado por denominaciones) para identificar diferencias.
    *   Gestionar el flujo de efectivo específico para **PAs en pedidos a domicilio** (egreso para compra, egreso para cambio del repartidor, ingreso del total al retorno).
5.  **Mejorar la Visibilidad Operativa:**
    *   Proveer **reportes básicos** sobre ventas diarias, movimientos de caja y productos más vendidos.
    *   Ofrecer una visión clara del **estado de los pedidos** (ej. Pendiente, En Preparación, En Ruta, Entregado).
6.  **Establecer Roles y Seguridad:**
    *   Definir roles de usuario claros (`Administrador`, `Cajero`, `Tablajero`, `Repartidor`) con permisos específicos para proteger la información y las funcionalidades.

**Enfoque de Desarrollo:**

El desarrollo del SGPM se guiará por los siguientes principios:

*   **Mobile First:** El diseño y la funcionalidad priorizarán la experiencia en dispositivos móviles (smartphones y tablets), dado que gran parte de la operación (toma de pedidos por WhatsApp, gestión de repartidores) se beneficia de esta aproximación. La interfaz será responsiva para adaptarse también a pantallas de escritorio.
*   **Modular y Escalable:** La arquitectura del software se diseñará en módulos cohesivos y débilmente acoplados, utilizando Blueprints en Flask. Esto facilitará el mantenimiento, las pruebas y la adición de nuevas funcionalidades en el futuro sin afectar drásticamente el sistema existente.
*   **Centrado en el Usuario (UX):** Aunque es un sistema interno, se buscará una interfaz intuitiva, eficiente y fácil de usar para minimizar la curva de aprendizaje y reducir errores operativos. Se considerarán los flujos de trabajo actuales de Pollería Montiel.
*   **Iterativo e Incremental:** Siguiendo las fases definidas, se entregarán funcionalidades de forma progresiva, permitiendo validación y retroalimentación temprana.
*   **Stack Tecnológico Principal (MVP):**
    *   **Backend:** Python (versión 3.8+) con el microframework Flask.
    *   **ORM:** SQLAlchemy para la interacción con la base de datos.
    *   **Base de Datos:** SQLite para el MVP por su simplicidad y facilidad de configuración. (Se considerará PostgreSQL para fases de producción más robustas).
    *   **Motor de Plantillas:** Jinja2 integrado en Flask.
    *   **Frontend:** HTML5 semántico, CSS3 personalizado (siguiendo `estilo.css` y variables CSS definidas), y JavaScript (Vanilla JS ES6+) para interactividad del lado del cliente y comunicación AJAX.
    *   **Gestión de Formularios:** Flask-WTF para la creación y validación de formularios.
    *   **Autenticación y Sesiones:** Mecanismos de Flask (ej. Flask-Login).
    *   **Servidor de Desarrollo:** Werkzeug (integrado en Flask).
    *   **Servidor de Producción (Consideración):** Gunicorn + Nginx.
    *   **Control de Versiones:** Git, con un repositorio centralizado (ej. GitHub).

**Alcance del MVP:**

El MVP se enfocará en las funcionalidades esenciales descritas en los objetivos anteriores. Características más avanzadas como gestión de inventario detallado, programas de lealtad complejos, integraciones con plataformas de contabilidad externas, o analítica avanzada se considerarán para fases post-MVP. El objetivo principal del MVP es tener un sistema funcional que cubra el ciclo de vida completo de un pedido y el control de caja asociado.

**Sección 2: Roles de Usuario y Permisos**.

Aquí detallaremos cada rol, sus responsabilidades dentro del sistema y los permisos específicos que tendrán sobre los diferentes módulos y entidades. Esto es fundamental para la seguridad y para que Copilot entienda quién puede hacer qué.

---

## 2. Roles de Usuario y Permisos

El Sistema de Gestión para Pollería Montiel (SGPM) implementará un sistema de control de acceso basado en roles (RBAC). Cada usuario del sistema será asignado a un rol específico que determinará las funcionalidades y datos a los que puede acceder y las acciones que puede realizar.

Los roles definidos para el MVP son:

*   Administrador (`ADMINISTRADOR`)
*   Cajero (`CAJERO`)
*   Tablajero (`TABLAJERO`)
*   Repartidor (`REPARTIDOR`)

A continuación, se detalla cada rol y sus permisos asociados. Las operaciones CRUD se refieren a Crear (Create), Leer (Read), Actualizar (Update) y Eliminar (Delete).

### 2.1 Administrador (`ADMINISTRADOR`)

*   **Descripción del Rol:**
    El Administrador posee el nivel más alto de acceso y control sobre el SGPM. Es responsable de la configuración general del sistema, la gestión de todos los usuarios, la supervisión completa de las operaciones, la auditoría y la resolución de problemas. Generalmente, este rol será asignado a los propietarios o gerentes principales de Pollería Montiel (ej. Rosy, Essaú).
*   **Permisos Específicos:**

    | Módulo / Entidad             | Crear (C) | Leer (R)    | Actualizar (U) | Eliminar (D) | Acciones Específicas Adicionales                                                                                                |
    |------------------------------|-----------|-------------|----------------|--------------|---------------------------------------------------------------------------------------------------------------------------------|
    | **Usuarios del Sistema**     | Sí        | Todos       | Todos          | Todos        | Asignar/cambiar roles, Activar/Desactivar usuarios, Resetear contraseñas.                                                       |
    | **Clientes**                 | Sí        | Todos       | Todos          | Todos        | Ver historial completo de pedidos del cliente.                                                                                  |
    | **Productos (Catálogo)**     | Sí        | Todos       | Todos          | Todos        | Definir productos, subproductos, modificaciones.                                                                                |
    | **Precios**                  | Sí        | Todos       | Todos          | Todos        | Establecer y modificar precios por tipo de cliente y promociones.                                                               |
    | **Pedidos**                  | Sí        | Todos       | Todos          | Todos        | Crear pedidos, modificar cualquier campo de cualquier pedido (incl. ítems, precios manuales si es necesario), cancelar cualquier pedido en cualquier estado, cambiar estado de cualquier pedido. |
    | **Productos Adicionales (PAs)**| Sí        | Todos       | Todos          | Todos        | Definir reglas de comisión para PAs (si aplica).                                                                                |
    | **Movimientos de Caja**      | Sí        | Todos       | Todos          | Sí (con log) | Registrar cualquier tipo de ingreso/egreso, realizar ajustes.                                                                  |
    | **Cortes de Caja**           | Sí        | Todos       | Sí (reabrir)   | Sí (con log) | Realizar apertura, realizar y finalizar cortes de caja, ver historial de cortes, aprobar diferencias.                             |
    | **Reportes**                 | N/A       | Todos       | N/A            | N/A          | Acceso a todos los reportes generados por el sistema (ventas, caja, productos, clientes, etc.). Exportar reportes.               |
    | **Configuración del Sistema**| Sí        | Sí          | Sí             | Sí           | Modificar parámetros globales (nombre pollería, % comisión PAs, plantillas de mensajes, denominaciones aceptadas, etc.).         |

### 2.2 Cajero (`CAJERO`)

*   **Descripción del Rol:**
    El Cajero es el usuario principal del punto de venta. Responsable de tomar pedidos (mostrador y domicilio), procesar pagos, gestionar el flujo de efectivo de su turno, y realizar el conteo para el corte de caja. Este rol es fundamental para la operación diaria. (ej. Monserrath).
*   **Permisos Específicos:**

    | Módulo / Entidad             | Crear (C) | Leer (R)                      | Actualizar (U)                                     | Eliminar (D) | Acciones Específicas Adicionales                                                                                                |
    |------------------------------|-----------|-------------------------------|----------------------------------------------------|--------------|---------------------------------------------------------------------------------------------------------------------------------|
    | **Usuarios del Sistema**     | No        | Propio perfil                 | Propia contraseña                                  | No           |                                                                                                                                 |
    | **Clientes**                 | Sí        | Todos (búsqueda y selección)  | Existentes (datos contacto, dirección)             | No           | Ver historial de pedidos recientes del cliente seleccionado. No debe ver costos o información sensible de otros módulos.            |
    | **Productos (Catálogo)**     | No        | Todos (para seleccionar)      | No                                                 | No           | Ver precios aplicables al cliente/pedido actual.                                                                                |
    | **Precios**                  | No        | Aplicables al contexto        | No                                                 | No           |                                                                                                                                 |
    | **Pedidos**                  | Sí        | Pedidos del día/turno, activos| Propios o no asignados: ítems (antes de finalizar), estado (a 'EN_PREPARACION', 'LISTO_PARA_ENTREGA', 'ASIGNADO_REPARTIDOR'), forma de pago, Paga Con. | No (finalizados) | Asignar repartidor (si no hay rol específico de despachador). Generar ticket/nota. Enviar mensaje WhatsApp de confirmación. |
    | **Productos Adicionales (PAs)**| Sí        | En sus pedidos                | En sus pedidos (antes de finalizar)                | En sus pedidos (antes de finalizar) | Registrar costo de compra de PA (si es responsable de adquirirlo).                                                        |
    | **Movimientos de Caja**      | Sí (limitado) | Propios del turno/día         | No                                                 | No           | Registrar INGRESO por venta. Registrar EGRESO para compra de PAs (con autorización), EGRESO para cambio a repartidor.           |
    | **Cortes de Caja**           | No (directo) | Saldos actuales de su caja  | No                                                 | No           | Realizar APERTURA de su caja (registrar saldo inicial). Realizar CONTEO para el corte de caja.                                   |
    | **Reportes**                 | N/A       | Ventas del día/turno, Movimientos de caja propios | N/A                                                 | N/A          |                                                                                                                                 |
    | **Configuración del Sistema**| No        | No                            | No                                                 | No           |                                                                                                                                 |

### 2.3 Tablajero (`TABLAJERO`)

*   **Descripción del Rol:**
    El Tablajero es responsable de la preparación física de los productos de pollo según las especificaciones de los pedidos. Su interacción con el sistema se centra en visualizar los pedidos pendientes de preparación y marcar su progreso. (Rol con funcionalidad inicial más limitada en el MVP, enfocada en la visualización y actualización de estados).
*   **Permisos Específicos:**

    | Módulo / Entidad             | Crear (C) | Leer (R)                                 | Actualizar (U)                                       | Eliminar (D) | Acciones Específicas Adicionales                                                                                                |
    |------------------------------|-----------|------------------------------------------|------------------------------------------------------|--------------|---------------------------------------------------------------------------------------------------------------------------------|
    | **Usuarios del Sistema**     | No        | Propio perfil                            | Propia contraseña                                    | No           |                                                                                                                                 |
    | **Clientes**                 | No        | No (o solo nombre en pedido)             | No                                                   | No           |                                                                                                                                 |
    | **Productos (Catálogo)**     | No        | Todos (para referencia de preparación)   | No                                                   | No           | Ver detalles de modificaciones.                                                                                                 |
    | **Precios**                  | No        | No                                       | No                                                   | No           |                                                                                                                                 |
    | **Pedidos**                  | No        | Pedidos con estado 'PENDIENTE_PREPARACION' o 'EN_PREPARACION' | Estado del pedido/ítem a 'PREPARADO_LISTO_ENTREGA'. | No           | Ver detalle de ítems y sus modificaciones. Imprimir comanda de preparación.                                                    |
    | **Productos Adicionales (PAs)**| No        | En pedidos a preparar                    | No (o marcar como 'conseguido' si es responsable)    | No           |                                                                                                                                 |
    | **Movimientos de Caja**      | No        | No                                       | No                                                   | No           |                                                                                                                                 |
    | **Cortes de Caja**           | No        | No                                       | No                                                   | No           |                                                                                                                                 |
    | **Reportes**                 | N/A       | No (o reportes de producción si se implementan) | N/A                                                 | N/A          |                                                                                                                                 |
    | **Configuración del Sistema**| No        | No                                       | No                                                   | No           |                                                                                                                                 |

### 2.4 Repartidor (`REPARTIDOR`)

*   **Descripción del Rol:**
    El Repartidor es responsable de la entrega física de los pedidos a domicilio. Interactúa con el sistema para ver los pedidos que tiene asignados, actualizar su estado durante la entrega y registrar la liquidación del efectivo al regresar. (ej. Leticia).
*   **Permisos Específicos:**

    | Módulo / Entidad             | Crear (C) | Leer (R)                                     | Actualizar (U)                                                                 | Eliminar (D) | Acciones Específicas Adicionales                                                                                                |
    |------------------------------|-----------|----------------------------------------------|--------------------------------------------------------------------------------|--------------|---------------------------------------------------------------------------------------------------------------------------------|
    | **Usuarios del Sistema**     | No        | Propio perfil                                | Propia contraseña                                                              | No           |                                                                                                                                 |
    | **Clientes**                 | No        | Datos del cliente del pedido asignado (nombre, dirección, teléfono) | No                                                                             | No           |                                                                                                                                 |
    | **Productos (Catálogo)**     | No        | No (o solo nombres en el ticket del pedido)  | No                                                                             | No           |                                                                                                                                 |
    | **Precios**                  | No        | No                                           | No                                                                             | No           |                                                                                                                                 |
    | **Pedidos**                  | No        | Pedidos asignados a él con estado 'ASIGNADO_REPARTIDOR' o 'EN_RUTA' | Estado del pedido ('EN_RUTA', 'ENTREGADO', 'PROBLEMA_ENTREGA', 'PAGADO_AL_REPARTIDOR'). Notas de entrega. | No           | Ver detalle del pedido (ítems, total a cobrar, dirección). Posiblemente interactuar con mapa (futuro).                         |
    | **Productos Adicionales (PAs)**| No        | En sus pedidos asignados                     | No                                                                             | No           |                                                                                                                                 |
    | **Movimientos de Caja**      | Sí (limitado) | Propios (liquidaciones)                    | No                                                                             | No           | Registrar INGRESO por liquidación de pedidos entregados (detallando el efectivo y cambio devuelto). Solicitar cambio al Cajero. |
    | **Cortes de Caja**           | No        | No                                           | No                                                                             | No           |                                                                                                                                 |
    | **Reportes**                 | N/A       | Resumen de sus entregas del día (si aplica)  | N/A                                                                             | N/A          |                                                                                                                                 |
    | **Configuración del Sistema**| No        | No                                           | No                                                                             | No           |                                                                                                                                 |

**Notas Generales sobre Permisos:**

*   **Herencia:** No se contempla herencia compleja de roles en el MVP. Los permisos son explícitos por rol.
*   **Denegación Predeterminada:** Cualquier acción no explícitamente permitida para un rol se considera denegada.
*   **Auditoría:** Se recomienda que las acciones críticas (Crear, Actualizar, Eliminar en módulos sensibles como Pedidos, Caja, Productos) generen un log de auditoría (quién, qué, cuándo), especialmente para el rol de Administrador. Esto podría ser una tabla `AuditLog` o integrado en los modelos mismos con campos como `creado_por_id`, `actualizado_por_id`.



## 3. Modelos de Datos (Esquema de Base de Datos Detallado)

A continuación, se describen las tablas (clases de modelo SQLAlchemy) que conformarán la base de datos del Sistema de Gestión para Pollería Montiel (SGPM). Para cada modelo, se especifican sus atributos, tipos de datos, restricciones principales y relaciones con otros modelos.

**Convenciones:**

*   **Nombres de Tabla/Clase:** `PascalCase` para nombres de clase, `snake_case` y plural para nombres de tabla (ej. clase `PedidoItem`, tabla `pedido_items`). SQLAlchemy puede manejar esto automáticamente.
*   **Claves Primarias (PK):** Generalmente un campo `id` de tipo `Integer` autoincremental.
*   **Claves Foráneas (FK):** Nombradas como `nombretablaorigen_id` (ej. `cliente_id` en la tabla `Pedido`).
*   **Tipos de Datos SQLAlchemy:** Se usarán los tipos estándar de SQLAlchemy (`db.Integer`, `db.String`, `db.Float`, `db.Boolean`, `db.DateTime`, `db.Text`, `db.Date`).
*   **Valores por Defecto:** Especificados donde aplique (ej. `default=datetime.utcnow`).
*   **Relaciones:** Se describirán usando la sintaxis de `db.relationship`, especificando `backref` o `back_populates` para la navegación bidireccional y `lazy` para la estrategia de carga.
*   **Nulabilidad:** `nullable=False` implica que el campo es obligatorio.
*   **Índices:** `index=True` se añadirá a campos que se usarán frecuentemente en búsquedas o joins para optimizar el rendimiento.

---

### 3.1 Modelo `Usuario`

*   **Nombre de Tabla (sugerido):** `usuarios`
*   **Clase SQLAlchemy:** `Usuario`
*   **Descripción:** Almacena la información de los empleados que pueden acceder y operar el sistema.
*   ---
*   | Columna         | Tipo (SQLAlchemy) | Restricciones                             | Default           | Índice | Descripción                                      |
*   |-----------------|-------------------|-------------------------------------------|-------------------|--------|--------------------------------------------------|
*   | `id`            | `db.Integer`      | `primary_key=True`                        |                   |        | Identificador único del usuario.                 |
*   | `username`      | `db.String(80)`   | `nullable=False, unique=True`             |                   | `True` | Nombre de usuario para el login.                 |
*   | `password_hash` | `db.String(256)`  | `nullable=False`                          |                   |        | Hash de la contraseña (no almacenar en texto plano).|
*   | `nombre_completo`| `db.String(150)` | `nullable=False`                          |                   |        | Nombre real del empleado.                        |
*   | `rol`           | `db.String(30)`   | `nullable=False`                          |                   | `True` | Rol del usuario (ej. 'ADMINISTRADOR', 'CAJERO'). |
*   | `activo`        | `db.Boolean`      | `nullable=False`                          | `True`            | `True` | Indica si el usuario puede iniciar sesión.        |
*   | `fecha_creacion`| `db.DateTime`     | `nullable=False`                          | `datetime.utcnow` |        | Fecha y hora de creación del registro.           |
*   | `ultimo_login`  | `db.DateTime`     | `nullable=True`                           |                   |        | Fecha y hora del último inicio de sesión.         |
*   ---
*   **Relaciones:**
    *   `pedidos_registrados = db.relationship('Pedido', foreign_keys='Pedido.usuario_id', back_populates='usuario_creador', lazy='dynamic')`
    *   `pedidos_asignados_repartidor = db.relationship('Pedido', foreign_keys='Pedido.repartidor_id', back_populates='repartidor_asignado', lazy='dynamic')`
    *   `movimientos_caja_registrados = db.relationship('MovimientoCaja', back_populates='usuario_responsable', lazy='dynamic')`
    *   `cortes_caja_realizados = db.relationship('CorteCaja', back_populates='usuario_responsable_corte', lazy='dynamic')`
*   **Métodos Sugeridos:**
    *   `set_password(self, password)`: Para generar el hash de la contraseña.
    *   `check_password(self, password)`: Para verificar la contraseña durante el login.
    *   `is_admin(self)`, `is_cajero(self)`, etc.: Métodos helper para verificar roles.

---

### 3.2 Modelo `Cliente`

*   **Nombre de Tabla (sugerido):** `clientes`
*   **Clase SQLAlchemy:** `Cliente`
*   **Descripción:** Almacena la información de los clientes de Pollería Montiel.
*   ---
*   | Columna        | Tipo (SQLAlchemy) | Restricciones                             | Default           | Índice | Descripción                                       |
*   |----------------|-------------------|-------------------------------------------|-------------------|--------|---------------------------------------------------|
*   | `id`           | `db.Integer`      | `primary_key=True`                        |                   |        | Identificador único del cliente.                  |
*   | `nombre`       | `db.String(100)`  | `nullable=False`                          |                   | `True` | Nombre(s) del cliente.                            |
*   | `apellidos`    | `db.String(150)`  | `nullable=True`                           |                   | `True` | Apellidos del cliente.                            |
*   | `alias`        | `db.String(80)`   | `nullable=True`                           |                   | `True` | Apodo o nombre corto para identificación rápida. |
*   | `tipo_cliente` | `db.String(50)`   | `nullable=False`                          | `'PUBLICO'`       | `True` | Tipo de cliente (ej. 'PUBLICO', 'COCINA').      |
*   | `notas_cliente`| `db.Text`         | `nullable=True`                           |                   |        | Preferencias, historial relevante, etc.           |
*   | `fecha_registro`| `db.DateTime`    | `nullable=False`                          | `datetime.utcnow` |        | Fecha de alta del cliente.                        |
*   | `activo`       | `db.Boolean`      | `nullable=False`                          | `True`            | `True` | Si el cliente está activo en el sistema.          |
*   ---
*   **Relaciones:**
    *   `telefonos = db.relationship('Telefono', back_populates='cliente', lazy='dynamic', cascade='all, delete-orphan')`
    *   `direcciones = db.relationship('Direccion', back_populates='cliente', lazy='dynamic', cascade='all, delete-orphan')`
    *   `pedidos = db.relationship('Pedido', back_populates='cliente', lazy='dynamic')`
*   **Métodos Sugeridos:**
    *   `get_nombre_completo(self)`: Retorna nombre y apellidos concatenados.
    *   `get_telefono_principal(self)`: Retorna el teléfono marcado como principal.
    *   `get_direccion_principal(self)`: Retorna la dirección marcada como principal.

---

### 3.3 Modelo `Telefono`

*   **Nombre de Tabla (sugerido):** `telefonos_cliente`
*   **Clase SQLAlchemy:** `Telefono`
*   **Descripción:** Almacena los números de teléfono asociados a un cliente. Un cliente puede tener múltiples teléfonos.
*   ---
*   | Columna         | Tipo (SQLAlchemy) | Restricciones                               | Default     | Índice | Descripción                                          |
*   |-----------------|-------------------|---------------------------------------------|-------------|--------|------------------------------------------------------|
*   | `id`            | `db.Integer`      | `primary_key=True`                          |             |        | Identificador único del teléfono.                    |
*   | `cliente_id`    | `db.Integer`      | `db.ForeignKey('clientes.id'), nullable=False`|             | `True` | FK al cliente al que pertenece el teléfono.          |
*   | `numero_telefono`| `db.String(20)`  | `nullable=False`                            |             | `True` | Número de teléfono.                                  |
*   | `tipo_telefono` | `db.String(30)`   | `nullable=False`                            | `'CELULAR'` | `True` | Tipo (ej. 'CELULAR', 'WHATSAPP', 'CASA', 'NEGOCIO').|
*   | `es_principal`  | `db.Boolean`      | `nullable=False`                            | `False`     | `True` | Indica si es el teléfono principal de contacto.       |
*   ---
*   **Relaciones:**
    *   `cliente = db.relationship('Cliente', back_populates='telefonos')`
*   **Constraints:**
    *   Considerar un `UniqueConstraint('cliente_id', 'numero_telefono')` para evitar duplicados por cliente.
    *   Lógica a nivel de aplicación para asegurar que solo un teléfono por cliente sea `es_principal=True`.

---

### 3.4 Modelo `Direccion`

*   **Nombre de Tabla (sugerido):** `direcciones_cliente`
*   **Clase SQLAlchemy:** `Direccion`
*   **Descripción:** Almacena las direcciones asociadas a un cliente. Un cliente puede tener múltiples direcciones.
*   ---
*   | Columna         | Tipo (SQLAlchemy) | Restricciones                               | Default    | Índice | Descripción                                            |
*   |-----------------|-------------------|---------------------------------------------|------------|--------|--------------------------------------------------------|
*   | `id`            | `db.Integer`      | `primary_key=True`                          |            |        | Identificador único de la dirección.                   |
*   | `cliente_id`    | `db.Integer`      | `db.ForeignKey('clientes.id'), nullable=False`|            | `True` | FK al cliente al que pertenece la dirección.           |
*   | `calle_numero`  | `db.String(200)`  | `nullable=False`                            |            |        | Calle, número exterior e interior.                     |
*   | `colonia`       | `db.String(100)`  | `nullable=True`                             |            | `True` | Colonia o barrio.                                      |
*   | `ciudad`        | `db.String(100)`  | `nullable=False`                            |            | `True` | Ciudad o municipio.                                    |
*   | `codigo_postal` | `db.String(10)`   | `nullable=True`                             |            | `True` | Código Postal.                                         |
*   | `referencias`   | `db.Text`         | `nullable=True`                             |            |        | Indicaciones adicionales para la entrega (color casa, etc.). |
*   | `tipo_direccion`| `db.String(30)`   | `nullable=False`                            | `'CASA'`   | `True` | Tipo (ej. 'CASA', 'NEGOCIO', 'ENTREGA_PRINCIPAL').   |
*   | `latitud`       | `db.Float`        | `nullable=True`                             |            |        | Coordenada de latitud (opcional).                      |
*   | `longitud`      | `db.Float`        | `nullable=True`                             |            |        | Coordenada de longitud (opcional).                     |
*   | `es_principal`  | `db.Boolean`      | `nullable=False`                            | `False`    | `True` | Indica si es la dirección principal de entrega.        |
*   ---
*   **Relaciones:**
    *   `cliente = db.relationship('Cliente', back_populates='direcciones')`
*   **Constraints:**
    *   Lógica a nivel de aplicación para asegurar que solo una dirección por cliente sea `es_principal=True`.

---

### 3.5 Modelo `Producto`

*   **Nombre de Tabla (sugerido):** `productos`
*   **Clase SQLAlchemy:** `Producto`
*   **Descripción:** Catálogo de los productos principales de pollo que ofrece la pollería (ej. Pechuga, Alas).
*   ---
*   | Columna       | Tipo (SQLAlchemy) | Restricciones                             | Default | Índice | Descripción                                        |
*   |---------------|-------------------|-------------------------------------------|---------|--------|----------------------------------------------------|
*   | `id`          | `db.String(10)`   | `primary_key=True`                        |         |        | Código único del producto (simbología, ej. 'PECH').|
*   | `nombre`      | `db.String(100)`  | `nullable=False, unique=True`             |         | `True` | Nombre descriptivo del producto (ej. Pechuga).       |
*   | `descripcion` | `db.Text`         | `nullable=True`                           |         |        | Descripción más detallada si es necesario.         |
*   | `categoria`   | `db.String(50)`   | `nullable=False`                          |         | `True` | Categoría del producto (ej. 'POLLO_CRUDO', 'MENUDENCIA'). |
*   | `activo`      | `db.Boolean`      | `nullable=False`                          | `True`  | `True` | Si el producto está disponible para la venta.      |
*   ---
*   **Relaciones:**
    *   `subproductos = db.relationship('Subproducto', back_populates='producto_padre', lazy='dynamic', cascade='all, delete-orphan')`
    *   `modificaciones_directas = db.relationship('Modificacion', secondary='producto_modificacion_association', back_populates='productos_asociados', lazy='dynamic')` (Tabla de asociación `producto_modificacion_association`)
    *   `precios = db.relationship('Precio', foreign_keys='Precio.producto_id', back_populates='producto_base', lazy='dynamic', cascade='all, delete-orphan')`
    *   `items_pedido = db.relationship('PedidoItem', foreign_keys='PedidoItem.producto_id', back_populates='producto', lazy='dynamic')`

---

### 3.6 Modelo `Subproducto`

*   **Nombre de Tabla (sugerido):** `subproductos`
*   **Clase SQLAlchemy:** `Subproducto`
*   **Descripción:** Partes o derivados específicos de un `Producto` principal (ej. Pulpa de Pechuga de Pechuga), o "Especiales" que son variantes (ej. Cadera de Retazo).
*   ---
*   | Columna         | Tipo (SQLAlchemy) | Restricciones                                  | Default | Índice | Descripción                                                  |
*   |-----------------|-------------------|------------------------------------------------|---------|--------|--------------------------------------------------------------|
*   | `id`            | `db.Integer`      | `primary_key=True`                             |         |        | Identificador numérico único del subproducto.               |
*   | `producto_padre_id`|`db.String(10)`| `db.ForeignKey('productos.id'), nullable=False`  |         | `True` | FK al `Producto` principal al que pertenece.                 |
*   | `codigo_subprod`| `db.String(15)`   | `nullable=False, unique=True`                  |         | `True` | Código único del subproducto (ej. 'PP', 'PG', 'CD').         |
*   | `nombre`        | `db.String(100)`  | `nullable=False`                               |         | `True` | Nombre descriptivo del subproducto (ej. Pulpa de Pechuga).   |
*   | `descripcion`   | `db.Text`         | `nullable=True`                                |         |        |                                                              |
*   | `activo`        | `db.Boolean`      | `nullable=False`                               | `True`  | `True` | Si el subproducto está disponible para la venta.             |
*   ---
*   **Relaciones:**
    *   `producto_padre = db.relationship('Producto', back_populates='subproductos')`
    *   `modificaciones_aplicables = db.relationship('Modificacion', secondary='subproducto_modificacion_association', back_populates='subproductos_asociados', lazy='dynamic')` (Tabla de asociación `subproducto_modificacion_association`)
    *   `precios = db.relationship('Precio', foreign_keys='Precio.subproducto_id', back_populates='subproducto_base', lazy='dynamic', cascade='all, delete-orphan')`
    *   `items_pedido = db.relationship('PedidoItem', foreign_keys='PedidoItem.subproducto_id', back_populates='subproducto', lazy='dynamic')`

---

### 3.7 Modelo `Modificacion`

*   **Nombre de Tabla (sugerido):** `modificaciones`
*   **Clase SQLAlchemy:** `Modificacion`
*   **Descripción:** Las diferentes preparaciones, cortes o presentaciones que se pueden aplicar a un `Producto` o `Subproducto` (ej. Entera, Molida, Para Asar).
*   ---
*   | Columna      | Tipo (SQLAlchemy) | Restricciones                        | Default | Índice | Descripción                                          |
*   |--------------|-------------------|--------------------------------------|---------|--------|------------------------------------------------------|
*   | `id`         | `db.Integer`      | `primary_key=True`                   |         |        | Identificador numérico único de la modificación.     |
*   | `codigo_modif`|`db.String(20)`  | `nullable=False, unique=True`        |         | `True` | Código corto de la modificación (ej. 'MOLI', 'ASAR').|
*   | `nombre`     | `db.String(100)`  | `nullable=False`                     |         | `True` | Nombre descriptivo (ej. Molida, Para Asar).          |
*   | `descripcion`| `db.Text`         | `nullable=True`                      |         |        |                                                      |
*   | `activo`     | `db.Boolean`      | `nullable=False`                     | `True`  | `True` | Si esta modificación está disponible.                |
*   ---
*   **Relaciones:**
    *   `productos_asociados = db.relationship('Producto', secondary='producto_modificacion_association', back_populates='modificaciones_directas', lazy='dynamic')`
    *   `subproductos_asociados = db.relationship('Subproducto', secondary='subproducto_modificacion_association', back_populates='modificaciones_aplicables', lazy='dynamic')`
    *   `items_pedido = db.relationship('PedidoItem', back_populates='modificacion_aplicada', lazy='dynamic')`

---

**Tablas de Asociación para Modificaciones (Many-to-Many):**

*   **`producto_modificacion_association`**
    *   `producto_id`: `db.String(10)`, `db.ForeignKey('productos.id')`, `primary_key=True`
    *   `modificacion_id`: `db.Integer`, `db.ForeignKey('modificaciones.id')`, `primary_key=True`

*   **`subproducto_modificacion_association`**
    *   `subproducto_id`: `db.Integer`, `db.ForeignKey('subproductos.id')`, `primary_key=True`
    *   `modificacion_id`: `db.Integer`, `db.ForeignKey('modificaciones.id')`, `primary_key=True`

---

### 3.8 Modelo `Precio`

*   **Nombre de Tabla (sugerido):** `precios`
*   **Clase SQLAlchemy:** `Precio`
*   **Descripción:** Define el precio de un `Producto` o `Subproducto` específico, considerando el `tipo_cliente` y una posible `cantidad_minima` para promociones.
*   ---
*   | Columna          | Tipo (SQLAlchemy) | Restricciones                                      | Default | Índice | Descripción                                                                  |
*   |------------------|-------------------|----------------------------------------------------|---------|--------|------------------------------------------------------------------------------|
*   | `id`             | `db.Integer`      | `primary_key=True`                                 |         |        | Identificador único del registro de precio.                                  |
*   | `producto_id`    | `db.String(10)`   | `db.ForeignKey('productos.id'), nullable=True`     |         | `True` | FK a `Producto` si el precio es para un producto base.                       |
*   | `subproducto_id` | `db.Integer`      | `db.ForeignKey('subproductos.id'), nullable=True`  |         | `True` | FK a `Subproducto` si el precio es para un subproducto.                    |
*   | `tipo_cliente`   | `db.String(50)`   | `nullable=False`                                   |         | `True` | Tipo de cliente al que aplica este precio.                                   |
*   | `precio_kg`      | `db.Float`        | `nullable=False`                                   |         |        | Precio por kilogramo (o unidad base).                                        |
*   | `cantidad_minima_kg`| `db.Float`     | `nullable=False`                                   | `0.0`   | `True` | Cantidad mínima en kg para que este precio aplique (0 si es general).        |
*   | `etiqueta_promo` | `db.String(100)`  | `nullable=True`                                    |         |        | Etiqueta descriptiva para la promoción (ej. "Promo 2kg", "Precio Especial"). |
*   | `fecha_inicio_vigencia`| `db.Date`   | `nullable=True`                                    |         | `True` | Fecha de inicio de validez del precio (opcional).                            |
*   | `fecha_fin_vigencia`| `db.Date`      | `nullable=True`                                    |         | `True` | Fecha de fin de validez del precio (opcional).                               |
*   | `activo`         | `db.Boolean`      | `nullable=False`                                   | `True`  | `True` | Si este registro de precio está activo.                                      |
*   ---
*   **Relaciones:**
    *   `producto_base = db.relationship('Producto', foreign_keys=[producto_id], back_populates='precios')`
    *   `subproducto_base = db.relationship('Subproducto', foreign_keys=[subproducto_id], back_populates='precios')`
*   **Constraints:**
    *   `db.CheckConstraint('(producto_id IS NOT NULL AND subproducto_id IS NULL) OR (producto_id IS NULL AND subproducto_id IS NOT NULL)', name='chk_precio_target')` (Debe aplicar a un producto O a un subproducto, no a ambos ni a ninguno).
    *   `db.UniqueConstraint('producto_id', 'tipo_cliente', 'cantidad_minima_kg', name='uq_precio_prod')`
    *   `db.UniqueConstraint('subproducto_id', 'tipo_cliente', 'cantidad_minima_kg', name='uq_precio_subprod')`
---

### 3.9 Modelo `Pedido`

*   **Nombre de Tabla (sugerido):** `pedidos`
*   **Clase SQLAlchemy:** `Pedido`
*   **Descripción:** Registra cada transacción de venta o solicitud de productos, tanto para mostrador como para domicilio. Es una entidad central que agrupa la información del cliente, los ítems, los pagos y el estado de la orden.
*   ---
*   | Columna                | Tipo (SQLAlchemy) | Restricciones                                    | Default           | Índice | Descripción                                                                                                |
*   |------------------------|-------------------|--------------------------------------------------|-------------------|--------|------------------------------------------------------------------------------------------------------------|
*   | `id`                   | `db.Integer`      | `primary_key=True`                               |                   |        | Identificador único del pedido. Podría ser un número de folio consecutivo.                               |
*   | `cliente_id`           | `db.Integer`      | `db.ForeignKey('clientes.id'), nullable=True`    |                   | `True` | FK al cliente. Nulo si es una venta de mostrador genérica sin identificación de cliente.                  |
*   | `usuario_id`           | `db.Integer`      | `db.ForeignKey('usuarios.id'), nullable=False`   |                   | `True` | FK al `Usuario` (Cajero/Admin) que registró el pedido.                                                   |
*   | `repartidor_id`        | `db.Integer`      | `db.ForeignKey('usuarios.id'), nullable=True`    |                   | `True` | FK al `Usuario` (Repartidor) asignado para la entrega, si `tipo_venta` es 'DOMICILIO'.                   |
*   | `direccion_entrega_id` | `db.Integer`      | `db.ForeignKey('direcciones_cliente.id'), nullable=True` |        | `True` | FK a la `Direccion` de entrega, si `tipo_venta` es 'DOMICILIO' y el cliente tiene direcciones.           |
*   | `tipo_venta`           | `db.String(20)`   | `nullable=False`                                 |                   | `True` | Tipo de venta: 'MOSTRADOR', 'DOMICILIO'.                                                                   |
*   | `forma_pago`           | `db.String(50)`   | `nullable=True`                                  |                   | `True` | Forma de pago principal (ej. 'EFECTIVO', 'TARJETA_DEBITO', 'TRANSFERENCIA', 'CREDITO_INTERNO').           |
*   | `paga_con`             | `db.Float`        | `nullable=True`                                  |                   |        | Monto con el que el cliente paga (relevante para pagos en efectivo que requieren cambio).                   |
*   | `cambio_entregado`     | `db.Float`        | `nullable=True`                                  |                   |        | Monto del cambio devuelto al cliente.                                                                      |
*   | `subtotal_productos_pollo`| `db.Float`     | `nullable=False`                                 | `0.0`             |        | Suma de los subtotales de todos los `PedidoItem` (productos de pollo).                                   |
*   | `subtotal_productos_adicionales`| `db.Float`| `nullable=False`                                 | `0.0`             |        | Suma de los subtotales de todos los `ProductoAdicional`.                                                  |
*   | `descuento_aplicado`   | `db.Float`        | `nullable=False`                                 | `0.0`             |        | Monto total de descuentos aplicados al pedido (si aplica).                                                 |
*   | `costo_envio`          | `db.Float`        | `nullable=False`                                 | `0.0`             |        | Costo de envío si aplica (para pedidos a domicilio).                                                       |
*   | `total_pedido`         | `db.Float`        | `nullable=False`                                 | `0.0`             | `True` | Monto final a pagar: `(subtotal_productos_pollo + subtotal_productos_adicionales + costo_envio) - descuento_aplicado`. |
*   | `estado_pedido`        | `db.String(30)`   | `nullable=False`                                 | `'PENDIENTE_CONFIRMACION'` | `True` | Estado actual del pedido (ver sección 7.4 para valores).                                                  |
*   | `notas_pedido`         | `db.Text`         | `nullable=True`                                  |                   |        | Observaciones generales sobre el pedido (ej. "Cliente pide llamar antes de entregar").                   |
*   | `fecha_creacion`       | `db.DateTime`     | `nullable=False`                                 | `datetime.utcnow` | `True` | Fecha y hora de creación del pedido.                                                                       |
*   | `fecha_actualizacion`  | `db.DateTime`     | `nullable=False`                                 | `datetime.utcnow` | `True` | Fecha y hora de la última modificación (usar `onupdate=datetime.utcnow`).                                 |
*   | `fecha_entrega_programada`| `db.DateTime`  | `nullable=True`                                  |                   | `True` | Fecha y hora programada para la entrega (para pedidos a domicilio).                                        |
*   | `requiere_factura`     | `db.Boolean`      | `nullable=False`                                 | `False`           |        | Indica si el cliente solicitó factura para este pedido.                                                    |
*   ---
*   **Relaciones:**
    *   `cliente = db.relationship('Cliente', back_populates='pedidos')`
    *   `usuario_creador = db.relationship('Usuario', foreign_keys=[usuario_id], back_populates='pedidos_registrados')`
    *   `repartidor_asignado = db.relationship('Usuario', foreign_keys=[repartidor_id], back_populates='pedidos_asignados_repartidor')`
    *   `direccion_entrega = db.relationship('Direccion')`
    *   `items = db.relationship('PedidoItem', back_populates='pedido', lazy='dynamic', cascade='all, delete-orphan')`
    *   `productos_adicionales_pedido = db.relationship('ProductoAdicional', back_populates='pedido', lazy='dynamic', cascade='all, delete-orphan')`
    *   `movimientos_caja_asociados = db.relationship('MovimientoCaja', back_populates='pedido_asociado', lazy='dynamic')`
*   **Métodos Sugeridos:**
    *   `calcular_totales()`: Método para recalcular `subtotal_productos_pollo`, `subtotal_productos_adicionales` y `total_pedido` basado en sus ítems y PAs.
    *   `puede_ser_modificado()`: Lógica para determinar si el pedido aún puede ser modificado según su estado.
    *   `generar_folio_display()`: Para mostrar un folio formateado (ej. PM-000123).

---

### 3.10 Modelo `PedidoItem`

*   **Nombre de Tabla (sugerido):** `pedido_items`
*   **Clase SQLAlchemy:** `PedidoItem`
*   **Descripción:** Detalla cada producto de pollo (ya sea un `Producto` base o un `Subproducto`) incluido en un `Pedido`, junto con su cantidad, modificación aplicada y precio al momento de la venta.
*   ---
*   | Columna              | Tipo (SQLAlchemy) | Restricciones                                     | Default | Índice | Descripción                                                                                                   |
*   |----------------------|-------------------|---------------------------------------------------|---------|--------|---------------------------------------------------------------------------------------------------------------|
*   | `id`                 | `db.Integer`      | `primary_key=True`                                |         |        | Identificador único del ítem dentro del pedido.                                                               |
*   | `pedido_id`          | `db.Integer`      | `db.ForeignKey('pedidos.id'), nullable=False`     |         | `True` | FK al `Pedido` al que pertenece este ítem.                                                                    |
*   | `producto_id`        | `db.String(10)`   | `db.ForeignKey('productos.id'), nullable=True`    |         | `True` | FK al `Producto` base, si este ítem se refiere a un producto principal.                                       |
*   | `subproducto_id`     | `db.Integer`      | `db.ForeignKey('subproductos.id'), nullable=True` |         | `True` | FK al `Subproducto`, si este ítem se refiere a un subproducto específico.                                     |
*   | `modificacion_id`    | `db.Integer`      | `db.ForeignKey('modificaciones.id'), nullable=True`|        | `True` | FK a la `Modificacion` aplicada a este producto/subproducto.                                                  |
*   | `descripcion_item_venta`| `db.String(255)`| `nullable=False`                                  |         |        | Descripción consolidada y textual del ítem como se vendió (ej. "Pechuga Entera, para Asar", "1/2kg Pulpa de Pernil Molida"). |
*   | `cantidad`           | `db.Float`        | `nullable=False`                                  |         |        | Cantidad del producto/subproducto.                                                                            |
*   | `unidad_medida`      | `db.String(10)`   | `nullable=False`                                  | `'kg'`  |        | Unidad de medida para la `cantidad` (ej. 'kg', 'pieza', 'paquete').                                           |
*   | `precio_unitario_venta`| `db.Float`      | `nullable=False`                                  |         |        | Precio por `unidad_medida` al momento de la venta (puede incluir ajustes o ser el precio de catálogo).          |
*   | `subtotal_item`      | `db.Float`        | `nullable=False`                                  |         |        | Calculado como `cantidad * precio_unitario_venta`.                                                            |
*   | `notas_item`         | `db.Text`         | `nullable=True`                                   |         |        | Notas específicas para este ítem en el pedido (ej. "Cortar en trozos pequeños", "Piel bien dorada").          |
*   | `costo_unitario_item`| `db.Float`        | `nullable=True`                                   |         |        | (Opcional, para análisis de rentabilidad futuro) Costo del producto para la pollería.                         |
*   ---
*   **Relaciones:**
    *   `pedido = db.relationship('Pedido', back_populates='items')`
    *   `producto = db.relationship('Producto', foreign_keys=[producto_id], back_populates='items_pedido')`
    *   `subproducto = db.relationship('Subproducto', foreign_keys=[subproducto_id], back_populates='items_pedido')`
    *   `modificacion_aplicada = db.relationship('Modificacion', back_populates='items_pedido')`
*   **Constraints:**
    *   `db.CheckConstraint('(producto_id IS NOT NULL AND subproducto_id IS NULL) OR (producto_id IS NULL AND subproducto_id IS NOT NULL) OR (producto_id IS NOT NULL AND subproducto_id IS NOT NULL)', name='chk_pedidoitem_target')`
        *   Lógica: Un ítem debe referenciar a un `producto_id` O a un `subproducto_id`. Si es un `subproducto_id`, `producto_id` DEBERÍA ser el padre de ese subproducto para consistencia, aunque el constraint solo valida que al menos uno esté presente. La lógica de la aplicación debe asegurar la correcta asignación.
*   **Métodos Sugeridos:**
    *   `actualizar_subtotal()`: Recalcula `subtotal_item`.

---

### 3.11 Modelo `ProductoAdicional`

*   **Nombre de Tabla (sugerido):** `pedido_productos_adicionales`
*   **Clase SQLAlchemy:** `ProductoAdicional`
*   **Descripción:** Registra ítems que no forman parte del catálogo de pollo principal y que se añaden a un pedido específico. Estos pueden ser comprados al momento o tener precios variables (ej. verduras, refrescos, carbón).
*   ---
*   | Columna             | Tipo (SQLAlchemy) | Restricciones                                  | Default | Índice | Descripción                                                                                                |
*   |---------------------|-------------------|------------------------------------------------|---------|--------|------------------------------------------------------------------------------------------------------------|
*   | `id`                | `db.Integer`      | `primary_key=True`                             |         |        | Identificador único del producto adicional en el pedido.                                                   |
*   | `pedido_id`         | `db.Integer`      | `db.ForeignKey('pedidos.id'), nullable=False`  |         | `True` | FK al `Pedido` al que pertenece.                                                                           |
*   | `nombre_pa`         | `db.String(150)`  | `nullable=False`                               |         | `True` | Nombre descriptivo del PA (ej. "Jitomate Saladet", "Coca-Cola 600ml", "$30 de Cebolla").                  |
*   | `cantidad_pa`       | `db.Float`        | `nullable=False`                               | `1.0`   |        | Cantidad del PA. Si `unidad_medida_pa` es 'MONTO', este campo suele ser 1.                               |
*   | `unidad_medida_pa`  | `db.String(20)`   | `nullable=False`                               |         |        | Unidad de medida (ej. 'kg', 'pieza', 'litro', 'paquete', 'MONTO').                                         |
*   | `costo_compra_unitario_pa`| `db.Float`  | `nullable=True`                                |         |        | Costo al que la pollería adquirió el PA por unidad (si aplica y se rastrea).                               |
*   | `precio_venta_unitario_pa`| `db.Float`| `nullable=False`                                 |         |        | Precio al que se vende el PA al cliente por unidad. Si `unidad_medida_pa` es 'MONTO', este es el total.   |
*   | `subtotal_pa`       | `db.Float`        | `nullable=False`                               |         |        | Calculado como `cantidad_pa * precio_venta_unitario_pa`.                                                   |
*   | `comision_calculada_pa`| `db.Float`     | `nullable=True`                                |         |        | Monto de comisión aplicado a este PA (si la lógica de comisiones está activa).                             |
*   | `notas_pa`          | `db.Text`         | `nullable=True`                                |         |        |                                                                                                            |
*   ---
*   **Relaciones:**
    *   `pedido = db.relationship('Pedido', back_populates='productos_adicionales_pedido')`
*   **Métodos Sugeridos:**
    *   `calcular_subtotal_pa()`: Recalcula `subtotal_pa`.

---

### 3.12 Modelo `MovimientoCaja`

*   **Nombre de Tabla (sugerido):** `movimientos_caja`
*   **Clase SQLAlchemy:** `MovimientoCaja`
*   **Descripción:** Registra todas las entradas (ingresos) y salidas (egresos) de dinero de la caja, proporcionando trazabilidad para cada transacción financiera.
*   ---
*   | Columna             | Tipo (SQLAlchemy) | Restricciones                                  | Default           | Índice | Descripción                                                                                                      |
*   |---------------------|-------------------|------------------------------------------------|-------------------|--------|------------------------------------------------------------------------------------------------------------------|
*   | `id`                | `db.Integer`      | `primary_key=True`                             |                   |        | Identificador único del movimiento de caja.                                                                      |
*   | `usuario_id`        | `db.Integer`      | `db.ForeignKey('usuarios.id'), nullable=False` |                   | `True` | FK al `Usuario` que registró o es responsable del movimiento.                                                    |
*   | `pedido_id`         | `db.Integer`      | `db.ForeignKey('pedidos.id'), nullable=True`   |                   | `True` | FK al `Pedido` asociado, si el movimiento está directamente relacionado (ej. cobro de venta, egreso para PAs).  |
*   | `corte_caja_id`     | `db.Integer`      | `db.ForeignKey('cortes_caja.id'), nullable=True`|                  | `True` | FK al `CorteCaja` al que pertenece este movimiento, una vez que el corte se realiza.                             |
*   | `tipo_movimiento`   | `db.String(20)`   | `nullable=False`                               |                   | `True` | Tipo de movimiento: 'INGRESO', 'EGRESO'.                                                                         |
*   | `motivo_movimiento` | `db.String(255)`  | `nullable=False`                               |                   |        | Descripción clara del motivo (ej. "Venta Pedido #123", "Compra PA: Jitomate Ped#123", "Retiro Parcial", "Saldo Inicial"). |
*   | `monto_movimiento`  | `db.Float`        | `nullable=False`                               |                   | `True` | Monto del movimiento. Se registra siempre como valor absoluto; `tipo_movimiento` indica si suma o resta.        |
*   | `forma_pago_efectuado`| `db.String(50)` | `nullable=False`                               |                   | `True` | Forma de pago/recepción del dinero (ej. 'EFECTIVO', 'TARJETA', 'TRANSFERENCIA', 'GASTO_INTERNO_CAJA').             |
*   | `fecha_movimiento`  | `db.DateTime`     | `nullable=False`                               | `datetime.utcnow` | `True` | Fecha y hora en que ocurrió y se registró el movimiento.                                                         |
*   | `notas_movimiento`  | `db.Text`         | `nullable=True`                                |                   |        |                                                                                                                  |
*   ---
*   **Relaciones:**
    *   `usuario_responsable = db.relationship('Usuario', back_populates='movimientos_caja_registrados')`
    *   `pedido_asociado = db.relationship('Pedido', back_populates='movimientos_caja_asociados')`
    *   `corte_caja_asignado = db.relationship('CorteCaja', back_populates='movimientos_del_corte')`
    *   `detalle_denominaciones = db.relationship('MovimientoDenominacion', back_populates='movimiento_caja_padre', lazy='dynamic', cascade='all, delete-orphan')` (Solo si `forma_pago_efectuado` es 'EFECTIVO').

---

### 3.13 Modelo `MovimientoDenominacion`

*   **Nombre de Tabla (sugerido):** `movimiento_denominaciones`
*   **Clase SQLAlchemy:** `MovimientoDenominacion`
*   **Descripción:** Detalla la cantidad de cada billete y moneda involucrada en un `MovimientoCaja` realizado en efectivo. Es crucial para el arqueo y control preciso del efectivo.
*   ---
*   | Columna             | Tipo (SQLAlchemy) | Restricciones                                       | Default | Índice | Descripción                                                                          |
*   |---------------------|-------------------|-----------------------------------------------------|---------|--------|--------------------------------------------------------------------------------------|
*   | `id`                | `db.Integer`      | `primary_key=True`                                  |         |        | Identificador único del detalle de denominación.                                     |
*   | `movimiento_caja_id`| `db.Integer`      | `db.ForeignKey('movimientos_caja.id'), nullable=False`|         | `True` | FK al `MovimientoCaja` al que pertenece este detalle.                                  |
*   | `denominacion_valor`| `db.Float`        | `nullable=False`                                    |         | `True` | Valor de la denominación (ej. 500.00, 100.00, 0.50). Ver sección 7.5 para valores. |
*   | `cantidad`          | `db.Integer`      | `nullable=False`                                    |         |        | Número de billetes/monedas de esta `denominacion_valor`. Positivo para ingresos, negativo para egresos (o siempre positivo y se infiere por el `MovimientoCaja.tipo_movimiento`). Se prefiere siempre positivo y que la lógica determine. |
*   ---
*   **Relaciones:**
    *   `movimiento_caja_padre = db.relationship('MovimientoCaja', back_populates='detalle_denominaciones')`
*   **Constraints:**
    *   `db.UniqueConstraint('movimiento_caja_id', 'denominacion_valor', name='uq_movimiento_denominacion_detalle')` (Solo una entrada por denominación para un movimiento dado).

---

### 3.14 Modelo `CorteCaja`

*   **Nombre de Tabla (sugerido):** `cortes_caja`
*   **Clase SQLAlchemy:** `CorteCaja`
*   **Descripción:** Registra el resultado de un arqueo o corte de caja, usualmente al final de un turno o del día, conciliando los saldos teóricos con el conteo físico del efectivo.
*   ---
*   | Columna                       | Tipo (SQLAlchemy) | Restricciones                                  | Default           | Índice | Descripción                                                                                                        |
*   |-------------------------------|-------------------|------------------------------------------------|-------------------|--------|--------------------------------------------------------------------------------------------------------------------|
*   | `id`                          | `db.Integer`      | `primary_key=True`                             |                   |        | Identificador único del corte de caja.                                                                             |
*   | `usuario_id_responsable`      | `db.Integer`      | `db.ForeignKey('usuarios.id'), nullable=False` |                   | `True` | FK al `Usuario` que realizó y es responsable del corte.                                                            |
*   | `fecha_apertura_periodo`      | `db.DateTime`     | `nullable=False`                               |                   | `True` | Fecha y hora de inicio del periodo que cubre este corte (usualmente la fecha del último corte o apertura inicial). |
*   | `fecha_cierre_corte`          | `db.DateTime`     | `nullable=False`                               | `datetime.utcnow` | `True` | Fecha y hora en que se realiza y finaliza el corte.                                                                |
*   | `saldo_inicial_efectivo_teorico`| `db.Float`      | `nullable=False`                               |                   |        | Saldo en efectivo que teóricamente debería haber al inicio del periodo.                                            |
*   | `total_ingresos_efectivo_periodo`| `db.Float`     | `nullable=False`                               |                   |        | Suma de todos los `MovimientoCaja` de INGRESO en EFECTIVO durante el periodo.                                      |
*   | `total_egresos_efectivo_periodo`| `db.Float`      | `nullable=False`                               |                   |        | Suma de todos los `MovimientoCaja` de EGRESO en EFECTIVO durante el periodo.                                       |
*   | `saldo_final_efectivo_teorico`| `db.Float`        | `nullable=False`                               |                   |        | Calculado: `saldo_inicial_efectivo_teorico + total_ingresos_efectivo_periodo - total_egresos_efectivo_periodo`.      |
*   | `saldo_final_efectivo_contado`| `db.Float`        | `nullable=False`                               |                   |        | Monto total de efectivo físico contado al momento del corte.                                                       |
*   | `diferencia_efectivo`         | `db.Float`        | `nullable=False`                               |                   | `True` | Calculado: `saldo_final_efectivo_contado - saldo_final_efectivo_teorico`.                                          |
*   | `total_ingresos_tarjeta_periodo`| `db.Float`      | `nullable=False`                               | `0.0`             |        | Suma de ingresos por tarjeta.                                                                                      |
*   | `total_ingresos_transfer_periodo`| `db.Float`    | `nullable=False`                               | `0.0`             |        | Suma de ingresos por transferencia.                                                                                |
*   | `total_ingresos_otros_periodo`| `db.Float`        | `nullable=False`                               | `0.0`             |        | Suma de ingresos por otras formas de pago.                                                                         |
*   | `estado_corte`                | `db.String(20)`   | `nullable=False`                               | `'ABIERTO'`       | `True` | Estado del corte: 'ABIERTO' (en proceso), 'CERRADO_CONCILIADO', 'CERRADO_CON_DIFERENCIA'.                        |
*   | `notas_corte`                 | `db.Text`         | `nullable=True`                                |                   |        | Observaciones sobre el corte, justificación de diferencias, etc.                                                   |
*   ---
*   **Relaciones:**
    *   `usuario_responsable_corte = db.relationship('Usuario', back_populates='cortes_caja_realizados')`
    *   `movimientos_del_corte = db.relationship('MovimientoCaja', back_populates='corte_caja_asignado', lazy='dynamic')` (Movimientos que se incluyen en este corte).
    *   `detalle_denominaciones_cierre = db.relationship('DenominacionCorteCaja', back_populates='corte_caja_padre', lazy='dynamic', cascade='all, delete-orphan')`

---

### 3.15 Modelo `DenominacionCorteCaja`

*   **Nombre de Tabla (sugerido):** `corte_caja_denominaciones`
*   **Clase SQLAlchemy:** `DenominacionCorteCaja`
*   **Descripción:** Detalla el conteo físico de cada billete y moneda al momento de realizar un `CorteCaja`.
*   ---
*   | Columna            | Tipo (SQLAlchemy) | Restricciones                                     | Default | Índice | Descripción                                                                   |
*   |--------------------|-------------------|---------------------------------------------------|---------|--------|-------------------------------------------------------------------------------|
*   | `id`               | `db.Integer`      | `primary_key=True`                                |         |        | Identificador único.                                                          |
*   | `corte_caja_id`    | `db.Integer`      | `db.ForeignKey('cortes_caja.id'), nullable=False` |         | `True` | FK al `CorteCaja` al que pertenece este conteo.                                 |
*   | `denominacion_valor`| `db.Float`       | `nullable=False`                                  |         | `True` | Valor de la denominación contada (ej. 500.00, 0.50).                          |
*   | `cantidad_contada` | `db.Integer`      | `nullable=False`                                  |         |        | Número de billetes/monedas de esta denominación contados físicamente.         |
*   | `total_por_denominacion`| `db.Float`    | `nullable=False`                                  |         |        | Calculado: `denominacion_valor * cantidad_contada`.                             |
*   ---
*   **Relaciones:**
    *   `corte_caja_padre = db.relationship('CorteCaja', back_populates='detalle_denominaciones_cierre')`
*   **Constraints:**
    *   `db.UniqueConstraint('corte_caja_id', 'denominacion_valor', name='uq_corte_denominacion_detalle')`

---

### 3.16 Modelo `ConfiguracionSistema`

*   **Nombre de Tabla (sugerido):** `configuracion_sistema`
*   **Clase SQLAlchemy:** `ConfiguracionSistema`
*   **Descripción:** Almacena parámetros y configuraciones globales del sistema que pueden ser ajustados por el Administrador. Se puede implementar como una tabla con una única fila o como un sistema clave-valor. Para MVP, una única fila puede ser más simple.
*   ---
*   | Columna                        | Tipo (SQLAlchemy) | Restricciones                             | Default                  | Índice | Descripción                                                                                    |
*   |--------------------------------|-------------------|-------------------------------------------|--------------------------|--------|------------------------------------------------------------------------------------------------|
*   | `id`                           | `db.Integer`      | `primary_key=True`                        | `1`                      |        | Siempre 1 si es una única fila.                                                                  |
*   | `nombre_negocio`               | `db.String(150)`  | `nullable=False`                          | `'Pollería Montiel'`     |        | Nombre oficial del negocio para tickets, reportes.                                             |
*   | `direccion_negocio`            | `db.String(255)`  | `nullable=True`                           |                          |        | Dirección física del negocio.                                                                  |
*   | `telefono_negocio`             | `db.String(50)`   | `nullable=True`                           |                          |        | Teléfono principal del negocio.                                                                |
*   | `rfc_negocio`                  | `db.String(13)`   | `nullable=True`                           |                          |        | RFC para facturación (si aplica).                                                              |
*   | `limite_items_pa_sin_comision` | `db.Integer`      | `nullable=False`                          | `3`                      |        | Número de PAs que se pueden agregar a un pedido sin generar comisión.                           |
*   | `monto_comision_fija_pa_extra` | `db.Float`        | `nullable=False`                          | `4.0`                    |        | Monto de comisión fija por cada PA que exceda el límite.                                       |
*   | `mensaje_whatsapp_confirmacion`| `db.Text`         | `nullable=True`                           | `'Hola {{cliente_nombre}}! Tu pedido #{{pedido_id}} de Pollería Montiel ha sido confirmado. Total: ${{pedido_total}}. Gracias!'` | | Plantilla para mensajes de WhatsApp (usando placeholders). |
*   | `porcentaje_iva`               | `db.Float`        | `nullable=False`                          | `16.0`                   |        | Porcentaje de IVA (si se maneja cálculo de impuestos).                                       |
*   | `permitir_venta_sin_stock`     | `db.Boolean`      | `nullable=False`                          | `True`                   |        | (Para futuro si se implementa inventario) Si se permite vender aunque no haya stock teórico.  |
*   | `ultimo_folio_pedido`          | `db.Integer`      | `nullable=False`                          | `0`                      |        | Para generar folios de pedido consecutivos.                                                      |
*   ---
*   **Constraints:**
    *   `db.CheckConstraint('id = 1', name='chk_single_row_config')` (Si se opta por una única fila).

---
**Sección 4: Lógica de Negocio y Funciones Clave**.

En esta sección, describiremos los algoritmos, cálculos y procesos más importantes que el sistema deberá realizar. No será código Python como tal, sino una descripción detallada de la lógica, las entradas esperadas, las salidas y los pasos involucrados. Esto es crucial para que Copilot pueda generar funciones correctas y para que los desarrolladores entiendan el *cómo* de las operaciones.

---

## 4. Lógica de Negocio y Funciones Clave

Esta sección detalla los procesos y cálculos fundamentales que el Sistema de Gestión para Pollería Montiel (SGPM) debe ejecutar para cumplir con los requisitos del negocio.

### 4.1 Gestión del Carrito de Pedidos

*   **Función/Proceso:** `agregar_item_al_carrito`
    *   **Propósito:** Añadir un producto de pollo (con sus modificaciones) o un producto adicional al carrito de un pedido en curso.
    *   **Entradas:**
        *   `id_sesion_carrito` (o `id_pedido_en_curso` si ya existe).
        *   `tipo_item`: 'POLLO' o 'PA'.
        *   Si `tipo_item` es 'POLLO':
            *   `producto_id` o `subproducto_id`.
            *   `modificacion_id` (opcional).
            *   `cantidad` (Float).
            *   `unidad_medida` (String, ej. 'kg').
            *   `cliente_id` (para cálculo de precio).
        *   Si `tipo_item` es 'PA':
            *   `nombre_pa` (String).
            *   `cantidad_pa` (Float).
            *   `unidad_medida_pa` (String).
            *   `precio_venta_unitario_pa` (Float) (puede ser ingresado directamente o calculado).
            *   `costo_compra_unitario_pa` (Float, opcional).
    *   **Lógica Principal:**
        1.  **Para `tipo_item` 'POLLO':**
            a.  Validar que `producto_id` o `subproducto_id` exista y esté activo.
            b.  Validar que `modificacion_id` (si se provee) sea aplicable al producto/subproducto.
            c.  Llamar a `obtener_precio_aplicable` (ver 4.2) para determinar `precio_unitario_venta` basado en `producto_id/subproducto_id`, `cliente_id` y `cantidad`.
            d.  Construir `descripcion_item_venta` (ej. "Pechuga Entera, para Asar").
            e.  Calcular `subtotal_item = cantidad * precio_unitario_venta`.
            f.  Crear o actualizar una instancia de `PedidoItem` en la sesión del carrito (o en la base de datos si el pedido ya está guardado).
        2.  **Para `tipo_item` 'PA':**
            a.  Si `precio_venta_unitario_pa` no se provee y `costo_compra_unitario_pa` sí, calcular `precio_venta_unitario_pa` aplicando la lógica de comisión (ver 4.3).
            b.  Calcular `subtotal_pa = cantidad_pa * precio_venta_unitario_pa`.
            c.  Crear una instancia de `ProductoAdicional` en la sesión del carrito.
        3.  Llamar a `recalcular_totales_carrito`.
    *   **Salida:** Carrito actualizado (lista de `PedidoItem` y `ProductoAdicional` con subtotales). Estado de éxito o mensaje de error.
    *   **Consideraciones:**
        *   Manejo de ítems existentes en el carrito (¿actualizar cantidad o añadir como nueva línea?). Para MVP, se podría añadir como nueva línea o actualizar si es exactamente el mismo producto/modificación.

*   **Función/Proceso:** `modificar_item_del_carrito`
    *   **Propósito:** Cambiar la cantidad o atributos de un ítem ya existente en el carrito.
    *   *(Similar a `agregar_item_al_carrito` pero opera sobre un ítem existente, recalculando precios y subtotales).*

*   **Función/Proceso:** `eliminar_item_del_carrito`
    *   **Propósito:** Quitar un ítem del carrito.
    *   **Entradas:** `id_sesion_carrito`, `id_item_carrito` (puede ser índice o ID único del ítem en el carrito).
    *   **Lógica Principal:**
        1.  Remover el ítem especificado de la lista de ítems del carrito.
        2.  Llamar a `recalcular_totales_carrito`.
    *   **Salida:** Carrito actualizado.

*   **Función/Proceso:** `recalcular_totales_carrito`
    *   **Propósito:** Actualizar los subtotales y el total general del carrito cada vez que se añade, modifica o elimina un ítem.
    *   **Entradas:** `id_sesion_carrito` (o la lista de ítems y PAs).
    *   **Lógica Principal:**
        1.  `subtotal_productos_pollo = SUM(item.subtotal_item)` para todos los `PedidoItem`.
        2.  `subtotal_productos_adicionales = SUM(pa.subtotal_pa)` para todos los `ProductoAdicional`.
        3.  `total_pedido_carrito = subtotal_productos_pollo + subtotal_productos_adicionales + costo_envio_carrito - descuento_carrito`. (Inicialmente `costo_envio` y `descuento` pueden ser 0).
    *   **Salida:** Objeto con `subtotal_productos_pollo`, `subtotal_productos_adicionales`, `total_pedido_carrito`.

---

### 4.2 Obtención y Aplicación de Precios

*   **Función/Proceso:** `obtener_precio_aplicable`
    *   **Propósito:** Determinar el precio unitario correcto para un producto de pollo (o subproducto) basándose en el tipo de cliente y la cantidad solicitada (para promociones por volumen).
    *   **Entradas:**
        *   `producto_id` O `subproducto_id`.
        *   `cliente_id` (para obtener `tipo_cliente`).
        *   `cantidad_solicitada` (Float, en kg).
    *   **Lógica Principal:**
        1.  Obtener el `tipo_cliente` a partir del `cliente_id`. Si no hay `cliente_id` (venta mostrador genérica), usar `tipo_cliente = 'PUBLICO'`.
        2.  Consultar la tabla `Precio` filtrando por:
            a.  `producto_id` o `subproducto_id` correspondiente.
            b.  `tipo_cliente`.
            c.  `activo = True`.
            d.  `fecha_inicio_vigencia <= hoy` (si aplica) Y `fecha_fin_vigencia >= hoy` (si aplica).
        3.  De los precios resultantes, seleccionar el más específico:
            a.  Priorizar precios que tengan una `cantidad_minima_kg` igual o menor a la `cantidad_solicitada`, y entre estos, el que tenga la `cantidad_minima_kg` más alta (para obtener la mejor promo por volumen que aplique).
            b.  Si no hay promociones por volumen que apliquen, tomar el precio general (`cantidad_minima_kg = 0` o la más cercana a 0).
        4.  Si no se encuentra ningún precio aplicable, retornar un error o un precio base por defecto (definir política).
    *   **Salida:** `precio_kg_aplicable` (Float) o `None`/Error.
    *   **Consideraciones:**
        *   La lógica de desempate debe ser clara si múltiples precios promocionales pudieran aplicar. Se prioriza la promoción que beneficie más al cliente y que cumpla con la cantidad.

---

### 4.3 Cálculo de Comisiones (PAs)

*   **Función/Proceso:** `calcular_comision_pa`
    *   **Propósito:** Calcular la comisión a añadir al costo de los Productos Adicionales (PAs) cuando se compran externamente, basado en la política de la pollería.
    *   **Entradas:**
        *   `lista_productos_adicionales_del_pedido` (Lista de objetos `ProductoAdicional` del pedido actual).
        *   (Desde `ConfiguracionSistema`): `limite_items_pa_sin_comision`, `monto_comision_fija_pa_extra`.
    *   **Lógica Principal:**
        1.  Contar el número total de PAs en `lista_productos_adicionales_del_pedido`.
        2.  `numero_pas_con_comision = MAX(0, total_pas - limite_items_pa_sin_comision)`.
        3.  `comision_total_pas = numero_pas_con_comision * monto_comision_fija_pa_extra`.
        4.  Esta comisión total se puede distribuir entre los PAs que generan comisión o simplemente sumarse al costo total de los PAs para determinar el precio de venta final al cliente. Para el MVP, se puede aplicar el `monto_comision_fija_pa_extra` individualmente a cada PA que exceda el límite al momento de calcular su `precio_venta_unitario_pa`.
            *   Es decir, al agregar un PA, si este PA hace que se supere `limite_items_pa_sin_comision`, su `precio_venta_unitario_pa = costo_compra_unitario_pa + monto_comision_fija_pa_extra`.
    *   **Salida:**
        *   Si se calcula por PA: `comision_aplicada_a_este_pa` (Float).
        *   Si se calcula total: `comision_total_para_los_pas_del_pedido` (Float).
    *   **Consideraciones:**
        *   Para el MVP, la lógica más simple es que si un PA es el 4to, 5to, etc., y el límite es 3, ese PA específico tiene la comisión sumada a su costo para obtener el precio de venta.

---

### 4.4 Cálculo de Cambio (con Denominaciones)

*   **Función/Proceso:** `calcular_y_sugerir_cambio_con_denominaciones`
    *   **Propósito:** Calcular el monto de cambio a devolver al cliente y sugerir la combinación óptima de billetes y monedas disponibles en caja para dar ese cambio.
    *   **Entradas:**
        *   `total_a_pagar` (Float).
        *   `monto_pagado_por_cliente` (Float).
        *   `existencias_denominaciones_en_caja` (Dict): Estado actual de la caja, ej. `{500.00: 2, 200.00: 5, ..., 0.50: 10}`. (Esto se obtendría de `MovimientoDenominacion`).
        *   `lista_denominaciones_ordenadas` (List): Lista de valores de denominación ordenados de mayor a menor (ej. `[1000.00, 500.00, ..., 0.50]`). (Desde `ConfiguracionSistema` o constante).
    *   **Lógica Principal (Algoritmo Greedy Modificado):**
        1.  `cambio_a_dar = monto_pagado_por_cliente - total_a_pagar`.
        2.  Si `cambio_a_dar < 0`, retornar error "Monto pagado insuficiente".
        3.  Si `cambio_a_dar == 0`, retornar `cambio_total=0`, `denominaciones_a_entregar={}`.
        4.  Inicializar `denominaciones_a_entregar = {}`.
        5.  `cambio_restante = cambio_a_dar`.
        6.  Iterar sobre `lista_denominaciones_ordenadas` (de mayor a menor):
            a.  Para cada `valor_denominacion_actual`:
                i.  Si `cambio_restante >= valor_denominacion_actual` Y `existencias_denominaciones_en_caja[valor_denominacion_actual] > 0`:
                    1.  `cantidad_maxima_de_esta_denominacion = floor(cambio_restante / valor_denominacion_actual)`.
                    2.  `cantidad_a_usar_de_esta_denominacion = MIN(cantidad_maxima_de_esta_denominacion, existencias_denominaciones_en_caja[valor_denominacion_actual])`.
                    3.  Si `cantidad_a_usar_de_esta_denominacion > 0`:
                        *   `denominaciones_a_entregar[valor_denominacion_actual] = cantidad_a_usar_de_esta_denominacion`.
                        *   `cambio_restante -= cantidad_a_usar_de_esta_denominacion * valor_denominacion_actual`.
                        *   `cambio_restante = round(cambio_restante, 2)` (para evitar problemas de precisión con flotantes).
        7.  Si `cambio_restante > 0.005` (un pequeño umbral para errores de flotantes):
            *   Retornar error "No se puede dar cambio exacto con las denominaciones disponibles. Falta: ${cambio_restante}". (Se podría intentar una estrategia de backtracking o informar qué denominaciones faltan, pero para MVP, un error es suficiente).
        8.  Si `cambio_restante <= 0.005`:
            *   Retornar `cambio_total=cambio_a_dar`, `denominaciones_a_entregar`.
    *   **Salida (Dict):**
        *   `cambio_total` (Float).
        *   `denominaciones_a_entregar` (Dict: `{valor_denominacion: cantidad}`).
        *   `mensaje_error` (String o None).
    *   **Consideraciones:**
        *   Esta función *sugiere* el cambio. La actualización real de las existencias en `MovimientoDenominacion` ocurre cuando se confirma el `MovimientoCaja` de egreso del cambio.
        *   La precisión de los flotantes es importante; redondear en puntos clave.

---

### 4.5 Flujo de Caja para PAs en Domicilio

*   **Proceso:** Gestión del efectivo para Productos Adicionales (PAs) y cambio para repartidores en pedidos a domicilio.
*   **Lógica de Movimientos de Caja:**
    1.  **Egreso para Compra de PAs (si la pollería los compra):**
        *   **Disparador:** Cuando se confirma un pedido a domicilio que incluye PAs que necesitan ser comprados.
        *   **Acción:** Se registra un `MovimientoCaja` de tipo `EGRESO`.
            *   `usuario_id`: Cajero que autoriza/entrega el dinero.
            *   `pedido_id`: ID del pedido asociado.
            *   `motivo_movimiento`: "Compra PA para Pedido #{{pedido_id}} - {{nombre_pa}}".
            *   `monto_movimiento`: Costo de compra del PA.
            *   `forma_pago_efectuado`: 'EFECTIVO'.
            *   Se registra el `MovimientoDenominacion` correspondiente a la salida de efectivo.
    2.  **Egreso para Cambio del Repartidor:**
        *   **Disparador:** Cuando el Cajero prepara el cambio que el Repartidor llevará para el pedido.
        *   **Acción:** Se registra un `MovimientoCaja` de tipo `EGRESO`.
            *   `usuario_id`: Cajero.
            *   `pedido_id`: ID del pedido asociado.
            *   `motivo_movimiento`: "Cambio entregado a Repartidor {{repartidor_nombre}} para Pedido #{{pedido_id}}".
            *   `monto_movimiento`: Monto total del cambio entregado al repartidor.
            *   `forma_pago_efectuado`: 'EFECTIVO'.
            *   Se registra el `MovimientoDenominacion` correspondiente.
    3.  **Ingreso por Liquidación del Repartidor:**
        *   **Disparador:** Cuando el Repartidor regresa y liquida el dinero de los pedidos entregados.
        *   **Acción:** Se registra un `MovimientoCaja` de tipo `INGRESO` por cada pedido liquidado (o un consolidado si se prefiere, pero individual es más trazable).
            *   `usuario_id`: Repartidor (o Cajero que recibe).
            *   `pedido_id`: ID del pedido entregado.
            *   `motivo_movimiento`: "Liquidación Pedido #{{pedido_id}} por Repartidor {{repartidor_nombre}}".
            *   `monto_movimiento`: Monto total entregado por el repartidor para ESE pedido (incluye el total del pedido pagado por el cliente y el cambio que el repartidor no usó y devuelve).
            *   `forma_pago_efectuado`: 'EFECTIVO'.
            *   Se registra el `MovimientoDenominacion` correspondiente al efectivo recibido del repartidor.
    *   **Consideraciones:**
        *   El sistema debe facilitar la conciliación de estos movimientos.
        *   El estado del pedido debe actualizarse (`ENTREGADO`, `PAGADO_AL_REPARTIDOR`).

---

### 4.6 Apertura y Corte de Caja

*   **Proceso:** `realizar_apertura_caja`
    *   **Propósito:** Registrar el saldo inicial de efectivo en caja al comienzo de un turno o día.
    *   **Entradas:**
        *   `usuario_id_responsable` (Cajero/Admin).
        *   `fecha_apertura_periodo` (Normalmente `datetime.now()`).
        *   `saldo_inicial_contado_por_denominaciones` (Dict: `{valor_denominacion: cantidad_contada}`).
    *   **Lógica Principal:**
        1.  Calcular `saldo_inicial_efectivo_total = SUM(valor_denominacion * cantidad_contada)` del diccionario de entrada.
        2.  Crear un registro `CorteCaja`:
            *   `usuario_id_responsable`.
            *   `fecha_apertura_periodo`.
            *   `fecha_cierre_corte`: NULL inicialmente (o una fecha muy futura).
            *   `saldo_inicial_efectivo_teorico = saldo_inicial_efectivo_total` (ya que es el inicio).
            *   `saldo_final_efectivo_contado = saldo_inicial_efectivo_total`.
            *   Los demás totales de ingresos/egresos en 0.
            *   `diferencia_efectivo = 0`.
            *   `estado_corte = 'ABIERTO'`.
        3.  Para cada entrada en `saldo_inicial_contado_por_denominaciones`, crear un registro `DenominacionCorteCaja` asociado al nuevo `CorteCaja.id`.
        4.  Crear un `MovimientoCaja` de tipo `INGRESO`:
            *   `usuario_id`: `usuario_id_responsable`.
            *   `motivo_movimiento`: "Saldo Inicial Apertura de Caja".
            *   `monto_movimiento`: `saldo_inicial_efectivo_total`.
            *   `forma_pago_efectuado`: 'EFECTIVO'.
            *   `corte_caja_id`: ID del `CorteCaja` recién creado.
            *   Asociar los `MovimientoDenominacion` correspondientes a este ingreso inicial.
    *   **Salida:** Nuevo `CorteCaja` y `MovimientoCaja` creados. Estado de éxito.

*   **Proceso:** `realizar_cierre_de_caja`
    *   **Propósito:** Finalizar un periodo de caja, contar el efectivo, compararlo con el saldo teórico y registrar el resultado.
    *   **Entradas:**
        *   `corte_caja_id_actual` (ID del `CorteCaja` que está 'ABIERTO').
        *   `usuario_id_cierre` (Usuario que realiza el conteo final y cierre).
        *   `efectivo_contado_final_por_denominaciones` (Dict: `{valor_denominacion: cantidad_contada}`).
        *   (Opcional) Totales contados para otras formas de pago si no se registran automáticamente (ej. vouchers de tarjeta).
    *   **Lógica Principal:**
        1.  Obtener el `CorteCaja` actual usando `corte_caja_id_actual`. Validar que esté 'ABIERTO'.
        2.  Calcular `saldo_final_efectivo_contado = SUM(valor_denominacion * cantidad_contada)` del diccionario de entrada.
        3.  Consultar todos los `MovimientoCaja` asociados a este `corte_caja_id_actual` (o aquellos desde `fecha_apertura_periodo` hasta `now()` si no se asigna el `corte_caja_id` a los movimientos hasta el cierre).
            *   Calcular `total_ingresos_efectivo_periodo`.
            *   Calcular `total_egresos_efectivo_periodo`.
            *   (Similar para otras formas de pago: tarjeta, transferencia).
        4.  Calcular `saldo_final_efectivo_teorico = CorteCaja.saldo_inicial_efectivo_teorico + total_ingresos_efectivo_periodo - total_egresos_efectivo_periodo`.
        5.  Calcular `diferencia_efectivo = saldo_final_efectivo_contado - saldo_final_efectivo_teorico`.
        6.  Actualizar el registro `CorteCaja`:
            *   `fecha_cierre_corte = datetime.utcnow()`.
            *   `total_ingresos_efectivo_periodo`, `total_egresos_efectivo_periodo`.
            *   `saldo_final_efectivo_teorico`, `saldo_final_efectivo_contado`, `diferencia_efectivo`.
            *   (Actualizar totales de otras formas de pago).
            *   `estado_corte = 'CERRADO_CONCILIADO'` si `diferencia_efectivo` es 0 (o dentro de un umbral mínimo).
            *   `estado_corte = 'CERRADO_CON_DIFERENCIA'` si hay diferencia.
            *   `notas_corte` (si el usuario las provee).
        7.  Para cada entrada en `efectivo_contado_final_por_denominaciones`, crear o actualizar un registro `DenominacionCorteCaja` asociado a este `CorteCaja.id` (si se guardan al final, o ya se fueron creando durante el día).
    *   **Salida:** `CorteCaja` actualizado. Reporte del corte.
    *   **Consideraciones:**
        *   Definir si los `MovimientoCaja` se asocian al `CorteCaja` en el momento de su creación o al final, durante el proceso de cierre. Lo primero es más robusto.
        *   El `saldo_inicial_efectivo_teorico` del siguiente corte será el `saldo_final_efectivo_contado` de este corte (o el teórico si se decide no arrastrar diferencias y ajustarlas).

---

### 4.7 Generación de Mensaje para WhatsApp

*   **Función/Proceso:** `generar_mensaje_confirmacion_whatsapp`
    *   **Propósito:** Crear un mensaje de texto formateado para enviar al cliente por WhatsApp confirmando su pedido.
    *   **Entradas:**
        *   `pedido_obj` (Objeto `Pedido` completo, con sus `PedidoItem` y `ProductoAdicional`).
        *   (Desde `ConfiguracionSistema`): `plantilla_mensaje_whatsapp_confirmacion`.
    *   **Lógica Principal:**
        1.  Obtener la plantilla del mensaje (ej. "¡Hola {{cliente_alias_o_nombre}}! Tu pedido #{{pedido_folio}} de Pollería Montiel ha sido confirmado. Detalles: \n{{lista_items}}\nTotal a pagar: ${{pedido_total_formateado}}. ¡Gracias por tu preferencia!").
        2.  Obtener los datos necesarios del `pedido_obj`:
            *   `cliente_alias_o_nombre`: `pedido_obj.cliente.alias` o `pedido_obj.cliente.get_nombre_completo()`.
            *   `pedido_folio`: `pedido_obj.generar_folio_display()`.
            *   `lista_items`: Iterar sobre `pedido_obj.items` y `pedido_obj.productos_adicionales_pedido` para formatear una lista legible:
                *   Ej. "- 1.50 kg Pechuga Entera, para Asar: $180.00"
                *   Ej. "- 1 pz Jitomate (PA): $20.00"
            *   `pedido_total_formateado`: `"{:,.2f}".format(pedido_obj.total_pedido)`.
        3.  Reemplazar los placeholders en la plantilla con los datos obtenidos.
    *   **Salida:** `mensaje_formateado` (String).
    *   **Consideraciones:**
        *   La función solo genera el texto. El envío real por WhatsApp está fuera del alcance del MVP (se haría manualmente o con una integración futura).
        *   Considerar diferentes plantillas para diferentes estados del pedido (ej. "Tu pedido está en ruta").

**Seción 5: Flujos de Usuario Principales (User Stories)**.

Esta sección es vital para dar contexto a todas las funcionalidades y modelos que hemos definido. Describe cómo los diferentes roles interactuarán con el sistema para lograr objetivos específicos. Usaremos el formato estándar de User Story (Actor, Objetivo, Pasos, etc.) para asegurar claridad.

---

## 5. Flujos de Usuario Principales (User Stories)

A continuación, se describen los flujos de interacción más importantes de los usuarios con el Sistema de Gestión para Pollería Montiel (SGPM). Estas User Stories ayudan a contextualizar las funcionalidades y a asegurar que el sistema cumple con las necesidades operativas.

---

### 5.1 US-001: Cajero - Registrar Venta Rápida en Mostrador (Pago en Efectivo)

*   **ID User Story:** US-001
*   **Título:** Registro de Venta Rápida en Mostrador con Pago en Efectivo.
*   **Actor Principal:** Cajero (`CAJERO`)
*   **Objetivo del Actor:** Registrar de forma rápida y eficiente una venta a un cliente en el mostrador que paga en efectivo, calculando el cambio correctamente.
*   **Precondiciones:**
    1.  El Cajero ha iniciado sesión en el SGPM.
    2.  La caja del Cajero ha sido abierta y tiene un saldo inicial registrado.
    3.  El sistema está operativo y el catálogo de productos está accesible.
*   **Flujo Principal (Pasos):**
    1.  El Cajero selecciona la opción "Nueva Venta en Mostrador" en la interfaz principal.
    2.  **Sistema:** Muestra el formulario/interfaz de nueva venta, preseleccionando "Cliente Mostrador Genérico" (o permite omitir la selección de cliente).
    3.  El Cajero comienza a agregar ítems al pedido (carrito):
        a.  **Cajero:** Selecciona el producto "Pechuga" (`PECH`).
        b.  **Sistema:** Muestra opciones (ej. Pechuga Entera, Pulpa de Pechuga).
        c.  **Cajero:** Selecciona "Pechuga Entera".
        d.  **Sistema:** Muestra las `Modificacion` aplicables (ej. Entera, Cortada en 2, Para Asar).
        e.  **Cajero:** Selecciona "Entera". Ingresa Cantidad: "1.5" (kg).
        f.  **Sistema:** Consulta `obtener_precio_aplicable` (usando `tipo_cliente='PUBLICO'`), calcula el `precio_unitario_venta` (ej. $120/kg) y el `subtotal_item` (ej. $180.00). Añade el `PedidoItem` al carrito y actualiza los totales del carrito visiblemente.
    4.  El Cajero repite el paso 3 para cualquier otro producto de pollo (ej. "0.5 kg de Alas (`AL`), Cortadas en 2").
    5.  El Cajero añade un Producto Adicional (PA):
        a.  **Cajero:** Selecciona "Añadir Producto Adicional". Ingresa Nombre: "Refresco Coca-Cola 600ml", Cantidad: "1", Unidad: "pieza", Precio Venta Unitario: "$15.00".
        b.  **Sistema:** Añade el `ProductoAdicional` al carrito y actualiza los totales del carrito visiblemente. Llama a `calcular_comision_pa` si aplica, aunque para este flujo simple se asume precio de venta directo.
    6.  **Sistema:** Muestra el resumen del pedido en el carrito, incluyendo:
        *   `subtotal_productos_pollo` (ej. $180.00 Alas + $59.00 Pechuga = $239.00).
        *   `subtotal_productos_adicionales` (ej. $15.00).
        *   `total_pedido` (ej. $254.00).
    7.  El Cajero indica la forma de pago:
        a.  **Cajero:** Selecciona "Efectivo".
        b.  **Cajero:** Ingresa el monto con el que paga el cliente en el campo "Paga con": "$300.00".
    8.  **Sistema:** Llama a `calcular_y_sugerir_cambio_con_denominaciones` (total_a_pagar=$254.00, monto_pagado=$300.00). Retorna `cambio_total=$46.00` y `denominaciones_a_entregar` (ej. `{20.00: 2, 5.00: 1, 1.00: 1}`). Muestra esta información al Cajero.
    9.  El Cajero entrega el cambio al cliente y los productos.
    10. **Cajero:** Confirma/Finaliza la venta en el sistema.
*   **Postcondiciones:**
    1.  Se crea un nuevo registro en la tabla `Pedido` con:
        *   `cliente_id`: ID del "Cliente Mostrador Genérico" o `NULL`.
        *   `usuario_id`: ID del Cajero.
        *   `tipo_venta`: 'MOSTRADOR'.
        *   `forma_pago`: 'EFECTIVO'.
        *   `paga_con`: 300.00.
        *   `cambio_entregado`: 46.00.
        *   Subtotales y total_pedido calculados.
        *   `estado_pedido`: 'PAGADO' o 'ENTREGADO' (definir el estado final para ventas de mostrador inmediatas).
    2.  Se crean los registros `PedidoItem` correspondientes en la base de datos, asociados al `Pedido.id`.
    3.  Se crea el registro `ProductoAdicional` correspondiente, asociado al `Pedido.id`.
    4.  Se crea un `MovimientoCaja` de tipo `INGRESO`:
        *   `usuario_id`: ID del Cajero.
        *   `pedido_id`: ID del `Pedido` recién creado.
        *   `motivo_movimiento`: "Venta Pedido Mostrador #{{Pedido.id}}".
        *   `monto_movimiento`: 254.00 (el total del pedido).
        *   `forma_pago_efectuado`: 'EFECTIVO'.
        *   Se crean los `MovimientoDenominacion` asociados a este ingreso, reflejando los $300.00 recibidos (ej. 1 billete de $200, 1 billete de $100) y los $46.00 entregados como cambio (esto se maneja restando las denominaciones entregadas de las recibidas, o como dos movimientos separados: uno de ingreso por $300 y uno de egreso por $46 "Cambio Venta #X"). *Para MVP, más simple: se registran las denominaciones con las que el cliente pagó, y el egreso del cambio se infiere o se registra como un movimiento de denominaciones negativo dentro del mismo movimiento de caja.*
    5.  (Opcional) El sistema genera e imprime un ticket de venta simplificado.
    6.  La interfaz del Cajero queda lista para una nueva venta.
*   **Flujos Alternativos/Excepciones:**
    *   **A-001.1: Cliente solicita un producto no disponible o modificación no válida:** El sistema no permite agregarlo o muestra un aviso.
    *   **A-001.2: Monto pagado es insuficiente:** El sistema muestra un error "Monto pagado es menor al total del pedido" y no permite finalizar.
    *   **A-001.3: No hay cambio exacto disponible:** El sistema informa al Cajero (según `calcular_y_sugerir_cambio_con_denominaciones`). El Cajero debe resolverlo manualmente (ej. preguntar al cliente si tiene cambio, o buscar cambio internamente). El sistema debe permitir registrar el cambio real entregado.
    *   **A-001.4: Cajero cancela la venta antes de finalizar:** No se guarda ningún registro de Pedido ni Movimiento de Caja. El carrito se vacía.

---

### 5.2 US-002: Cajero - Registrar Pedido a Domicilio (Cliente Nuevo, Pago Contra Entrega)

*   **ID User Story:** US-002
*   **Título:** Registro de Pedido a Domicilio para un Cliente Nuevo con Pago Contra Entrega.
*   **Actor Principal:** Cajero (`CAJERO`)
*   **Objetivo del Actor:** Tomar un pedido para entrega a domicilio de un cliente nuevo, registrando sus datos de contacto y dirección, y preparando el pedido para su posterior asignación a un repartidor. El pago se realizará al momento de la entrega.
*   **Precondiciones:**
    1.  El Cajero ha iniciado sesión en el SGPM.
    2.  La caja del Cajero está abierta.
*   **Flujo Principal (Pasos):**
    1.  El Cajero selecciona la opción "Nuevo Pedido a Domicilio".
    2.  **Sistema:** Muestra el formulario de nuevo pedido.
    3.  El Cajero intenta buscar al cliente por nombre o teléfono y no lo encuentra.
    4.  **Cajero:** Selecciona "Crear Nuevo Cliente".
    5.  **Sistema:** Presenta campos para registrar al nuevo cliente.
    6.  **Cajero:** Ingresa los datos del nuevo cliente:
        *   Nombre: "Laura".
        *   Apellidos: "Gómez".
        *   Alias: "Lau".
        *   Teléfono Principal: "5512345678" (Tipo: WHATSAPP).
        *   (Opcional) Otro teléfono.
        *   Tipo de Cliente: "PUBLICO" (por defecto).
    7.  **Cajero:** Ingresa los datos de la dirección de entrega:
        *   Calle y Número: "Calle Falsa 123, Int A".
        *   Colonia: "Centro".
        *   Ciudad: "Ciudad Ejemplo".
        *   Código Postal: "12345".
        *   Referencias: "Casa azul con portón negro, tocar fuerte".
        *   Tipo de Dirección: "CASA", marcar como "Dirección Principal de Entrega".
    8.  **Cajero:** Guarda los datos del nuevo cliente y su dirección.
    9.  **Sistema:** Crea el registro `Cliente`, `Telefono` y `Direccion`. Asocia este cliente y dirección al pedido en curso.
    10. El Cajero procede a agregar ítems al pedido de forma similar al US-001 (ej. "2 kg de Pernil (`PM`), Cortado y Sin Piel", "1 Pollo Surtida (`SRT`)").
    11. El Cajero añade Productos Adicionales que el cliente solicita y que la pollería deberá comprar (ej. "1 kg de Tortillas", "Salsa Verde Grande"). Para estos PAs, el Cajero puede ingresar el `costo_compra_unitario_pa` estimado y el sistema calculará el `precio_venta_unitario_pa` aplicando la comisión (ver 4.3).
    12. **Sistema:** Muestra el resumen del pedido, incluyendo subtotales y `total_pedido`.
    13. El Cajero selecciona "Forma de Pago": "EFECTIVO_CONTRA_ENTREGA".
    14. **Cajero:** (Opcional) Ingresa una `fecha_entrega_programada` o un rango horario en las `notas_pedido`.
    15. **Cajero:** Confirma el pedido.
*   **Postcondiciones:**
    1.  Se crea un nuevo registro en `Cliente`, `Telefono`, `Direccion`.
    2.  Se crea un nuevo registro en `Pedido` con:
        *   `cliente_id`: ID del nuevo cliente.
        *   `usuario_id`: ID del Cajero.
        *   `direccion_entrega_id`: ID de la nueva dirección.
        *   `tipo_venta`: 'DOMICILIO'.
        *   `forma_pago`: 'EFECTIVO_CONTRA_ENTREGA'.
        *   `paga_con`, `cambio_entregado`: `NULL` (se manejarán al momento de la liquidación del repartidor).
        *   Subtotales y `total_pedido` calculados.
        *   `estado_pedido`: 'PENDIENTE_PREPARACION' (o 'PENDIENTE_CONFIRMACION_CLIENTE' si se requiere una llamada de vuelta).
    3.  Se crean los registros `PedidoItem` y `ProductoAdicional` asociados.
    4.  **Movimientos de Caja (Flujo de PAs - ver 4.5):**
        *   Si hay PAs que la pollería debe comprar, el Cajero (o Admin) deberá registrar un `MovimientoCaja` de `EGRESO` por el costo de compra de esos PAs, asociándolo a este `Pedido.id`.
    5.  El pedido aparece en la lista de pedidos pendientes de preparación y/o asignación a repartidor.
    6.  (Opcional) El Cajero genera un mensaje de confirmación para enviar por WhatsApp al cliente (ver 4.7).
*   **Flujos Alternativos/Excepciones:**
    *   **A-002.1: Cliente ya existe pero con otra dirección:** El Cajero puede seleccionar una dirección existente o añadir una nueva para ese cliente.
    *   **A-002.2: Dirección de entrega fuera de zona de cobertura:** (No contemplado en MVP, pero a futuro el sistema podría advertir).
    *   **A-002.3: Cliente solicita pago con tarjeta contra entrega:** El sistema debe permitir registrar esto, y el repartidor debe llevar la terminal.

---

### 5.3 US-003: Repartidor - Gestionar Entrega de Pedido y Liquidación

*   **ID User Story:** US-003
*   **Título:** Repartidor Gestiona Entrega de Pedido y Liquida el Efectivo.
*   **Actor Principal:** Repartidor (`REPARTIDOR`), Cajero (`CAJERO`)
*   **Objetivo del Actor:** (Repartidor) Recoger un pedido preparado, entregarlo al cliente, cobrar y regresar a liquidar el efectivo. (Cajero) Recibir la liquidación del repartidor.
*   **Precondiciones:**
    1.  El Repartidor ha iniciado sesión.
    2.  Existe un `Pedido` con `estado_pedido` = 'LISTO_PARA_ENTREGA' o 'ASIGNADO_REPARTIDOR' (a este repartidor).
    3.  El Cajero ha entregado al Repartidor el cambio necesario para la ruta (este es un `MovimientoCaja` de `EGRESO` registrado por el Cajero, asociado al Repartidor o a los pedidos que lleva, ver 4.5).
*   **Flujo Principal (Pasos):**
    1.  **Cajero/Admin:** Asigna el `Pedido` (que está 'LISTO_PARA_ENTREGA') al Repartidor a través del sistema. `estado_pedido` cambia a 'ASIGNADO_REPARTIDOR'.
    2.  **Repartidor:** Consulta en el sistema los pedidos que tiene asignados.
    3.  **Repartidor:** Recoge los productos físicos del pedido. Selecciona el pedido en el sistema y actualiza `estado_pedido` a 'EN_RUTA'.
    4.  **Repartidor:** Llega a la dirección del cliente. Entrega el pedido.
    5.  **Cliente:** Paga al Repartidor (ej. $350.00 en efectivo para un pedido de $320.00).
    6.  **Repartidor:** Entrega el cambio al cliente (ej. $30.00).
    7.  **Repartidor:** (Idealmente en el momento, o al regresar) Actualiza el `estado_pedido` a 'ENTREGADO' o 'PAGADO_AL_REPARTIDOR'. Puede añadir `notas_pedido` (ej. "Cliente satisfecho", "No se encontraba, se dejó con vecino con autorización").
    8.  **Repartidor:** Regresa a la pollería.
    9.  **Repartidor:** Se presenta con el Cajero para liquidar el efectivo de los pedidos entregados. Entrega el total cobrado menos el cambio que dio, más el cambio que le sobró del que le dieron inicialmente.
    10. **Cajero:** En el sistema, busca el pedido (o pedidos) que el Repartidor está liquidando.
    11. **Cajero:** Confirma el monto recibido del Repartidor para el `Pedido` (ej. $320.00).
    12. **Sistema/Cajero:** Registra un `MovimientoCaja` de tipo `INGRESO` por la liquidación del pedido:
        *   `usuario_id`: ID del Repartidor (o Cajero que recibe).
        *   `pedido_id`: ID del `Pedido` liquidado.
        *   `motivo_movimiento`: "Liquidación Pedido Domicilio #{{Pedido.id}} por Repartidor {{Repartidor.nombre_completo}}".
        *   `monto_movimiento`: 320.00 (el total del pedido).
        *   `forma_pago_efectuado`: 'EFECTIVO'.
        *   Se registran los `MovimientoDenominacion` del efectivo recibido del repartidor.
    13. **Sistema:** Actualiza `estado_pedido` a 'PAGADO' (si no lo estaba ya).
*   **Postcondiciones:**
    1.  El `estado_pedido` se actualiza a 'PAGADO'.
    2.  Se registra el `MovimientoCaja` de INGRESO por la liquidación.
    3.  El efectivo en caja (teórico) se incrementa.
*   **Flujos Alternativos/Excepciones:**
    *   **A-003.1: Cliente no se encuentra o rechaza el pedido:** Repartidor actualiza `estado_pedido` a 'PROBLEMA_ENTREGA' y añade notas. Se sigue un proceso interno para resolver.
    *   **A-003.2: Cliente paga con monto exacto:** No hay cambio que entregar.
    *   **A-003.3: Cliente paga con tarjeta (si el repartidor lleva terminal):** `forma_pago` del pedido se actualiza. El `MovimientoCaja` de liquidación reflejará "INGRESO POR TARJETA (Liquidación Repartidor)".
    *   **A-003.4: Discrepancia en la liquidación:** El Cajero y Repartidor deben resolver. El sistema debe permitir registrar el monto real recibido, y la diferencia se reflejará en el corte de caja.

---

### 5.4 US-004: Administrador/Cajero - Realizar Corte de Caja Diario

*   **ID User Story:** US-004
*   **Título:** Realizar el Corte de Caja al Final del Día/Turno.
*   **Actor Principal:** Administrador (`ADMINISTRADOR`) o Cajero (`CAJERO`) (el responsable del turno).
*   **Objetivo del Actor:** Contar el efectivo y otros valores en caja, compararlos con el saldo teórico calculado por el sistema, registrar cualquier diferencia y cerrar formalmente el periodo de caja.
*   **Precondiciones:**
    1.  El Usuario (Admin/Cajero) ha iniciado sesión.
    2.  Existe un `CorteCaja` con `estado_corte = 'ABIERTO'` para el turno/día actual.
    3.  Idealmente, todos los pedidos del día/turno han sido procesados y los movimientos de caja correspondientes registrados.
*   **Flujo Principal (Pasos):**
    1.  El Usuario selecciona la opción "Realizar Corte de Caja".
    2.  **Sistema:** Muestra la interfaz de corte de caja. Presenta el `saldo_inicial_efectivo_teorico` del `CorteCaja` abierto.
    3.  **Sistema:** Calcula y muestra (solo para referencia, no editable en este punto):
        *   `total_ingresos_efectivo_periodo` (basado en `MovimientoCaja` desde la apertura).
        *   `total_egresos_efectivo_periodo` (basado en `MovimientoCaja` desde la apertura).
        *   `saldo_final_efectivo_teorico` (calculado).
        *   (Similar para otras formas de pago: totales de ingresos por tarjeta, transferencia, etc.).
    4.  **Usuario:** Realiza el conteo físico del efectivo en caja.
    5.  **Usuario:** Ingresa en el sistema la cantidad contada para cada denominación de billete y moneda en los campos correspondientes (ej. Billetes de $500: 3, Billetes de $200: 5, ..., Monedas de $0.50: 10).
    6.  **Sistema:** Calcula automáticamente el `saldo_final_efectivo_contado` sumando los valores de las denominaciones ingresadas. Lo muestra al usuario.
    7.  **Sistema:** Calcula la `diferencia_efectivo = saldo_final_efectivo_contado - saldo_final_efectivo_teorico`. Muestra la diferencia (si la hay) al usuario, idealmente con un indicador visual (verde si 0, rojo si faltante, azul si sobrante).
    8.  **Usuario:** (Opcional) Ingresa los totales contados para otras formas de pago (ej. suma de vouchers de tarjeta).
    9.  **Usuario:** (Opcional) Añade `notas_corte` (ej. "Sobrante de $5.00 por redondeo", "Faltante de $20.00, se revisará video").
    10. **Usuario:** Confirma y cierra el corte de caja.
*   **Postcondiciones:**
    1.  El registro `CorteCaja` actual se actualiza con:
        *   `fecha_cierre_corte`.
        *   Todos los totales calculados y contados (ingresos, egresos, saldos, diferencia).
        *   `estado_corte` se actualiza a 'CERRADO_CONCILIADO' o 'CERRADO_CON_DIFERENCIA'.
        *   `notas_corte`.
    2.  Se crean los registros `DenominacionCorteCaja` asociados, detallando el conteo físico final.
    3.  Todos los `MovimientoCaja` ocurridos durante el periodo del corte son formalmente asociados a este `CorteCaja.id` (si no se hizo en tiempo real).
    4.  El sistema está listo para una nueva "Apertura de Caja" para el siguiente turno/día (el `saldo_inicial_efectivo_teorico` del nuevo corte podría ser el `saldo_final_efectivo_contado` del corte actual, o el teórico, según política).
    5.  (Opcional) Se genera un reporte imprimible/digital del corte de caja.
*   **Flujos Alternativos/Excepciones:**
    *   **A-004.1: Diferencia significativa en el corte:** Requiere autorización o revisión del Administrador antes de cerrar.
    *   **A-004.2: Olvido de registrar un movimiento:** El sistema debería permitir (idealmente al Admin) realizar ajustes o movimientos retroactivos ANTES de cerrar el corte, o el corte reflejará la discrepancia.

---
**Sección 6: Directrices de Interfaz de Usuario (UI/UX)**.

Esta sección, aunque no define código directamente, es crucial para guiar a Copilot (y a los desarrolladores) sobre cómo deben lucir y sentirse las interacciones. Describe los principios de diseño, las vistas clave y cómo se deben presentar ciertos elementos, como la simbología de productos.

---

## 6. Directrices de Interfaz de Usuario (UI/UX)

Esta sección establece los principios y directrices para el diseño de la interfaz de usuario (UI) y la experiencia de usuario (UX) del Sistema de Gestión para Pollería Montiel (SGPM). El objetivo es crear un sistema que sea eficiente, fácil de usar, visualmente claro y adaptado a las necesidades operativas de la pollería, especialmente considerando el enfoque "Mobile First".

### 6.1 Principios Generales de Diseño y Usabilidad

1.  **Mobile First y Diseño Responsivo:**
    *   Todas las vistas y funcionalidades deben diseñarse priorizando la experiencia en dispositivos móviles (smartphones, tablets).
    *   La interfaz debe ser completamente responsiva, adaptándose de forma fluida a diferentes tamaños de pantalla, incluyendo monitores de escritorio para tareas administrativas.
    *   Los elementos táctiles deben ser de tamaño adecuado para facilitar la interacción en pantallas pequeñas.
    *   La navegación principal debe ser fácilmente accesible en móviles (ej. menú lateral colapsable, barra de navegación inferior).

2.  **Claridad y Simplicidad Visual:**
    *   Utilizar un diseño limpio y sin desorden, enfocándose en la información y acciones más relevantes para la tarea en curso.
    *   Jerarquía visual clara: usar tamaño de fuente, peso, color y espaciado para guiar la atención del usuario.
    *   Iconografía consistente y reconocible (ej. Feather Icons o similar, como se mencionó en el documento maestro original) para complementar etiquetas de texto y mejorar la comprensión rápida.
    *   Adherirse a la paleta de colores y tipografía definida en `estilo.css` y las variables CSS (ej. `var(--rojo-principal)`, `var(--fuente-base)`, `var(--espacio-m)`).

3.  **Eficiencia y Flujo de Trabajo Optimizado:**
    *   Minimizar el número de clics/taps para completar tareas comunes.
    *   Pre-rellenar campos con valores por defecto o información contextual cuando sea posible.
    *   Utilizar componentes de UI interactivos (ej. autocompletado para búsqueda de clientes/productos, selectores dinámicos) para agilizar la entrada de datos.
    *   Proporcionar atajos de teclado para acciones frecuentes en la versión de escritorio (consideración futura).

4.  **Consistencia:**
    *   Mantener un lenguaje visual y patrones de interacción consistentes a lo largo de toda la aplicación.
    *   Los botones para acciones similares (ej. "Guardar", "Cancelar", "Añadir") deben lucir y comportarse de la misma manera en todas las vistas.
    *   La terminología utilizada debe ser consistente con el dominio de la pollería y fácil de entender para los usuarios.

5.  **Retroalimentación Inmediata y Clara:**
    *   Proporcionar feedback visual instantáneo a las acciones del usuario (ej. cambio de estado de un botón al ser presionado, indicadores de carga para operaciones asíncronas).
    *   Usar mensajes `flash` (con categorías: `success`, `error`, `info`, `warning`) para notificar el resultado de las operaciones.
    *   Para errores de validación en formularios, mostrar mensajes claros y específicos junto a los campos correspondientes.
    *   Considerar alertas sonoras sutiles (opcionales y configurables) para eventos críticos como nuevos pedidos a domicilio.

6.  **Accesibilidad (Principios Básicos):**
    *   Asegurar un buen contraste de color entre texto y fondo.
    *   Utilizar etiquetas HTML semánticas correctamente.
    *   Proporcionar texto alternativo para imágenes significativas.
    *   Asegurar que la navegación por teclado sea posible para los elementos interactivos.
    *   Usar indicadores de campos requeridos (ej. un asterisco o el `required-indicator` mencionado).

### 6.2 Vistas Clave (Descripción Funcional y Visual Esperada)

A continuación, se describen algunas de las vistas más importantes y cómo deberían funcionar y lucir.

1.  **Panel Principal / Dashboard de Pedidos:**
    *   **Propósito:** Vista principal para Cajeros y Administradores, mostrando pedidos activos y permitiendo acciones rápidas.
    *   **Layout:**
        *   **Mobile:** Tarjetas apiladas verticalmente, cada una representando un pedido. Scroll infinito o paginación simple si hay muchos pedidos.
        *   **Desktop:** Tabla interactiva con columnas clave o una vista de "kanban" con columnas por estado del pedido.
    *   **Contenido por Pedido (Tarjeta/Fila):**
        *   Número de Folio del Pedido (grande y visible).
        *   Nombre del Cliente (o "Mostrador") y Tipo de Venta (icono 🐔 Mostrador / 🛵 Domicilio).
        *   Resumen de Productos Principales (usando simbología, ej. "2kg PECH MOL, 1 SRT").
        *   Monto Total.
        *   Estado del Pedido (con código de color: ej. Amarillo=En Preparación, Naranja=Listo para Entrega/Asignado, Verde=En Ruta, Azul Oscuro=Entregado, Rojo=Cancelado/Problema).
        *   (Para Domicilio) Nombre del Repartidor asignado.
        *   Hora del pedido o tiempo transcurrido.
    *   **Acciones Rápidas (por pedido):**
        *   Botón/Icono para "Ver Detalle Completo / Editar".
        *   Botón/Icono para "Cambiar Estado" (dropdown con estados siguientes válidos).
        *   Botón/Icono para "Asignar Repartidor" (si aplica y el rol tiene permiso).
        *   Botón/Icono para "Imprimir Ticket/Comanda".
    *   **Filtros/Búsqueda:**
        *   Filtro por Tipo de Venta (Mostrador/Domicilio).
        *   Filtro por Estado del Pedido.
        *   Buscador universal (por folio, nombre cliente, teléfono).
    *   **Botón Principal:** "Nuevo Pedido" (claramente visible).

2.  **Formulario de Nuevo Pedido / Modificación de Pedido:**
    *   **Propósito:** Interfaz para crear o editar los detalles de un pedido.
    *   **Layout:**
        *   Sección de Datos del Cliente (búsqueda por nombre/teléfono/alias con autocompletado, o campos para alta rápida si es nuevo; selección de dirección de entrega para domicilios).
        *   Sección de Carrito de Compras:
            *   Área para seleccionar/buscar Productos de Pollo:
                *   Selector 1: `Producto` (ej. Pechuga, Alas).
                *   Selector 2 (dinámico): `Subproducto` (si el Producto tiene, ej. Pulpa de Pechuga).
                *   Selector 3 (dinámico): `Modificacion` (aplicable al Producto/Subproducto seleccionado).
                *   Campo para `Cantidad` (con unidad predeterminada, ej. kg).
                *   Botón "Añadir al Pedido".
            *   Área para añadir `Productos Adicionales (PAs)`:
                *   Campo `Nombre PA`.
                *   Campo `Cantidad PA`.
                *   Selector `Unidad Medida PA` (kg, pz, monto).
                *   Campo `Precio Venta Unitario PA` (o `Costo Compra` si se calcula con comisión).
                *   Botón "Añadir PA".
            *   Lista visible de ítems en el carrito (con `descripcion_item_venta`, cantidad, precio unitario, subtotal, y botón para eliminar/editar ítem).
        *   Sección de Resumen y Pago:
            *   Subtotal Productos Pollo.
            *   Subtotal Productos Adicionales.
            *   (Opcional) Campo para Descuento.
            *   (Opcional, para Domicilio) Campo para Costo de Envío.
            *   **Total Pedido (grande y claro).**
            *   Selector `Forma de Pago`.
            *   Si es Efectivo: Campo `Paga Con`, y área para mostrar `Cambio Entregado` y `Denominaciones Sugeridas`.
        *   Campo para `Notas del Pedido`.
        *   Botones de Acción: "Guardar Pedido", "Enviar a Cocina", "Finalizar Venta", "Cancelar".
    *   **Interacción:**
        *   Actualización dinámica de precios y totales del carrito al añadir/modificar ítems (idealmente con AJAX para no recargar la página).
        *   Validación de campos en tiempo real o al intentar guardar.

3.  **Módulo de Caja (Corte de Caja):**
    *   **Propósito:** Interfaz para que el Cajero/Administrador realice el corte de caja.
    *   **Layout:**
        *   Sección de Información del Corte: Fecha, Hora, Usuario Responsable, Saldo Inicial Teórico.
        *   Sección de Saldos Teóricos (Calculados por el Sistema):
            *   Total Ingresos Efectivo (del periodo).
            *   Total Egresos Efectivo (del periodo).
            *   **Saldo Final Teórico en Efectivo.**
            *   (Resumen de totales para otras formas de pago: Tarjeta, Transferencia).
        *   Sección de Conteo Físico de Efectivo:
            *   Filas por cada `Denominacion` de moneda/billete (ej. "$500", "$200", ... "$0.50").
            *   Campo de entrada numérica para `Cantidad Contada` por cada denominación.
            *   Columna (auto-calculada) de `Total por Denominacion`.
            *   **Total Efectivo Contado (suma de todos los totales por denominación).**
        *   Sección de Diferencia:
            *   **Diferencia Efectivo (Total Contado - Total Teórico), con indicador de color.**
        *   Campo para `Notas del Corte`.
        *   Botones de Acción: "Guardar Conteo Parcial", "Finalizar y Cerrar Corte".
    *   **Interacción:**
        *   Los totales y la diferencia se actualizan dinámicamente a medida que el usuario ingresa las cantidades contadas por denominación.

4.  **Otras Vistas Clave (Breve Descripción):**
    *   **Gestión de Clientes:** Tabla listando clientes, con opciones para ver/editar detalles (direcciones, teléfonos, historial de pedidos). Formulario para crear/editar cliente.
    *   **Gestión de Productos:** (Principalmente para Admin) Tabla listando productos, subproductos, modificaciones. Formularios para CRUD de estas entidades y para la gestión de precios.
    *   **Historial de Pedidos:** Tabla con todos los pedidos (pasados y presentes), con filtros avanzados (fecha, cliente, estado, etc.) y opción de ver detalle.
    *   **Movimientos de Caja (Log):** Lista cronológica de todos los movimientos de caja, con filtros por fecha, tipo, usuario, motivo.
    *   **Login:** Formulario simple con campos para `username` y `password`.

### 6.3 Simbología y Códigos de Producto en UI

*   **Uso Extensivo de Simbología:**
    *   En el carrito de compras, al listar los ítems, mostrar la simbología junto al nombre para rápida identificación visual (ej. "🐔 PECH Entera", "🍗 AL Crt/2").
    *   En los tickets de venta y comandas de preparación.
    *   En las listas de pedidos del dashboard.
*   **Selectores de Producto:**
    *   Al seleccionar productos, el dropdown o campo de búsqueda podría mostrar "Pechuga (PECH)", "Alas (AL)", etc.
*   **Códigos Internos:** Los códigos (`PECH`, `PP`, `MOLI_PECH`) son principalmente para la lógica interna y la base de datos, pero pueden mostrarse sutilmente en interfaces administrativas o de configuración si ayuda a la claridad para usuarios avanzados (Admin). Para el Cajero, priman los nombres descriptivos y la simbología visual.

### 6.4 Estilo Visual y Componentes (Referencia a `estilo.css`)

*   La UI debe seguir estrictamente las directrices, variables y clases de utilidad definidas en el archivo `estilo.css` (o su equivalente si se estructura en varios archivos CSS).
*   **Componentes Reutilizables:**
    *   Botones: `.btn`, `.btn--primary`, `.btn--secondary`, `.btn--danger`, `.btn--sm`, etc.
    *   Tarjetas: `.card`, `.card__header`, `.card__body`, `.card__footer`.
    *   Formularios: `.form-group`, `.form-control`, `.form-label`, `.form-check`.
    *   Alertas: `.alert`, `.alert--success`, `.alert--error`.
    *   Tablas: Estilos para `<table>`, `<thead>`, `<tbody>`, `<th>`, `<td>`.
    *   Modales: Para confirmaciones o formularios emergentes.
*   **Espaciado y Tipografía:** Utilizar las variables CSS para márgenes, paddings (`var(--espacio-xs)`, `var(--espacio-s)`, etc.) y familias/tamaños de fuente (`var(--fuente-base)`, `var(--fuente-encabezado)`).
*   **Colores:** Usar la paleta de colores definida en las variables CSS (`var(--rojo-principal)`, `var(--verde-exito)`, `var(--amarillo-advertencia)`, `var(--gris-claro)`, etc.).

---
**Sección 7: Datos Maestros y de Ejemplo**.

En esta sección, consolidaremos los datos clave que el sistema utilizará, como el catálogo de productos detallado (que ya hemos trabajado bastante), tipos de cliente, formas de pago, estados de pedido y denominaciones de moneda. Estos datos son esenciales para poblar la base de datos inicial (seeding) y para que Copilot tenga ejemplos concretos al generar lógica o pruebas.

### 7.1 Catálogo de Productos de Pollo, Subproductos, Modificaciones y Precios

Esta sección detalla el catálogo inicial de productos de pollo, sus variantes (subproductos o especiales), las modificaciones (cortes o preparaciones) aplicables a cada uno, y sus estructuras de precios. Esta información es fundamental para poblar las tablas `Producto`, `Subproducto`, `Modificacion`, `Precio` y sus tablas de asociación.

**Convenciones de Códigos:**

*   **Producto Principal:** Ej. `PECH`
*   **Subproducto/Especial:** Ej. `PP` (Pulpa de Pechuga), `CD` (Cadera)
*   **Modificación:** Ej. `ENT` (Entera), `MOLI` (Molida), `ASAR` (Para Asar). Se añadirán sufijos para denotar a qué aplican si es necesario para desambiguar (ej. `ASAR_PP`, `ASAR_PECH`).

---
**Producto Principal: Pechuga de Pollo**
*   **Código Producto Principal:** `PECH`
*   **Nombre Producto Principal:** Pechuga de Pollo
*   **Categoría:** Pollo Crudo
*   **Activo:** `True`

*   **Subproductos Asociados:**
    *   **Subproducto 1.1:**
        *   **Código Subproducto:** `PP`
        *   **Nombre Subproducto:** Pulpa de Pechuga
        *   **Producto Padre:** `PECH`
        *   **Activo:** `True`
        *   **Modificaciones Aplicables a `PP` (Pulpa de Pechuga):**
            *   `ASAR_PP`: Para Asar
            *   `MILA_PP`: Milanesa
            *   `CUBOS_PP`: En Cubos
            *   `MOLI_PP`: Molida
            *   `FILE_PP`: Filetes
            *   `ENT_PP`: Entera (la pulpa)
        *   **Precios para `PP` (Pulpa de Pechuga):**
            *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 185.00`, `CANT_MIN_KG: 0`
            *   `TIPO_CLIENTE: COCINA`, `PRECIO_KG: 165.00`, `CANT_MIN_KG: 0`

*   **Modificaciones Aplicables directamente a `PECH` (Pechuga Entera/Base):**
    *   `ENT_PECH`: Entera
    *   `CORT2_PECH`: Cortada en 2 piezas
    *   `CORT3_PECH`: Cortada en 3 piezas
    *   `CORT4_PECH`: Cortada en 4 piezas
    *   `CORT6_PECH`: Cortada en 6 piezas
    *   `ASAR_PECH`: Para Asar
    *   `FREIR_PECH`: Para Freír
    *   `MILA_PECH`: Milanesa
    *   `FAJI_PECH`: Fajitas
    *   `CUBOS_PECH`: En Cubos
    *   `MOLI_PECH`: Molida
    *   `FILE_PECH`: Filetes

*   **Precios para `PECH` (Pechuga Entera/Base):**
    *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 120.00`, `CANT_MIN_KG: 0`
    *   `TIPO_CLIENTE: COCINA`, `PRECIO_KG: 115.00`, `CANT_MIN_KG: 0`
    *   `TIPO_CLIENTE: LEAL`, `PRECIO_KG: 110.00`, `CANT_MIN_KG: 0`
    *   `TIPO_CLIENTE: ALIADO`, `PRECIO_KG: 105.00`, `CANT_MIN_KG: 0`
    *   `TIPO_CLIENTE: MAYOREO`, `PRECIO_KG: 100.00`, `CANT_MIN_KG: 10`, `ETIQUETA_PROMO: Precio Mayoreo (desde 10kg)`
---
**Producto Principal: Alas de Pollo**
*   **Código Producto Principal:** `AL`
*   **Nombre Producto Principal:** Alas de Pollo
*   **Categoría:** Pollo Crudo
*   **Activo:** `True`

*   **Subproductos Asociados:** Ninguno.

*   **Modificaciones Aplicables a `AL` (Alas):**
    *   `ENT_AL`: Enteras
    *   `CORT2_AL`: Cortadas en 2 (drumette y flat)
    *   `CORT3_AL`: Cortadas en 3 (drumette, flat y tip)

*   **Precios para `AL` (Alas):**
    *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 118.00`, `CANT_MIN_KG: 0`
    *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 115.00`, `CANT_MIN_KG: 10`, `ETIQUETA_PROMO: Paquete Alas 10kg`
    *   `TIPO_CLIENTE: COCINA`, `PRECIO_KG: 107.00`, `CANT_MIN_KG: 0`
    *   `TIPO_CLIENTE: MAYOREO`, `PRECIO_KG: 100.00`, `CANT_MIN_KG: 10`, `ETIQUETA_PROMO: Precio Mayoreo (desde 10kg)`
---
**Producto Principal: Retazo de Pollo**
*   **Código Producto Principal:** `RTZ`
*   **Nombre Producto Principal:** Retazo de Pollo
*   **Categoría:** Pollo Crudo
*   **Activo:** `True`

*   **Subproductos Asociados (Considerados como "Especiales" del Retazo):**
    *   **Subproducto 3.1 (Especial):**
        *   **Código Subproducto:** `CD`
        *   **Nombre Subproducto:** Cadera de Pollo
        *   **Producto Padre:** `RTZ`
        *   **Activo:** `True`
        *   **Modificaciones Aplicables a `CD` (Cadera):**
            *   `ENT_CD`: Entera
            *   `CORT_CD`: Cortada
            *   `SINPIEL_CD`: Sin Piel
        *   **Precios para `CD` (Cadera):** (Asignar un precio si se vende individualmente, o se puede calcular como un porcentaje del precio de RTZ o tener su propio precio base).
            *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 45.00`, `CANT_MIN_KG: 0` *(Precio ejemplo si se vende por separado)*

    *   **Subproducto 3.2 (Especial):**
        *   **Código Subproducto:** `HCL` *(Usamos HCL en lugar de H para evitar confusión con Hígado)*
        *   **Nombre Subproducto:** Huacal de Pollo
        *   **Producto Padre:** `RTZ`
        *   **Activo:** `True`
        *   **Modificaciones Aplicables a `HCL` (Huacal):**
            *   `ENT_HCL`: Entero
            *   `CORT_HCL`: Cortado
        *   **Precios para `HCL` (Huacal):**
            *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 25.00`, `CANT_MIN_KG: 0` *(Precio ejemplo si se vende por separado)*

*   **Modificaciones Aplicables directamente a `RTZ` (Retazo General):**
    *   `ENT_RTZ`: Entero
    *   `CORT_RTZ`: Cortado
    *   `SINPIEL_RTZ`: Sin Piel

*   **Precios para `RTZ` (Retazo General):**
    *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 40.00`, `CANT_MIN_KG: 0`
    *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 25.00`, `CANT_MIN_KG: 2`, `ETIQUETA_PROMO: Promo Retazo 2kg`
    *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 20.00`, `CANT_MIN_KG: 3`, `ETIQUETA_PROMO: Promo Retazo 3kg`
---
**Producto Principal: Perniles de Pollo**
*   **Código Producto Principal:** `PM`
*   **Nombre Producto Principal:** Perniles (Pierna y Muslo unidos o separados)
*   **Categoría:** Pollo Crudo
*   **Activo:** `True`

*   **Subproductos Asociados (Partes o Derivados del Pernil):**
    *   **Subproducto 4.1 (Parte Principal):**
        *   **Código Subproducto:** `PG`
        *   **Nombre Subproducto:** Pierna de Pollo
        *   **Producto Padre:** `PM`
        *   **Activo:** `True`
        *   **Modificaciones Aplicables a `PG` (Pierna):**
            *   `ENT_PG`: Enteras
            *   `ASAR_PG`: Para Asar
            *   `MILA_PG`: Milanesa
            *   `FREIR_PG`: Para Freír
            *   `SINPIEL_PG`: Sin Piel
        *   **Precios para `PG` (Pierna):**
            *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 95.00`, `CANT_MIN_KG: 0`

    *   **Subproducto 4.2 (Parte Principal):**
        *   **Código Subproducto:** `MSL`
        *   **Nombre Subproducto:** Muslo de Pollo
        *   **Producto Padre:** `PM`
        *   **Activo:** `True`
        *   **Modificaciones Aplicables a `MSL` (Muslo):**
            *   `ENT_MSL`: Entero(s)
            *   `ASAR_MSL`: Para Asar
            *   `FREIR_MSL`: Para Freír
            *   `MILA_MSL`: Milanesa
            *   `SINPIEL_MSL`: Sin Piel
        *   **Precios para `MSL` (Muslo):**
            *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 85.00`, `CANT_MIN_KG: 0`

    *   **Subproducto 4.3 (Derivado):**
        *   **Código Subproducto:** `PP-PM`
        *   **Nombre Subproducto:** Pulpa de Perniles (Pierna y Muslo)
        *   **Producto Padre:** `PM`
        *   **Activo:** `True`
        *   **Modificaciones Aplicables a `PP-PM`:**
            *   `ASAR_PPPM`: Para Asar
            *   `MILA_PPPM`: Milanesa
            *   `FAJI_PPPM`: Fajitas
            *   `ENT_PPPM`: Entera (la pulpa)
        *   **Precios para `PP-PM`:**
            *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 105.00`, `CANT_MIN_KG: 0`
            *   `TIPO_CLIENTE: MAYOREO`, `PRECIO_KG: 95.00`, `CANT_MIN_KG: 5`, `ETIQUETA_PROMO: Mayoreo Pulpa Pernil (desde 5kg)`

    *   **Subproducto 4.4 (Derivado):**
        *   **Código Subproducto:** `M-PM`
        *   **Nombre Subproducto:** Molida de Perniles (Pierna y Muslo)
        *   **Producto Padre:** `PM`
        *   **Activo:** `True`
        *   **Modificaciones Aplicables a `M-PM`:**
            *   `NINGUNA_MPM`: (Generalmente ninguna, ya es molida)
        *   **Precios para `M-PM`:**
            *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 110.00`, `CANT_MIN_KG: 0`

*   **Modificaciones Aplicables directamente a `PM` (Perniles como conjunto o pieza grande):**
    *   `ENT_PM`: Enteros (unidos pierna y muslo)
    *   `CORT_PM`: Cortados (separados en pierna y muslo)
    *   `ASAR_PM`: Para Asar (unidos)
    *   `MILA_PM`: Milanesa (de la pieza completa si es viable)
    *   `FREIR_PM`: Para Freír (unidos)
    *   `SINPIEL_PM`: Sin Piel

*   **Precios para `PM` (Perniles como conjunto):**
    *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 85.00`, `CANT_MIN_KG: 0`
    *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 80.00`, `CANT_MIN_KG: 2`, `ETIQUETA_PROMO: Promo Perniles 2kg`
    *   `TIPO_CLIENTE: COCINA`, `PRECIO_KG: 70.00`, `CANT_MIN_KG: 0`
---
**Producto Principal: Patas de Pollo**
*   **Código Producto Principal:** `PT`
*   **Nombre Producto Principal:** Patas de Pollo
*   **Categoría:** Menudencia
*   **Activo:** `True`

*   **Subproductos Asociados:** Ninguno.

*   **Modificaciones Aplicables a `PT` (Patas):**
    *   `LIMP_PT`: Limpias (sin uñas, etc.)
    *   `ENT_PT`: Enteras (como vienen)

*   **Precios para `PT` (Patas):**
    *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 65.00`, `CANT_MIN_KG: 0`
    *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 55.00`, `CANT_MIN_KG: 2`, `ETIQUETA_PROMO: Promo Patas 2kg`
---
**Producto Principal: Molleja con Hígado**
*   **Código Producto Principal:** `MHG`
*   **Nombre Producto Principal:** Molleja con Hígado (Paquete)
*   **Categoría:** Menudencia
*   **Activo:** `True`

*   **Subproductos Asociados (Partes que se pueden vender por separado):**
    *   **Subproducto 6.1:**
        *   **Código Subproducto:** `MLJ`
        *   **Nombre Subproducto:** Molleja de Pollo (Sola)
        *   **Producto Padre:** `MHG`
        *   **Activo:** `True`
        *   **Modificaciones Aplicables a `MLJ` (Molleja):**
            *   `SINGRASA_MLJ`: Sin Grasa
            *   `LIMP_MLJ`: Limpia
        *   **Precios para `MLJ` (Molleja Sola):**
            *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 65.00`, `CANT_MIN_KG: 0`

    *   **Subproducto 6.2:**
        *   **Código Subproducto:** `HGD`
        *   **Nombre Subproducto:** Hígado de Pollo (Solo)
        *   **Producto Padre:** `MHG`
        *   **Activo:** `True`
        *   **Modificaciones Aplicables a `HGD` (Hígado):**
            *   `LIMP_HGD`: Limpio
        *   **Precios para `HGD` (Hígado Solo):**
            *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 25.00`, `CANT_MIN_KG: 0`

*   **Modificaciones Aplicables directamente a `MHG` (Paquete Molleja con Hígado):**
    *   `SINGRASA_MHG`: Sin Grasa (principalmente para la molleja del paquete)
    *   `LIMP_MHG`: Limpios (ambos componentes)

*   **Precios para `MHG` (Paquete Molleja con Hígado):**
    *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 35.00`, `CANT_MIN_KG: 0`
    *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 25.00`, `CANT_MIN_KG: 2`, `ETIQUETA_PROMO: Promo Molleja c/Hígado 2kg`
---
**Producto Principal: Pollo Surtido**
*   **Código Producto Principal:** `SRT`
*   **Nombre Producto Principal:** Pollo Surtido (Piezas Variadas)
*   **Categoría:** Pollo Crudo
*   **Descripción:** Mezcla de diferentes piezas de pollo, usualmente incluye pierna, muslo, ala, huacal y/o cadera.
*   **Activo:** `True`

*   **Subproductos Asociados:** Ninguno (es una mezcla definida).

*   **Modificaciones Aplicables a `SRT` (Surtida):**
    *   `CONHCL_SRT`: Con Huacal (asegurar que incluya huacal)
    *   `CONCD_SRT`: Con Cadera (asegurar que incluya cadera)
    *   `SINPIEL_SRT`: Predominantemente Sin Piel (las piezas que lo permitan)
    *   `PIEZASGRANDES_SRT`: Piezas Grandes
    *   `PIEZASCHICAS_SRT`: Piezas Chicas/Medianas

*   **Precios para `SRT` (Surtida):**
    *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 68.00`, `CANT_MIN_KG: 0`
    *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 65.00`, `CANT_MIN_KG: 2`, `ETIQUETA_PROMO: Promo Surtida 2kg`
    *   `TIPO_CLIENTE: PUBLICO`, `PRECIO_KG: 60.00`, `CANT_MIN_KG: 3`, `ETIQUETA_PROMO: Promo Surtida 3kg`
    *   `TIPO_CLIENTE: COCINA`, `PRECIO_KG: 60.00`, `CANT_MIN_KG: 0`
---

### 7.2 Tipos de Cliente

Estos son los valores predefinidos para el campo `tipo_cliente` en el modelo `Cliente` y que se utilizan como referencia en el modelo `Precio` para aplicar tarifas diferenciadas.

| Código        | Nombre Descriptivo    | Descripción Detallada                                                                  |
|---------------|-----------------------|----------------------------------------------------------------------------------------|
| `PUBLICO`     | Público General       | Cliente estándar sin descuentos preestablecidos. Tarifa base.                          |
| `COCINA`      | Cocina / Restaurante  | Negocios del sector gastronómico (restaurantes, fondas, comedores) que suelen comprar con mayor frecuencia o volumen y pueden tener precios preferenciales. |
| `LEAL`        | Cliente Leal/Frecuente| Cliente individual reconocido por su lealtad y frecuencia de compra, puede acceder a promociones o pequeños descuentos específicos. |
| `ALIADO`      | Aliado Comercial      | Revendedores, pequeños distribuidores o negocios asociados con acuerdos de precios especiales para la reventa o uso en sus productos. |
| `MAYOREO`     | Cliente de Mayoreo    | Clientes que realizan compras de gran volumen (ej. para eventos, carnicerías más pequeñas) y acceden a precios de mayoreo, usualmente condicionados a una cantidad mínima. |
| `EMPLEADO`    | Empleado              | (Opcional, si se implementa) Para registrar ventas internas a empleados, posiblemente con un descuento fijo o política especial. |
| `GENERICO_MOSTRADOR` | Cliente Mostrador Genérico | (Valor especial para el sistema) Usado para ventas rápidas en mostrador donde no se identifican los datos del cliente. Se le aplica tarifa `PUBLICO`. |

**Nota:** El sistema debe permitir al Administrador gestionar (añadir, editar, desactivar) estos tipos de cliente en una fase posterior, aunque para el MVP se pueden hardcodear o cargar desde una semilla inicial.

---

### 7.3 Formas de Pago

Estos son los valores predefinidos para el campo `forma_pago` en el modelo `Pedido` y `forma_pago_efectuado` en `MovimientoCaja`. Indican cómo se liquidó una transacción o se realizó un movimiento de caja.

| Código                  | Nombre Descriptivo      | Descripción Detallada                                                                 | ¿Implica Movimiento de Efectivo en Caja? |
|-------------------------|-------------------------|---------------------------------------------------------------------------------------|------------------------------------------|
| `EFECTIVO`              | Efectivo                | Pago realizado con billetes y monedas físicas.                                        | Sí                                       |
| `TARJETA_DEBITO`        | Tarjeta de Débito       | Pago realizado mediante terminal punto de venta (TPV) con tarjeta de débito.          | No (Ingreso bancario)                    |
| `TARJETA_CREDITO`       | Tarjeta de Crédito      | Pago realizado mediante TPV con tarjeta de crédito.                                   | No (Ingreso bancario)                    |
| `TRANSFERENCIA_BANCARIA`| Transferencia Bancaria  | Pago recibido mediante transferencia electrónica (SPEI, TEF).                          | No (Ingreso bancario)                    |
| `QR_PAGO`               | Pago con Código QR      | Pago realizado mediante aplicaciones de pago que utilizan códigos QR (CoDi, MercadoPago QR, etc.). | No (Ingreso a cuenta digital/bancaria) |
| `CREDITO_INTERNO`       | Crédito Interno         | Venta realizada a crédito a un cliente autorizado (ej. `COCINA`). El pago se registra posteriormente. | No (hasta que el crédito se pague)       |
| `CORTESIA`              | Cortesía / Sin Costo    | El pedido fue una cortesía de la casa, no generó ingreso monetario.                  | No                                       |
| `PAGO_MULTIPLE`         | Pago Múltiple           | (Para `Pedido.forma_pago` si se permite) El cliente usó más de una forma de pago (ej. parte efectivo, parte tarjeta). Los `MovimientoCaja` detallarían cada parte. | Depende de los componentes           |
| `GASTO_INTERNO_CAJA`    | Gasto Interno de Caja   | (Solo para `MovimientoCaja`) Salida de efectivo de la caja para un gasto operativo menor. | Sí (Egreso)                              |
| `AJUSTE_INGRESO_CAJA`   | Ajuste Ingreso en Caja  | (Solo para `MovimientoCaja`) Ingreso manual para corregir sobrante en caja.           | Sí (Ingreso)                             |
| `AJUSTE_EGRESO_CAJA`    | Ajuste Egreso en Caja   | (Solo para `MovimientoCaja`) Egreso manual para corregir faltante en caja.            | Sí (Egreso)                              |
| `SALDO_INICIAL_CAJA`    | Saldo Inicial de Caja   | (Solo para `MovimientoCaja`) Registro del efectivo al iniciar un `CorteCaja`.         | Sí (Ingreso "virtual" al periodo)        |
| `RETIRO_EFECTIVO_CAJA`  | Retiro de Efectivo      | (Solo para `MovimientoCaja`) Retiro de efectivo de la caja para depósito bancario o resguardo. | Sí (Egreso)                              |

---

### 7.4 Estados de Pedido

Estos son los valores predefinidos para el campo `estado_pedido` en el modelo `Pedido`. Definen el flujo y el estado actual de un pedido dentro del sistema.

| Código                             | Nombre Descriptivo             | Descripción Detallada                                                                                                 |
|------------------------------------|--------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| `PENDIENTE_CONFIRMACION`           | Pendiente de Confirmación      | Pedido tomado (ej. por teléfono/WhatsApp) pero aún no ha sido confirmado por el cliente para su preparación.          |
| `PENDIENTE_PREPARACION`            | Pendiente de Preparación       | Pedido confirmado por el cliente y/o Cajero, listo para que el área de Tablajería comience a prepararlo.               |
| `EN_PREPARACION`                   | En Preparación                 | El Tablajero está actualmente alistando los productos del pedido (cortando, pesando, modificando).                   |
| `LISTO_PARA_ENTREGA`               | Listo para Entrega/Recogida    | Todos los ítems del pedido han sido preparados y están listos para ser entregados al cliente en mostrador o asignados a un repartidor. |
| `ASIGNADO_A_REPARTIDOR`            | Asignado a Repartidor          | (Solo Domicilio) El pedido ha sido asignado a un repartidor específico para su entrega.                                 |
| `EN_RUTA`                          | En Ruta                        | (Solo Domicilio) El repartidor ha salido de la pollería y está en camino para entregar el pedido.                       |
| `ENTREGADO_PENDIENTE_PAGO`         | Entregado, Pendiente de Pago   | (Solo Domicilio, si aplica) El cliente recibió el pedido, pero el repartidor aún no liquida el pago en caja.           |
| `ENTREGADO_Y_PAGADO`               | Entregado y Pagado             | El cliente recibió el pedido y el pago ha sido completado y registrado en el sistema (para mostrador o liquidación de repartidor). |
| `PAGADO`                           | Pagado                         | (Estado general) El pedido ha sido completamente pagado. Puede ser un estado final o transitorio antes de 'ENTREGADO_Y_PAGADO'. |
| `PROBLEMA_EN_ENTREGA`              | Problema en Entrega            | (Solo Domicilio) Hubo un inconveniente durante el intento de entrega (cliente no encontrado, dirección errónea, etc.). Requiere acción. |
| `REPROGRAMADO`                     | Reprogramado                   | (Solo Domicilio) La entrega del pedido ha sido reprogramada para una fecha/hora posterior.                             |
| `CANCELADO_POR_CLIENTE`            | Cancelado por Cliente          | El cliente solicitó la cancelación del pedido.                                                                        |
| `CANCELADO_POR_NEGOCIO`            | Cancelado por Negocio          | La pollería tuvo que cancelar el pedido (ej. falta de producto irreparable, problema logístico mayor).                 |

**Nota:** El flujo exacto y los estados disponibles para transición dependerán de la lógica de negocio implementada (ej. un pedido `EN_RUTA` no puede volver a `PENDIENTE_PREPARACION` directamente).

---

### 7.5 Denominaciones de Moneda (México - MXN)

Estos son los valores numéricos para el campo `denominacion_valor` en los modelos `MovimientoDenominacion` y `DenominacionCorteCaja`, representando los billetes y monedas de curso legal en México (MXN) que se espera maneje la pollería.

*   **Monedas (Valor Numérico):**
    *   `0.50`
    *   `1.00`
    *   `2.00`
    *   `5.00`
    *   `10.00`
    *   `20.00` *(Considerar si la moneda de $20 se maneja comúnmente o se agrupa con el billete)*
*   **Billetes (Valor Numérico):**
    *   `20.00`
    *   `50.00`
    *   `100.00`
    *   `200.00`
    *   `500.00`
    *   `1000.00` *(Definir si la pollería acepta y maneja billetes de $1000 de forma regular. Si no, se puede omitir o marcar como "aceptación especial")*

**Nota:** El sistema debe permitir al Administrador configurar qué denominaciones están activas o se utilizan para el conteo en `ConfiguracionSistema` si es necesario.

---

### 7.6 Motivos Comunes de Movimiento de Caja

Estos son ejemplos y valores sugeridos para el campo `motivo_movimiento` en el modelo `MovimientoCaja`. El objetivo es estandarizar las descripciones para facilitar la auditoría y la generación de reportes. El sistema puede permitir la entrada de motivos libres, pero ofrecer estos como una lista predefinida o autocompletado. Los placeholders `{{...}}` serían reemplazados dinámicamente por el sistema.

*   **Ingresos por Ventas:**
    *   `Venta Pedido Mostrador #{{ID_PEDIDO}}`
    *   `Venta Pedido Domicilio #{{ID_PEDIDO}} (Pago en Entrega)`
    *   `Liquidación Pedido Domicilio #{{ID_PEDIDO}} por Repartidor {{NOMBRE_REPARTIDOR}}`
    *   `Anticipo Pedido #{{ID_PEDIDO}}`
    *   `Pago de Crédito Cliente {{NOMBRE_CLIENTE}} - Pedido #{{ID_PEDIDO_O_REFERENCIA}}`
*   **Ingresos Varios:**
    *   `Ingreso Diverso: {{DESCRIPCION_INGRESO_DIVERSO}}`
    *   `Ajuste por Sobrante en Corte de Caja #{{ID_CORTE}}`
    *   `Saldo Inicial Apertura de Caja - Turno {{IDENTIFICADOR_TURNO}} / Fecha {{FECHA}}`
*   **Egresos por Compras y Operación:**
    *   `Compra PA para Pedido #{{ID_PEDIDO}} - {{DESCRIPCION_PA}}`
    *   `Entrega de Cambio a Repartidor {{NOMBRE_REPARTIDOR}} para Ruta Pedidos #{{LISTA_IDS_PEDIDOS}}`
    *   `Compra de Mercancía/Insumos Proveedor {{NOMBRE_PROVEEDOR}} - Fact. #{{NUM_FACTURA}}`
    *   `Pago de Servicio: {{TIPO_SERVICIO}} (ej. Luz, Agua, Renta) - Periodo {{PERIODO}}`
    *   `Gasto Operativo Menor: {{DESCRIPCION_GASTO}}` (ej. Papelería, Limpieza, Gasolina Moto)
    *   `Devolución a Cliente Pedido #{{ID_PEDIDO}}`
*   **Egresos por Retiros y Ajustes:**
    *   `Retiro Parcial de Caja por {{NOMBRE_RESPONSABLE_RETIRO}}`
    *   `Retiro Final de Caja para Depósito/Resguardo (Cierre Día {{FECHA}})`
    *   `Ajuste por Faltante en Corte de Caja #{{ID_CORTE}}`
*   **Egresos por Nómina/Préstamos (si se manejan por caja):**
    *   `Pago de Nómina Empleado {{NOMBRE_EMPLEADO}} - Periodo {{PERIODO_NOMINA}}`
    *   `Préstamo a Empleado {{NOMBRE_EMPLEADO}}`

---
**Sección 8: Consideraciones de Seguridad**.

Esta sección es fundamental para asegurar que el sistema se desarrolle teniendo en cuenta las buenas prácticas de seguridad desde el inicio, protegiendo los datos de la pollería y de sus clientes, y previniendo accesos no autorizados o actividades maliciosas.

## 8. Consideraciones de Seguridad

La seguridad es un aspecto integral del desarrollo del Sistema de Gestión para Pollería Montiel (SGPM). Se deben implementar medidas proactivas para proteger la confidencialidad, integridad y disponibilidad de los datos y funcionalidades del sistema. Las siguientes consideraciones deben ser tenidas en cuenta durante todo el ciclo de vida del desarrollo:

### 8.1 Autenticación Segura

1.  **Contraseñas Robustas:**
    *   **Hashing y Salting:** Todas las contraseñas de usuario deben almacenarse en la base de datos utilizando algoritmos de hashing robustos y actualizados (ej. Argon2, scrypt, o como mínimo PBKDF2_sha256 disponible en `werkzeug.security`) con un salt único por usuario. **Nunca almacenar contraseñas en texto plano.**
    *   **Política de Contraseñas (Recomendación Futura):** Para fases posteriores, considerar implementar políticas de complejidad de contraseñas (longitud mínima, combinación de caracteres) y expiración periódica, aunque para el MVP puede ser más simple.
2.  **Protección contra Ataques de Fuerza Bruta:**
    *   Implementar mecanismos de limitación de intentos de inicio de sesión (rate limiting) para una IP o cuenta de usuario después de un número determinado de intentos fallidos (ej. bloqueo temporal).
    *   Considerar el uso de CAPTCHA después de varios intentos fallidos (puede ser excesivo para un sistema interno MVP, pero tenerlo en cuenta).
3.  **Manejo de Sesiones Seguro:**
    *   Utilizar el sistema de sesiones de Flask (`SecureCookieSessionInterface`) que firma criptográficamente las cookies de sesión para prevenir su manipulación.
    *   Configurar las cookies de sesión con los atributos `HttpOnly`, `Secure` (en producción sobre HTTPS) y `SameSite=Lax` o `SameSite=Strict`.
    *   Implementar un tiempo de expiración razonable para las sesiones inactivas, forzando al usuario a re-autenticarse.
    *   Proveer una funcionalidad clara de "Cerrar Sesión" que invalide la sesión en el servidor y elimine la cookie del cliente.

### 8.2 Autorización y Control de Acceso

1.  **Principio de Mínimo Privilegio:**
    *   Los usuarios solo deben tener acceso a los datos y funcionalidades estrictamente necesarios para realizar sus tareas asignadas, según lo definido en la **Sección 2: Roles de Usuario y Permisos**.
2.  **Control de Acceso Basado en Roles (RBAC):**
    *   Implementar decoradores personalizados en Flask (ej. `@login_required` de Flask-Login, y un `@role_required(['ADMINISTRADOR', 'CAJERO'])` personalizado) para proteger rutas y acciones específicas, verificando el rol del usuario autenticado.
    *   La lógica de negocio también debe verificar permisos antes de realizar operaciones sensibles, no confiando únicamente en la protección de la interfaz de usuario.
3.  **Protección de Rutas y Endpoints:**
    *   Asegurar que todos los endpoints que modifican datos o exponen información sensible estén debidamente protegidos y requieran autenticación y autorización adecuada.
    *   Evitar la exposición de IDs o información sensible en URLs cuando no sea estrictamente necesario (aunque para un sistema interno es menos crítico que para uno público).

### 8.3 Protección contra Vulnerabilidades Comunes de Aplicaciones Web

1.  **Prevención de Cross-Site Scripting (XSS):**
    *   **Escapado de Salidas:** Jinja2 (el motor de plantillas de Flask) escapa automáticamente las variables por defecto. Mantener esta configuración y ser extremadamente cauto al usar el filtro `|safe`, asegurándose de que el contenido es sanitizado o de una fuente confiable.
    *   **Content Security Policy (CSP):** Considerar la implementación de cabeceras CSP para mitigar el riesgo de XSS y otros ataques de inyección (puede ser para una fase post-MVP si la complejidad inicial es alta).
2.  **Prevención de Cross-Site Request Forgery (CSRF):**
    *   Utilizar la extensión Flask-WTF (o Flask-SeaSurf) para generar e validar tokens CSRF en todos los formularios que realicen acciones de modificación de estado (POST, PUT, DELETE).
3.  **Prevención de Inyección SQL:**
    *   **Uso Exclusivo de ORM:** Priorizar el uso de SQLAlchemy (ORM) para todas las interacciones con la base de datos. El ORM maneja el escapado de parámetros y previene la mayoría de los ataques de inyección SQL.
    *   **Consultas Crudas con Precaución:** Si por alguna razón extrema se necesita usar consultas SQL crudas, asegurarse de que todos los parámetros de entrada del usuario sean debidamente sanitizados o parametrizados.
4.  **Redirecciones y Reenvíos Seguros:**
    *   Validar y sanitizar todas las URLs proporcionadas por el usuario antes de realizar redirecciones para evitar ataques de "Open Redirect". No redirigir a URLs externas a menos que estén en una lista blanca.
5.  **Manejo Seguro de Carga de Archivos (si se implementa):**
    *   Validar el tipo de archivo (MIME type y extensión), el tamaño del archivo.
    *   Almacenar los archivos cargados fuera del directorio raíz de la web o con permisos de ejecución desactivados.
    *   Utilizar nombres de archivo generados por el sistema para evitar ataques de path traversal.
    *   (No parece ser una funcionalidad del MVP actual, pero es una consideración general).

### 8.4 Seguridad de la Configuración y el Entorno

1.  **Variables de Entorno para Datos Sensibles:**
    *   Almacenar claves secretas (`SECRET_KEY` de Flask), credenciales de base de datos (para producción), claves API, etc., en variables de entorno y no directamente en el código. Utilizar un archivo `.env` (añadido a `.gitignore`) y la librería `python-dotenv` para cargarlas.
2.  **Modo DEBUG Desactivado en Producción:**
    *   Asegurar que la variable `DEBUG` de Flask esté configurada a `False` en entornos de producción para evitar la exposición de información sensible de depuración y stack traces.
3.  **HTTPS en Producción:**
    *   Todo el tráfico en el entorno de producción debe ser servido sobre HTTPS para cifrar la comunicación entre el cliente y el servidor. Configurar el servidor web (Nginx/Gunicorn) para forzar HTTPS.
4.  **Actualizaciones de Software:**
    *   Mantener actualizadas todas las dependencias del proyecto (Python, Flask, SQLAlchemy, librerías de frontend, sistema operativo del servidor) para protegerse contra vulnerabilidades conocidas. Utilizar herramientas de gestión de dependencias y auditoría (ej. `pip-audit`, Snyk).
5.  **Logging y Monitorización:**
    *   Implementar un sistema de logging robusto (ver Sección 4.1 de "Instrucciones para GitHub Copilot") para registrar eventos de seguridad importantes, intentos de acceso fallidos, errores y actividad sospechosa.
    *   Monitorizar los logs regularmente.

### 8.5 Protección de Datos (Consideraciones de Privacidad)

1.  **Manejo de Datos Personales:**
    *   Aunque es un sistema interno, los datos de clientes (nombres, teléfonos, direcciones) son información personal. Limitar el acceso a esta información según los roles.
    *   Considerar políticas de retención de datos y mecanismos para anonimizar o eliminar datos de clientes si es necesario en el futuro (cumplimiento normativo).
2.  **No Exponer Datos Innecesarios:**
    *   Las APIs y vistas solo deben exponer la cantidad mínima de información necesaria para su propósito. Evitar devolver objetos completos de la base de datos si solo se necesitan unos pocos campos.

### 8.6 Seguridad Física y de Acceso (Contexto Operativo)

*   Aunque fuera del alcance del software en sí, recordar a Pollería Montiel la importancia de proteger el acceso físico a los terminales donde se usa el sistema y asegurar que los empleados no compartan sus credenciales de acceso.

---
**Sección 9: Próximos Pasos y Fases de Desarrollo**.


## 9. Próximos Pasos y Fases de Desarrollo

El desarrollo del Sistema de Gestión para Pollería Montiel (SGPM) se llevará a cabo de manera iterativa e incremental, siguiendo un enfoque por fases. Este enfoque permite entregar valor de forma continua, obtener retroalimentación temprana y gestionar la complejidad del proyecto de manera más efectiva.

Las fases de desarrollo detalladas, incluyendo los objetivos y tareas clave para cada una, se encuentran especificadas en el documento complementario: **"Instrucciones para GitHub Copilot: Proyecto Pollería Montiel", Sección 7: Fases de Desarrollo Sugeridas (MVP y Post-MVP)**. Se recomienda consultar dicho documento para una comprensión completa del plan de trabajo.

A continuación, se presenta un resumen de alto nivel de estas fases para contextualizar los próximos pasos inmediatos tras la finalización de este documento de especificaciones:

**Resumen de Fases de Desarrollo:**

1.  **Fase 0: Fundación y Configuración Inicial**
    *   **Objetivo Principal:** Establecer la estructura básica del proyecto Flask, configurar el entorno de desarrollo, definir los modelos SQLAlchemy iniciales y poner en marcha el control de versiones.
    *   **Próximo Paso Inmediato:** Implementación de la estructura de directorios del proyecto, configuración de `app.py`, `config.py`, y creación de los modelos base (`Usuario`, `Producto`, `Cliente`) en `models.py` según lo detallado en la Sección 3 de este documento.

2.  **Fase 1: Gestión de Datos Maestros y Autenticación**
    *   **Objetivo Principal:** Desarrollar los módulos CRUD para las entidades principales (Productos, Clientes) y el sistema de autenticación y gestión de sesiones para usuarios.

3.  **Fase 2: Operaciones de Venta en Mostrador y Caja Inicial**
    *   **Objetivo Principal:** Implementar el flujo completo de venta en mostrador, incluyendo la gestión del carrito de compras, cálculo de totales y cambio, y el registro básico de movimientos de caja.

4.  **Fase 3: Pedidos a Domicilio y Gestión de Repartidores (Básico)**
    *   **Objetivo Principal:** Extender la funcionalidad de pedidos para incluir entregas a domicilio, asignación de repartidores y seguimiento básico de estados de entrega.

5.  **Fase 4: Gestión de Productos Adicionales (PAs) y Caja Avanzada**
    *   **Objetivo Principal:** Integrar la funcionalidad para manejar Productos Adicionales (PAs) y desarrollar las características avanzadas de gestión de caja, incluyendo el control de denominaciones y cortes de caja detallados.

6.  **Fase 5: Roles, Permisos Detallados y Reportes Básicos**
    *   **Objetivo Principal:** Refinar la implementación de roles y permisos en todas las funcionalidades del sistema y desarrollar los reportes básicos definidos (ventas, caja).

7.  **Fase 6: Mejoras de UI/UX y Funcionalidades Adicionales**
    *   **Objetivo Principal:** Pulir la interfaz de usuario, mejorar la experiencia general del usuario basándose en la retroalimentación, y añadir funcionalidades de valor secundarias que no fueron críticas para el MVP inicial.

8.  **Fase 7: Pruebas Exhaustivas, Optimización y Despliegue (Preparación para Producción)**
    *   **Objetivo Principal:** Realizar pruebas completas del sistema, optimizar el rendimiento y preparar la aplicación para su despliegue en un entorno de producción o producción ligera.

**Siguientes Pasos Inmediatos (Post-Documentación):**

1.  **Revisión y Validación Final del Documento:** Asegurar que todas las partes interesadas (equipo de desarrollo, representantes de Pollería Montiel) revisen y aprueben este documento de especificaciones.
2.  **Configuración del Entorno de Desarrollo:** Preparar los entornos locales de los desarrolladores con Python, Flask, SQLAlchemy, Git, y las herramientas necesarias.
3.  **Inicio de la Fase 0:** Comenzar con las tareas de la "Fase 0: Fundación y Configuración Inicial", priorizando la creación de la estructura del proyecto y los modelos de datos base.
4.  **Planificación de Sprints/Iteraciones (si se usa metodología ágil):** Desglosar las tareas de las primeras fases en unidades de trabajo más pequeñas y planificar las primeras iteraciones de desarrollo.
5.  **Comunicación Continua:** Mantener una comunicación fluida entre el equipo de desarrollo y Pollería Montiel para resolver dudas y validar progresos.

---
**Sección 10: Apéndice A: Glosario de Términos**.

Esta sección es útil para asegurar que todos los involucrados en el proyecto (desarrolladores, stakeholders de Pollería Montiel, y también Copilot al procesar el documento) tengan una comprensión común de la terminología específica del negocio y del sistema.

---

## 10. Apéndice A: Glosario de Términos

Este glosario define términos clave utilizados a lo largo de este documento y en el contexto del proyecto del Sistema de Gestión para Pollería Montiel (SGPM) para asegurar una comprensión uniforme.

| Término                      | Definición                                                                                                                                                             | Contexto/Ejemplo de Uso                                   |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------|
| **SGPM**                     | Siglas de **Sistema de Gestión para Pollería Montiel**.                                                                                                                | El SGPM automatizará los pedidos y la caja.             |
| **MVP**                      | **Producto Mínimo Viable (Minimum Viable Product)**. La versión inicial del SGPM con las funcionalidades esenciales para ser útil y obtener retroalimentación.         | El MVP se centrará en pedidos, caja y clientes.          |
| **Producto Principal**       | Unidad base del catálogo de pollo (ej. Pechuga, Alas). Representado por el modelo `Producto`.                                                                          | "La Pechuga es un Producto Principal."                     |
| **Subproducto**              | Una parte o derivado específico de un Producto Principal (ej. Pulpa de Pechuga) o una variante especial (ej. Cadera). Representado por el modelo `Subproducto`.         | "La Pulpa de Pernil es un Subproducto del Pernil."         |
| **Modificación**             | Corte, preparación o presentación específica aplicada a un Producto Principal o Subproducto (ej. Molida, Para Asar). Representado por el modelo `Modificacion`.         | "El cliente pidió la Pechuga con Modificación 'Milanesa'."|
| **Simbología de Producto**   | Códigos cortos y/o iconos usados para identificar rápidamente productos y subproductos en la interfaz (ej. PECH, 🐔).                                                   | "Usar la Simbología de Producto en el ticket de venta."    |
| **PA (Producto Adicional)**  | Ítem vendido que no forma parte del catálogo de pollo principal, usualmente comprado externamente o con precio/cantidad variable (ej. verduras, refrescos, carbón). Representado por el modelo `ProductoAdicional`. | "Añadir un PA de $20 de jitomate al pedido."            |
| **Tipo de Cliente**          | Categorización de clientes para aplicar precios diferenciados o promociones (ej. Público, Cocina, Leal). Campo `tipo_cliente` en el modelo `Cliente`.                | "El precio para Tipo de Cliente 'Cocina' es menor."     |
| **Forma de Pago**            | Método utilizado por el cliente para pagar un pedido (ej. Efectivo, Tarjeta). Campo `forma_pago` en `Pedido` y `forma_pago_efectuado` en `MovimientoCaja`.             | "El cliente eligió la Forma de Pago 'Transferencia'."   |
| **Denominación (Moneda)**    | Valor específico de un billete o moneda física (ej. billete de $200, moneda de $10). Campo `denominacion_valor` en `MovimientoDenominacion` y `DenominacionCorteCaja`. | "Contar las Denominaciones al hacer el corte de caja."    |
| **Movimiento de Caja**       | Cualquier entrada (ingreso) o salida (egreso) de dinero registrada en el sistema. Representado por el modelo `MovimientoCaja`.                                       | "Se registró un Movimiento de Caja por la venta."        |
| **Apertura de Caja**         | Proceso de iniciar un turno o día de caja registrando el saldo inicial de efectivo.                                                                                    | "Realizar la Apertura de Caja antes de la primera venta."|
| **Corte de Caja / Arqueo**   | Proceso de contar el efectivo y otros valores al final de un turno/día para conciliar con las ventas y movimientos registrados. Representado por el modelo `CorteCaja`. | "El Corte de Caja mostró un sobrante de $10."           |
| **Saldo Teórico (Caja)**     | Monto de efectivo que se espera tener en caja según los registros del sistema (Saldo Inicial + Ingresos - Egresos).                                                      | "El Saldo Teórico no coincide con el conteo físico."    |
| **CRUD**                     | Acrónimo de las operaciones básicas en bases de datos o gestión de datos: **C**rear (Create), **L**eer (Read), **A**ctualizar (Update), **E**liminar (Delete).          | "El Administrador tiene permisos CRUD sobre Productos."   |
| **UI (User Interface)**      | **Interfaz de Usuario**. Los elementos visuales y controles con los que el usuario interactúa en el sistema.                                                              | "La UI debe ser intuitiva y Mobile First."              |
| **UX (User Experience)**     | **Experiencia de Usuario**. La percepción y respuesta general de una persona como resultado del uso o anticipación del uso de un producto, sistema o servicio.      | "Debemos optimizar la UX del proceso de pedido."        |
| **Mobile First**             | Enfoque de diseño y desarrollo que prioriza la experiencia en dispositivos móviles, adaptándose luego a pantallas más grandes.                                         | "El SGPM sigue un diseño Mobile First."                 |
| **Flask Blueprint**          | Componente de Flask que permite organizar una aplicación en módulos más pequeños y reutilizables.                                                                   | "El módulo de Pedidos se implementará en un Blueprint."   |
| **ORM (Object-Relational Mapper)** | Técnica de programación que convierte datos entre sistemas de tipos incompatibles en programación orientada a objetos, como una base de datos relacional y un lenguaje OO. SQLAlchemy es el ORM usado. | "SQLAlchemy es el ORM para interactuar con la BD."      |
| **Jinja2**                   | Motor de plantillas moderno y amigable para diseñadores para Python, usado por Flask para renderizar HTML.                                                              | "Las vistas se renderizarán con plantillas Jinja2."       |
| **AJAX (Asynchronous JavaScript and XML)** | Técnica de desarrollo web para crear aplicaciones interactivas, permitiendo la actualización de partes de una página sin recargarla completamente.                | "Usar AJAX para actualizar el carrito dinámicamente."    |
| **Seed / Seeding (Base de Datos)** | Proceso de poblar una base de datos con un conjunto inicial de datos (datos maestros, ejemplos) para pruebas o para la configuración inicial del sistema.        | "Crear un script de Seeding para los productos."        |
| **Ticket (Venta)**           | Comprobante impreso o digital que se entrega al cliente detallando su compra.                                                                                          | "El sistema debe poder generar un Ticket de Venta."      |
| **Comanda (Preparación)**    | Nota o ticket interno que se envía al área de preparación (Tablajería) con los detalles de los ítems a preparar para un pedido.                                      | "Imprimir la Comanda para el Tablajero."                  |
| **Folio (Pedido)**           | Número único (generalmente consecutivo y/o con prefijo) asignado a un pedido para su identificación y seguimiento.                                                    | "El Pedido tiene el Folio PM-00123."                    |
| **Liquidación (Repartidor)** | Proceso por el cual un repartidor entrega el dinero recaudado de los pedidos a domicilio y devuelve el cambio no utilizado.                                           | "El repartidor hizo la Liquidación de sus entregas."    |

---

Este glosario puede crecer a medida que el proyecto avance y surjan nuevos términos específicos. Es una buena práctica mantenerlo actualizado.

¡Y con esto, hemos completado el esqueleto detallado de todo el "Documento de Especificaciones y Lógica de Negocio: Pollería Montiel MVP"! Ha sido un trabajo exhaustivo, pero el nivel de detalle que hemos alcanzado será increíblemente valioso.

**Próximos pasos después de esto:**

1.  **Revisión Interna:** Tú y tu equipo (si aplica) deben revisar cada sección cuidadosamente para asegurar la precisión, completitud y consistencia.
2.  **Validación con Pollería Montiel:** Presentar las secciones clave (especialmente flujos de usuario, lógica de negocio que les impacta, y datos maestros) a los stakeholders de Pollería Montiel para su validación y asegurar que refleja correctamente sus operaciones y expectativas.
3.  **"Congelar" la Versión para MVP:** Una vez validado, esta versión del documento se convierte en la base para el desarrollo del MVP. Los cambios mayores deberían pasar por un proceso de gestión de cambios.
4.  **¡Empezar a Desarrollar (Fase 0)!** Utilizar este documento y las "Instrucciones para GitHub Copilot" para guiar el desarrollo.

¡Felicidades por llegar hasta aquí! Este documento es un activo muy importante para el proyecto. 