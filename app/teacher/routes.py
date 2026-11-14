from datetime import datetime, date
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user
from app.teacher import teacher_bp
from app.models import (
    db, Student, ClassRoom, DailyJournal, DevelopmentScore,
    PickupLog, HealthAlert, SCORE_LABELS
)
from app.utils import role_required, save_upload_file, log_audit

def get_teacher_classes(teacher_id):
    """Get classes taught by teacher, or fallback to all classes if not assigned."""
    classes = ClassRoom.query.filter_by(teacher_id=teacher_id).all()
    if not classes:
        classes = ClassRoom.query.all()
    return classes

@teacher_bp.route('/dashboard')
@role_required('teacher')
def dashboard():
    classes = get_teacher_classes(current_user.id)
    class_ids = [c.id for c in classes]
    students = Student.query.filter(Student.class_id.in_(class_ids)).all() if class_ids else []

    today = date.today()
    student_ids = [s.id for s in students]

    # Today's journals
    journals_today = DailyJournal.query.filter(
        DailyJournal.student_id.in_(student_ids),
        DailyJournal.date == today
    ).all() if student_ids else []

    # Map of student_id -> journal today
    today_journal_map = {j.student_id: j for j in journals_today}

    # Today's pickup logs
    pickups_today = PickupLog.query.filter(
        PickupLog.student_id.in_(student_ids),
        db.func.date(PickupLog.created_at) == today
    ).all() if student_ids else []

    pickup_map = {p.student_id: p for p in pickups_today}
    picked_up_count = sum(1 for p in pickups_today if p.status == 'SUDAH_DIJEMPUT')
    waiting_count = len(students) - picked_up_count

    # Active alerts
    active_alerts = HealthAlert.query.filter(
        HealthAlert.student_id.in_(student_ids),
        HealthAlert.is_acknowledged == False
    ).order_by(HealthAlert.created_at.desc()).limit(5).all() if student_ids else []

    return render_template(
        'teacher/dashboard.html',
        classes=classes,
        students=students,
        total_students=len(students),
        journals_today_count=len(journals_today),
        picked_up_count=picked_up_count,
        waiting_count=waiting_count,
        active_alerts=active_alerts,
        today_journal_map=today_journal_map,
        pickup_map=pickup_map,
        today=today
    )

# --- DAILY JOURNAL ---
@teacher_bp.route('/journal', methods=['GET', 'POST'])
@role_required('teacher')
def journal():
    classes = get_teacher_classes(current_user.id)
    selected_class_id = request.args.get('class_id', type=int)
    if not selected_class_id and classes:
        selected_class_id = classes[0].id

    date_str = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = date.today()

    students = Student.query.filter_by(class_id=selected_class_id).all() if selected_class_id else []
    student_ids = [s.id for s in students]

    journals = DailyJournal.query.filter(
        DailyJournal.student_id.in_(student_ids),
        DailyJournal.date == selected_date
    ).all() if student_ids else []

    journal_map = {j.student_id: j for j in journals}

    return render_template(
        'teacher/journal.html',
        classes=classes,
        selected_class_id=selected_class_id,
        selected_date=selected_date,
        students=students,
        journal_map=journal_map
    )

@teacher_bp.route('/journal/save', methods=['POST'])
@role_required('teacher')
def save_journal():
    student_id = request.form.get('student_id', type=int)
    date_str = request.form.get('date')
    attendance = request.form.get('attendance', 'HADIR')
    activity_summary = request.form.get('activity_summary', '').strip()
    meal_notes = request.form.get('meal_notes', '').strip()
    mood_status = request.form.get('mood_status', 'Ceria')

    try:
        journal_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        journal_date = date.today()

    student = Student.query.get_or_404(student_id)

    # Check existing journal for this date
    journal = DailyJournal.query.filter_by(student_id=student_id, date=journal_date).first()
    if not journal:
        journal = DailyJournal(
            student_id=student_id,
            teacher_id=current_user.id,
            date=journal_date
        )
        db.session.add(journal)

    journal.teacher_id = current_user.id
    journal.attendance = attendance
    journal.activity_summary = activity_summary
    journal.meal_notes = meal_notes
    journal.mood_status = mood_status

    if 'photo' in request.files and request.files['photo'].filename != '':
        saved_photo = save_upload_file(request.files['photo'], 'journals')
        if saved_photo:
            journal.photo_url = saved_photo

    db.session.commit()
    log_audit("SAVE_JOURNAL", f"Saved daily journal for student {student.nickname} on {journal_date}")
    flash(f"Jurnal harian untuk {student.nickname} berhasil disimpan!", "success")

    return redirect(url_for('teacher.journal', class_id=student.class_id, date=journal_date.strftime('%Y-%m-%d')))

