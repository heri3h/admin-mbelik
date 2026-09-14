#!/usr/bin/env bash
# Script otomatis Git Add, Commit & Push ke GitHub

# Set pesan commit (menggunakan argumen pertama atau timestamp jika kosong)
MSG="${1:-Update project: $(date '+%Y-%m-%d %H:%M:%S')}"

echo "---------------------------------------"
echo "🚀 1. Menambahkan berkas terbaru (git add)..."
git add .

echo "📦 2. Membuat commit: '$MSG'..."
git commit -m "$MSG"

echo "⬆️ 3. Mengunggah perubahan ke GitHub (origin/main)..."
git push origin main

echo "---------------------------------------"
echo "✅ Push Berhasil Selesai!"
