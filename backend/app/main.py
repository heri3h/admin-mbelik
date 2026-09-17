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
        count = db.query(JSONExportTarget).count()
        if count == 0:
            default_target = JSONExportTarget(
                domain="spotgames.top",
                target_filepath="/home/mbummm/web/spotgames.top/public_html/current_pricing.json",
                start_hour=10,
                end_hour=23,
                is_active=True
            )
            db.add(default_target)
            db.commit()
    except Exception as e:
        db.rollback()
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
    Background worker that runs every 20 minutes in a separate thread (asyncio.to_thread)
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

        # Repeat every 20 minutes (1200 seconds)
        await asyncio.sleep(1200)

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
