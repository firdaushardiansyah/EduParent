from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import auth_bp
from app.models import db, User
from app.utils import log_audit

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'teacher':
            return redirect(url_for('teacher.dashboard'))
        elif current_user.role == 'parent':
            return redirect(url_for('parent.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            log_audit(action="LOGIN", details=f"User {user.username} logged in with role {user.role}", user_id=user.id)
            flash(f"Selamat datang kembali, {user.full_name}!", "success")

            next_page = request.args.get('next')
            if next_page and not next_page.startswith('//') and not next_page.startswith('http'):
                return redirect(next_page)

            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'teacher':
                return redirect(url_for('teacher.dashboard'))
            elif user.role == 'parent':
                return redirect(url_for('parent.dashboard'))
            return redirect(url_for('auth.login'))
        else:
            flash("Username atau kata sandi tidak valid. Silakan coba lagi.", "danger")

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    log_audit(action="LOGOUT", details=f"User {current_user.username} logged out", user_id=current_user.id)
    logout_user()
    flash("Anda telah berhasil keluar dari sistem.", "info")
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not full_name:
            flash("Nama lengkap tidak boleh kosong.", "danger")
            return redirect(url_for('auth.profile'))

        current_user.full_name = full_name
        current_user.phone_number = phone_number

        if new_password:
            if len(new_password) < 6:
                flash("Kata sandi minimal 6 karakter.", "danger")
                return redirect(url_for('auth.profile'))
            if new_password != confirm_password:
                flash("Konfirmasi kata sandi tidak cocok.", "danger")
                return redirect(url_for('auth.profile'))
            current_user.set_password(new_password)
            flash("Kata sandi berhasil diperbarui!", "success")

        db.session.commit()
        log_audit(action="UPDATE_PROFILE", details=f"User {current_user.username} updated profile data", user_id=current_user.id)
        flash("Profil Anda berhasil disimpan.", "success")
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html')
