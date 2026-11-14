from datetime import datetime, date
from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user
from app.admin import admin_bp
from app.models import db, User, ClassRoom, Student, DailyJournal, PickupLog, AuditLog
from app.utils import role_required, save_upload_file, log_audit

@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    total_students = Student.query.count()
    total_teachers = User.query.filter_by(role='teacher').count()
    total_parents = User.query.filter_by(role='parent').count()
    total_classes = ClassRoom.query.count()

    today = date.today()
    journals_today = DailyJournal.query.filter_by(date=today).all()
    present_today = sum(1 for j in journals_today if j.attendance == 'HADIR')

    # Pickup stats today
    pickups_today = PickupLog.query.filter(
        db.func.date(PickupLog.created_at) == today
    ).all()
    picked_up_today = sum(1 for p in pickups_today if p.status == 'SUDAH_DIJEMPUT')

    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(8).all()
    recent_students = Student.query.order_by(Student.created_at.desc()).limit(5).all()

    all_classes = ClassRoom.query.order_by(ClassRoom.name).all()

    return render_template(
        'admin/dashboard.html',
        total_students=total_students,
        total_teachers=total_teachers,
        total_parents=total_parents,
        total_classes=total_classes,
        present_today=present_today,
        journals_count=len(journals_today),
        pickups_today=len(pickups_today),
        picked_up_today=picked_up_today,
        recent_logs=recent_logs,
        recent_students=recent_students,
        classes=all_classes
    )

# --- USERS MANAGEMENT (TEACHERS & PARENTS) ---
@admin_bp.route('/users')
@role_required('admin')
def users():
    role_filter = request.args.get('role', '')
    search_query = request.args.get('q', '').strip()
    query = User.query
    if role_filter in ['admin', 'teacher', 'parent']:
        query = query.filter_by(role=role_filter)
    if search_query:
        query = query.filter(
            (User.full_name.ilike(f'%{search_query}%')) |
            (User.username.ilike(f'%{search_query}%')) |
            (User.phone_number.ilike(f'%{search_query}%'))
        )
    users_list = query.order_by(User.role, User.full_name).all()
    all_students = Student.query.order_by(Student.full_name).all()
    return render_template('admin/users.html', users=users_list, current_role=role_filter, all_students=all_students)

