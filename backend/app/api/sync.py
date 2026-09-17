from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import Optional

from app.database import get_db
from app.schemas import SyncResponse
from app.models import User
from app.services.auth import get_current_user
from app.services.sync import sync_service, _sync_lock

router = APIRouter(prefix="/api/sync", tags=["Sync"])

@router.post("/trigger", response_model=SyncResponse)
def trigger_sync(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = date.today()
    if not start_date:
        d_start = today - timedelta(days=6)  # Default last 7 days sync for fast response
    else:
        d_start = datetime.strptime(start_date, "%Y-%m-%d").date()

    if not end_date:
        d_end = today
    else:
        d_end = datetime.strptime(end_date, "%Y-%m-%d").date()

    try:
        result = sync_service.sync_range(db, d_start, d_end)
        return SyncResponse(**result)
    except Exception as e:
        return SyncResponse(
            status="error",
            message=f"Gagal menyinkronkan data API: {str(e)}",
            records_synced=0,
            sync_date_start=d_start.strftime("%Y-%m-%d"),
            sync_date_end=d_end.strftime("%Y-%m-%d"),
            is_mock_data=False
        )

import os
import sys
import threading
import subprocess
import logging

logger = logging.getLogger(__name__)

def try_auto_git_pull_and_deploy():
    try:
        # Attempt auto-pull from GitHub on the server
        res = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True, timeout=15)
        logger.info(f"Auto git pull output: {res.stdout}")
        
        # Copy compiled frontend assets to HestiaCP public_html directory if present
        public_html = "/home/mbummm/web/admin.mbelik.com/public_html"
        if os.path.exists(public_html):
            if os.path.exists("frontend/dist"):
                subprocess.run(f"cp -r frontend/dist/* '{public_html}/'", shell=True, timeout=10)
            elif os.path.exists("dist"):
                subprocess.run(f"cp -r dist/* '{public_html}/'", shell=True, timeout=10)
            logger.info("Synced frontend assets to public_html")

        # If code was updated, restart the python process via systemd auto-restart
        if res.stdout and ("Updating " in res.stdout or "files changed" in res.stdout or "Fast-forward" in res.stdout):
            logger.info("New commits pulled on server. Triggering service auto-reload...")
            def _restart():
                import time
                time.sleep(1)
                os._exit(0)  # systemd with Restart=always will instantly revive the service with new code
            threading.Thread(target=_restart, daemon=True).start()
    except Exception as e:
        logger.warning(f"Auto git pull notice: {e}")

@router.get("/auto-deploy")
@router.post("/auto-deploy")
def public_auto_deploy():
    try_auto_git_pull_and_deploy()
    return {"status": "success", "message": "VPS auto git pull and deployment executed successfully!"}

@router.post("/restart-backend")
def restart_backend_service(current_user: User = Depends(get_current_user)):
    try_auto_git_pull_and_deploy()
    def _restart():
        import time
        time.sleep(0.5)
        os._exit(0)
    threading.Thread(target=_restart, daemon=True).start()
    return {"status": "success", "message": "Backend service deploying latest updates and restarting..."}

@router.post("/clear-cache", response_model=SyncResponse)
def clear_cache_and_resync(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = date.today()
    d_start_7d = today - timedelta(days=6)
    d_start_30d = today - timedelta(days=30)
    
    from app.models import DailyProfitSummary, GoogleAdsMetric, GAMMetric, GAMCountryMetric
    
    with _sync_lock:
        try:
            logger.info("Clearing analytics data cache tables...")
            db.query(DailyProfitSummary).delete(synchronize_session=False)
            db.query(GoogleAdsMetric).delete(synchronize_session=False)
            db.query(GAMMetric).delete(synchronize_session=False)
            db.query(GAMCountryMetric).delete(synchronize_session=False)
            db.commit()
            
            logger.info(f"Synchronously re-syncing live data from {d_start_7d} to {today}...")
            res = sync_service.sync_range(db, d_start_7d, today)
            records_count = res.get("records_synced", 0) if isinstance(res, dict) else 0
            
            # Background sync for older 30-day historical range
            def _bg_historical_sync():
                from app.database import SessionLocal
                bg_db = SessionLocal()
                try:
                    sync_service.sync_range(bg_db, d_start_30d, d_start_7d - timedelta(days=1))
                except Exception as e:
                    logger.warning(f"Background 30d sync notice: {e}")
                finally:
                    bg_db.close()
            threading.Thread(target=_bg_historical_sync, daemon=True).start()
            
            return SyncResponse(
                status="success",
                message=f"Cache berhasil dihapus! {records_count} data 7 hari terakhir telah selesai disinkron ulang dari GAM & Google Ads.",
                records_synced=records_count,
                sync_date_start=d_start_7d.strftime("%Y-%m-%d"),
                sync_date_end=today.strftime("%Y-%m-%d"),
                is_mock_data=False
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Error clearing cache and re-syncing: {e}")
            return SyncResponse(
                status="error",
                message=f"Gagal menghapus cache & re-sync: {str(e)}",
                records_synced=0,
                sync_date_start=d_start_7d.strftime("%Y-%m-%d"),
                sync_date_end=today.strftime("%Y-%m-%d"),
                is_mock_data=False
            )
