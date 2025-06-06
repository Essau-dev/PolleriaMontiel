
from app import create_app, db
from app.models import Usuario # Importa tus modelos aquí a medida que los crees
# from flask_migrate import Migrate # Descomentar si usas Flask-Migrate

app = create_app()
# migrate = Migrate(app, db) # Descomentar si usas Flask-Migrate

# Ejemplo de cómo podrías añadir un usuario admin inicial (más adelante esto iría en un comando CLI o seed)
# @app.cli.command("create_admin")
# def create_admin_user():
#     """Crea un usuario administrador inicial."""
#     from werkzeug.security import generate_password_hash
#     if not Usuario.query.filter_by(username="admin").first():
#         admin_user = Usuario(
#             username="admin",
#             password_hash=generate_password_hash("adminpass"), # Cambiar en producción
#             nombre_completo="Administrador del Sistema",
#             rol="ADMINISTRADOR",
#             activo=True
#         )
#         db.session.add(admin_user)
#         db.session.commit()
#         print("Usuario administrador 'admin' creado.")
#     else:
#         print("Usuario administrador 'admin' ya existe.")


if __name__ == '__main__':
    app.run(debug=True) # debug=True solo para desarrollo
