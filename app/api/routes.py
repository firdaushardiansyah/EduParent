from datetime import datetime, date
from flask import jsonify, request, abort
from flask_login import current_user, login_required
from app.api import api_bp
from app.models import db, Student, PickupLog, DevelopmentScore, HealthAlert
from app.utils import log_audit

@api_bp.route('/pickup/status/<int:student_id>')
@login_required
def get_pickup_status(student_id):
    student = Student.query.get_or_404(student_id)
    # Check parent isolation if role is parent
    if current_user.role == 'parent' and student.parent_id != current_user.id:
        abort(403)

    today = date.today()
    pickup = PickupLog.query.filter(
        PickupLog.student_id == student_id,
        db.func.date(PickupLog.created_at) == today
    ).order_by(PickupLog.created_at.desc()).first()

    if not pickup:
        return jsonify({
            'status': 'BELUM_DIJEMPUT',
            'collector_name': '-',
            'collector_relation': '-',
            'pickup_time': '-',
            'proof_photo_url': None
        })

    return jsonify(pickup.to_dict())

@api_bp.route('/pickup/quick-verify', methods=['POST'])
@login_required
def quick_verify_pickup():
    if current_user.role not in ['teacher', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json() or {}
    student_id = data.get('student_id')
    new_status = data.get('status', 'SUDAH_DIJEMPUT')
    collector_name = data.get('collector_name', 'Orang Tua / Wali')
    collector_relation = data.get('collector_relation', 'ORANG_TUA')

    student = Student.query.get_or_404(student_id)
    today = date.today()

    pickup = PickupLog.query.filter(
        PickupLog.student_id == student_id,
        db.func.date(PickupLog.created_at) == today
    ).first()

    if not pickup:
        pickup = PickupLog(
            student_id=student_id,
            teacher_id=current_user.id,
            status=new_status,
            created_at=datetime.utcnow()
        )
        db.session.add(pickup)

    pickup.status = new_status
    pickup.teacher_id = current_user.id
    if new_status == 'SUDAH_DIJEMPUT':
        pickup.collector_name = collector_name
        pickup.collector_relation = collector_relation
        pickup.pickup_time = datetime.now()
    else:
        pickup.collector_name = None
        pickup.collector_relation = None
        pickup.pickup_time = None

    db.session.commit()
    log_audit("API_PICKUP_UPDATE", f"Pickup status for {student.nickname} changed to {new_status}")

    return jsonify({
        'success': True,
        'message': f"Status penjemputan {student.nickname} diperbarui.",
        'pickup': pickup.to_dict()
    })

@api_bp.route('/child/<int:student_id>/development-stats')
@login_required
def child_development_stats(student_id):
    student = Student.query.get_or_404(student_id)
    if current_user.role == 'parent' and student.parent_id != current_user.id:
        abort(403)

    scores = DevelopmentScore.query.filter_by(
        student_id=student_id
    ).order_by(DevelopmentScore.evaluation_date.asc()).all()

    return jsonify({
        'student_id': student.id,
        'student_name': student.full_name,
        'scores': [s.to_dict() for s in scores]
    })
