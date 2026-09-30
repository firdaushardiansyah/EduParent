# EduParent — Platform Monitoring Tumbuh Kembang & Verifikasi Penjemputan Anak PAUD/TK

<div align="center">
  <img src="app/static/img/logo.svg" alt="EduParent Logo" width="100"/>
  <h3>Sistem Informasi Terpadu PAUD & Taman Kanak-Kanak</h3>
  <p><strong>Early Childhood Development Tracking & Real-Time Pickup Verification Platform</strong></p>
</div>

---

## 🌟 Ringkasan Aplikasi

**EduParent** adalah platform web terpadu untuk Pendidikan Anak Usia Dini (PAUD) dan Taman Kanak-Kanak (TK) yang mengintegrasikan pencatatan tumbuh kembang anak, jurnal harian, dan protokol keamanan penjemputan anak secara *real-time*.

Aplikasi dibangun dengan arsitektur **Python Flask Modular Blueprint**, **SQLAlchemy ORM**, **Tailwind CSS v3**, **Chart.js** (Radar Spider Chart & Historical Line Progression), serta sistem otentikasi berbasis peran (**Role-Based Access Control / RBAC**) dengan isolasi data ketat untuk orang tua.

---

## ✨ Fitur Utama

### 1. 🛡️ Papan Kendali Verifikasi Penjemputan (*Pickup Verification Board*)
- **Status Real-Time:** Guru dapat mengubah status penjemputan (`BELUM_DIJEMPUT` ➡️ `SUDAH_DIJEMPUT`).
- **Verifikasi Identitas:** Pencatatan nama penjemput, hubungan keluarga (`ORANG_TUA`, `PENGASUH`, `SUPIR`, `KERABAT`), dan stempel waktu (*timestamp*).
- **Bukti Foto:** Unggah foto dokumentasi penyerahan anak secara langsung di gerbang sekolah.
- **Polling Real-Time Orang Tua:** Dashboard orang tua memperbarui status penjemputan otomatis setiap 8 detik via API tanpa perlu me-refresh halaman.

### 2. 📊 Analitik Tumbuh Kembang Berstandar PAUD (4 Aspek Capaian)
- Evaluasi 4 pilar perkembangan:
  1. **Motorik Kasar** (Keseimbangan, berlari, melompat)
  2. **Motorik Halus** (Memegang krayon, meronce, menggunting)
  3. **Kognitif & Bahasa** (Simbol huruf, logika bentuk, kosakata)
  4. **Sosial & Emosional** (Kemandirian, berbagi, regulasi emosi)
- Skala capaian standar PAUD:
  - `1`: **BB** (Belum Berkembang)
  - `2`: **MB** (Mulai Berkembang)
  - `3`: **BSH** (Berkembang Sesuai Harapan)
  - `4`: **BSB** (Berkembang Sangat Baik)
- **Visualisasi Interaktif:**
  - **Radar Spider Chart:** Keseimbangan 4 pilar stimulasi terkini.
  - **Historical Line Chart:** Tren grafik peningkatan rata-rata capaian anak dari waktu ke waktu.
  - Catatan naratif apresiasi dan rekomendasi stimulasi dari guru kelas.

### 3. 📖 Jurnal Aktivitas & Kehadiran Harian
- Guru mencatat kehadiran (`HADIR`, `SAKIT`, `IZIN`, `ALPA`), ringkasan aktivitas bermain-belajar, catatan menu & porsi makan siang, serta *mood status* anak.
- Dokumentasi foto kegiatan harian yang langsung tampil pada linimasa orang tua.

### 4. 🚨 Catatan Kesehatan & Peringatan Medis
- Guru dapat memicu peringatan darurat atau catatan fisik (`LOW`, `MEDIUM`, `HIGH`).
- Orang tua menerima badge peringatan prioritas tinggi di dashboard dan dapat melakukan konfirmasi baca (*acknowledgement*).

### 5. 🔒 Strict Data Isolation & RBAC
- **Admin Sekolah:** Manajemen master data (Kelas, Guru, Siswa, Orang Tua) dan audit log sistem.
- **Guru / Wali Kelas:** Akses penuh untuk input jurnal, penilaian, verifikasi kepulangan, dan catatan kesehatan siswa di kelasnya.
- **Orang Tua:** **Isolasi data ketat** — hanya dapat mengakses dan melihat data anak kandung yang terdaftar pada akunnya (akses ke ID anak lain diblokir dengan kode `403 Forbidden`). Mendukung akun wali murid dengan banyak anak (*multi-child switcher*).