@admin_bp.route('/users/create', methods=['POST'])
@role_required('admin')
def create_user():
    username = request.form.get('username', '').strip()
    full_name = request.form.get('full_name', '').strip()
    phone_number = request.form.get('phone_number', '').strip()
    role = request.form.get('role', 'parent')
    password = request.form.get('password', '123456')

    if not username or not full_name:
        flash("Username dan nama lengkap wajib diisi.", "danger")
        return redirect(url_for('admin.users'))

    if User.query.filter_by(username=username).first():
        flash("Username sudah terdaftar! Gunakan username lain.", "danger")
        return redirect(url_for('admin.users'))

    new_user = User(
        username=username,
        full_name=full_name,
        phone_number=phone_number,
        role=role
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.flush()

    # Link children if parent
    if role == 'parent':
        student_ids = request.form.getlist('student_ids')
        if student_ids:
            Student.query.filter(Student.id.in_([int(sid) for sid in student_ids])).update(
                {'parent_id': new_user.id}, synchronize_session=False
            )

    db.session.commit()

    log_audit("CREATE_USER", f"Created user {username} with role {role}")
    flash(f"Pengguna {full_name} ({role.capitalize()}) berhasil ditambahkan!", "success")
    return redirect(url_for('admin.users', role=role))

@admin_bp.route('/users/<int:user_id>/edit', methods=['POST'])
@role_required('admin')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    user.full_name = request.form.get('full_name', '').strip() or user.full_name
    user.phone_number = request.form.get('phone_number', '').strip()
    new_role = request.form.get('role', user.role)
    if new_role in ['admin', 'teacher', 'parent']:
        user.role = new_role

    new_password = request.form.get('password', '').strip()
    if new_password:
        user.set_password(new_password)

    # Link children if role is parent
    if user.role == 'parent':
        student_ids = request.form.getlist('student_ids')
        # Reset existing links for this parent
        Student.query.filter_by(parent_id=user.id).update({'parent_id': None}, synchronize_session=False)
        if student_ids:
            Student.query.filter(Student.id.in_([int(sid) for sid in student_ids])).update(
                {'parent_id': user.id}, synchronize_session=False
            )

    db.session.commit()
    log_audit("EDIT_USER", f"Updated user {user.username} (ID: {user.id})")
    flash(f"Data pengguna {user.full_name} berhasil diperbarui.", "success")
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@role_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Anda tidak dapat menghapus akun Anda sendiri.", "danger")
        return redirect(url_for('admin.users'))

    username = user.username
    # Unlink any children from parent
    Student.query.filter_by(parent_id=user.id).update({'parent_id': None}, synchronize_session=False)
    # Unlink any classes taught
    ClassRoom.query.filter_by(teacher_id=user.id).update({'teacher_id': None}, synchronize_session=False)

    db.session.delete(user)
    db.session.commit()
    log_audit("DELETE_USER", f"Deleted user {username} (ID: {user_id})")
    flash(f"Pengguna {username} berhasil dihapus.", "info")
    return redirect(url_for('admin.users'))

# --- CLASSES MANAGEMENT ---
@admin_bp.route('/classes')
@role_required('admin')
def classes():
    all_classes = ClassRoom.query.order_by(ClassRoom.name).all()
    teachers = User.query.filter_by(role='teacher').order_by(User.full_name).all()
    return render_template('admin/classes.html', classes=all_classes, teachers=teachers)

@admin_bp.route('/classes/create', methods=['POST'])
@role_required('admin')
def create_class():
    name = request.form.get('name', '').strip()
    academic_year = request.form.get('academic_year', '2025/2026').strip()
    teacher_id = request.form.get('teacher_id') or None

    if not name:
        flash("Nama kelas wajib diisi.", "danger")
        return redirect(url_for('admin.classes'))

    new_class = ClassRoom(
        name=name,
        academic_year=academic_year,
        teacher_id=int(teacher_id) if teacher_id else None
    )
    db.session.add(new_class)
    db.session.commit()
    log_audit("CREATE_CLASS", f"Created classroom {name}")
    flash(f"Kelas '{name}' berhasil dibuat!", "success")
    return redirect(url_for('admin.classes'))

@admin_bp.route('/classes/<int:class_id>/edit', methods=['POST'])
@role_required('admin')
def edit_class(class_id):
    classroom = ClassRoom.query.get_or_404(class_id)
    classroom.name = request.form.get('name', classroom.name).strip()
    classroom.academic_year = request.form.get('academic_year', classroom.academic_year).strip()
    teacher_id = request.form.get('teacher_id')
    classroom.teacher_id = int(teacher_id) if teacher_id else None

    db.session.commit()
    log_audit("EDIT_CLASS", f"Updated classroom {classroom.name}")
    flash("Data kelas berhasil diperbarui.", "success")
    return redirect(url_for('admin.classes'))

@admin_bp.route('/classes/<int:class_id>/delete', methods=['POST'])
@role_required('admin')
def delete_class(class_id):
    classroom = ClassRoom.query.get_or_404(class_id)
    name = classroom.name
    db.session.delete(classroom)
    db.session.commit()
    log_audit("DELETE_CLASS", f"Deleted classroom {name}")
    flash(f"Kelas '{name}' telah dihapus.", "info")
    return redirect(url_for('admin.classes'))

# --- STUDENTS MANAGEMENT & PARENT MAPPING ---
@admin_bp.route('/students')
@role_required('admin')
def students():
    class_id = request.args.get('class_id', type=int)
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = Student.query
    if search_query:
        query = query.filter(
            (Student.full_name.ilike(f'%{search_query}%')) |
            (Student.nickname.ilike(f'%{search_query}%'))
        )
    if class_id:
        query = query.filter_by(class_id=class_id)
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)

    students_list = query.order_by(Student.full_name).all()

    all_classes = ClassRoom.query.order_by(ClassRoom.name).all()
    parents = User.query.filter_by(role='parent').order_by(User.full_name).all()

    return render_template(
        'admin/students.html',
        students=students_list,
        classes=all_classes,
        parents=parents,
        selected_class_id=class_id,
        search_query=search_query,
        status_filter=status_filter
    )

