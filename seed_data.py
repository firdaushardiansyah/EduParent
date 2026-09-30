import os
from datetime import datetime, date, timedelta
from app import create_app
from app.models import (
    db, User, ClassRoom, Student, DailyJournal,
    DevelopmentScore, PickupLog, HealthAlert, AuditLog
)

app = create_app('development')

def seed():
    with app.app_context():
        print("🌱 Menginisialisasi basis data dan data benih (seed data)...")
        db.create_all()

        # Check if already seeded
        if User.query.filter_by(username='admin').first():
            print("Database sudah memiliki data awal.")
            return

        # 1. USERS
        admin = User(
            username='admin',
            role='admin',
            full_name='Hj. Nurul Hidayah, M.Pd.',
            phone_number='081122334455'
        )
        admin.set_password('admin123')

        teacher1 = User(
            username='guru_rina',
            role='teacher',
            full_name='Rina Marlina, S.Pd.AUD',
            phone_number='081233445566'
        )
        teacher1.set_password('guru123')

        teacher2 = User(
            username='guru_budi',
            role='teacher',
            full_name='Budi Santoso, S.Pd.',
            phone_number='081344556677'
        )
        teacher2.set_password('guru123')

        parent_dewi = User(
            username='ortu_dewi',
            role='parent',
            full_name='Dewi Lestari, S.Farm.',
            phone_number='081234567890'
        )
        parent_dewi.set_password('ortu123')

        parent_fajar = User(
            username='ortu_fajar',
            role='parent',
            full_name='Fajar Pratama, S.T.',
            phone_number='081298765432'
        )
        parent_fajar.set_password('ortu123')

        parent_siti = User(
            username='ortu_siti',
            role='parent',
            full_name='Siti Rahmawati, S.E.',
            phone_number='085612345678'
        )
        parent_siti.set_password('ortu123')

        db.session.add_all([admin, teacher1, teacher2, parent_dewi, parent_fajar, parent_siti])
        db.session.commit()

        # 2. CLASSROOMS
        class_a = ClassRoom(
            name="TK-A Bintang Kecil (Usia 4-5 Thn)",
            academic_year="2025/2026",
            teacher_id=teacher1.id
        )
        class_b = ClassRoom(
            name="TK-B Mentari Pagi (Usia 5-6 Thn)",
            academic_year="2025/2026",
            teacher_id=teacher2.id
        )
        db.session.add_all([class_a, class_b])
        db.session.commit()

        # 3. STUDENTS
        # Arkan & Nayla share parent_dewi (demonstrating multi-child handling for parents)
        s1 = Student(
            full_name="Muhammad Arkan Al-Ghifari",
            nickname="Arkan",
            dob=date(2021, 5, 14),
            gender="L",
            class_id=class_a.id,
            parent_id=parent_dewi.id,
            photo_url="/static/img/avatar_arkan.svg"
        )
        s2 = Student(
            full_name="Nayla Putri Kirana",
            nickname="Nayla",
            dob=date(2020, 8, 22),
            gender="P",
            class_id=class_b.id,
            parent_id=parent_dewi.id,
            photo_url="/static/img/avatar_nayla.svg"
        )
        s3 = Student(
            full_name="Kenzo Danendra Wiratama",
            nickname="Kenzo",
            dob=date(2021, 3, 10),
            gender="L",
            class_id=class_a.id,
            parent_id=parent_fajar.id,
            photo_url="/static/img/avatar_kenzo.svg"
        )
        s4 = Student(
            full_name="Syifa Aulia Zahra",
            nickname="Syifa",
            dob=date(2021, 9, 5),
            gender="P",
            class_id=class_a.id,
            parent_id=parent_siti.id,
            photo_url="/static/img/avatar_syifa.svg"
        )
        s5 = Student(
            full_name="Rayyan Malik Ibrahim",
            nickname="Rayyan",
            dob=date(2020, 11, 18),
            gender="L",
            class_id=class_b.id,
            parent_id=None,
            photo_url="/static/img/avatar_rayyan.svg"
        )

        db.session.add_all([s1, s2, s3, s4, s5])
        db.session.commit()

        # 4. DAILY JOURNALS
        today = date.today()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)

        j1 = DailyJournal(
            student_id=s1.id,
            teacher_id=teacher1.id,
            date=today,
            attendance="HADIR",
            activity_summary="Mengikuti senam pagi ceria, meronce manik-manik kayu untuk melatih motorik halus, dan menyusun balok geometri warna-warni secara berkelompok.",
            meal_notes="Makan siang habis 1 porsi: Nasi putih, sup ayam jagung manis, tahu kukus, dan 1 buah pisang mas.",
            mood_status="Ceria & Aktif",
            photo_url=None
        )
        j2 = DailyJournal(
            student_id=s1.id,
            teacher_id=teacher1.id,
            date=yesterday,
            attendance="HADIR",
            activity_summary="Kegiatan finger painting melukis kupu-kupu warna-warni dengan pasta tepung. Arkan mampu mencampur warna merah dan kuning menjadi jingga dengan mandiri.",
            meal_notes="Habis 3/4 porsi sayur bayam wortel dan rolade telur ayam.",
            mood_status="Ceria",
            photo_url=None
        )
        j3 = DailyJournal(
            student_id=s2.id,
            teacher_id=teacher2.id,
            date=today,
            attendance="HADIR",
            activity_summary="Latihan membaca suku kata terbuka (ba-ca-bu-ku), bernyanyi lagu kebangsaan Indonesia Raya, dan bermain puzzle peta pulau Indonesia.",
            meal_notes="Makan bekal bersama: Nasi goreng telur dadar selada, air mineral 400ml habis.",
            mood_status="Sangat Antusias",
            photo_url=None
        )
        j4 = DailyJournal(
            student_id=s3.id,
            teacher_id=teacher1.id,
            date=today,
            attendance="HADIR",
            activity_summary="Bermain peran menjadi petugas pemadam kebakaran, bernyanyi lagu 'Aku Anak Hebat', serta mewarnai gambar mobil dinas.",
            meal_notes="Habis 1 mangkok bubur kacang hijau & biskuit gandum.",
            mood_status="Aktif",
            photo_url=None
        )
        j5 = DailyJournal(
            student_id=s4.id,
            teacher_id=teacher1.id,
            date=today,
            attendance="HADIR",
            activity_summary="Mendengarkan dongeng kancil dan gajah, menirukan suara hewan hutan, serta merapikan mainan ke kotak penyimpanan secara mandiri.",
            meal_notes="Makan bekal nasi kepal abon dan potongan apel.",
            mood_status="Tenang & Mandiri",
            photo_url=None
        )

        db.session.add_all([j1, j2, j3, j4, j5])
        db.session.commit()

        # 5. DEVELOPMENT SCORES (Indonesian PAUD Milestone Evaluation)
        # S1 Arkan - Evaluations over 3 periods
        ds1_prev2 = DevelopmentScore(
            student_id=s1.id,
            teacher_id=teacher1.id,
            evaluation_date=today - timedelta(days=60),
            gross_motor_score=2, # MB
            fine_motor_score=2,  # MB
            cognitive_score=3,   # BSH
            social_emotional_score=2, # MB
            teacher_comments="Arkan mulai terbiasa melompat dengan dua kaki dan antusias mengikuti instruksi permainan sederhana di kelas."
        )
        ds1_prev1 = DevelopmentScore(
            student_id=s1.id,
            teacher_id=teacher1.id,
            evaluation_date=today - timedelta(days=30),
            gross_motor_score=3, # BSH
            fine_motor_score=3,  # BSH
            cognitive_score=3,   # BSH
            social_emotional_score=3, # BSH
            teacher_comments="Peningkatan pesat pada koordinasi genggaman krayon dan kemampuan berbagi mainan dengan teman sebangku."
        )
        ds1_current = DevelopmentScore(
            student_id=s1.id,
            teacher_id=teacher1.id,
            evaluation_date=today - timedelta(days=3),
            gross_motor_score=4, # BSB (Berkembang Sangat Baik)
            fine_motor_score=3,  # BSH (Berkembang Sesuai Harapan)
            cognitive_score=4,   # BSB
            social_emotional_score=4, # BSB
            teacher_comments="Alhamdulillah, Arkan menunjukkan inisiatif tinggi membantu teman, daya ingat simbol huruf sangat kuat, serta kelincahan motorik kasar di atas rata-rata kelompok usianya."
        )

        # S2 Nayla
        ds2 = DevelopmentScore(
            student_id=s2.id,
            teacher_id=teacher2.id,
            evaluation_date=today - timedelta(days=5),
            gross_motor_score=4,
            fine_motor_score=4,
            cognitive_score=4,
            social_emotional_score=3,
            teacher_comments="Nayla sudah sangat matang dalam persiapan memasuki jenjang Sekolah Dasar (SD). Kemampuan fonik dan menulis tegak bersambung halus sangat rapi."
        )

        # S3 Kenzo
        ds3 = DevelopmentScore(
            student_id=s3.id,
            teacher_id=teacher1.id,
            evaluation_date=today - timedelta(days=5),
            gross_motor_score=4,
            fine_motor_score=3,
            cognitive_score=3,
            social_emotional_score=3,
            teacher_comments="Kenzo sangat lincah pada kegiatan fisik luar ruang, fokus motorik halus saat menggunting pola lengkung terus ditingkatkan."
        )

        db.session.add_all([ds1_prev2, ds1_prev1, ds1_current, ds2, ds3])
        db.session.commit()

        # 6. PICKUP LOGS (Today)
        # Kenzo: already picked up by his mother
        pl_kenzo = PickupLog(
            student_id=s3.id,
            teacher_id=teacher1.id,
            status="SUDAH_DIJEMPUT",
            collector_name="Ibu Ratna (Mama Kenzo)",
            collector_relation="ORANG_TUA",
            pickup_time=datetime.now() - timedelta(minutes=45),
            proof_photo_url=None,
            created_at=datetime.utcnow()
        )
        # Arkan: currently waiting (BELUM_DIJEMPUT) for real-time demo
        pl_arkan = PickupLog(
            student_id=s1.id,
            teacher_id=teacher1.id,
            status="BELUM_DIJEMPUT",
            collector_name=None,
            collector_relation=None,
            pickup_time=None,
            proof_photo_url=None,
            created_at=datetime.utcnow()
        )
        # Nayla: currently waiting
        pl_nayla = PickupLog(
            student_id=s2.id,
            teacher_id=teacher2.id,
            status="BELUM_DIJEMPUT",
            collector_name=None,
            collector_relation=None,
            pickup_time=None,
            proof_photo_url=None,
            created_at=datetime.utcnow()
        )
        # Syifa: already picked up by uncle
        pl_syifa = PickupLog(
            student_id=s4.id,
            teacher_id=teacher1.id,
            status="SUDAH_DIJEMPUT",
            collector_name="Paman Ridwan",
            collector_relation="KERABAT",
            pickup_time=datetime.now() - timedelta(minutes=20),
            proof_photo_url=None,
            created_at=datetime.utcnow()
        )

        db.session.add_all([pl_kenzo, pl_arkan, pl_nayla, pl_syifa])
        db.session.commit()

        # 7. HEALTH ALERTS
        ha1 = HealthAlert(
            student_id=s1.id,
            teacher_id=teacher1.id,
            severity="MEDIUM",
            title="Catatan Suhu Tubuh Agak Hangat",
            description="Pukul 11.20 WIB suhu tubuh Arkan 37.4°C setelah jam bermain luar. Sudah dikompres air hangat dan beristirahat di ruang UKS. Saat ini ceria kembali dan minum banyak air putih.",
            is_acknowledged=False,
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        ha2 = HealthAlert(
            student_id=s3.id,
            teacher_id=teacher1.id,
            severity="LOW",
            title="Luka Gores Kecil di Lutut",
            description="Tergores ringan saat bermain perosotan taman. Sudah dibersihkan dengan antiseptik dan diberi plester karakter hewan. Kenzo tidak menangis dan melanjutkan main.",
            is_acknowledged=True,
            created_at=datetime.utcnow() - timedelta(days=1)
        )

        db.session.add_all([ha1, ha2])
        db.session.commit()

        # 8. AUDIT LOGS
        al1 = AuditLog(
            user_id=admin.id,
            action="SYSTEM_INIT",
            details="Sistem EduParent PAUD/TK diinisialisasi untuk Tahun Ajaran 2025/2026",
            ip_address="127.0.0.1"
        )
        al2 = AuditLog(
            user_id=teacher1.id,
            action="VERIFY_PICKUP",
            details=f"Verifikasi penjemputan Kenzo Danendra oleh Ibu Ratna (ORANG_TUA)",
            ip_address="127.0.0.1"
        )
        db.session.add_all([al1, al2])
        db.session.commit()

        print(" Data benih EduParent berhasil diunggah!")
        print(" Akun demo siap digunakan:")
        print("   - Admin:      admin / admin123")
        print("   - Guru TK-A:  guru_rina / guru123")
        print("   - Guru TK-B:  guru_budi / guru123")
        print("   - Orang Tua:  ortu_dewi / ortu123  (Memiliki 2 anak: Arkan di TK-A & Nayla di TK-B)")
        print("   - Orang Tua:  ortu_fajar / ortu123 (Kenzo di TK-A)")

if __name__ == '__main__':
    seed()
