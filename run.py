import os
from app import create_app
from app.models import db, User
from seed_data import seed

app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Auto-seed if database is empty
        if not User.query.filter_by(username='admin').first():
            print("📦 Database kosong terdeteksi. Menjalankan auto-seeding...")
            seed()

    port = int(os.environ.get('PORT', 5000))
    print(f"\n========================================================")
    print(f"🚀 EduParent berjalan di: http://127.0.0.1:{port}")
    print(f"========================================================\n")
    app.run(host='0.0.0.0', port=port, debug=True)
