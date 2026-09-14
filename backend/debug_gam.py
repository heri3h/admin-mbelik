import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.services.gam import gam_service
from app.services.sync import sync_service
from app.api.dashboard import get_site_country_placements_breakdown

def main():
    print("==========================================================================")
    print("🎯 DEBUG FOKUS PRODUKSI: 1 SITUS (play.gemol.me) & 1 NEGARA (Kazakhstan)")
    print("==========================================================================\n")

    yesterday = date.today() - timedelta(days=1)
    target_domain = "play.gemol.me"
    target_country = "Kazakhstan"
    print(f"📅 Tanggal Uji : {yesterday}")
    print(f"🌐 Target Situs: {target_domain}")
    print(f"🌍 Target Negara: {target_country}\n")

    # Step 1: Run Live GAM Country Data Pull
    print("--- 1. TARIK DATA LIVE GAM API (PRODUKSI) ---")
    try:
        live_country_data = gam_service._fetch_live_gam_country_data(yesterday, yesterday)
        print(f"📊 Total baris ditarik dari GAM API: {len(live_country_data)}")

        # Filter strictly for play.gemol.me (or gemol) and Kazakhstan
        filtered = [
            r for r in live_country_data 
            if ("gemol" in r.get("domain", "").lower() or target_domain in r.get("domain", "").lower())
            and ("kazakhstan" in r.get("country", "").lower() or "kz" in r.get("country_code", "").lower())
        ]

        if not filtered:
            # Fallback if domain match is broad
            filtered = [
                r for r in live_country_data 
                if "kazakhstan" in r.get("country", "").lower()
            ]

        sorted_live = sorted(filtered, key=lambda x: str(x.get("ad_unit", "")).lower())

        print(f"\n📌 STREAM DATA MENTAH LIVE GAM API ({target_domain} - {target_country}):")
        print(f"{'AD UNIT':<25} | {'AD REQS':<12} | {'MATCHED':<12} | {'MATCH RATE':<10} | {'IMPRESSIONS':<12} | {'REVENUE ($)':<12}")
        print("-" * 95)

        for r in sorted_live:
            unit = str(r.get("ad_unit"))[:25]
            reqs = r.get("ad_requests", 0)
            matched = r.get("matched_requests", 0)
            mr = r.get("match_rate", 0.0)
            imps = r.get("impressions", 0)
            rev = round(r.get("revenue", 0.0) * 0.92, 2)  # Net Revenue -8% fee
            print(f"{unit:<25} | {reqs:<12,} | {matched:<12,} | {mr:>8.2f}% | {imps:<12,} | ${rev:<11.2f}")

        print("=" * 95 + "\n")

    except Exception as e:
        print(f"❌ Error saat menarik data GAM API: {e}\n")

    # Step 2: Test Database & Endpoint Response
    print("--- 2. UJI ENDPOINT ADUNIT DASHBOARD (/sites/play.gemol.me/countries/Kazakhstan/placements) ---")
    db = SessionLocal()
    try:
        # Perform sync for yesterday
        sync_service.sync_range(db, yesterday, yesterday)

        # Call exact API endpoint logic
        results = get_site_country_placements_breakdown(
            domain=target_domain,
            country=target_country,
            start_date=str(yesterday),
            end_date=str(yesterday),
            db=db,
            current_user=None
        )

        print(f"✅ Endpoint mengembalikan {len(results)} item unit iklan.\n")
        print(f"{'AD UNIT':<25} | {'AD REQS':<12} | {'MATCHED':<12} | {'MATCH RATE':<10} | {'IMPRESSIONS':<12} | {'REVENUE ($)':<12}")
        print("-" * 95)

        sorted_endpoint = sorted(results, key=lambda x: x.ad_unit.lower())
        for item in sorted_endpoint:
            unit = item.ad_unit[:25]
            reqs = item.ad_requests
            matched = item.matched_requests
            mr = item.match_rate
            imps = item.impressions
            rev = item.total_revenue
            print(f"{unit:<25} | {reqs:<12,} | {matched:<12,} | {mr:>8.2f}% | {imps:<12,} | ${rev:<11.2f}")

        print("=" * 95 + "\n")

    except Exception as e:
        print(f"❌ Error saat menguji endpoint dashboard: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
