from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

SCORE_LABELS = {
    1: {"code": "BB", "name": "Belum Berkembang", "color": "rose", "desc": "Anak belum memperlihatkan perilaku yang diharapkan"},
    2: {"code": "MB", "name": "Mulai Berkembang", "color": "amber", "desc": "Anak mulai memperlihatkan perilaku namun masih dibimbing"},
    3: {"code": "BSH", "name": "Berkembang Sesuai Harapan", "color": "teal", "desc": "Anak sudah konsisten berkembang sesuai usianya"},
    4: {"code": "BSB", "name": "Berkembang Sangat Baik", "color": "emerald", "desc": "Anak menunjukkan perkembangan di atas rata-rata & mandiri"}
}

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='parent') # 'admin', 'teacher', 'parent'
    full_name = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(30), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    classes_taught = db.relationship('ClassRoom', back_populates='teacher', lazy=True)
    children = db.relationship('Student', back_populates='parent', lazy=True, foreign_keys='Student.parent_id')
    audit_logs = db.relationship('AuditLog', back_populates='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_teacher(self):
        return self.role == 'teacher'

    @property
    def is_parent(self):
        return self.role == 'parent'

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class ClassRoom(db.Model):
    __tablename__ = 'class_rooms'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # e.g. "TK-A Bintang Kecil"
    academic_year = db.Column(db.String(20), nullable=False, default="2025/2026")
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relationships
    teacher = db.relationship('User', back_populates='classes_taught')
    students = db.relationship('Student', back_populates='classroom', cascade="all, delete-orphan", lazy=True)

    def __repr__(self):
        return f"<ClassRoom {self.name} - {self.academic_year}>"


class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    nickname = db.Column(db.String(50), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False) # 'L' (Laki-laki) or 'P' (Perempuan)
    class_id = db.Column(db.Integer, db.ForeignKey('class_rooms.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    photo_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    classroom = db.relationship('ClassRoom', back_populates='students')
    parent = db.relationship('User', back_populates='children', foreign_keys=[parent_id])
    daily_journals = db.relationship('DailyJournal', back_populates='student', cascade="all, delete-orphan", lazy=True, order_by="desc(DailyJournal.date)")
    development_scores = db.relationship('DevelopmentScore', back_populates='student', cascade="all, delete-orphan", lazy=True, order_by="desc(DevelopmentScore.evaluation_date)")
    pickup_logs = db.relationship('PickupLog', back_populates='student', cascade="all, delete-orphan", lazy=True, order_by="desc(PickupLog.pickup_time)")
    health_alerts = db.relationship('HealthAlert', back_populates='student', cascade="all, delete-orphan", lazy=True, order_by="desc(HealthAlert.created_at)")

    @property
    def age(self):
        if not self.dob:
            return 0
        today = date.today()
        years = today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
        months = (today.month - self.dob.month) % 12
        return f"{years} thn {months} bln"

    @property
    def latest_pickup(self):
        today = date.today()
        # Look for today's pickup log
        for p in self.pickup_logs:
            if p.pickup_time and p.pickup_time.date() == today:
                return p
        # return latest
        return self.pickup_logs[0] if self.pickup_logs else None

    @property
    def unacknowledged_alerts(self):
        return [a for a in self.health_alerts if not a.is_acknowledged]

    def __repr__(self):
        return f"<Student {self.nickname} ({self.full_name})>"


class DailyJournal(db.Model):
    __tablename__ = 'daily_journals'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    attendance = db.Column(db.String(20), nullable=False, default='HADIR') # HADIR, SAKIT, IZIN, ALPA
    activity_summary = db.Column(db.Text, nullable=False)
    meal_notes = db.Column(db.Text, nullable=True) # e.g. "Habis 1 porsi nasi sayur bayam + buah pisang"
    mood_status = db.Column(db.String(50), nullable=False, default='Ceria') # Ceria, Tenang, Aktif, Sedih, Reog
    photo_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', back_populates='daily_journals')
    teacher = db.relationship('User', foreign_keys=[teacher_id])

    def __repr__(self):
        return f"<DailyJournal {self.student_id} - {self.date}>"


class DevelopmentScore(db.Model):
    __tablename__ = 'development_scores'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    evaluation_date = db.Column(db.Date, nullable=False, default=date.today)
    gross_motor_score = db.Column(db.Integer, nullable=False, default=3) # 1-4
    fine_motor_score = db.Column(db.Integer, nullable=False, default=3)   # 1-4
    cognitive_score = db.Column(db.Integer, nullable=False, default=3)    # 1-4
    social_emotional_score = db.Column(db.Integer, nullable=False, default=3) # 1-4
    teacher_comments = db.Column(db.Text, nullable=True)

    # Relationships
    student = db.relationship('Student', back_populates='development_scores')
    teacher = db.relationship('User', foreign_keys=[teacher_id])

    @property
    def gross_motor_label(self):
        return SCORE_LABELS.get(self.gross_motor_score, {})

    @property
    def fine_motor_label(self):
        return SCORE_LABELS.get(self.fine_motor_score, {})

    @property
    def cognitive_label(self):
        return SCORE_LABELS.get(self.cognitive_score, {})

    @property
    def social_emotional_label(self):
        return SCORE_LABELS.get(self.social_emotional_score, {})

    @property
    def average_score(self):
        total = self.gross_motor_score + self.fine_motor_score + self.cognitive_score + self.social_emotional_score
        return round(total / 4.0, 1)

    def to_dict(self):
        return {
            'id': self.id,
            'evaluation_date': self.evaluation_date.strftime('%Y-%m-%d'),
            'gross_motor': self.gross_motor_score,
            'fine_motor': self.fine_motor_score,
            'cognitive': self.cognitive_score,
            'social_emotional': self.social_emotional_score,
            'average': self.average_score,
            'comments': self.teacher_comments
        }


class PickupLog(db.Model):
    __tablename__ = 'pickup_logs'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(30), nullable=False, default='BELUM_DIJEMPUT') # 'BELUM_DIJEMPUT', 'SUDAH_DIJEMPUT'
    collector_name = db.Column(db.String(120), nullable=True)
    collector_relation = db.Column(db.String(50), nullable=True) # 'ORANG_TUA', 'PENGASUH', 'SUPIR', 'KERABAT'
    pickup_time = db.Column(db.DateTime, nullable=True)
    proof_photo_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', back_populates='pickup_logs')
    teacher = db.relationship('User', foreign_keys=[teacher_id])

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'status': self.status,
            'collector_name': self.collector_name,
            'collector_relation': self.collector_relation,
            'pickup_time': self.pickup_time.strftime('%H:%M WIB, %d %b %Y') if self.pickup_time else None,
            'proof_photo_url': self.proof_photo_url
        }


class HealthAlert(db.Model):
    __tablename__ = 'health_alerts'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    severity = db.Column(db.String(20), nullable=False, default='LOW') # 'LOW', 'MEDIUM', 'HIGH'
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    is_acknowledged = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', back_populates='health_alerts')
    teacher = db.relationship('User', foreign_keys=[teacher_id])

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else '',
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'is_acknowledged': self.is_acknowledged,
            'created_at': self.created_at.strftime('%d %b %Y, %H:%M')
        }


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='audit_logs')
