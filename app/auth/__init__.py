
from flask import Blueprint

# El nombre 'auth' aquí debe coincidir con el nombre del directorio
# y con el usado en app/app.py al registrarlo.
# El segundo argumento es __name__, ayuda a Flask a localizar plantillas/estáticos.
# El tercer argumento, template_folder, es opcional si las plantillas están en app/templates/nombre_blueprint/
auth = Blueprint('auth', __name__, template_folder='templates') 

from . import routes # Importa las rutas del blueprint
