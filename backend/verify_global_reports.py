import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import User
from app.api.dashboard import (
    get_summary,
    get_daily_trend,
    get_accounts_breakdown,
    get_sites_breakdown,
    get_placements_breakdown,
    get_site_countries_breakdown
)

db = SessionLocal()
user = db.query(User).first()

today = date.today()
last7_start = (today - timedelta(days=6)).strftime("%Y-%m-%d")
last7_end = today.strftime("%Y-%m-%d")

print("=" * 70)
print(f"=== GLOBAL REPORT VERIFICATION TEST ({last7_start} to {last7_end}) ===")
print("=" * 70)

try:
    summary = get_summary(last7_start, last7_end, db, user)
    print("\n1. SUMMARY METRICS:")
    print(f"   - Spend         : Rp {summary.total_spend:,.2f}")
    print(f"   - Revenue       : Rp {summary.total_revenue:,.2f}")
    print(f"   - Net Profit    : Rp {summary.net_profit:,.2f}")
    print(f"   - ROI           : {summary.roi:.2f}%")
    print(f"   - Profit Margin : {summary.profit_margin:.2f}%")

    sites = get_sites_breakdown(last7_start, last7_end, db, user)
    tot_sites_spend = sum(s.total_spend for s in sites)
    tot_sites_rev = sum(s.total_revenue for s in sites)
    print("\n2. SITES BREAKDOWN:")
    print(f"   - Total Sites Count : {len(sites)}")
    print(f"   - Total Sites Spend : Rp {tot_sites_spend:,.2f}")
    print(f"   - Total Sites Rev   : Rp {tot_sites_rev:,.2f}")

    accounts = get_accounts_breakdown(last7_start, last7_end, db, user)
    tot_accounts_spend = sum(a.total_spend for a in accounts)
    print("\n3. ACCOUNTS BREAKDOWN:")
    print(f"   - Accounts Count     : {len(accounts)}")
    print(f"   - Total Accounts Sp  : Rp {tot_accounts_spend:,.2f}")

    trend = get_daily_trend(last7_start, last7_end, db, user)
    tot_trend_spend = sum(t.spend for t in trend)
    tot_trend_rev = sum(t.revenue for t in trend)
    print("\n4. DAILY TREND:")
    print(f"   - Days Count        : {len(trend)}")
    print(f"   - Total Trend Spend : Rp {tot_trend_spend:,.2f}")
    print(f"   - Total Trend Rev   : Rp {tot_trend_rev:,.2f}")

    print("\n" + "=" * 70)
    print("=== DATA CONSISTENCY CHECK ===")
    print(f"   - Spend Match (Summary vs Sites)   : {'YES' if abs(summary.total_spend - tot_sites_spend) < 1.0 else 'NO'}")
    print(f"   - Spend Match (Summary vs Accounts): {'YES' if abs(summary.total_spend - tot_accounts_spend) < 1.0 else 'NO'}")
    print(f"   - Rev Match   (Summary vs Sites)   : {'YES' if abs(summary.total_revenue - tot_sites_rev) < 1.0 else 'NO'}")
    print(f"   - Rev Match   (Summary vs Trend)   : {'YES' if abs(summary.total_revenue - tot_trend_rev) < 1.0 else 'NO'}")
    print("=" * 70)

except Exception as e:
    print(f"Error during report verification: {e}")
    import traceback
    traceback.print_exc()

finally:
    db.close()