@teacher_bp.route('/journal/<int:journal_id>/delete', methods=['POST'])
@role_required('teacher')
def delete_journal(journal_id):
    journal = DailyJournal.query.get_or_404(journal_id)
    class_id = journal.student.class_id
    journal_date = journal.date.strftime('%Y-%m-%d')
    db.session.delete(journal)
    db.session.commit()
    log_audit("DELETE_JOURNAL", f"Deleted journal ID {journal_id}")
    flash("Jurnal harian berhasil dihapus.", "info")
    return redirect(url_for('teacher.journal', class_id=class_id, date=journal_date))

# --- DEVELOPMENT SCORES ---
@teacher_bp.route('/development')
@role_required('teacher')
def development():
    classes = get_teacher_classes(current_user.id)
    selected_class_id = request.args.get('class_id', type=int)
    if not selected_class_id and classes:
        selected_class_id = classes[0].id

    students = Student.query.filter_by(class_id=selected_class_id).all() if selected_class_id else []

    # Map student to their latest development assessment
    latest_scores = {}
    for s in students:
        if s.development_scores:
            latest_scores[s.id] = s.development_scores[0] # ordered by desc date

    return render_template(
        'teacher/development.html',
        classes=classes,
        selected_class_id=selected_class_id,
        students=students,
        latest_scores=latest_scores,
        score_labels=SCORE_LABELS
    )

