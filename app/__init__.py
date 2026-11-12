import os
from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from app.config import config_by_name
from app.models import db, User

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Silakan masuk untuk mengakses sistem.'
login_manager.login_message_category = 'info'

csrf = CSRFProtect()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    for sub in ['students', 'journals', 'pickups', 'misc']:
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], sub), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register Blueprints
    from app.auth.routes import auth_bp
    from app.admin.routes import admin_bp
    from app.teacher.routes import teacher_bp
    from app.parent.routes import parent_bp
    from app.api.routes import api_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    app.register_blueprint(parent_bp, url_prefix='/parent')
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif current_user.role == 'teacher':
                return redirect(url_for('teacher.dashboard'))
            elif current_user.role == 'parent':
                return redirect(url_for('parent.dashboard'))
        return redirect(url_for('auth.login'))

    # Custom Jinja filters
    @app.template_filter('format_date_id')
    def format_date_id(value):
        if not value:
            return '-'
        months = [
            '', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
            'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
        ]
        try:
            return f"{value.day} {months[value.month]} {value.year}"
        except Exception:
            return str(value)

    @app.template_filter('format_datetime_id')
    def format_datetime_id(value):
        if not value:
            return '-'
        months = [
            '', 'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
            'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'
        ]
        try:
            return f"{value.day} {months[value.month]} {value.year}, {value.strftime('%H:%M')} WIB"
        except Exception:
            return str(value)

    return app
