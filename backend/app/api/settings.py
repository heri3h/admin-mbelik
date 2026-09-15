from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.config import settings, BASE_DIR
from app.database import get_db
from app.schemas import (
    SettingsStatusResponse, GoogleAdsAccountCreate, GoogleAdsAccountUpdate, GoogleAdsAccountResponse,
    JSONExportTargetCreate, JSONExportTargetUpdate, JSONExportTargetResponse, PricingConfigSchema
)

from app.models import User, GoogleAdsAccount, JSONExportTarget
from app.services.auth import get_current_user
from app.services.google_ads import google_ads_service
from app.services.gam import gam_service
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["Settings"])

@router.get("/status", response_model=SettingsStatusResponse)
def get_settings_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    missing = []

    if settings.USE_MOCK_DATA:
        missing.append("USE_MOCK_DATA di .env masih diset ke 'true'")

    # Google Ads checks
    if settings.is_placeholder(settings.GOOGLE_ADS_DEVELOPER_TOKEN):
        missing.append("GOOGLE_ADS_DEVELOPER_TOKEN belum diisi / masih placeholder")
    if settings.is_placeholder(settings.GOOGLE_ADS_CLIENT_ID):
        missing.append("GOOGLE_ADS_CLIENT_ID belum diisi / masih placeholder")
    if settings.is_placeholder(settings.GOOGLE_ADS_CLIENT_SECRET):
        missing.append("GOOGLE_ADS_CLIENT_SECRET belum diisi / masih placeholder")
    if settings.is_placeholder(settings.GOOGLE_ADS_REFRESH_TOKEN):
        missing.append("GOOGLE_ADS_REFRESH_TOKEN belum diisi / masih placeholder")
    if settings.is_placeholder(settings.GOOGLE_ADS_CUSTOMER_IDS):
        missing.append("GOOGLE_ADS_CUSTOMER_IDS belum diisi / masih placeholder")

    # GAM checks
    if settings.is_placeholder(settings.GAM_NETWORK_CODE):
        missing.append("GAM_NETWORK_CODE belum diisi / masih placeholder")
    
    json_path = settings.GAM_JSON_KEY_FILE_PATH
    if json_path and not os.path.isabs(json_path):
        json_path = os.path.join(BASE_DIR, json_path)
    
    has_json = bool(json_path and os.path.exists(json_path))
    has_oauth = bool(
        not settings.is_placeholder(settings.GAM_CLIENT_ID)
        and not settings.is_placeholder(settings.GAM_CLIENT_SECRET)
        and not settings.is_placeholder(settings.GAM_REFRESH_TOKEN)
    )
    if not (has_json or has_oauth):
        missing.append("GAM Service Account JSON file (gam_service_account.json) tidak ditemukan & OAuth GAM belum lengkap")

    # Combine Customer IDs from DB and .env
    db_accounts = db.query(GoogleAdsAccount).all()
    cids_set = set(settings.customer_ids_list)
    for acc in db_accounts:
        cids_set.add(acc.customer_id)

    return SettingsStatusResponse(
        use_mock_data=google_ads_service.use_mock or gam_service.use_mock,
        google_ads_configured=settings.is_google_ads_configured or len(db_accounts) > 0,
        gam_configured=settings.is_gam_configured,
        configured_customer_ids=sorted(list(cids_set)),
        gam_network_code=settings.GAM_NETWORK_CODE,
        missing_fields=missing,
        currency=settings.CURRENCY
    )

# Google Ads Accounts & Domain Mapping CRUD
@router.get("/google-ads-accounts", response_model=List[GoogleAdsAccountResponse])
def get_google_ads_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    accounts = db.query(GoogleAdsAccount).all()
    # Auto-populate from .env if table is empty but .env has customer IDs
    if not accounts and settings.customer_ids_list:
        for cid in settings.customer_ids_list:
            acc = GoogleAdsAccount(
                customer_id=cid,
                account_name=f"Google Ads ({cid})",
                assigned_domain="All / Unassigned"
            )
            db.add(acc)
        db.commit()
        accounts = db.query(GoogleAdsAccount).all()
    return accounts

