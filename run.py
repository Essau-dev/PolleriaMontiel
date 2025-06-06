from app import create_app, db
from app.models import Usuario # Importa tus modelos aquí a medida que los crees
from flask_migrate import Migrate # Descomentar si usas Flask-Migrate

app = create_app()
migrate = Migrate(app, db) # Descomentar si usas Flask-Migrate


if __name__ == '__main__':
    app.run(debug=True) # debug=True solo para desarrollo
