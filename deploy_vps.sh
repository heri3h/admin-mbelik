#!/usr/bin/env bash
# Script Deploy Otomatis untuk VPS (HestiaCP / CyberPanel / cPanel)
set -e

PUBLIC_HTML="/home/mbummm/web/admin.mbelik.com/public_html"

echo "---------------------------------------"
echo "🚀 1. Menarik update terbaru dari GitHub..."
git pull origin main

echo "📦 2. Memperbarui dependensi Backend..."
if [ -d "venv" ]; then
    venv/bin/pip install -r backend/requirements.txt
elif [ -d "backend/venv" ]; then
    backend/venv/bin/pip install -r backend/requirements.txt
fi

echo "🏗️ 3. Mengompilasi Frontend (npm run build)..."
cd frontend
npm install
npm run build
cd ..

echo "📂 4. Menyalin berkas frontend dist ke public_html..."
cp -r frontend/dist/* "$PUBLIC_HTML/"

echo "🔄 5. Merestart ad-analytics service..."
sudo systemctl restart ad-analytics.service

echo "---------------------------------------"
echo "✅ Deploy ke VPS Berhasil Selesai!"
