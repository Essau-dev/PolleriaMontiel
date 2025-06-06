
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from app import db
from app.models import Usuario
from . import auth # . es el directorio actual (auth)
from .forms import LoginForm, RegistrationForm # Asumiendo que creas estas formas

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data) or not user.activo:
            flash('Nombre de usuario o contraseña inválidos, o usuario inactivo.', 'error')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        flash(f'Bienvenido de nuevo, {user.nombre_completo}!', 'success')
        
        # Redirigir a la página solicitada originalmente o al index
        next_page = request.args.get('next')
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
@login_required # Solo un admin puede registrar otros usuarios inicialmente
def registro_usuario():
    if not current_user.has_role('ADMINISTRADOR'):
        flash('No tienes permiso para registrar usuarios.', 'error')
        return redirect(url_for('main.index'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Usuario(
            username=form.username.data,
            nombre_completo=form.nombre_completo.data,
            rol=form.rol.data,
            activo=form.activo.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Usuario {user.username} registrado exitosamente.', 'success')
        return redirect(url_for('auth.listar_usuarios')) # O a donde quieras redirigir
    return render_template('auth/registro_usuario.html', title='Registrar Usuario', form=form)

@auth.route('/usuarios')
@login_required
def listar_usuarios():
    if not current_user.has_role('ADMINISTRADOR'):
        flash('Acceso no autorizado.', 'error')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    per_page = 10 # Usuarios por página
    usuarios_pagination = Usuario.query.order_by(Usuario.nombre_completo.asc()).paginate(page=page, per_page=per_page, error_out=False)
    usuarios = usuarios_pagination.items
    # Necesitarás una plantilla 'auth/listar_usuarios.html'
    return render_template('auth/listar_usuarios.html', title='Lista de Usuarios', usuarios=usuarios, pagination=usuarios_pagination)

# Más rutas para editar usuario, cambiar contraseña, etc.
