from datetime import datetime, date
from flask import render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import current_user
from app.parent import parent_bp
from app.models import (
    db, Student, DailyJournal, DevelopmentScore,
    PickupLog, HealthAlert, SCORE_LABELS
)
from app.utils import role_required, log_audit

def get_authorized_child(student_id):
    """
    STRICT DATA ISOLATION:
    Ensures the student belongs to the current logged-in parent.
    Raises 403 or 404 if not authorized.
    """
    student = Student.query.get_or_404(student_id)
    if student.parent_id != current_user.id:
        abort(403)
    return student

@parent_bp.route('/dashboard')
@role_required('parent')
def dashboard():
    children = Student.query.filter_by(parent_id=current_user.id).all()

    if not children:
        return render_template('parent/no_child.html')

    selected_id = request.args.get('child_id', type=int)
    if selected_id:
        selected_child = get_authorized_child(selected_id)
    else:
        selected_child = children[0]

    today = date.today()

    # Today's journal
    today_journal = DailyJournal.query.filter_by(
        student_id=selected_child.id,
        date=today
    ).first()

    # Recent journals
    recent_journals = DailyJournal.query.filter_by(
        student_id=selected_child.id
    ).order_by(DailyJournal.date.desc()).limit(5).all()

    # Latest pickup status today
    today_pickup = PickupLog.query.filter(
        PickupLog.student_id == selected_child.id,
        db.func.date(PickupLog.created_at) == today
    ).order_by(PickupLog.created_at.desc()).first()

    # Active alerts
    alerts = HealthAlert.query.filter_by(
        student_id=selected_child.id
    ).order_by(HealthAlert.created_at.desc()).limit(5).all()

    # Latest development score
    latest_dev = DevelopmentScore.query.filter_by(
        student_id=selected_child.id
    ).order_by(DevelopmentScore.evaluation_date.desc()).first()

    return render_template(
        'parent/dashboard.html',
        children=children,
        selected_child=selected_child,
        today_journal=today_journal,
        recent_journals=recent_journals,
        today_pickup=today_pickup,
        alerts=alerts,
        latest_dev=latest_dev,
        score_labels=SCORE_LABELS,
        today=today
    )

@parent_bp.route('/child/<int:student_id>/journals')
@role_required('parent')
def journal_feed(student_id):
    child = get_authorized_child(student_id)
    children = Student.query.filter_by(parent_id=current_user.id).all()

    journals = DailyJournal.query.filter_by(
        student_id=child.id
    ).order_by(DailyJournal.date.desc()).all()

    return render_template(
        'parent/journal_feed.html',
        children=children,
        selected_child=child,
        journals=journals
    )

@parent_bp.route('/child/<int:student_id>/development')
@role_required('parent')
def development_report(student_id):
    child = get_authorized_child(student_id)
    children = Student.query.filter_by(parent_id=current_user.id).all()

    # All development scores ordered by date ascending for line chart
    scores_asc = DevelopmentScore.query.filter_by(
        student_id=child.id
    ).order_by(DevelopmentScore.evaluation_date.asc()).all()

    # Latest score for radar chart
    latest_score = scores_asc[-1] if scores_asc else None

    # Chart data serialization
    radar_data = {
        'labels': [
            'Motorik Kasar (Gross Motor)',
            'Motorik Halus (Fine Motor)',
            'Kognitif & Bahasa',
            'Sosial & Emosional'
        ],
        'scores': [
            latest_score.gross_motor_score if latest_score else 0,
            latest_score.fine_motor_score if latest_score else 0,
            latest_score.cognitive_score if latest_score else 0,
            latest_score.social_emotional_score if latest_score else 0
        ] if latest_score else [0, 0, 0, 0]
    }

    history_dates = [s.evaluation_date.strftime('%d/%m/%Y') for s in scores_asc]
    history_averages = [s.average_score for s in scores_asc]
    history_gross = [s.gross_motor_score for s in scores_asc]
    history_fine = [s.fine_motor_score for s in scores_asc]
    history_cognitive = [s.cognitive_score for s in scores_asc]
    history_social = [s.social_emotional_score for s in scores_asc]

    line_chart_data = {
        'dates': history_dates,
        'averages': history_averages,
        'gross': history_gross,
        'fine': history_fine,
        'cognitive': history_cognitive,
        'social': history_social
    }

    return render_template(
        'parent/development_report.html',
        children=children,
        selected_child=child,
        scores=list(reversed(scores_asc)),
        latest_score=latest_score,
        radar_data=radar_data,
        line_chart_data=line_chart_data,
        score_labels=SCORE_LABELS
    )

@parent_bp.route('/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@role_required('parent')
def acknowledge_alert(alert_id):
    alert = HealthAlert.query.get_or_404(alert_id)
    # Validate child belongs to this parent
    if alert.student.parent_id != current_user.id:
        abort(403)

    alert.is_acknowledged = True
    db.session.commit()
    log_audit("ACK_ALERT", f"Parent {current_user.username} acknowledged alert ID {alert.id}", user_id=current_user.id)
    flash("Pemberitahuan telah Anda konfirmasi.", "success")
    return redirect(request.referrer or url_for('parent.dashboard', child_id=alert.student_id))