@teacher_bp.route('/development/save', methods=['POST'])
@role_required('teacher')
def save_development():
    student_id = request.form.get('student_id', type=int)
    eval_date_str = request.form.get('evaluation_date')
    gross_motor = request.form.get('gross_motor_score', type=int)
    fine_motor = request.form.get('fine_motor_score', type=int)
    cognitive = request.form.get('cognitive_score', type=int)
    social_emotional = request.form.get('social_emotional_score', type=int)
    comments = request.form.get('teacher_comments', '').strip()

    try:
        eval_date = datetime.strptime(eval_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        eval_date = date.today()

    student = Student.query.get_or_404(student_id)

    # Check if entry already exists on this date
    dev_score = DevelopmentScore.query.filter_by(student_id=student_id, evaluation_date=eval_date).first()
    if not dev_score:
        dev_score = DevelopmentScore(
            student_id=student_id,
            teacher_id=current_user.id,
            evaluation_date=eval_date
        )
        db.session.add(dev_score)

    dev_score.teacher_id = current_user.id
    dev_score.gross_motor_score = gross_motor or 3
    dev_score.fine_motor_score = fine_motor or 3
    dev_score.cognitive_score = cognitive or 3
    dev_score.social_emotional_score = social_emotional or 3
    dev_score.teacher_comments = comments

    db.session.commit()
    log_audit("SAVE_DEVELOPMENT", f"Recorded development score for {student.nickname} on {eval_date}")
    flash(f"Penilaian capaian tumbuh kembang {student.nickname} berhasil disimpan!", "success")

    return redirect(url_for('teacher.development', class_id=student.class_id))

@teacher_bp.route('/development/<int:score_id>/delete', methods=['POST'])
@role_required('teacher')
def delete_development(score_id):
    score = DevelopmentScore.query.get_or_404(score_id)
    class_id = score.student.class_id
    student_name = score.student.nickname
    db.session.delete(score)
    db.session.commit()
    log_audit("DELETE_DEVELOPMENT", f"Deleted development score ID {score_id} for {student_name}")
    flash(f"Data evaluasi capaian untuk {student_name} telah dihapus.", "info")
    return redirect(url_for('teacher.development', class_id=class_id))

# --- PICKUP VERIFICATION (KEY FEATURE) ---
@teacher_bp.route('/pickup')
@role_required('teacher')
def pickup():
    classes = get_teacher_classes(current_user.id)
    selected_class_id = request.args.get('class_id', type=int)
    if not selected_class_id and classes:
        selected_class_id = classes[0].id

    today = date.today()
    students = Student.query.filter_by(class_id=selected_class_id).all() if selected_class_id else []

    # Get today's pickups for these students
    student_ids = [s.id for s in students]
    pickups = PickupLog.query.filter(
        PickupLog.student_id.in_(student_ids),
        db.func.date(PickupLog.created_at) == today
    ).all() if student_ids else []

    pickup_map = {p.student_id: p for p in pickups}

    return render_template(
        'teacher/pickup.html',
        classes=classes,
        selected_class_id=selected_class_id,
        students=students,
        pickup_map=pickup_map,
        today=today
    )

@teacher_bp.route('/pickup/verify', methods=['POST'])
@role_required('teacher')
def verify_pickup():
    student_id = request.form.get('student_id', type=int)
    collector_name = request.form.get('collector_name', '').strip()
    collector_relation = request.form.get('collector_relation', 'ORANG_TUA')
    new_status = request.form.get('status', 'SUDAH_DIJEMPUT')

    student = Student.query.get_or_404(student_id)
    today = date.today()

    # Find today's pickup record or create new
    pickup_log = PickupLog.query.filter(
        PickupLog.student_id == student_id,
        db.func.date(PickupLog.created_at) == today
    ).first()

    if not pickup_log:
        pickup_log = PickupLog(
            student_id=student_id,
            teacher_id=current_user.id,
            status=new_status,
            created_at=datetime.utcnow()
        )
        db.session.add(pickup_log)

    pickup_log.teacher_id = current_user.id
    pickup_log.status = new_status
    pickup_log.collector_name = collector_name if new_status == 'SUDAH_DIJEMPUT' else None
    pickup_log.collector_relation = collector_relation if new_status == 'SUDAH_DIJEMPUT' else None
    pickup_log.pickup_time = datetime.now() if new_status == 'SUDAH_DIJEMPUT' else None

    # Handle photo upload
    if 'proof_photo' in request.files and request.files['proof_photo'].filename != '':
        saved_photo = save_upload_file(request.files['proof_photo'], 'pickups')
        if saved_photo:
            pickup_log.proof_photo_url = saved_photo

    db.session.commit()
    log_audit("VERIFY_PICKUP", f"Pickup status for {student.nickname} set to {new_status} by {collector_name} ({collector_relation})")
    flash(f"Status penjemputan {student.nickname} berhasil diperbarui menjadi '{new_status}'!", "success")

    return redirect(url_for('teacher.pickup', class_id=student.class_id))

# --- HEALTH & EMERGENCY ALERTS ---
@teacher_bp.route('/alerts')
@role_required('teacher')
def alerts():
    classes = get_teacher_classes(current_user.id)
    selected_class_id = request.args.get('class_id', type=int)
    if not selected_class_id and classes:
        selected_class_id = classes[0].id

    students = Student.query.filter_by(class_id=selected_class_id).all() if selected_class_id else []
    student_ids = [s.id for s in students]

    all_alerts = HealthAlert.query.filter(
        HealthAlert.student_id.in_(student_ids)
    ).order_by(HealthAlert.created_at.desc()).all() if student_ids else []

    return render_template(
        'teacher/alerts.html',
        classes=classes,
        selected_class_id=selected_class_id,
        students=students,
        alerts=all_alerts
    )

@teacher_bp.route('/alerts/create', methods=['POST'])
@role_required('teacher')
def create_alert():
    student_id = request.form.get('student_id', type=int)
    severity = request.form.get('severity', 'LOW') # LOW, MEDIUM, HIGH
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()

    if not student_id or not title or not description:
        flash("Mohon isi siswa, judul, dan deskripsi peringatan kesehatan.", "danger")
        return redirect(url_for('teacher.alerts'))

    student = Student.query.get_or_404(student_id)

    alert = HealthAlert(
        student_id=student_id,
        teacher_id=current_user.id,
        severity=severity,
        title=title,
        description=description,
        is_acknowledged=False
    )
    db.session.add(alert)
    db.session.commit()

    log_audit("CREATE_HEALTH_ALERT", f"Triggered {severity} alert for {student.nickname}: {title}")
    flash(f"Peringatan kesehatan untuk {student.nickname} berhasil dikirim ke orang tua!", "warning" if severity == 'HIGH' else "success")

    return redirect(url_for('teacher.alerts', class_id=student.class_id))

@teacher_bp.route('/alerts/<int:alert_id>/toggle', methods=['POST'])
@role_required('teacher')
def toggle_alert(alert_id):
    alert = HealthAlert.query.get_or_404(alert_id)
    alert.is_acknowledged = not alert.is_acknowledged
    db.session.commit()
    return redirect(url_for('teacher.alerts', class_id=alert.student.class_id))

@teacher_bp.route('/alerts/<int:alert_id>/edit', methods=['POST'])
@role_required('teacher')
def edit_alert(alert_id):
    alert = HealthAlert.query.get_or_404(alert_id)
    alert.severity = request.form.get('severity', alert.severity)
    alert.title = request.form.get('title', alert.title).strip()
    alert.description = request.form.get('description', alert.description).strip()
    db.session.commit()
    log_audit("EDIT_HEALTH_ALERT", f"Updated health alert ID {alert.id} for {alert.student.nickname}")
    flash("Catatan kesehatan berhasil diperbarui.", "success")
    return redirect(url_for('teacher.alerts', class_id=alert.student.class_id))

@teacher_bp.route('/alerts/<int:alert_id>/delete', methods=['POST'])
@role_required('teacher')
def delete_alert(alert_id):
    alert = HealthAlert.query.get_or_404(alert_id)
    class_id = alert.student.class_id
    title = alert.title
    db.session.delete(alert)
    db.session.commit()
    log_audit("DELETE_HEALTH_ALERT", f"Deleted health alert '{title}'")
    flash("Catatan kesehatan berhasil dihapus.", "info")
    return redirect(url_for('teacher.alerts', class_id=class_id))
