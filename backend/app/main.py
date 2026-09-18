import os
import threading
import time
from datetime import date, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database import engine, Base, SessionLocal
import app.models
from app.models import User
from app.services.auth import get_password_hash
from app.api import auth, dashboard, sync, settings as settings_api

# Create database tables
Base.metadata.create_all(bind=engine)

from sqlalchemy import text

def auto_migrate_db():
    try:
        with engine.connect() as conn:
            if settings.DATABASE_URL.startswith("sqlite"):
                conn.execute(text("PRAGMA journal_mode=WAL;"))
                conn.execute(text("PRAGMA busy_timeout=30000;"))

                # Recreate gam_metrics if it still has old unique constraint
                res_m = conn.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='gam_metrics';")).fetchone()
                if res_m and res_m[0] and "_date_domain_adunit_uc" in res_m[0]:
                    print("Migrating gam_metrics table schema...")
                    conn.execute(text("DROP TABLE IF EXISTS gam_metrics;"))
                    conn.commit()

                # Recreate gam_country_metrics if it still has old unique constraint
                res_c = conn.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='gam_country_metrics';")).fetchone()
                if res_c and res_c[0] and "_date_domain_country_adunit_uc" in res_c[0]:
                    print("Migrating gam_country_metrics table schema...")
                    conn.execute(text("DROP TABLE IF EXISTS gam_country_metrics;"))
                    conn.commit()

        # Re-create tables with new schema metadata
        Base.metadata.create_all(bind=engine)

        with engine.connect() as conn:
            if settings.DATABASE_URL.startswith("sqlite"):
                res = conn.execute(text("PRAGMA table_info(gam_metrics);"))
                columns = [row[1] for row in res.fetchall()]
                if "match_rate" not in columns:
                    conn.execute(text("ALTER TABLE gam_metrics ADD COLUMN match_rate FLOAT DEFAULT 0.0;"))
                if "ad_requests" not in columns:
                    conn.execute(text("ALTER TABLE gam_metrics ADD COLUMN ad_requests INTEGER DEFAULT 0;"))
                if "matched_requests" not in columns:
                    conn.execute(text("ALTER TABLE gam_metrics ADD COLUMN matched_requests INTEGER DEFAULT 0;"))
                if "device_category" not in columns:
                    conn.execute(text("ALTER TABLE gam_metrics ADD COLUMN device_category VARCHAR(20) DEFAULT 'all';"))

                res_c = conn.execute(text("PRAGMA table_info(gam_country_metrics);"))
                c_columns = [row[1] for row in res_c.fetchall()]
                if "pricing_rule_name" not in c_columns:
                    conn.execute(text("ALTER TABLE gam_country_metrics ADD COLUMN pricing_rule_name VARCHAR(150) DEFAULT 'All Rules';"))
                if "device_category" not in c_columns:
                    conn.execute(text("ALTER TABLE gam_country_metrics ADD COLUMN device_category VARCHAR(20) DEFAULT 'all';"))

                conn.commit()
            else:
                conn.execute(text("ALTER TABLE gam_metrics ADD COLUMN IF NOT EXISTS match_rate FLOAT DEFAULT 0.0;"))
                conn.execute(text("ALTER TABLE gam_metrics ADD COLUMN IF NOT EXISTS ad_requests INTEGER DEFAULT 0;"))
                conn.execute(text("ALTER TABLE gam_metrics ADD COLUMN IF NOT EXISTS matched_requests INTEGER DEFAULT 0;"))
                conn.execute(text("ALTER TABLE gam_metrics ADD COLUMN IF NOT EXISTS pricing_rule_name VARCHAR(150) DEFAULT 'All Rules';"))
                conn.execute(text("ALTER TABLE gam_metrics ADD COLUMN IF NOT EXISTS device_category VARCHAR(20) DEFAULT 'all';"))
                conn.execute(text("ALTER TABLE gam_country_metrics ADD COLUMN IF NOT EXISTS pricing_rule_name VARCHAR(150) DEFAULT 'All Rules';"))
                conn.execute(text("ALTER TABLE gam_country_metrics ADD COLUMN IF NOT EXISTS device_category VARCHAR(20) DEFAULT 'all';"))
                conn.commit()
    except Exception as e:
        print(f"Auto DB migration notice: {e}")

auto_migrate_db()

import asyncio
import logging
from datetime import date
from app.services.sync import sync_service

logger = logging.getLogger(__name__)

