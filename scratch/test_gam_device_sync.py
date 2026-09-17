import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import SessionLocal
from app.services.gam import gam_service
from app.services.sync import sync_service
from app.models import GAMMetric, GAMCountryMetric

yesterday = date.today() - timedelta(days=1)
print(f"Testing GAM daily & country metrics for date: {yesterday}")

try:
    daily_data = gam_service.fetch_daily_metrics(yesterday, yesterday)
    print(f"Daily metrics fetched: {len(daily_data)} rows")
    devices_daily = set(r.get("device_category") for r in daily_data)
    print(f"Daily device categories found: {devices_daily}")

    country_data = gam_service.fetch_country_metrics(yesterday, yesterday)
    print(f"Country metrics fetched: {len(country_data)} rows")
    devices_country = set(r.get("device_category") for r in country_data)
    print(f"Country device categories found: {devices_country}")

except Exception as e:
    print(f"Error fetching from GAM: {e}")
    import traceback
    traceback.print_exc()

db = SessionLocal()
try:
    print("\nRunning sync_service.sync_range...")
    sync_service.sync_range(db, yesterday, yesterday)
    
    rows_gam = db.query(GAMMetric).filter(GAMMetric.date == yesterday).all()
    print(f"\nGAMMetric rows in DB for {yesterday}: {len(rows_gam)}")
    devices_in_db = set(r.device_category for r in rows_gam)
    print(f"Device categories in GAMMetric DB: {devices_in_db}")
    for dev in devices_in_db:
        cnt = sum(1 for r in rows_gam if r.device_category == dev)
        rev = sum(r.revenue for r in rows_gam if r.device_category == dev)
        print(f"  - {dev}: {cnt} rows, Revenue: Rp {rev:,.2f}")

    rows_country = db.query(GAMCountryMetric).filter(GAMCountryMetric.date == yesterday).all()
    print(f"\nGAMCountryMetric rows in DB for {yesterday}: {len(rows_country)}")
    c_devices_in_db = set(r.device_category for r in rows_country)
    print(f"Device categories in GAMCountryMetric DB: {c_devices_in_db}")
    for dev in c_devices_in_db:
        cnt = sum(1 for r in rows_country if r.device_category == dev)
        rev = sum(r.revenue for r in rows_country if r.device_category == dev)
        print(f"  - {dev}: {cnt} rows, Revenue: Rp {rev:,.2f}")

finally:
    db.close()
