from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from flask_wtf import FlaskForm # Importar FlaskForm
from wtforms import PasswordField, SubmitField # Importar campos necesarios
from wtforms.validators import DataRequired, Length, EqualTo # Importar validadores necesarios
from app import db
from app.models import Usuario, RolUsuario # Importar RolUsuario si se usa directamente en rutas (ej. para verificar roles)
from . import auth # . es el directorio actual (auth)
from .forms import LoginForm, RegistrationForm # Reutilizaremos RegistrationForm para editar
from .services import create_user, get_user_by_username, get_user_by_id, get_all_users, update_user, delete_user, reset_password, activate_user, deactivate_user # Importar todas las funciones de servicio
from app.utils.decorators import role_required # Importar el decorador de roles

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        # Usar servicio para buscar usuario
        user = get_user_by_username(form.username.data)
        if user is None or not user.check_password(form.password.data) or not user.activo:
            flash('Nombre de usuario o contraseña inválidos, o usuario inactivo.', 'error')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        flash(f'Bienvenido de nuevo, {user.nombre_completo}!', 'success')

        # Redirigir a la página solicitada originalmente o al index
        next_page = request.args.get('next')
        # Validar next_page para prevenir ataques de redirección abierta
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Iniciar Sesión', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('main.index'))

@auth.route('/registro', methods=['GET', 'POST'])
# Usar el decorador role_required para restringir acceso solo a ADMINISTRADOR
@role_required(RolUsuario.ADMINISTRADOR)
def registro_usuario():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Usar servicio para crear usuario
        user = create_user(
            username=form.username.data,
            password=form.password.data,
            nombre_completo=form.nombre_completo.data,
            rol=form.rol.data, # El valor del SelectField ya es el string del Enum
            activo=form.activo.data
        )
        if user:
            flash(f'Usuario "{user.username}" registrado exitosamente.', 'success')
            return redirect(url_for('auth.listar_usuarios')) # Redirigir a la lista de usuarios
        else:
            # Si create_user retorna None, es probable que el usuario ya exista (validado en el form, pero doble check)
            # O hubo un error interno (ej. rol inválido)
            flash('Error al registrar usuario. El nombre de usuario podría ya existir o el rol es inválido.', 'danger')
            # Mantener al usuario en la página de registro para corregir
            return render_template('auth/registro_usuario.html', title='Registrar Usuario', form=form)

    return render_template('auth/registro_usuario.html', title='Registrar Usuario', form=form)

@auth.route('/usuarios')
@login_required
# Usar el decorador role_required para restringir acceso solo a ADMINISTRADOR
@role_required(RolUsuario.ADMINISTRADOR)
def listar_usuarios():
    page = request.args.get('page', 1, type=int)
    per_page = 10 # Usuarios por página
    # Usar servicio para obtener usuarios paginados
    usuarios_pagination = get_all_users(page=page, per_page=per_page)
    usuarios = usuarios_pagination.items

    # Necesitarás una plantilla 'auth/listar_usuarios.html'
    return render_template('auth/listar_usuarios.html', title='Lista de Usuarios', usuarios=usuarios, pagination=usuarios_pagination)

