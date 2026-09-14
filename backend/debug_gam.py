import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.gam import gam_service

def main():
    print("==========================================================================")
    print("🔍 DEBUGGING METODE PRODUKSI UTAMA: gam_service._fetch_live_gam_data")
    print("==========================================================================\n")

    yesterday = date.today() - timedelta(days=1)
    print(f"📅 Tanggal Uji Produksi (Yesterday): {yesterday}\n")

    try:
        # 1. Metodologi Produksi Utama: Domain / Site Level GAM Data
        print("--- 1. MENJALANKAN gam_service._fetch_live_gam_data ---")
        site_data = gam_service._fetch_live_gam_data(yesterday, yesterday)
        print(f"✅ Total {len(site_data)} baris ditarik dari _fetch_live_gam_data.\n")

        print(f"{'DATE':<10} | {'DOMAIN':<20} | {'AD UNIT':<20} | {'AD REQS':<10} | {'MATCHED':<10} | {'MATCH RATE':<10} | {'REVENUE ($)':<12}")
        print("-" * 100)

        for r in site_data[:15]:
            r_date = str(r.get("date"))
            dom = str(r.get("domain"))[:20]
            unit = str(r.get("ad_unit"))[:20]
            reqs = r.get("ad_requests", 0)
            matched = r.get("matched_requests", 0)
            mr = r.get("match_rate", 0.0)
            rev = round(r.get("revenue", 0.0) * 0.92, 2)  # Net revenue -8% fee
            print(f"{r_date:<10} | {dom:<20} | {unit:<20} | {reqs:<10,} | {matched:<10,} | {mr:>8.2f}% | ${rev:<11.2f}")

        print("=" * 100 + "\n")

        # 2. Metodologi Produksi Utama: Country / AdUnit Level GAM Data
        print("--- 2. MENJALANKAN gam_service._fetch_live_gam_country_data ---")
        country_data = gam_service._fetch_live_gam_country_data(yesterday, yesterday)
        print(f"✅ Total {len(country_data)} baris ditarik dari _fetch_live_gam_country_data.\n")

        print(f"{'DATE':<10} | {'COUNTRY':<15} | {'DOMAIN':<18} | {'AD UNIT':<18} | {'AD REQS':<10} | {'MATCHED':<10} | {'MATCH RATE':<10}")
        print("-" * 100)

        # Filter Kazakhstan or target domains if available
        kz_rows = [r for r in country_data if "kazakhstan" in r.get("country", "").lower() or "kz" in r.get("country_code", "").lower()]
        display_rows = kz_rows if kz_rows else country_data

        for r in display_rows[:15]:
            r_date = str(r.get("date"))
            c_name = str(r.get("country"))[:15]
            dom = str(r.get("domain"))[:18]
            unit = str(r.get("ad_unit"))[:18]
            reqs = r.get("ad_requests", 0)
            matched = r.get("matched_requests", 0)
            mr = r.get("match_rate", 0.0)
            print(f"{r_date:<10} | {c_name:<15} | {dom:<18} | {unit:<18} | {reqs:<10,} | {matched:<10,} | {mr:>8.2f}%")

        print("=" * 100 + "\n")

    except Exception as e:
        print(f"❌ Error saat menarik data GAM API: {e}")

if __name__ == "__main__":
    main()
