import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.gam import gam_service

def main():
    print("==========================================================================")
    print("🔍 DIAGNOSTIK STREAM LIVE DATA GAM API (DUAL QUERY PASS 1 & PASS 2)")
    print("==========================================================================\n")

    end_date = date.today()
    start_date = end_date - timedelta(days=7)

    try:
        data = gam_service._fetch_live_gam_data(start_date, end_date)
        print(f"📊 Total Baris Data GAM Ditarik: {len(data)}\n")
        
        if not data:
            print("⚠️ Data kosong dari GAM API (atau akun GAM tidak mengembalikan baris).")
            return

        print(f"{'DATE':<10} | {'DOMAIN':<18} | {'AD UNIT':<20} | {'AD REQS':<10} | {'MATCHED':<10} | {'MATCH RATE':<10}")
        print("-" * 82)

        for row in data[:20]:
            r_date = str(row.get("date"))
            dom = str(row.get("domain"))[:18]
            unit = str(row.get("ad_unit"))[:20]
            reqs = row.get("ad_requests", 0)
            matched = row.get("matched_requests", 0)
            mr = row.get("match_rate", 0.0)

            print(f"{r_date:<10} | {dom:<18} | {unit:<20} | {reqs:<10,} | {matched:<10,} | {mr:>8.2f}%")

        print("==========================================================================\n")
    except Exception as e:
        print(f"❌ Error saat menarik data GAM API: {e}")

if __name__ == "__main__":
    main()
