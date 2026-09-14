import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from app.models import GoogleAdsMetric, GAMMetric, DailyProfitSummary, GoogleAdsAccount
from sqlalchemy import func

Base.metadata.create_all(bind=engine)
db = SessionLocal()

today = date.today()
yesterday = today - timedelta(days=1)

print("=" * 70)
print(f"=== VPS DATABASE INSPECTION REPORT (WIB Date: {today}) ===")
print("=" * 70)

for d in [yesterday, today]:
    lbl = "YESTERDAY" if d == yesterday else "TODAY"
    print(f"\n--- [{lbl} : {d}] ---")
    
    # 1. Spends in GoogleAdsMetric
    gads_rows = db.query(GoogleAdsMetric.customer_id, func.sum(GoogleAdsMetric.spend)).filter(GoogleAdsMetric.date == d).group_by(GoogleAdsMetric.customer_id).all()
    tot_spend = sum(r[1] for r in gads_rows) if gads_rows else 0.0
    print(f"  > Total Spend (+11% PPN) : Rp {tot_spend:,.2f}")
    for cid, sp in gads_rows:
        print(f"     - Account [{cid}]: Rp {sp:,.2f}")
    if not gads_rows:
        print("     - (Belum ada data Google Ads di DB untuk tanggal ini)")

    # 2. Revenue in GAMMetric
    gam_rows = db.query(GAMMetric.domain, func.sum(GAMMetric.revenue)).filter(GAMMetric.date == d).group_by(GAMMetric.domain).all()
    tot_rev = sum(r[1] for r in gam_rows) if gam_rows else 0.0
    print(f"  > Total Revenue (-8% Fee): Rp {tot_rev:,.2f}")
    for dom, rev in gam_rows:
        print(f"     - Site [{dom}]: Rp {rev:,.2f}")
    if not gam_rows:
        print("     - (Belum ada data GAM di DB untuk tanggal ini)")

    print(f"  > NET PROFIT DASHBOARD  : Rp {tot_rev - tot_spend:,.2f}")

print("\n" + "=" * 70)
db.close()
