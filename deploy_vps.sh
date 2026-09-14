#!/usr/bin/env bash
# Script Deploy Otomatis untuk VPS (HestiaCP / CyberPanel / cPanel)
set -e

PUBLIC_HTML="/home/mbummm/web/admin.mbelik.com/public_html"

echo "---------------------------------------"
echo "🚀 1. Menarik update terbaru dari GitHub..."
git pull origin main

echo "📦 2. Memperbarui dependensi Backend..."
if [ -d "venv" ]; then
    chmod -R +x venv/bin/ 2>/dev/null || true
    venv/bin/python -m pip install -r backend/requirements.txt || pip install -r backend/requirements.txt
elif [ -d "backend/venv" ]; then
    chmod -R +x backend/venv/bin/ 2>/dev/null || true
    backend/venv/bin/python -m pip install -r backend/requirements.txt || pip install -r backend/requirements.txt
fi

echo "🏗️ 3. Mengompilasi Frontend (npm run build)..."
cd frontend
npm install
npm run build
cd ..

echo "📂 4. Menyalin berkas frontend dist ke public_html..."
cp -r frontend/dist/* "$PUBLIC_HTML/"

echo "🔑 4.5. Memperbarui hak akses file database SQLite (ad_analytics.db)..."
sudo chmod 777 . backend 2>/dev/null || true
sudo chmod 777 ad_analytics.db* backend/ad_analytics.db* 2>/dev/null || true
sudo chown -R mbummm:mbummm . backend 2>/dev/null || true

echo "🔄 5. Merestart ad-analytics service..."
sudo systemctl restart ad-analytics.service

echo "---------------------------------------"
echo "✅ Deploy ke VPS Berhasil Selesai!"
