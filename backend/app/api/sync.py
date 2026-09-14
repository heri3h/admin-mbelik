from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import Optional

from app.database import get_db
from app.schemas import SyncResponse
from app.models import User
from app.services.auth import get_current_user
from app.services.sync import sync_service

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

@router.post("/clear-cache", response_model=SyncResponse)
def clear_cache_and_resync(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = date.today()
    d_start_7d = today - timedelta(days=6)
    d_start_30d = today - timedelta(days=30)
    try:
        from app.models import DailyProfitSummary, GoogleAdsMetric, GAMMetric, GAMCountryMetric
        db.query(DailyProfitSummary).delete()
        db.query(GoogleAdsMetric).delete()
        db.query(GAMMetric).delete()
        db.query(GAMCountryMetric).delete()
        db.commit()

        # Fast 7-day sync for instant response (< 2s)
        result = sync_service.sync_range(db, d_start_7d, today)

        # Background thread for 30-day sync so UI returns instantly
        import threading
        def _run_bg_30d():
            from app.database import SessionLocal
            bg_db = SessionLocal()
            try:
                sync_service.sync_range(bg_db, d_start_30d, today)
            except Exception:
                bg_db.rollback()
            finally:
                bg_db.close()

        threading.Thread(target=_run_bg_30d, daemon=True).start()
        return SyncResponse(**result)
    except Exception as e:
        db.rollback()
        return SyncResponse(
            status="error",
            message=f"Gagal reset cache: {str(e)}",
            records_synced=0,
            sync_date_start=d_start_7d.strftime("%Y-%m-%d"),
            sync_date_end=today.strftime("%Y-%m-%d"),
            is_mock_data=False
        )
