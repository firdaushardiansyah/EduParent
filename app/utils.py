import os
import uuid
from functools import wraps
from flask import current_app, flash, redirect, url_for, request, abort
from flask_login import current_user
from werkzeug.utils import secure_filename
from app.models import db, AuditLog

def role_required(*allowed_roles):
    """
    Decorator for RBAC. Ensures user is authenticated and has one of the allowed roles.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Silakan masuk terlebih dahulu untuk mengakses halaman ini.", "warning")
                return redirect(url_for('auth.login', next=request.url))
            
            if current_user.role not in allowed_roles:
                flash("Akses ditolak. Anda tidak memiliki izin untuk halaman tersebut.", "danger")
                if current_user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                elif current_user.role == 'teacher':
                    return redirect(url_for('teacher.dashboard'))
                elif current_user.role == 'parent':
                    return redirect(url_for('parent.dashboard'))
                return redirect(url_for('auth.login'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def save_upload_file(file_storage, subfolder='misc'):
    """
    Saves an uploaded file securely with a unique UUID filename.
    Returns relative URL path e.g. '/static/uploads/journals/uuid.jpg'.
    """
    if not file_storage or file_storage.filename == '':
        return None

    if not allowed_file(file_storage.filename):
        return None

    ext = file_storage.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"

    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(upload_folder, exist_ok=True)

    target_path = os.path.join(upload_folder, unique_filename)
    file_storage.save(target_path)

    # Return web-accessible URL
    return f"/static/uploads/{subfolder}/{unique_filename}"


def log_audit(action, details=None, user_id=None):
    """
    Records an administrative or security event into AuditLog.
    """
    try:
        uid = user_id if user_id is not None else (current_user.id if current_user.is_authenticated else None)
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()

        audit = AuditLog(
            user_id=uid,
            action=action,
            details=details,
            ip_address=ip
        )
        db.session.add(audit)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error logging audit: {e}")
