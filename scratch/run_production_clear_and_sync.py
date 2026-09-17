import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import SessionLocal, engine
from app.models import DailyProfitSummary, GoogleAdsMetric, GAMMetric, GAMCountryMetric
from app.services.sync import sync_service

today = date.today()
d_start = today - timedelta(days=7)

print(f"=== CLEAR CACHE AND RE-SYNC ({d_start} to {today}) ===")

db = SessionLocal()
try:
    print("1. Clearing stale cache tables...")
    db.query(DailyProfitSummary).delete(synchronize_session=False)
    db.query(GoogleAdsMetric).delete(synchronize_session=False)
    db.query(GAMMetric).delete(synchronize_session=False)
    db.query(GAMCountryMetric).delete(synchronize_session=False)
    db.commit()
    print("✓ Cache tables cleared successfully.")

    print(f"\n2. Re-syncing live data from GAM & Google Ads for {d_start} to {today}...")
    res = sync_service.sync_range(db, d_start, today)
    print(f"✓ Sync complete: {res}")

    # Inspect device categories in GAMMetric DB
    gam_rows = db.query(GAMMetric).all()
    devices = set(r.device_category for r in gam_rows)
    print(f"\n📊 Device categories found in GAMMetric DB: {devices}")
    for dev in devices:
        cnt = sum(1 for r in gam_rows if r.device_category == dev)
        rev = sum(r.revenue for r in gam_rows if r.device_category == dev)
        print(f"   - {dev.upper()}: {cnt} rows | Total Revenue: Rp {rev:,.2f}")

    # Inspect device categories in GAMCountryMetric DB
    c_rows = db.query(GAMCountryMetric).all()
    c_devices = set(r.device_category for r in c_rows)
    print(f"\n🌍 Device categories found in GAMCountryMetric DB: {c_devices}")
    for dev in c_devices:
        cnt = sum(1 for r in c_rows if r.device_category == dev)
        rev = sum(r.revenue for r in c_rows if r.device_category == dev)
        print(f"   - {dev.upper()}: {cnt} rows | Total Revenue: Rp {rev:,.2f}")

except Exception as e:
    print(f"❌ Error during clear and sync: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
