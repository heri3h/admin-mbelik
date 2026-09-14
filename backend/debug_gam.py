import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.gam import gam_service

def main():
    print("==========================================================================")
    print("🔍 DIAGNOSTIK LIVE GAM API: DOMAIN AGGREGATION & MATCH RATE DEBUG")
    print("==========================================================================\n")

    end_date = date.today()
    start_date = end_date - timedelta(days=7)

    try:
        data = gam_service._fetch_live_gam_data(start_date, end_date)
        print(f"📊 Total Baris Data Mentah GAM Ditarik: {len(data)}\n")
        
        if not data:
            print("⚠️ Data kosong dari GAM API (atau akun GAM tidak mengembalikan baris).")
            return

        # Group data by (date, domain)
        domain_summary = {}
        for row in data:
            d_date = row.get("date")
            dom = row.get("domain", "").strip().lower()
            if not dom:
                continue
            key = (d_date, dom)
            if key not in domain_summary:
                domain_summary[key] = {
                    "date": d_date,
                    "domain": dom,
                    "revenue": 0.0,
                    "impressions": 0,
                    "clicks": 0,
                    "ad_requests": 0,
                    "matched_requests": 0
                }
            s = domain_summary[key]
            s["revenue"] += row.get("revenue", 0.0)
            s["impressions"] += row.get("impressions", 0)
            s["clicks"] += row.get("clicks", 0)
            s["ad_requests"] += row.get("ad_requests", 0)
            s["matched_requests"] += row.get("matched_requests", 0)

        print("==========================================================================")
        print("📌 RINGKASAN DATA PER DOMAIN (AKUMULASI HARIAN)")
        print("==========================================================================")
        print(f"{'DATE':<10} | {'DOMAIN':<22} | {'AD REQS':<12} | {'MATCHED':<12} | {'MATCH RATE':<10} | {'REVENUE ($)':<12}")
        print("-" * 88)

        sorted_summary = sorted(domain_summary.values(), key=lambda x: (x['date'], x['domain']), reverse=True)
        for s in sorted_summary:
            r_date = str(s["date"])
            dom = s["domain"][:22]
            reqs = s["ad_requests"]
            matched = s["matched_requests"]
            mr = (matched / reqs * 100.0) if reqs > 0 else 0.0
            rev = round(s["revenue"] * 0.92, 2)  # Net Revenue -8% fee

            # Highlight target domain
            flag = " 🎯" if "gemol" in dom or "mbelik" in dom else ""
            print(f"{r_date:<10} | {dom:<22} | {reqs:<12,} | {matched:<12,} | {mr:>8.2f}% | ${rev:<11.2f}{flag}")

        print("==========================================================================\n")
        
        # Detail view for gemol or target domains
        gemol_rows = [r for r in data if "gemol" in r.get("domain", "").lower()]
        if gemol_rows:
            print("==========================================================================")
            print("🎯 DETAIL BREAKDOWN AD UNIT UNTUK DOMAIN: play.gemol.me / gemol")
            print("==========================================================================")
            print(f"{'DATE':<10} | {'AD UNIT':<25} | {'AD REQS':<12} | {'MATCHED':<12} | {'MATCH RATE':<10}")
            print("-" * 75)
            for r in gemol_rows:
                r_date = str(r.get("date"))
                unit = str(r.get("ad_unit"))[:25]
                reqs = r.get("ad_requests", 0)
                matched = r.get("matched_requests", 0)
                mr = r.get("match_rate", 0.0)
                print(f"{r_date:<10} | {unit:<25} | {reqs:<12,} | {matched:<12,} | {mr:>8.2f}%")
            print("==========================================================================\n")

    except Exception as e:
        print(f"❌ Error saat menarik data GAM API: {e}")

if __name__ == "__main__":
    main()
