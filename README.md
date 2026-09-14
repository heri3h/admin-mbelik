# Dashboard Analitik Performa & Profitabilitas Iklan

Aplikasi web dashboard internal untuk memantau performa dan profitabilitas iklan dengan mengintegrasikan data pengeluaran dari **Google Ads API** (multi-account) dan pendapatan dari **Google Ad Manager (GAM / AdX) API**.

![Dashboard Preview](https://img.shields.io/badge/Status-Ready-brightgreen)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-blue)
![React](https://img.shields.io/badge/Frontend-React%20Vite%20%2B%20Tailwind-61dafb)

---

## 📌 Fitur Utama

1. **Integrasi Data Multi-Source**:
   - **Google Ads API**: Mendukung penarikan data dari beberapa akun/MCC (Spend, Impressions, Clicks, CPC, CTR, Account Name, Campaign Name).
   - **Google Ad Manager API**: Penarikan pendapatan AdX (Revenue, Impressions, eCPM, Clicks, Domain/Ad Unit).
2. **Kalkulasi Profitabilitas Otomatis**:
   - **Total Spend (Cost)** = Total pengeluaran dari semua akun Google Ads.
   - **Total Revenue** = Total pendapatan dari AdX / GAM.
   - **Net Profit** = Total Revenue - Total Spend.
   - **ROI / ROAS** = `(Total Revenue / Total Spend) * 100%`.
   - **Profit Margin** = `(Net Profit / Total Revenue) * 100%`.
   - *Highlighting*: Indikator visual hijau jika untung ($>0$) dan merah jika rugi ($<0$).
3. **Penyimpanan Historis (Caching & Sync)**:
   - Menggunakan SQLite / PostgreSQL agar penelusuran dashboard cepat tanpa harus selalu memanggil API eksternal.
   - Sinkronisasi data manual (Tombol Sync) dan cron scheduler otomatis.
4. **Antarmuka Modern & Responsi**:
   - Filter Rentang Tanggal: Hari Ini, Kemarin, 7 Hari Terakhir, Bulan Ini, dan Custom Date Range.
   - Executive Summary Cards.
   - Grafik Tren Harian (Spend vs Revenue vs Profit).
   - Tabel Breakdown Detail per Akun Google Ads dan per Domain GAM.
5. **Mock Mode Fallback**:
   - Jika kredensial API belum diisi di `.env`, aplikasi otomatis menggunakan simulator data realistis agar UI dashboard dapat diuji secara instan.

---

## 🚀 Panduan Konfigurasi & Setup Kredensial API

### 1. Setup Google Cloud Console & Google Ads API

1. Buka [Google Cloud Console](https://console.cloud.google.com/).
2. Buat proyek baru atau pilih proyek yang sudah ada.
3. Buka **APIs & Services > Library**, cari **Google Ads API** dan klik **Enable**.
4. Buka **APIs & Services > OAuth consent screen**:
   - Pilih User Type (**Internal** jika Workspace, atau **External**).
   - Isi App Name, Support Email, dan Developer Contact.
5. Buka **APIs & Services > Credentials**:
   - Klik **Create Credentials** > **OAuth client ID**.
   - Pilih Application type: **Web application** atau **Desktop app**.
   - Simpan `Client ID` dan `Client Secret`.
6. Dapatkan **Developer Token Google Ads**:
   - Login ke akun pengelola Google Ads (MCC Manager Account).
   - Buka **Tools & Settings > API Center**.
   - Salin **Developer Token**.
7. Dapatkan **OAuth Refresh Token**:
   - Gunakan alat autentikasi Google OAuth playground atau script SDK `google-ads` (`generate_user_credentials.py`) untuk menghasilkan `Refresh Token`.

### 2. Setup Google Ad Manager (GAM / AdX) API

1. **Membuat Service Account**:
   - Buka Google Cloud Console > **IAM & Admin > Service Accounts**.
   - Klik **Create Service Account**, beri nama (misal `gam-api-service-account`).
   - Klik **Create and Continue**, lalu **Done**.
   - Klik pada Service Account yang baru dibuat > Tab **Keys** > **Add Key** > **Create new key** (Pilih format **JSON**).
   - Simpan file JSON tersebut ke direktori backend (misal: `./gam_service_account.json`).
2. **Memberikan Akses Service Account di Google Ad Manager**:
   - Login ke [Google Ad Manager Console](https://admanager.google.com/).
   - Buka **Admin > Global settings > Network settings**.
   - Pastikan **API access** sudah diaktifkan.
   - Buka **Admin > Access & permission > Users**.
   - Klik **New user**:
     - Name: `API Service Account`
     - Email: *(Masukkan email Service Account dari GCP, contoh: `gam-api@project-id.iam.gserviceaccount.com`)*
     - Role: **Trafficker** atau role kustom dengan izin melihat laporan (Reporting access).
   - Simpan **Network Code** Ad Manager Anda.

---

## ⚙️ Variabel Lingkungan (`.env`)

Buat file `.env` di folder utama aplikasi berdasarkan `.env.example`:

```env
# Configuration
PORT=8000
SECRET_KEY=ganti_dengan_secret_key_random_yang_aman
DATABASE_URL=sqlite:///./ad_analytics.db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# Mata Uang Dashboard (IDR untuk Rupiah, USD untuk Dollar)
CURRENCY=IDR

# Toggle Mock Data (set false jika ingin menggunakan API asli)
USE_MOCK_DATA=false

# Google Ads API Credentials
GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token_here
GOOGLE_ADS_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=your_client_secret_here
GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token_here
GOOGLE_ADS_CUSTOMER_IDS=123-456-7890
GOOGLE_ADS_LOGIN_CUSTOMER_ID=123-456-7890

# Google Ad Manager API Credentials
GAM_NETWORK_CODE=123456789
GAM_APPLICATION_NAME=AdAnalyticsDashboard
GAM_JSON_KEY_FILE_PATH=./gam_service_account.json
```

---

## 📦 Instalasi & Cara Menjalankan Aplikasi

### 1. Menjalankan Backend (FastAPI)

```bash
# Pindah ke direktori backend
cd backend

# Buat virtual environment (opsional tetapi disarankan)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependensi
pip install -r requirements.txt

# Inisialisasi database & user admin default
python seed.py

# Jalankan server FastAPI
uvicorn app.main:app --reload --port 8000
```
Server backend akan berjalan di `http://localhost:8000`. Dokumentasi OpenAPI Swagger tersedia di `http://localhost:8000/docs`.

### 2. Menjalankan Frontend (React + Vite)

```bash
# Pindah ke direktori frontend
cd frontend

# Install dependensi Node.js
npm install

# Jalankan dev server Vite
npm run dev
```
Aplikasi web frontend akan berjalan di `http://localhost:5173`.

### 3. Deployment di Server Production (HestiaCP + Nginx)

Untuk memasang aplikasi ini di server HestiaCP dengan username **`mbummm`** dan domain **`admin.mbelik.com`**:

#### Langkah A: Build Frontend & Deploy Ke `public_html`
```bash
cd frontend
npm install
npm run build
```
Salin seluruh isi folder `frontend/dist/` ke direktori web domain:
`/home/mbummm/web/admin.mbelik.com/public_html/`

#### Langkah B: Menjalankan Backend via Systemd Service
Upload folder `backend/` ke `/home/mbummm/web/admin.mbelik.com/private/backend/` *(bukan di dalam public_html)*.

> [!NOTE]
> Jika Anda mengunggah folder `venv` dari komputer lokal (Mac/Windows), hapus terlebih dahulu folder `venv` tersebut di server dan buat ulang secara native di Linux:
> ```bash
> cd /home/mbummm/web/admin.mbelik.com/private/backend
> rm -rf venv
> python3 -m venv venv
> ./venv/bin/pip install -r requirements.txt
> ./venv/bin/python seed.py
> ```

Buat file service di VPS: `/etc/systemd/system/ad-analytics.service`
```ini
[Unit]
Description=Ad Analytics FastAPI Service
After=network.target

[Service]
User=mbummm
WorkingDirectory=/home/mbummm/web/admin.mbelik.com/private/backend
ExecStart=/home/mbummm/web/admin.mbelik.com/private/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Aktifkan service:
```bash
sudo systemctl daemon-reload
sudo systemctl start ad-analytics
sudo systemctl enable ad-analytics
```

#### Langkah C: Konfigurasi Nginx Include di HestiaCP
Buat file include Nginx di server:
- `/home/mbummm/conf/web/admin.mbelik.com/nginx.conf_incl`
- `/home/mbummm/conf/web/admin.mbelik.com/nginx.ssl.conf_incl`

Isi kedua file tersebut dengan:
```nginx
location /api {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```
Reload Nginx:
```bash
sudo systemctl reload nginx
```

---

### 4. Login Default
- **Username**: `admin`
- **Password**: `admin123` *(bisa diubah via .env)*

---

## 🛠️ Struktur Proyek

```
admin/
├── backend/
│   ├── app/
│   │   ├── api/          # Route controller (auth, dashboard, sync, settings)
│   │   ├── services/     # Logic Google Ads, GAM API, kalkulasi profit & sync
│   │   ├── config.py     # Environment configuration
│   │   ├── database.py   # SQLAlchemy setup
│   │   ├── models.py     # Database schema tables
│   │   ├── schemas.py    # Pydantic validation schemas
│   │   └── main.py       # FastAPI application entrypoint
│   ├── seed.py           # Initial database setup script
│   └── requirements.txt  # Python package dependencies
├── frontend/
│   ├── src/
│   │   ├── components/   # UI Reusable Components (Summary, Charts, Tables)
│   │   ├── pages/        # Login, Dashboard, Settings
│   │   ├── services/     # API Axios client
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── .env.example
└── README.md
```

---

## 📊 Rumus Kalkulasi Profitabilitas

- **Spend**: $\sum \text{Google Ads Cost (Micros / 1.000.000)}$
- **Revenue**: $\sum \text{Ad Exchange Revenue}$
- **Net Profit**: $\text{Revenue} - \text{Spend}$
- **ROI / ROAS**: $\left( \frac{\text{Revenue}}{\text{Spend}} \right) \times 100\%$
- **Profit Margin**: $\left( \frac{\text{Net Profit}}{\text{Revenue}} \right) \times 100\%$
