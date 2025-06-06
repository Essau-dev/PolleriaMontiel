# Sistema de Gestión para Pollería Montiel (SGPM) - MVP

## 1. Introducción

Este proyecto es el **Producto Mínimo Viable (MVP)** del Sistema de Gestión para Pollería Montiel (SGPM). El objetivo es digitalizar y optimizar las operaciones diarias clave de la pollería, enfocándose inicialmente en la gestión de pedidos, el control de caja y la administración básica de clientes y productos.

El desarrollo sigue un enfoque **Mobile First**, con una interfaz responsiva adaptada a dispositivos móviles y de escritorio, utilizando Flask, SQLAlchemy y Jinja2.

## 2. Estado Actual del Proyecto (MVP)

El proyecto se encuentra en fase de desarrollo del MVP. Se ha establecido la estructura base, los modelos de datos principales y se han implementado las funcionalidades iniciales para los módulos clave.

**Funcionalidades Implementadas (Parcialmente o Completamente en MVP):**

*   **Autenticación y Gestión de Usuarios:**
    *   Registro de nuevos usuarios (vía CLI o ruta de registro).
    *   Inicio y cierre de sesión.
    *   Gestión básica de usuarios (listar, ver, editar, resetear contraseña - solo para Administradores).
    *   Control de acceso basado en roles (`ADMINISTRADOR`, `CAJERO`, `TABLAJERO`, `REPARTIDOR`).
*   **Gestión de Clientes:**
    *   Creación, visualización y edición de clientes.
    *   Registro de múltiples teléfonos y direcciones por cliente.
    *   Visualización del historial de pedidos por cliente.
*   **Gestión de Catálogo (Productos, Subproductos, Modificaciones):**
    *   Creación, visualización y edición de Productos, Subproductos y Modificaciones.
    *   Asociación de Modificaciones a Productos/Subproductos.
    *   Gestión de Precios por Producto/Subproducto, Tipo de Cliente y Cantidad Mínima.
*   **Gestión de Pedidos:**
    *   Creación de nuevos pedidos (Mostrador y Domicilio).
    *   Adición de ítems de catálogo (Productos/Subproductos con Modificaciones) al pedido.
    *   Adición de Productos Adicionales (PAs) al pedido.
    *   Visualización detallada de pedidos.
    *   Edición básica de pedidos (estructura inicial).
    *   Impresión de Nota de Preparación (Comanda).
*   **Gestión de Caja:**
    *   Apertura de Caja (registro de saldo inicial por denominaciones).
    *   Registro de Movimientos de Caja (Ingresos/Egresos).
    *   Visualización del Dashboard de Caja (corte actual, movimientos recientes).
    *   Proceso de Cierre de Caja (conteo físico, cálculo de diferencia).
    *   Visualización del historial de Cortes de Caja.
*   **Utilidades:**
    *   Helpers para formato de moneda, fechas y folios de pedido.
    *   Decorador para restricción de acceso por rol.

## 3. Tecnologías Utilizadas

*   **Backend:** Python 3.x, Flask
*   **ORM:** SQLAlchemy, Flask-SQLAlchemy
*   **Base de Datos:** SQLite (para MVP)
*   **Migraciones:** Flask-Migrate
*   **Formularios:** Flask-WTF
*   **Autenticación:** Flask-Login
*   **Frontend:** HTML5, CSS3 (custom, Mobile First), JavaScript (Vanilla JS)
*   **Variables de Entorno:** python-dotenv

## 4. Configuración del Entorno y Ejecución

### 4.1 Prerrequisitos

*   Python 3.8+ instalado.
*   `pip` (gestor de paquetes de Python).
*   Un entorno virtual (`venv` recomendado).

### 4.2 Instalación

1.  Clona este repositorio (si aplica) o navega al directorio del proyecto.
2.  Crea un entorno virtual:
    ```sh
    python -m venv venv
    ```
3.  Activa el entorno virtual:
    *   En Windows:
        ```bat
        venv\Scripts\activate
        ```
    *   En macOS/Linux:
        ```bash
        source venv/bin/activate
        ```
4.  Instala las dependencias del proyecto:
    ```sh
    pip install -r requirements.txt
    ```
5.  Crea un archivo `.env` en la raíz del proyecto con al menos la clave secreta:
    ```dotenv
    SECRET_KEY='tu_clave_secreta_aleatoria_aqui'
    DATABASE_URL='sqlite:///app.db' # Opcional, si no usas la configuración por defecto
    ```
    Reemplaza `'tu_clave_secreta_aleatoria_aqui'` por una cadena aleatoria y segura.

### 4.3 Configuración de la Base de Datos

1.  Asegúrate de que tu entorno virtual está activado.
2.  Inicializa el repositorio de migraciones (solo la primera vez):
    ```sh
    flask db init
    ```
3.  Crea la primera migración (o migraciones subsiguientes al modificar modelos):
    ```sh
    flask db migrate -m "Initial migration"
    ```
    *(Si ya has ejecutado migraciones antes, usa un mensaje descriptivo de los cambios actuales, ej. `flask db migrate -m "Add new Pedido fields"`)*
4.  Aplica las migraciones a la base de datos:
    ```sh
    flask db upgrade
    ```

### 4.4 Poblar la Base de Datos (Seeding)

Para tener datos iniciales (productos, tipos de cliente, etc.) para pruebas, puedes ejecutar el script de seeding:

```sh
flask seed-db
```
