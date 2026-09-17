import sys
import os
from sqlalchemy import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import engine, Base
import app.models

print("=== FIXING DATABASE SCHEMA MIGRATION ===")

with engine.connect() as conn:
    print("1. Checking table info for gam_metrics...")
    res = conn.execute(text("PRAGMA table_info(gam_metrics);")).fetchall()
    cols = [row[1] for row in res]
    print(f"   Existing gam_metrics columns: {cols}")

    if "device_category" not in cols:
        print("   Adding missing 'device_category' column to gam_metrics...")
        try:
            conn.execute(text("ALTER TABLE gam_metrics ADD COLUMN device_category VARCHAR(20) DEFAULT 'mobile';"))
            conn.commit()
            print("   ✓ Column 'device_category' added to gam_metrics!")
        except Exception as e:
            print(f"   Notice: {e}")

    if "match_rate" not in cols:
        try:
            conn.execute(text("ALTER TABLE gam_metrics ADD COLUMN match_rate FLOAT DEFAULT 0.0;"))
            conn.commit()
        except Exception:
            pass

    if "ad_requests" not in cols:
        try:
            conn.execute(text("ALTER TABLE gam_metrics ADD COLUMN ad_requests INTEGER DEFAULT 0;"))
            conn.commit()
        except Exception:
            pass

    if "matched_requests" not in cols:
        try:
            conn.execute(text("ALTER TABLE gam_metrics ADD COLUMN matched_requests INTEGER DEFAULT 0;"))
            conn.commit()
        except Exception:
            pass

    print("2. Checking table info for gam_country_metrics...")
    res_c = conn.execute(text("PRAGMA table_info(gam_country_metrics);")).fetchall()
    c_cols = [row[1] for row in res_c]
    print(f"   Existing gam_country_metrics columns: {c_cols}")

    if "device_category" not in c_cols:
        print("   Adding missing 'device_category' column to gam_country_metrics...")
        try:
            conn.execute(text("ALTER TABLE gam_country_metrics ADD COLUMN device_category VARCHAR(20) DEFAULT 'mobile';"))
            conn.commit()
            print("   ✓ Column 'device_category' added to gam_country_metrics!")
        except Exception as e:
            print(f"   Notice: {e}")

    if "pricing_rule_name" not in c_cols:
        try:
            conn.execute(text("ALTER TABLE gam_country_metrics ADD COLUMN pricing_rule_name VARCHAR(150) DEFAULT 'All Rules';"))
            conn.commit()
        except Exception:
            pass

Base.metadata.create_all(bind=engine)
print("=== SCHEMA MIGRATION COMPLETED SUCCESSFULLY ===")