# Auto-seed default admin user if database was recreated
def auto_seed_admin():
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        if not admin_user:
            hashed_pwd = get_password_hash(settings.ADMIN_PASSWORD)
            admin = User(username=settings.ADMIN_USERNAME, hashed_password=hashed_pwd)
            db.add(admin)
            db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()

auto_seed_admin()

def auto_seed_export_targets():
    from app.models import JSONExportTarget
    db = SessionLocal()
    try:
        # Schema migration check for SQLite
        try:
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE json_export_targets ADD COLUMN conversion_enabled BOOLEAN DEFAULT 1;"))
                conn.execute(text("ALTER TABLE json_export_targets ADD COLUMN conversion_send_to VARCHAR(255);"))
                conn.execute(text("ALTER TABLE json_export_targets ADD COLUMN conversion_currency VARCHAR(10) DEFAULT 'IDR';"))
                conn.execute(text("ALTER TABLE json_export_targets ADD COLUMN pv1_value FLOAT DEFAULT 0.0;"))
                conn.execute(text("ALTER TABLE json_export_targets ADD COLUMN pv2_value FLOAT DEFAULT 1000.0;"))
                conn.execute(text("ALTER TABLE json_export_targets ADD COLUMN pv3_value FLOAT DEFAULT 3000.0;"))
                conn.execute(text("ALTER TABLE json_export_targets ADD COLUMN pv4_value FLOAT DEFAULT 6000.0;"))
                conn.execute(text("ALTER TABLE json_export_targets ADD COLUMN slot_header VARCHAR(255);"))
                conn.execute(text("ALTER TABLE json_export_targets ADD COLUMN slot_feed VARCHAR(255);"))
                conn.execute(text("ALTER TABLE json_export_targets ADD COLUMN slot_side1 VARCHAR(255);"))
                conn.execute(text("ALTER TABLE json_export_targets ADD COLUMN slot_side2 VARCHAR(255);"))
                conn.execute(text("ALTER TABLE json_export_targets ADD COLUMN slot_interstitial VARCHAR(255);"))
                conn.execute(text("ALTER TABLE json_export_targets ADD COLUMN slot_anchor VARCHAR(255);"))
                conn.commit()
        except Exception:
            pass

        domain_meta = {
            "play.gemol.me": {
                "send_to": "AW-16785269892/nNVJCMe5mowaEITJ68M-",
                "header": "/22806125615/play-1",
                "feed": "/22806125615/play-2",
                "side1": "/22806125615/play-3",
                "side2": "/22806125615/play-4"
            },
            "skuy.me/pastime": {
                "send_to": "AW-11112849736/1g6LCPDi2JUYEMjCgrMp",
                "header": "/22806125615/skuy-header",
                "feed": "/22806125615/skuy-feed",
                "side1": "/22806125615/skuy-side",
                "side2": "/22806125615/skuy-side-2",
                "interstitial": "/22806125615/skuy-int",
                "anchor": "/22806125615/skuy-sticky"
            },
            "hits.spotgames.top": {
                "send_to": "AW-16530351013/g5yyCJiOzqgcEKXHpMo9"
            },
            "hot.mbelik.com": {
                "send_to": "AW-16478951650/2v_RCLr_p5sZEOKx47E9"
            },
            "kedung.net": {
                "send_to": "AW-16528567544/xUeRCOXd8aUZEPjZt8k9"
            },
            "sleepwell.henden.top": {
                "send_to": "AW-17820503102/ckbfCJ3089QbEL6YvbFC"
            }
        }

        default_targets = [
            ("spotgames.top", "/home/mbummm/web/spotgames.top/public_html/current_pricing.json"),
            ("mbelik.com", "/home/mbummm/web/mbelik.com/public_html/current_pricing.json"),
            ("baleq.me", "/home/mbummm/web/baleq.me/public_html/current_pricing.json"),
            ("nub.skuy.me", "/home/mbummm/web/nub.skuy.me/public_html/current_pricing.json"),
            ("xdr.nubmaster.com", "/home/mbummm/web/xdr.nubmaster.com/public_html/current_pricing.json"),
            ("alt.polpasulsa.com", "/home/mbummm/web/alt.polpasulsa.com/public_html/current_pricing.json"),
            ("enew.spotgames.top", "/home/mbummm/web/enew.spotgames.top/public_html/current_pricing.json"),
            ("henden.top", "/home/mbummm/web/henden.top/public_html/current_pricing.json"),
            ("play.gemol.me", "/home/mbummm/web/play.gemol.me/public_html/current_pricing.json"),
            ("skuy.me", "/home/mbummm/web/skuy.me/public_html/current_pricing.json"),
            ("skuy.me/pastime", "/home/mbummm/web/skuy.me/public_html/pastime/current_pricing.json"),
            ("vinn.henden.top", "/home/mbummm/web/vinn.henden.top/public_html/current_pricing.json")
        ]
        for dom, path in default_targets:
            meta = domain_meta.get(dom, {})
            existing = db.query(JSONExportTarget).filter(JSONExportTarget.domain == dom).first()
            if not existing:
                t = JSONExportTarget(
                    domain=dom,
                    target_filepath=path,
                    start_hour=10,
                    end_hour=23,
                    is_active=True,
                    conversion_enabled=True,
                    conversion_send_to=meta.get("send_to"),
                    conversion_currency="IDR",
                    pv1_value=0.0,
                    pv2_value=1000.0,
                    pv3_value=3000.0,
                    pv4_value=6000.0,
                    slot_header=meta.get("header"),
                    slot_feed=meta.get("feed"),
                    slot_side1=meta.get("side1"),
                    slot_side2=meta.get("side2"),
                    slot_interstitial=meta.get("interstitial"),
                    slot_anchor=meta.get("anchor")
                )
                db.add(t)
            else:
                if meta.get("send_to") and not existing.conversion_send_to:
                    existing.conversion_send_to = meta.get("send_to")
                if meta.get("header") and not existing.slot_header:
                    existing.slot_header = meta.get("header")
                if meta.get("feed") and not existing.slot_feed:
                    existing.slot_feed = meta.get("feed")
                if meta.get("side1") and not existing.slot_side1:
                    existing.slot_side1 = meta.get("side1")
                if meta.get("side2") and not existing.slot_side2:
                    existing.slot_side2 = meta.get("side2")
                if meta.get("interstitial") and not existing.slot_interstitial:
                    existing.slot_interstitial = meta.get("interstitial")
                if meta.get("anchor") and not existing.slot_anchor:
                    existing.slot_anchor = meta.get("anchor")
        db.commit()

        from app.services.sync import load_pricing_config, save_pricing_config_and_sync
        cfg = load_pricing_config()
        save_pricing_config_and_sync(cfg, db=db)
    except Exception as e:
        db.rollback()
        logger.warning(f"Error seeding export target meta: {e}")
    finally:
        db.close()