---

## 🗄️ Desain Skema Database (SQLAlchemy Models)

| Model | Tabel | Deskripsi |
| :--- | :--- | :--- |
| `User` | `users` | Akun pengguna (`admin`, `teacher`, `parent`), password hash, kontak |
| `ClassRoom` | `class_rooms` | Kelompok kelas PAUD/TK (contoh: *TK-A Bintang Kecil*), penugasan wali kelas |
| `Student` | `students` | Data siswa, tanggal lahir, jenis kelamin, relasi kelas & wali murid |
| `DailyJournal` | `daily_journals` | Kehadiran, rangkuman aktivitas harian, catatan makan, mood, foto |
| `DevelopmentScore` | `development_scores` | Evaluasi 4 pilar PAUD (skala 1-4) & catatan guru |
| `PickupLog` | `pickup_logs` | Log verifikasi penjemputan anak, nama penjemput, relasi, bukti foto |
| `HealthAlert` | `health_alerts` | Peringatan medis/kesehatan (`LOW`, `MEDIUM`, `HIGH`) & status konfirmasi |
| `AuditLog` | `audit_logs` | Jejak audit keamanan sistem & aktivitas pengguna |

---

## 🚀 Panduan Menjalankan Aplikasi

### 1. Prasyarat
- Python 3.11+ (atau Python 3.15)
- Git (opsional)

### 2. Instalasi Dependensi
```bash
py -m pip install -r requirements.txt
```

### 3. Menginisialisasi Basis Data & Seed Data Awal
Jalankan skrip seed data untuk menginisialisasi tabel dan memuat data simulasi PAUD yang realistis:
```bash
py seed_data.py
```

### 4. Menjalankan Server Web
```bash
py run.py
```
Buka peramban (browser) di: **`http://127.0.0.1:5000`**

---

## 👥 Akun Demo Pengujian

Aplikasi telah dilengkapi tombol **Akses Instan Akun Pengujian** di halaman login:

| Peran | Username | Kata Sandi | Deskripsi Akun |
| :--- | :--- | :--- | :--- |
| **Admin Sekolah** | `admin` | `admin123` | Kepala Sekolah (*Hj. Nurul Hidayah, M.Pd.*) - Full CRUD & Audit Log |
| **Guru TK-A** | `guru_rina` | `guru123` | Wali Kelas TK-A Bintang Kecil (*Rina Marlina, S.Pd.*) |
| **Guru TK-B** | `guru_budi` | `guru123` | Wali Kelas TK-B Mentari Pagi (*Budi Santoso, S.Pd.*) |
| **Orang Tua** | `ortu_dewi` | `ortu123` | Wali Murid (*Dewi Lestari*) — Memiliki 2 anak: Arkan (TK-A) & Nayla (TK-B) |
| **Orang Tua** | `ortu_fajar`| `ortu123` | Wali Murid (*Fajar Pratama*) — Ayah dari Kenzo (TK-A) |

---

## 📁 Struktur Direktori Proyek

```
PRPL/
├── app/
│   ├── __init__.py          # Flask App Factory, Jinja Filters, LoginManager
│   ├── config.py            # Konfigurasi SQLite / PostgreSQL & upload
│   ├── models.py            # 8 SQLAlchemy Models & scoring helpers
│   ├── utils.py             # RBAC role_required decorator, upload & audit log
│   ├── auth/                # Blueprint Autentikasi (login, logout, profile)
│   ├── admin/               # Blueprint Admin (dashboard, users, classes, students)
│   ├── teacher/             # Blueprint Guru (dashboard, journal, development, pickup, alerts)
│   ├── parent/              # Blueprint Ortu (dashboard, feed, development radar & line charts)
│   ├── api/                 # Blueprint REST API (pickup polling, quick verify)
│   ├── static/
│   │   ├── css/custom.css   # Glassmorphism, pastel bento grid styling
│   │   ├── js/main.js       # Real-time polling (8s), modal handlers, previews
│   │   ├── img/             # SVG Logo & Cute Student Avatar illustrations
│   │   └── uploads/         # Direktori berkas foto kegiatan & bukti penjemputan
│   └── templates/
│       ├── base.html        # Master template glassmorphism nav & toasts
│       ├── auth/
│       ├── admin/
│       ├── teacher/
│       └── parent/
├── seed_data.py             # Data awal PAUD TK Bintang Ceria
├── run.py                   # Entry point aplikasi
└── requirements.txt         # Dependensi Python
```