@auth.route('/usuarios/<int:user_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required(RolUsuario.ADMINISTRADOR)
def editar_usuario(user_id):
    user = get_user_by_id(user_id)
    if user is None:
        flash('Usuario no encontrado.', 'warning')
        return redirect(url_for('auth.listar_usuarios'))

    # Usamos RegistrationForm para editar, pero ajustamos validadores si es necesario
    # Por ejemplo, no requerir la contraseña si no se va a cambiar
    form = RegistrationForm(obj=user) # Pre-llenar el formulario con datos del usuario

    # Eliminar validadores de contraseña para la edición si no se cambia
    # La lógica para cambiar contraseña se manejará en otra ruta o un campo opcional
    del form.password
    del form.password2
    # Si el username no debe ser editable, hacerlo de solo lectura en la plantilla
    # o eliminar el validador unique si se permite cambiarlo (requiere lógica adicional)
    # form.username.validators = [DataRequired(), Length(min=3, max=80)] # Ejemplo si se quita unique

    if form.validate_on_submit():
        # Actualizar usuario usando el servicio
        updated_user = update_user(
            user_id=user.id,
            nombre_completo=form.nombre_completo.data,
            rol=form.rol.data,
            activo=form.activo.data
        )
        if updated_user:
            flash(f'Usuario "{updated_user.username}" actualizado exitosamente.', 'success')
            return redirect(url_for('auth.listar_usuarios'))
        else:
            # update_user retorna None si el usuario no existe o hay un error interno
            flash('Error al actualizar usuario.', 'danger')
            # Mantener al usuario en la página de edición para corregir
            return render_template('auth/editar_usuario.html', title='Editar Usuario', form=form, user=user)

    # GET request: Renderizar el formulario pre-llenado
    # Necesitarás una plantilla 'auth/editar_usuario.html'
    return render_template('auth/editar_usuario.html', title='Editar Usuario', form=form, user=user)

@auth.route('/usuarios/<int:user_id>/eliminar', methods=['POST'])
@login_required
@role_required(RolUsuario.ADMINISTRADOR)
def eliminar_usuario(user_id):
    # Prevenir que un administrador se elimine a sí mismo
    if current_user.id == user_id:
        flash('No puedes eliminar tu propia cuenta de administrador.', 'warning')
        return redirect(url_for('auth.listar_usuarios'))

    success = delete_user(user_id)
    if success:
        flash('Usuario eliminado exitosamente.', 'success')
    else:
        flash('Error al eliminar usuario o usuario no encontrado.', 'danger')

    return redirect(url_for('auth.listar_usuarios'))

@auth.route('/usuarios/<int:user_id>/activar', methods=['POST'])
@login_required
@role_required(RolUsuario.ADMINISTRADOR)
def activar_usuario(user_id):
    user = activate_user(user_id)
    if user:
        flash(f'Usuario "{user.username}" activado exitosamente.', 'success')
    else:
        flash('Error al activar usuario o usuario no encontrado.', 'danger')

    return redirect(url_for('auth.listar_usuarios'))

@auth.route('/usuarios/<int:user_id>/desactivar', methods=['POST'])
@login_required
@role_required(RolUsuario.ADMINISTRADOR)
def desactivar_usuario(user_id):
    # Prevenir que un administrador se desactive a sí mismo
    if current_user.id == user_id:
        flash('No puedes desactivar tu propia cuenta de administrador.', 'warning')
        return redirect(url_for('auth.listar_usuarios'))

    user = deactivate_user(user_id)
    if user:
        flash(f'Usuario "{user.username}" desactivado exitosamente.', 'success')
    else:
        flash('Error al desactivar usuario o usuario no encontrado.', 'danger')

    return redirect(url_for('auth.listar_usuarios'))

@auth.route('/usuarios/<int:user_id>/reset_password', methods=['GET', 'POST'])
@login_required
@role_required(RolUsuario.ADMINISTRADOR)
def reset_password_usuario(user_id):
    user = get_user_by_id(user_id)
    if user is None:
        flash('Usuario no encontrado.', 'warning')
        return redirect(url_for('auth.listar_usuarios'))

    # Podríamos usar un formulario simple con solo los campos de nueva contraseña
    # Para MVP, podemos usar un formulario básico o incluso un modal de confirmación
    # Aquí usaremos un formulario simple
    class ResetPasswordForm(FlaskForm):
        password = PasswordField('Nueva Contraseña', validators=[DataRequired(), Length(min=8)])
        password2 = PasswordField(
            'Confirmar Nueva Contraseña', validators=[DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir.')])
        submit = SubmitField('Resetear Contraseña')

    form = ResetPasswordForm()

    if form.validate_on_submit():
        updated_user = reset_password(user.id, form.password.data)
        if updated_user:
            flash(f'Contraseña para usuario "{updated_user.username}" reseteada exitosamente.', 'success')
            return redirect(url_for('auth.listar_usuarios'))
        else:
            flash('Error al resetear contraseña.', 'danger')
            # Mantener al usuario en la página de reset para corregir
            return render_template('auth/reset_password.html', title='Resetear Contraseña', form=form, user=user)

    # GET request: Renderizar el formulario de reset
    # Necesitarás una plantilla 'auth/reset_password.html'
    return render_template('auth/reset_password.html', title='Resetear Contraseña', form=form, user=user)

# Nota: Las rutas de edición, eliminación, activación/desactivación y reseteo de contraseña
# asumen que se accede a ellas desde la lista de usuarios (listar_usuarios.html)
# y que las plantillas correspondientes (editar_usuario.html, reset_password.html) existen.