@router.post("/google-ads-accounts", response_model=GoogleAdsAccountResponse)
def create_google_ads_account(
    acc_data: GoogleAdsAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    clean_cid = acc_data.customer_id.strip()
    existing = db.query(GoogleAdsAccount).filter(GoogleAdsAccount.customer_id == clean_cid).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Google Ads Account ID {clean_cid} sudah terdaftar.")

    new_acc = GoogleAdsAccount(
        customer_id=clean_cid,
        account_name=acc_data.account_name or f"Google Ads ({clean_cid})",
        assigned_domain=acc_data.assigned_domain or "All / Unassigned"
    )
    db.add(new_acc)
    db.commit()
    db.refresh(new_acc)
    return new_acc

@router.put("/google-ads-accounts/{account_id}", response_model=GoogleAdsAccountResponse)
def update_google_ads_account(
    account_id: int,
    acc_data: GoogleAdsAccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    acc = db.query(GoogleAdsAccount).filter(GoogleAdsAccount.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Google Ads Account tidak ditemukan.")

    if acc_data.account_name is not None:
        acc.account_name = acc_data.account_name
    if acc_data.assigned_domain is not None:
        acc.assigned_domain = acc_data.assigned_domain

    db.commit()
    db.refresh(acc)
    return acc

@router.delete("/google-ads-accounts/{account_id}")
def delete_google_ads_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    acc = db.query(GoogleAdsAccount).filter(GoogleAdsAccount.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Google Ads Account tidak ditemukan.")

    db.delete(acc)
    db.commit()
    return {"status": "success", "message": f"Google Ads Account ID {acc.customer_id} berhasil dihapus."}

@router.get("/available-domains", response_model=List[str])
def get_available_domains(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models import GAMMetric, GoogleAdsAccount
    from datetime import date, timedelta

    domains = set()

    # 1. Fetch from GAMMetric DB table
    try:
        db_domains = db.query(GAMMetric.domain.distinct()).filter(GAMMetric.domain != None).all()
        for d in db_domains:
            if d[0] and d[0].strip() and d[0] != "All / Unassigned":
                domains.add(d[0].strip())
    except Exception as e:
        db.rollback()
        logger.warning(f"Failed querying GAMMetric domains from DB: {e}")

    # 2. Fetch from GoogleAdsAccount assigned domains in DB
    try:
        acc_domains = db.query(GoogleAdsAccount.assigned_domain.distinct()).filter(GoogleAdsAccount.assigned_domain != None).all()
        for d in acc_domains:
            if d[0] and d[0].strip() and d[0] != "All / Unassigned":
                domains.add(d[0].strip())
    except Exception as e:
        db.rollback()

    # 3. If DB is empty, attempt GAM API fetch
    if not domains:
        try:
            today = date.today()
            gam_metrics = gam_service.fetch_daily_metrics(today - timedelta(days=7), today)
            for m in gam_metrics:
                if m.get("domain"):
                    domains.add(m["domain"].strip())
        except Exception as e:
            logger.warning(f"Failed fetching GAM metrics for domain list: {e}")

    # Real network default fallback domains if DB is completely fresh
    default_real_domains = [
        "2b.nubmaster.com", "baleq.me", "dpr.skuy.me", "mbelik.com",
        "portal.mbelik.com", "news.mbelik.com", "sub.mbelik.com"
    ]
    for d in default_real_domains:
        domains.add(d)

    return sorted(list(domains))

# JSON Export Target Management Endpoints
@router.get("/export-targets", response_model=List[JSONExportTargetResponse])
def get_export_targets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    targets = db.query(JSONExportTarget).all()
    return targets

@router.post("/export-targets", response_model=JSONExportTargetResponse)
def create_export_target(
    target_data: JSONExportTargetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    clean_domain = target_data.domain.strip()
    clean_path = target_data.target_filepath.strip()

    if not clean_domain or not clean_path:
        raise HTTPException(status_code=400, detail="Domain dan Target Filepath wajib diisi.")

    new_target = JSONExportTarget(
        domain=clean_domain,
        target_filepath=clean_path,
        start_hour=target_data.start_hour,
        end_hour=target_data.end_hour,
        is_active=target_data.is_active
    )
    db.add(new_target)
    db.commit()
    db.refresh(new_target)

    # Automatically create pricing_config.json and current_pricing.json in target public_html
    try:
        from app.services.sync import load_pricing_config, save_pricing_config_and_sync, export_site_today_json
        cfg = load_pricing_config()
        save_pricing_config_and_sync(cfg, db=db)
        if new_target.is_active:
            export_site_today_json(
                db,
                domain=new_target.domain,
                target_filepath=new_target.target_filepath,
                start_hour=new_target.start_hour,
                end_hour=new_target.end_hour,
                force=True
            )
    except Exception as e:
        logger.warning(f"Auto-generate files for new export target {clean_domain} notice: {e}")

    return new_target

@router.put("/export-targets/{target_id}", response_model=JSONExportTargetResponse)
def update_export_target(
    target_id: int,
    target_data: JSONExportTargetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target = db.query(JSONExportTarget).filter(JSONExportTarget.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="JSON Export Target tidak ditemukan.")

    if target_data.domain is not None:
        target.domain = target_data.domain.strip()
    if target_data.target_filepath is not None:
        target.target_filepath = target_data.target_filepath.strip()
    if target_data.start_hour is not None:
        target.start_hour = target_data.start_hour
    if target_data.end_hour is not None:
        target.end_hour = target_data.end_hour
    if target_data.is_active is not None:
        target.is_active = target_data.is_active

    db.commit()
    db.refresh(target)

    # Auto sync pricing_config.json if active
    try:
        from app.services.sync import load_pricing_config, save_pricing_config_and_sync
        cfg = load_pricing_config()
        save_pricing_config_and_sync(cfg, db=db)
    except Exception as e:
        logger.warning(f"Auto-sync pricing_config on target update notice: {e}")

    return target


@router.delete("/export-targets/{target_id}")
def delete_export_target(
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target = db.query(JSONExportTarget).filter(JSONExportTarget.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="JSON Export Target tidak ditemukan.")

    db.delete(target)
    db.commit()
    return {"status": "success", "message": f"Export target untuk {target.domain} berhasil dihapus."}

@router.post("/export-targets/{target_id}/test")
def test_export_target(
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.services.sync import export_site_today_json
    target = db.query(JSONExportTarget).filter(JSONExportTarget.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="JSON Export Target tidak ditemukan.")

    try:
        export_site_today_json(
            db,
            domain=target.domain,
            target_filepath=target.target_filepath,
            start_hour=target.start_hour,
            end_hour=target.end_hour,
            force=True
        )
        return {"status": "success", "message": f"Uji coba export JSON untuk {target.domain} berhasil disimpan ke {target.target_filepath}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengekspor JSON: {str(e)}")

# GAM Auto Pricing Config Endpoints
@router.get("/pricing-config", response_model=PricingConfigSchema)
def get_pricing_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.services.sync import load_pricing_config
    return load_pricing_config()

@router.post("/pricing-config", response_model=dict)
def save_pricing_config(
    config_data: PricingConfigSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.services.sync import save_pricing_config_and_sync
    synced = save_pricing_config_and_sync(config_data.model_dump() if hasattr(config_data, 'model_dump') else config_data.dict(), db=db)
    return {
        "status": "success",
        "message": f"Pricing config successfully saved and synchronized across {len(synced)} site directories.",
        "synced_paths": synced
    }