auto_seed_export_targets()

app = FastAPI(
    title="Ad Performance & Profitability Analytics API",
    description="Backend API for Google Ads & Google Ad Manager Profitability Dashboard",
    version="1.0.0"
)

async def auto_sync_background_task():
    """
    Background worker that runs every 30 minutes in a separate thread (asyncio.to_thread)
    to automatically sync Yesterday & Today's Google Ads & GAM metrics into SQLite DB without blocking the API server!
    """
    await asyncio.sleep(10)  # Wait 10 seconds after server startup
    while True:
        try:
            logger.info("Executing automatic background sync for Yesterday & Today in worker thread...")

            def run_sync():
                db = SessionLocal()
                try:
                    today = date.today()
                    yesterday = today - timedelta(days=1)
                    sync_service.sync_range(db, yesterday, today)
                finally:
                    db.close()

            await asyncio.to_thread(run_sync)
            logger.info("Automatic background sync finished successfully.")
        except Exception as e:
            logger.error(f"Error in automatic background sync task: {e}")

        # Repeat every 30 minutes (1800 seconds)
        await asyncio.sleep(1800)

_auto_sync_task = None

@app.on_event("startup")
def start_auto_sync_task():
    global _auto_sync_task
    _auto_sync_task = asyncio.create_task(auto_sync_background_task())

@app.on_event("shutdown")
def stop_auto_sync_task():
    global _auto_sync_task
    if _auto_sync_task:
        _auto_sync_task.cancel()


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(sync.router)
app.include_router(settings_api.router)

# Serve Frontend static files if dist folder exists
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api"):
            return None
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    @app.get("/")
    def read_root():
        return {
            "message": "Ad Analytics Dashboard API Server Running",
            "docs": "/docs",
            "mock_mode": settings.USE_MOCK_DATA
        }

# Periodic background thread: Low-frequency safety auto-pull check (every 5 minutes)
def _auto_pull_loop():
    time.sleep(30)
    while True:
        try:
            from app.api.sync import try_auto_git_pull_and_deploy
            try_auto_git_pull_and_deploy()
        except Exception as e:
            logger.warning(f"Auto pull loop notice: {e}")
        time.sleep(300)

threading.Thread(target=_auto_pull_loop, daemon=True).start()