@admin_bp.route('/students/create', methods=['POST'])
@role_required('admin')
def create_student():
    full_name = request.form.get('full_name', '').strip()
    nickname = request.form.get('nickname', '').strip()
    dob_str = request.form.get('dob', '').strip()
    gender = request.form.get('gender', 'L')
    class_id = request.form.get('class_id', type=int)
    parent_id = request.form.get('parent_id') or None
    is_active = request.form.get('is_active', '1') == '1'

    if not full_name or not nickname or not dob_str or not class_id:
        flash("Mohon lengkapi semua kolom wajib untuk pendaftaran siswa.", "danger")
        return redirect(url_for('admin.students'))

    try:
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
    except ValueError:
        flash("Format tanggal lahir tidak valid.", "danger")
        return redirect(url_for('admin.students'))

    photo_url = None
    if 'photo' in request.files:
        photo_url = save_upload_file(request.files['photo'], 'students')

    student = Student(
        full_name=full_name,
        nickname=nickname,
        dob=dob,
        gender=gender,
        class_id=class_id,
        parent_id=int(parent_id) if parent_id else None,
        photo_url=photo_url,
        is_active=is_active
    )
    db.session.add(student)
    db.session.commit()

    log_audit("CREATE_STUDENT", f"Added student {full_name} ({nickname}) to class ID {class_id}")
    flash(f"Siswa {full_name} ({nickname}) berhasil ditambahkan!", "success")
    return redirect(url_for('admin.students', class_id=class_id))

@admin_bp.route('/students/<int:student_id>/edit', methods=['POST'])
@role_required('admin')
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.full_name = request.form.get('full_name', student.full_name).strip()
    student.nickname = request.form.get('nickname', student.nickname).strip()
    student.gender = request.form.get('gender', student.gender)
    student.class_id = request.form.get('class_id', student.class_id, type=int)
    student.is_active = (request.form.get('is_active', '1') == '1')

    parent_id = request.form.get('parent_id')
    student.parent_id = int(parent_id) if parent_id else None

    dob_str = request.form.get('dob')
    if dob_str:
        try:
            student.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    if 'photo' in request.files and request.files['photo'].filename != '':
        saved_url = save_upload_file(request.files['photo'], 'students')
        if saved_url:
            student.photo_url = saved_url

    db.session.commit()
    log_audit("EDIT_STUDENT", f"Updated student {student.full_name} (ID: {student.id})")
    flash(f"Data siswa {student.nickname} berhasil diperbarui.", "success")
    return redirect(url_for('admin.students'))

@admin_bp.route('/students/<int:student_id>/delete', methods=['POST'])
@role_required('admin')
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    name = student.full_name
    db.session.delete(student)
    db.session.commit()
    log_audit("DELETE_STUDENT", f"Deleted student {name} (ID: {student_id})")
    flash(f"Siswa {name} telah dihapus dari sistem.", "info")
    return redirect(url_for('admin.students'))

# --- AUDIT LOGS ---
@admin_bp.route('/audit-logs')
@role_required('admin')
def audit_logs():
    date_str = request.args.get('date', '').strip()
    action_filter = request.args.get('action', '').strip()

    query = AuditLog.query
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter(db.func.date(AuditLog.created_at) == target_date)
        except ValueError:
            pass

    if action_filter:
        query = query.filter(AuditLog.action.ilike(f'%{action_filter}%'))

    logs = query.order_by(AuditLog.created_at.desc()).limit(150).all()
    return render_template('admin/audit_logs.html', logs=logs, selected_date=date_str, selected_action=action_filter)
