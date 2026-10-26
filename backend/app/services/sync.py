import os
import json
import logging
from datetime import date, datetime, timedelta


from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import GoogleAdsMetric, GAMMetric, GAMCountryMetric, GoogleAdsCountryMetric, GoogleAdsDeviceMetric, DailyProfitSummary, GoogleAdsAccount

from app.services.google_ads import google_ads_service
from app.services.gam import gam_service
from app.config import settings

import threading

logger = logging.getLogger(__name__)

_sync_lock = threading.RLock()

class SyncService:
    def sync_range(self, db: Session, start_date: date, end_date: date, sync_gads: bool = True) -> Dict[str, Any]:
        """
        Pull Google Ads & GAM metrics for start_date to end_date, update DB cache tables,
        apply +11% tax on Google Ads spend and -8% deduction on GAM AdX revenue,
        and calculate daily profit summaries.
        Protected with _sync_lock to prevent concurrent SQLite write locks.
        """
        with _sync_lock:
            return self._sync_range_internal(db, start_date, end_date, sync_gads=sync_gads)

    def _sync_range_internal(self, db: Session, start_date: date, end_date: date, sync_gads: bool = True) -> Dict[str, Any]:
        messages = []
        records_synced = 0

        try:
            from app.database import Base, engine
            import app.models
            Base.metadata.create_all(bind=engine)
        except Exception as e:
            logger.warning(f"Sync table creation notice: {e}")

        # =========================================================================
        # PHASE 1: STAGING (Fetch all data into in-memory structures first)
        # No database deletes or commits happen during this network fetch phase.
        # =========================================================================
        gam_data = []
        gam_country_data = []
        gam_sync_start = start_date

        try:
            gam_data = gam_service.fetch_daily_metrics(gam_sync_start, end_date)
            gam_country_data = gam_service.fetch_country_metrics(start_date, end_date)
        except Exception as e:
            err_msg = str(e)
            logger.error(f"GAM API Error: {err_msg}")
            messages.append(f"GAM API Error: {err_msg}")

        gads_data = []
        gads_country_data = []
        gads_device_data = []
        balances_map = {}
        cids = None

        if sync_gads:
            try:
                db_accounts = db.query(GoogleAdsAccount).all()
                cids = [acc.customer_id for acc in db_accounts] if db_accounts else None
            except Exception:
                db.rollback()
                cids = None

            # 1a. Daily spend metrics
            try:
                gads_data = google_ads_service.fetch_daily_metrics(start_date, end_date, customer_ids=cids)
            except Exception as e:
                err_msg = str(e)
                logger.error(f"Google Ads API Error: {err_msg}")
                if "test accounts" in err_msg.lower():
                    messages.append("Google Ads: Developer Token is test account level. Apply for Basic Access in Google Ads API Center for live account access.")
                else:
                    messages.append(f"Google Ads API Error: {err_msg}")

            # 1b. Real-time account balances (with polite pacing delay)
            try:
                balances_map = google_ads_service.fetch_account_balances(customer_ids=cids)
            except Exception as ex:
                logger.warning(f"Notice fetching remaining account balances: {ex}")

            # 1c. Country metrics (with polite pacing delay)
            try:
                gads_country_data = google_ads_service.fetch_country_metrics(start_date, end_date, customer_ids=cids)
            except Exception as e:
                logger.warning(f"Google Ads Country Metrics fetch notice: {e}")

            # 1d. Device metrics
            try:
                gads_device_data = google_ads_service.fetch_device_metrics(start_date, end_date, customer_ids=cids)
            except Exception as e:
                logger.warning(f"Google Ads Device Metrics fetch notice: {e}")

        # =========================================================================
        # PHASE 2: ATOMIC COMMIT (Write all staged data to SQLite in one go)
        # Takes ~0.05s. Both GAM and GAds share the EXACT SAME synced_at timestamp.
        # =========================================================================
        unified_sync_time = datetime.utcnow()

        try:
            # 2a. Save GAM Daily Metrics
            if gam_data:
                db.query(GAMMetric).filter(
                    GAMMetric.date >= gam_sync_start,
                    GAMMetric.date <= end_date
                ).delete(synchronize_session=False)

                aggregated_gam = {}
                for item in gam_data:
                    dom = (item.get("domain") or "").strip().lower()
                    unit = (item.get("ad_unit") or "Standard Ad Unit").strip()
                    p_rule = (item.get("pricing_rule_name") or "All Rules").strip()
                    dev_cat = (item.get("device_category") or "mobile").strip().lower()
                    if not dom:
                        continue
                    norm_key = (item["date"], dom, unit.lower(), p_rule.lower(), dev_cat)
                    if norm_key not in aggregated_gam:
                        aggregated_gam[norm_key] = {
                            "date": item["date"],
                            "domain": dom,
                            "ad_unit": unit,
                            "pricing_rule_name": p_rule,
                            "device_category": dev_cat,
                            "revenue": 0.0,
                            "impressions": 0,
                            "clicks": 0,
                            "ad_requests": 0,
                            "matched_requests": 0
                        }
                    agg = aggregated_gam[norm_key]
                    agg["revenue"] += item.get("revenue", 0.0)
                    agg["impressions"] += item.get("impressions", 0)
                    agg["clicks"] += item.get("clicks", 0)
                    agg["ad_requests"] += item.get("ad_requests", 0)
                    agg["matched_requests"] += item.get("matched_requests", 0)

                new_gam_metrics = []
                for item in aggregated_gam.values():
                    raw_rev = item.get("revenue", 0.0)
                    adj_rev = round(raw_rev * 0.92, 2)  # Deducts 8% fee
                    imps = item.get("impressions", 0)
                    clicks = item.get("clicks", 0)
                    adj_ecpm = round((adj_rev / imps) * 1000.0, 2) if imps > 0 else 0.0

                    ad_reqs = item.get("ad_requests", 0)
                    matched_reqs = item.get("matched_requests", 0)
                    mr = (matched_reqs / ad_reqs * 100.0) if ad_reqs > 0 else 0.0

                    new_metric = GAMMetric(
                        date=item["date"],
                        domain=item["domain"],
                        ad_unit=item["ad_unit"],
                        pricing_rule_name=item.get("pricing_rule_name", "All Rules"),
                        device_category=item.get("device_category", "mobile"),
                        revenue=adj_rev,
                        impressions=imps,
                        ecpm=adj_ecpm,
                        clicks=clicks,
                        match_rate=round(mr, 2),
                        ad_requests=ad_reqs,
                        matched_requests=matched_reqs,
                        synced_at=unified_sync_time
                    )
                    new_gam_metrics.append(new_metric)
                    records_synced += 1

                if new_gam_metrics:
                    db.add_all(new_gam_metrics)

            # 2b. Save GAM Country Metrics
            if gam_country_data:
                db.query(GAMCountryMetric).filter(
                    GAMCountryMetric.date >= start_date,
                    GAMCountryMetric.date <= end_date
                ).delete(synchronize_session=False)

                aggregated_country = {}
                for item in gam_country_data:
                    dom = (item.get("domain") or "").strip().lower()
                    c_name = (item.get("country") or "Indonesia").strip()
                    unit = (item.get("ad_unit") or "Standard Ad Unit").strip()
                    p_rule = (item.get("pricing_rule_name") or "All Rules").strip()
                    dev_cat = (item.get("device_category") or "mobile").strip().lower()
                    if not dom:
                        continue
                    norm_c_key = (item["date"], dom, c_name.lower(), unit.lower(), p_rule.lower(), dev_cat)
                    if norm_c_key not in aggregated_country:
                        aggregated_country[norm_c_key] = {
                            "date": item["date"],
                            "domain": dom,
                            "country": c_name,
                            "country_code": item.get("country_code", "ID"),
                            "ad_unit": unit,
                            "pricing_rule_name": p_rule,
                            "device_category": dev_cat,
                            "revenue": 0.0,
                            "impressions": 0,
                            "clicks": 0,
                            "ad_requests": 0,
                            "matched_requests": 0
                        }
                    agg = aggregated_country[norm_c_key]
                    agg["revenue"] += item.get("revenue", 0.0)
                    agg["impressions"] += item.get("impressions", 0)
                    agg["clicks"] += item.get("clicks", 0)
                    agg["ad_requests"] += item.get("ad_requests", 0)
                    agg["matched_requests"] += item.get("matched_requests", 0)

                new_country_metrics = []
                for item in aggregated_country.values():
                    raw_rev = item.get("revenue", 0.0)
                    adj_rev = round(raw_rev * 0.92, 2)  # Deducts 8% fee
                    imps = item.get("impressions", 0)
                    clicks = item.get("clicks", 0)
                    adj_ecpm = round((adj_rev / imps) * 1000.0, 2) if imps > 0 else 0.0

                    ad_reqs = item.get("ad_requests", 0)
                    matched_reqs = item.get("matched_requests", 0)
                    country_code = item.get("country_code", "ID")
                    c_mr = (matched_reqs / ad_reqs * 100.0) if ad_reqs > 0 else 0.0

                    new_c_metric = GAMCountryMetric(
                        date=item["date"],
                        domain=item["domain"],
                        country=item["country"],
                        country_code=country_code,
                        ad_unit=item["ad_unit"],
                        pricing_rule_name=item.get("pricing_rule_name", "All Rules"),
                        device_category=item.get("device_category", "mobile"),
                        revenue=adj_rev,
                        impressions=imps,
                        ecpm=adj_ecpm,
                        clicks=clicks,
                        match_rate=round(c_mr, 2),
                        ad_requests=ad_reqs,
                        matched_requests=matched_reqs,
                        synced_at=unified_sync_time
                    )
                    new_country_metrics.append(new_c_metric)

                if new_country_metrics:
                    db.add_all(new_country_metrics)

            # 2c. Save Google Ads Daily Metrics
            if sync_gads and gads_data:
                db.query(GoogleAdsMetric).filter(
                    GoogleAdsMetric.date >= start_date,
                    GoogleAdsMetric.date <= end_date
                ).delete(synchronize_session=False)

                aggregated_gads = {}
                for item in gads_data:
                    key = (item["date"], item["customer_id"], item["campaign_name"])
                    if key not in aggregated_gads:
                        aggregated_gads[key] = {
                            "date": item["date"],
                            "customer_id": item["customer_id"],
                            "account_name": item["account_name"],
                            "campaign_name": item["campaign_name"],
                            "spend": 0.0,
                            "impressions": 0,
                            "clicks": 0
                        }
                    agg = aggregated_gads[key]
                    agg["spend"] += item.get("spend", 0.0)
                    agg["impressions"] += item.get("impressions", 0)
                    agg["clicks"] += item.get("clicks", 0)

                for item in aggregated_gads.values():
                    raw_spend = item.get("spend", 0.0)
                    adj_spend = round(raw_spend * 1.11, 2)  # Adds 11% PPN tax
                    clicks = item.get("clicks", 0)
                    imps = item.get("impressions", 0)
                    adj_cpc = round(adj_spend / clicks, 2) if clicks > 0 else 0.0
                    ctr = (clicks / imps * 100.0) if imps > 0 else 0.0

                    new_metric = GoogleAdsMetric(
                        date=item["date"],
                        customer_id=item["customer_id"],
                        account_name=item["account_name"],
                        campaign_name=item["campaign_name"],
                        spend=adj_spend,
                        impressions=imps,
                        clicks=clicks,
                        cpc=adj_cpc,
                        ctr=ctr,
                        synced_at=unified_sync_time
                    )
                    db.add(new_metric)
                    records_synced += 1

            # 2d. Update remaining balances on GoogleAdsAccount
            if sync_gads and balances_map:
                for cid, bal in balances_map.items():
                    acc = db.query(GoogleAdsAccount).filter(GoogleAdsAccount.customer_id == cid).first()
                    if acc:
                        acc.remaining_balance = bal

            # 2e. Save Google Ads Country Metrics
            if sync_gads and gads_country_data:
                db.query(GoogleAdsCountryMetric).filter(
                    GoogleAdsCountryMetric.date >= start_date,
                    GoogleAdsCountryMetric.date <= end_date
                ).delete(synchronize_session=False)

                aggregated_gads_country = {}
                for item in gads_country_data:
                    dev_cat = item.get("device_category", "mobile")
                    key = (item["date"], item["customer_id"], item["country"], dev_cat)
                    if key not in aggregated_gads_country:
                        aggregated_gads_country[key] = {
                            "date": item["date"],
                            "customer_id": item["customer_id"],
                            "country": item["country"],
                            "country_code": item.get("country_code", "ID"),
                            "device_category": dev_cat,
                            "spend": 0.0,
                            "impressions": 0,
                            "clicks": 0
                        }
                    agg = aggregated_gads_country[key]
                    agg["spend"] += item.get("spend", 0.0)
                    agg["impressions"] += item.get("impressions", 0)
                    agg["clicks"] += item.get("clicks", 0)

                for item in aggregated_gads_country.values():
                    raw_spend = item.get("spend", 0.0)
                    adj_spend = round(raw_spend * 1.11, 2)  # Adds 11% PPN tax
                    new_c_gads = GoogleAdsCountryMetric(
                        date=item["date"],
                        customer_id=item["customer_id"],
                        country=item["country"],
                        country_code=item["country_code"],
                        device_category=item["device_category"],
                        spend=adj_spend,
                        impressions=item["impressions"],
                        clicks=item["clicks"],
                        synced_at=unified_sync_time
                    )
                    db.add(new_c_gads)

            # 2f. Save Google Ads Device Metrics
            if sync_gads and gads_device_data:
                db.query(GoogleAdsDeviceMetric).filter(
                    GoogleAdsDeviceMetric.date >= start_date,
                    GoogleAdsDeviceMetric.date <= end_date
                ).delete(synchronize_session=False)

                aggregated_gads_device = {}
                for item in gads_device_data:
                    key = (item["date"], item["customer_id"], item["device_category"])
                    if key not in aggregated_gads_device:
                        aggregated_gads_device[key] = {
                            "date": item["date"],
                            "customer_id": item["customer_id"],
                            "device_category": item["device_category"],
                            "spend": 0.0,
                            "impressions": 0,
                            "clicks": 0
                        }
                    agg = aggregated_gads_device[key]
                    agg["spend"] += item.get("spend", 0.0)
                    agg["impressions"] += item.get("impressions", 0)
                    agg["clicks"] += item.get("clicks", 0)

                for item in aggregated_gads_device.values():
                    raw_spend = item.get("spend", 0.0)
                    adj_spend = round(raw_spend * 1.11, 2)  # Adds 11% PPN tax
                    new_d_gads = GoogleAdsDeviceMetric(
                        date=item["date"],
                        customer_id=item["customer_id"],
                        device_category=item["device_category"],
                        spend=adj_spend,
                        impressions=item["impressions"],
                        clicks=item["clicks"],
                        synced_at=unified_sync_time
                    )
                    db.add(new_d_gads)

            # 2g. Calculate daily profit summaries per date in the range
            curr_date = start_date
            while curr_date <= end_date:
                gads_spend = db.query(func.sum(GoogleAdsMetric.spend)).filter(GoogleAdsMetric.date == curr_date).scalar() or 0.0
                gam_rev = db.query(func.sum(GAMMetric.revenue)).filter(GAMMetric.date == curr_date).scalar() or 0.0

                net_profit = gam_rev - gads_spend
                roi = (gam_rev / gads_spend * 100.0) if gads_spend > 0 else 0.0
                margin = (net_profit / gam_rev * 100.0) if gam_rev > 0 else 0.0

                summary = db.query(DailyProfitSummary).filter(DailyProfitSummary.date == curr_date).first()
                if summary:
                    summary.total_spend = round(gads_spend, 2)
                    summary.total_revenue = round(gam_rev, 2)
                    summary.net_profit = round(net_profit, 2)
                    summary.roi = round(roi, 2)
                    summary.profit_margin = round(margin, 2)
                    summary.synced_at = unified_sync_time
                else:
                    summary = DailyProfitSummary(
                        date=curr_date,
                        total_spend=round(gads_spend, 2),
                        total_revenue=round(gam_rev, 2),
                        net_profit=round(net_profit, 2),
                        roi=round(roi, 2),
                        profit_margin=round(margin, 2),
                        synced_at=unified_sync_time
                    )
                    db.add(summary)

                curr_date += timedelta(days=1)

            # ATOMIC COMMIT: Everything commits together in < 0.05 seconds!
            db.commit()
            logger.info(f"[AtomicSync] Staged GAM & GAds records atomically committed at {unified_sync_time} (0.0s diff)")

        except Exception as e:
            db.rollback()
            logger.error(f"[AtomicSync] Error during atomic commit: {e}", exc_info=True)
            messages.append(f"Atomic commit error: {e}")

        # Auto-export today's data for all active target domains to their specified paths
        try:
            from app.models import JSONExportTarget
            targets = db.query(JSONExportTarget).filter(JSONExportTarget.is_active == True).all()
            if targets:
                for t in targets:
                    export_site_today_json(
                        db,
                        domain=t.domain,
                        target_filepath=t.target_filepath,
                        start_hour=t.start_hour,
                        end_hour=t.end_hour
                    )
            else:
                export_site_today_json(db, domain="spotgames.top", target_filepath="/home/mbummm/web/spotgames.top/public_html/current_pricing.json")
        except Exception as e:
            logger.warning(f"Error auto-exporting site JSON targets: {e}")

        status_str = "warning" if messages else "success"
        message_str = " | ".join(messages) if messages else f"Successfully synced data from {start_date} to {end_date}"

        return {
            "status": status_str,
            "message": message_str,
            "records_synced": records_synced,
            "sync_date_start": start_date.strftime("%Y-%m-%d"),
            "sync_date_end": end_date.strftime("%Y-%m-%d"),
            "is_mock_data": google_ads_service.use_mock or gam_service.use_mock
        }

def atomic_write_json(target_filepath: str, data: dict, indent: int = 2):
    """
    Writes data to a temporary file first, flushes to disk, and then performs
    an atomic file replacement (os.replace) to ensure target file is never read
    in a partial/corrupted state by concurrent web requests.
    """
    target_dir = os.path.dirname(target_filepath)
    if target_dir:
        os.makedirs(target_dir, exist_ok=True)

    temp_filepath = f"{target_filepath}.tmp.{os.getpid()}"
    try:
        with open(temp_filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())

        try:
            os.chmod(temp_filepath, 0o666)
        except Exception:
            pass

        os.replace(temp_filepath, target_filepath)
    except Exception as e:
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except Exception:
                pass
        raise e

def export_site_today_json(
    db: Session,
    domain: str = "spotgames.top",
    target_filepath: str = "/home/mbummm/web/spotgames.top/public_html/current_pricing.json",
    start_hour: int = 0,
    end_hour: int = 23,
    force: bool = False
):
    import os
    import json
    from datetime import timezone

    WIB = timezone(timedelta(hours=7))
    wib_now = datetime.now(WIB)
    current_hour = wib_now.hour

    # Jam operasional auto-export: 24 Jam Full (00:00 - 23:59 WIB)
    if not force and not (start_hour <= current_hour <= end_hour):
        logger.info(f"Auto-export JSON untuk {domain} dilewati (di luar jam operasional {start_hour}:00 - {end_hour}:00 WIB). Jam saat ini: {wib_now.strftime('%H:%M WIB')}")
        return

    today_date = wib_now.date()
    yesterday_date = today_date - timedelta(days=1)
    today_str = today_date.strftime("%Y-%m-%d")

    # Fetch GAM metrics for domain today to assess current volume
    gam_row_today = db.query(
        func.sum(GAMMetric.revenue).label("revenue"),
        func.sum(GAMMetric.impressions).label("impressions"),
        func.sum(GAMMetric.clicks).label("clicks"),
        func.sum(GAMMetric.ad_requests).label("ad_requests"),
        func.sum(GAMMetric.matched_requests).label("matched_requests"),
        func.avg(GAMMetric.match_rate).label("match_rate")
    ).filter(
        GAMMetric.domain == domain,
        GAMMetric.date == today_date
    ).first()

    today_ad_reqs = (gam_row_today.ad_requests or 0) if gam_row_today else 0
    today_imps = (gam_row_today.impressions or 0) if gam_row_today else 0

    # 4-Quadrant Adaptive Matrix:
    # 1. Subuh (< 06:00 WIB) & < 200 reqs -> Data kemarin (-20% diskon) + Soft Target
    # 2. Subuh (< 06:00 WIB) & >= 200 reqs -> Data hari ini + Soft Target
    # 3. Normal (>= 06:00 WIB) & >= 200 reqs -> Data hari ini normal (Dynamic)
    # 4. Normal (>= 06:00 WIB) & < 200 reqs -> Fallback data kemarin + Soft Target
    is_dawn_period = (0 <= current_hour < 6)
    has_sufficient_traffic = (today_ad_reqs >= 200 or today_imps >= 50)

    if is_dawn_period:
        if has_sufficient_traffic:
            source_date = today_date
            apply_dawn_discount = False
            force_soft_target = True
            decision_mode = "Subuh + Trafik Cukup (>=200 reqs): Data Hari Ini + Soft Target"
        else:
            source_date = yesterday_date
            apply_dawn_discount = True
            force_soft_target = True
            decision_mode = "Subuh + Trafik Awal (<200 reqs): Data Kemarin (-20% diskon) + Soft Target"
    else:
        if has_sufficient_traffic:
            source_date = today_date
            apply_dawn_discount = False
            force_soft_target = False
            decision_mode = "Normal (>=200 reqs): Data Hari Ini Penuh"
        else:
            source_date = yesterday_date
            apply_dawn_discount = False
            force_soft_target = True
            decision_mode = "Normal + Trafik Rendah (<200 reqs): Fallback Data Kemarin + Soft Target"

    logger.info(f"[{domain}] AutoPricing: {decision_mode} (Hour: {current_hour}:00 WIB, Today Reqs: {today_ad_reqs}, Imps: {today_imps}, Source Date: {source_date})")

    gam_row = gam_row_today if (source_date == today_date and gam_row_today and (gam_row_today.impressions or 0) > 0) else db.query(
        func.sum(GAMMetric.revenue).label("revenue"),
        func.sum(GAMMetric.impressions).label("impressions"),
        func.sum(GAMMetric.clicks).label("clicks"),
        func.sum(GAMMetric.ad_requests).label("ad_requests"),
        func.sum(GAMMetric.matched_requests).label("matched_requests"),
        func.avg(GAMMetric.match_rate).label("match_rate")
    ).filter(
        GAMMetric.domain == domain,
        GAMMetric.date == source_date
    ).first()

    tot_rev = (gam_row.revenue or 0.0) if gam_row else 0.0
    tot_imps = (gam_row.impressions or 0) if gam_row else 0
    tot_clicks = (gam_row.clicks or 0) if gam_row else 0
    tot_ad_reqs = (gam_row.ad_requests or 0) if gam_row else 0
    tot_matched_reqs = (gam_row.matched_requests or 0) if gam_row else 0
    avg_mr = (gam_row.match_rate or 0.0) if gam_row else 0.0

    if tot_matched_reqs == 0 and tot_imps > 0:
        tot_matched_reqs = tot_imps

    if tot_ad_reqs > 0 and tot_matched_reqs > 0:
        domain_mr = round((tot_matched_reqs / tot_ad_reqs) * 100.0, 1)
    elif avg_mr > 0:
        domain_mr = round(avg_mr, 1)
    else:
        domain_mr = 34.5

    if tot_ad_reqs == 0 and tot_matched_reqs > 0:
        tot_ad_reqs = int(tot_matched_reqs / (domain_mr / 100.0)) if domain_mr > 0 else int(tot_matched_reqs * 2.8)

    ecpm = round((tot_rev / tot_imps * 1000.0), 2) if tot_imps > 0 else 0.0
    if apply_dawn_discount and ecpm > 0:
        ecpm = round(ecpm * 0.80, 2)
    if force_soft_target and domain_mr > 55.0:
        domain_mr = 55.0

    d_start_7d = today_date - timedelta(days=7)

    # Pre-query 7-day historical device stats for fallback
    hist_c_p_d_rows = db.query(
        GAMCountryMetric.country,
        GAMCountryMetric.ad_unit,
        GAMCountryMetric.device_category,
        func.sum(GAMCountryMetric.revenue).label("revenue"),
        func.sum(GAMCountryMetric.impressions).label("impressions"),
        func.sum(GAMCountryMetric.ad_requests).label("ad_requests"),
        func.sum(GAMCountryMetric.matched_requests).label("matched_requests")
    ).filter(
        func.lower(GAMCountryMetric.domain) == domain.lower(),
        GAMCountryMetric.date >= d_start_7d,
        GAMCountryMetric.date <= today_date
    ).group_by(GAMCountryMetric.country, GAMCountryMetric.ad_unit, GAMCountryMetric.device_category).all()

    hist_cpd_map = {}
    for r in hist_c_p_d_rows:
        c_name = r.country or "Unknown Region"
        unit = r.ad_unit or "Standard Ad Unit"
        dev_cat = (r.device_category or "mobile").lower()
        if c_name not in hist_cpd_map:
            hist_cpd_map[c_name] = {}
        if unit not in hist_cpd_map[c_name]:
            hist_cpd_map[c_name][unit] = {}
        rev = r.revenue or 0.0
        imps = r.impressions or 0
        ad_reqs = r.ad_requests or 0
        matched_reqs = r.matched_requests or 0
        mr = round((matched_reqs / ad_reqs * 100.0), 1) if ad_reqs > 0 else 0.0
        ecpm = round((rev / imps * 1000.0), 2) if imps > 0 else 0.0
        hist_cpd_map[c_name][unit][dev_cat] = {"match_rate": mr, "ecpm": ecpm}

    hist_c_dev_rows = db.query(
        GAMCountryMetric.country,
        GAMCountryMetric.device_category,
        func.sum(GAMCountryMetric.revenue).label("revenue"),
        func.sum(GAMCountryMetric.impressions).label("impressions"),
        func.sum(GAMCountryMetric.ad_requests).label("ad_requests"),
        func.sum(GAMCountryMetric.matched_requests).label("matched_requests")
    ).filter(
        func.lower(GAMCountryMetric.domain) == domain.lower(),
        GAMCountryMetric.date >= d_start_7d,
        GAMCountryMetric.date <= today_date
    ).group_by(GAMCountryMetric.country, GAMCountryMetric.device_category).all()

    hist_c_dev_map = {}
    for r in hist_c_dev_rows:
        c_name = r.country or "Unknown Region"
        dev_cat = (r.device_category or "mobile").lower()
        if c_name not in hist_c_dev_map:
            hist_c_dev_map[c_name] = {}
        rev = r.revenue or 0.0
        imps = r.impressions or 0
        ad_reqs = r.ad_requests or 0
        matched_reqs = r.matched_requests or 0
        mr = round((matched_reqs / ad_reqs * 100.0), 1) if ad_reqs > 0 else 0.0
        ecpm = round((rev / imps * 1000.0), 2) if imps > 0 else 0.0
        hist_c_dev_map[c_name][dev_cat] = {"match_rate": mr, "ecpm": ecpm}

    hist_summary_rows = db.query(
        GAMMetric.device_category,
        func.sum(GAMMetric.revenue).label("revenue"),
        func.sum(GAMMetric.impressions).label("impressions"),
        func.sum(GAMMetric.ad_requests).label("ad_requests"),
        func.sum(GAMMetric.matched_requests).label("matched_requests")
    ).filter(
        GAMMetric.domain == domain,
        GAMMetric.date >= d_start_7d,
        GAMMetric.date <= today_date
    ).group_by(GAMMetric.device_category).all()

    hist_summary_dev_map = {}
    for r in hist_summary_rows:
        dev_cat = (r.device_category or "mobile").lower()
        rev = r.revenue or 0.0
        imps = r.impressions or 0
        ad_reqs = r.ad_requests or 0
        matched_reqs = r.matched_requests or 0
        mr = round((matched_reqs / ad_reqs * 100.0), 1) if ad_reqs > 0 else 0.0
        ecpm = round((rev / imps * 1000.0), 2) if imps > 0 else 0.0
        hist_summary_dev_map[dev_cat] = {"match_rate": mr, "ecpm": ecpm}

    def classify_ad_format(unit_name: str) -> str:
        if not unit_name:
            return "bnr"
        u = str(unit_name).lower().strip()
        if any(k in u for k in ["int", "vignet", "interstitial"]):
            return "int"
        if any(k in u for k in ["sticky", "anchor", "anc"]):
            return "anc"
        return "bnr"

    # 7-day historical format breakdown summary
    hist_fmt_summary_rows = db.query(
        GAMMetric.device_category,
        GAMMetric.ad_unit,
        func.sum(GAMMetric.revenue).label("revenue"),
        func.sum(GAMMetric.impressions).label("impressions"),
        func.sum(GAMMetric.ad_requests).label("ad_requests"),
        func.sum(GAMMetric.matched_requests).label("matched_requests")
    ).filter(
        GAMMetric.domain == domain,
        GAMMetric.date >= d_start_7d,
        GAMMetric.date <= today_date
    ).group_by(GAMMetric.device_category, GAMMetric.ad_unit).all()

    hist_summary_fmt_map = {}
    hist_fmt_temp = {}
    for r in hist_fmt_summary_rows:
        dev_cat = (r.device_category or "mobile").lower()
        fmt = classify_ad_format(r.ad_unit)
        if dev_cat not in hist_fmt_temp:
            hist_fmt_temp[dev_cat] = {}
        if fmt not in hist_fmt_temp[dev_cat]:
            hist_fmt_temp[dev_cat][fmt] = {"rev": 0.0, "imps": 0, "ad_reqs": 0, "matched": 0}
        hist_fmt_temp[dev_cat][fmt]["rev"] += (r.revenue or 0.0)
        hist_fmt_temp[dev_cat][fmt]["imps"] += (r.impressions or 0)
        hist_fmt_temp[dev_cat][fmt]["ad_reqs"] += (r.ad_requests or 0)
        hist_fmt_temp[dev_cat][fmt]["matched"] += (r.matched_requests or 0)

    for dev_cat, fmts in hist_fmt_temp.items():
        hist_summary_fmt_map[dev_cat] = {}
        for fmt, d in fmts.items():
            mr = round((d["matched"] / d["ad_reqs"] * 100.0), 1) if d["ad_reqs"] > 0 else 0.0
            ecpm = round((d["rev"] / d["imps"] * 1000.0), 2) if d["imps"] > 0 else 0.0
            hist_summary_fmt_map[dev_cat][fmt] = {"match_rate": mr, "ecpm": ecpm}

    # 7-day historical format breakdown per country+device
    hist_c_fmt_rows = db.query(
        GAMCountryMetric.country,
        GAMCountryMetric.device_category,
        GAMCountryMetric.ad_unit,
        func.sum(GAMCountryMetric.revenue).label("revenue"),
        func.sum(GAMCountryMetric.impressions).label("impressions"),
        func.sum(GAMCountryMetric.ad_requests).label("ad_requests"),
        func.sum(GAMCountryMetric.matched_requests).label("matched_requests")
    ).filter(
        func.lower(GAMCountryMetric.domain) == domain.lower(),
        GAMCountryMetric.date >= d_start_7d,
        GAMCountryMetric.date <= today_date
    ).group_by(GAMCountryMetric.country, GAMCountryMetric.device_category, GAMCountryMetric.ad_unit).all()

    hist_c_fmt_map = {}
    hist_cf_temp = {}
    for r in hist_c_fmt_rows:
        c_name = r.country or "Unknown Region"
        dev_cat = (r.device_category or "mobile").lower()
        fmt = classify_ad_format(r.ad_unit)
        if c_name not in hist_cf_temp:
            hist_cf_temp[c_name] = {}
        if dev_cat not in hist_cf_temp[c_name]:
            hist_cf_temp[c_name][dev_cat] = {}
        if fmt not in hist_cf_temp[c_name][dev_cat]:
            hist_cf_temp[c_name][dev_cat][fmt] = {"rev": 0.0, "imps": 0, "ad_reqs": 0, "matched": 0}
        hist_cf_temp[c_name][dev_cat][fmt]["rev"] += (r.revenue or 0.0)
        hist_cf_temp[c_name][dev_cat][fmt]["imps"] += (r.impressions or 0)
        hist_cf_temp[c_name][dev_cat][fmt]["ad_reqs"] += (r.ad_requests or 0)
        hist_cf_temp[c_name][dev_cat][fmt]["matched"] += (r.matched_requests or 0)

    for c_name, devs in hist_cf_temp.items():
        hist_c_fmt_map[c_name] = {}
        for dev_cat, fmts in devs.items():
            hist_c_fmt_map[c_name][dev_cat] = {}
            for fmt, d in fmts.items():
                mr = round((d["matched"] / d["ad_reqs"] * 100.0), 1) if d["ad_reqs"] > 0 else 0.0
                ecpm = round((d["rev"] / d["imps"] * 1000.0), 2) if d["imps"] > 0 else 0.0
                hist_c_fmt_map[c_name][dev_cat][fmt] = {"match_rate": mr, "ecpm": ecpm}

    def ensure_devices(dev_dict, fmt_today_map=None, hist_dict=None, hist_fmt_map=None, country_fallback=None, summary_fallback=None):
        out = {}
        for dev in ["mobile", "desktop"]:
            d_val = dev_dict.get(dev) if dev_dict else None
            out_dev = None
            if d_val and (d_val.get("ecpm", 0) > 0 or d_val.get("match_rate", 0) > 0):
                out_dev = dict(d_val)
            elif hist_dict and hist_dict.get(dev) and (hist_dict[dev].get("ecpm", 0) > 0 or hist_dict[dev].get("match_rate", 0) > 0):
                out_dev = dict(hist_dict[dev])
            elif country_fallback and country_fallback.get(dev) and (country_fallback[dev].get("ecpm", 0) > 0 or country_fallback[dev].get("match_rate", 0) > 0):
                out_dev = dict(country_fallback[dev])
            elif summary_fallback and summary_fallback.get(dev) and (summary_fallback[dev].get("ecpm", 0) > 0 or summary_fallback[dev].get("match_rate", 0) > 0):
                out_dev = dict(summary_fallback[dev])
            else:
                out_dev = {"match_rate": 0.0, "ecpm": 0.0}

            base_mr = out_dev.get("match_rate", 0.0)
            base_ecpm = out_dev.get("ecpm", 0.0)

            f_today_dev = fmt_today_map.get(dev, {}) if fmt_today_map else {}
            f_hist_dev = hist_fmt_map.get(dev, {}) if hist_fmt_map else {}

            for fmt in ["int", "anc", "bnr"]:
                t_data = f_today_dev.get(fmt)
                if t_data and (t_data.get("imps", 0) > 0 or t_data.get("ad_reqs", 0) > 0):
                    rev = t_data["rev"]
                    imps = t_data["imps"]
                    ad_reqs = t_data["ad_reqs"]
                    matched = t_data["matched"]
                    f_mr = round((matched / ad_reqs * 100.0), 1) if ad_reqs > 0 else (100.0 if imps > 0 else base_mr)
                    f_ecpm = round((rev / imps * 1000.0), 2) if imps > 0 else base_ecpm
                    out_dev[fmt] = {"match_rate": f_mr, "ecpm": f_ecpm}
                elif f_hist_dev.get(fmt) and (f_hist_dev[fmt].get("match_rate", 0) > 0 or f_hist_dev[fmt].get("ecpm", 0) > 0):
                    out_dev[fmt] = dict(f_hist_dev[fmt])
                elif country_fallback and country_fallback.get(dev) and country_fallback[dev].get(fmt):
                    out_dev[fmt] = dict(country_fallback[dev][fmt])
                elif summary_fallback and summary_fallback.get(dev) and summary_fallback[dev].get(fmt):
                    out_dev[fmt] = dict(summary_fallback[dev][fmt])
                else:
                    out_dev[fmt] = {"match_rate": base_mr, "ecpm": base_ecpm}

            # Apply dawn discount (-20%) if active
            if apply_dawn_discount:
                if out_dev.get("ecpm", 0.0) > 0:
                    out_dev["ecpm"] = round(out_dev["ecpm"] * 0.80, 2)
                for fmt in ["int", "anc", "bnr"]:
                    if out_dev.get(fmt, {}).get("ecpm", 0.0) > 0:
                        out_dev[fmt]["ecpm"] = round(out_dev[fmt]["ecpm"] * 0.80, 2)

            # Enforce Soft Target mode (cap match_rate under hard floor threshold) if active
            if force_soft_target:
                if out_dev.get("match_rate", 0.0) > 55.0:
                    out_dev["match_rate"] = 55.0
                for fmt in ["int", "anc", "bnr"]:
                    if out_dev.get(fmt, {}).get("match_rate", 0.0) > 55.0:
                        out_dev[fmt]["match_rate"] = 55.0

            # Interstitial MR >= 75% protection guard:
            # If Interstitial match rate drops below 75%, cap match_rate at 50.0 to trigger
            # AdsHeader step-down gap (65 - 50 = 15 > 10 => 2-level drop) and force Soft Target mode (<75.0).
            # Also apply a gentle -10% discount on interstitial eCPM to recover auction clearing.
            int_data = out_dev.get("int")
            if int_data and isinstance(int_data, dict):
                int_mr = int_data.get("match_rate", 0.0)
                if 0 < int_mr < 75.0:
                    int_data["match_rate"] = 50.0
                    if int_data.get("ecpm", 0.0) > 0:
                        int_data["ecpm"] = round(int_data["ecpm"] * 0.90, 2)

            out[dev] = out_dev
        return out

    # Format breakdown summary query
    summary_fmt_today_rows = db.query(
        GAMMetric.device_category,
        GAMMetric.ad_unit,
        func.sum(GAMMetric.revenue).label("revenue"),
        func.sum(GAMMetric.impressions).label("impressions"),
        func.sum(GAMMetric.ad_requests).label("ad_requests"),
        func.sum(GAMMetric.matched_requests).label("matched_requests")
    ).filter(
        GAMMetric.domain == domain,
        GAMMetric.date == source_date
    ).group_by(GAMMetric.device_category, GAMMetric.ad_unit).all()

    summary_fmt_today_map = {}
    for r in summary_fmt_today_rows:
        dev_cat = (r.device_category or "mobile").lower()
        fmt = classify_ad_format(r.ad_unit)
        if dev_cat not in summary_fmt_today_map:
            summary_fmt_today_map[dev_cat] = {}
        if fmt not in summary_fmt_today_map[dev_cat]:
            summary_fmt_today_map[dev_cat][fmt] = {"rev": 0.0, "imps": 0, "ad_reqs": 0, "matched": 0}
        summary_fmt_today_map[dev_cat][fmt]["rev"] += (r.revenue or 0.0)
        summary_fmt_today_map[dev_cat][fmt]["imps"] += (r.impressions or 0)
        summary_fmt_today_map[dev_cat][fmt]["ad_reqs"] += (r.ad_requests or 0)
        summary_fmt_today_map[dev_cat][fmt]["matched"] += (r.matched_requests or 0)

    # Query per-device summary breakdown
    summary_dev_rows = db.query(
        GAMMetric.device_category,
        func.sum(GAMMetric.revenue).label("revenue"),
        func.sum(GAMMetric.impressions).label("impressions"),
        func.sum(GAMMetric.clicks).label("clicks"),
        func.sum(GAMMetric.ad_requests).label("ad_requests"),
        func.sum(GAMMetric.matched_requests).label("matched_requests")
    ).filter(
        GAMMetric.domain == domain,
        GAMMetric.date == source_date
    ).group_by(GAMMetric.device_category).all()

    summary_devices_raw = {}
    for sdr in summary_dev_rows:
        dev_cat = (sdr.device_category or "mobile").lower()
        dev_rev = sdr.revenue or 0.0
        dev_imps = sdr.impressions or 0
        dev_ad_reqs = sdr.ad_requests or 0
        dev_matched_reqs = sdr.matched_requests or 0
        dev_mr = round((dev_matched_reqs / dev_ad_reqs * 100.0), 1) if dev_ad_reqs > 0 else 0.0
        dev_ecpm = round((dev_rev / dev_imps * 1000.0), 2) if dev_imps > 0 else 0.0
        summary_devices_raw[dev_cat] = {
            "match_rate": dev_mr,
            "ecpm": dev_ecpm
        }
    summary_devices = ensure_devices(
        summary_devices_raw,
        fmt_today_map=summary_fmt_today_map,
        hist_dict=hist_summary_dev_map,
        hist_fmt_map=hist_summary_fmt_map
    )

    # Query real GAM country metrics from DB for the specified domain
    target_c_date = source_date
    db_country_rows = db.query(
        GAMCountryMetric.country,
        GAMCountryMetric.country_code,
        GAMCountryMetric.pricing_rule_name,
        func.sum(GAMCountryMetric.revenue).label("revenue"),
        func.sum(GAMCountryMetric.impressions).label("impressions"),
        func.sum(GAMCountryMetric.clicks).label("clicks"),
        func.sum(GAMCountryMetric.ad_requests).label("ad_requests"),
        func.sum(GAMCountryMetric.matched_requests).label("matched_requests")
    ).filter(
        func.lower(GAMCountryMetric.domain) == domain.lower(),
        GAMCountryMetric.date == source_date
    ).group_by(GAMCountryMetric.country, GAMCountryMetric.country_code, GAMCountryMetric.pricing_rule_name).all()

    if not db_country_rows:
        latest_c_date = db.query(func.max(GAMCountryMetric.date)).filter(
            func.lower(GAMCountryMetric.domain) == domain.lower()
        ).scalar()
        if latest_c_date:
            target_c_date = latest_c_date
            db_country_rows = db.query(
                GAMCountryMetric.country,
                GAMCountryMetric.country_code,
                GAMCountryMetric.pricing_rule_name,
                func.sum(GAMCountryMetric.revenue).label("revenue"),
                func.sum(GAMCountryMetric.impressions).label("impressions"),
                func.sum(GAMCountryMetric.clicks).label("clicks"),
                func.sum(GAMCountryMetric.ad_requests).label("ad_requests"),
                func.sum(GAMCountryMetric.matched_requests).label("matched_requests")
            ).filter(
                func.lower(GAMCountryMetric.domain) == domain.lower(),
                GAMCountryMetric.date == latest_c_date
            ).group_by(GAMCountryMetric.country, GAMCountryMetric.country_code, GAMCountryMetric.pricing_rule_name).all()

    # Query per-device breakdown per country & ad_unit
    db_c_p_d_rows = db.query(
        GAMCountryMetric.country,
        GAMCountryMetric.ad_unit,
        GAMCountryMetric.device_category,
        func.sum(GAMCountryMetric.revenue).label("revenue"),
        func.sum(GAMCountryMetric.impressions).label("impressions"),
        func.sum(GAMCountryMetric.ad_requests).label("ad_requests"),
        func.sum(GAMCountryMetric.matched_requests).label("matched_requests")
    ).filter(
        func.lower(GAMCountryMetric.domain) == domain.lower(),
        GAMCountryMetric.date == target_c_date
    ).group_by(GAMCountryMetric.country, GAMCountryMetric.ad_unit, GAMCountryMetric.device_category).all()

    cpd_map = {}
    for r in db_c_p_d_rows:
        c_name = r.country or "Unknown Region"
        unit = r.ad_unit or "Standard Ad Unit"
        dev_cat = (r.device_category or "mobile").lower()

        if c_name not in cpd_map:
            cpd_map[c_name] = {}
        if unit not in cpd_map[c_name]:
            cpd_map[c_name][unit] = {}

        rev = r.revenue or 0.0
        imps = r.impressions or 0
        ad_reqs = r.ad_requests or 0
        matched_reqs = r.matched_requests or 0
        mr = round((matched_reqs / ad_reqs * 100.0), 1) if ad_reqs > 0 else 0.0
        ecpm = round((rev / imps * 1000.0), 2) if imps > 0 else 0.0

        cpd_map[c_name][unit][dev_cat] = {
            "match_rate": mr,
            "ecpm": ecpm
        }

    # Query format breakdown per country and device for target_c_date
    c_fmt_today_rows = db.query(
        GAMCountryMetric.country,
        GAMCountryMetric.device_category,
        GAMCountryMetric.ad_unit,
        func.sum(GAMCountryMetric.revenue).label("revenue"),
        func.sum(GAMCountryMetric.impressions).label("impressions"),
        func.sum(GAMCountryMetric.ad_requests).label("ad_requests"),
        func.sum(GAMCountryMetric.matched_requests).label("matched_requests")
    ).filter(
        func.lower(GAMCountryMetric.domain) == domain.lower(),
        GAMCountryMetric.date == target_c_date
    ).group_by(GAMCountryMetric.country, GAMCountryMetric.device_category, GAMCountryMetric.ad_unit).all()

    c_fmt_today_map = {}
    for r in c_fmt_today_rows:
        c_name = r.country or "Unknown Region"
        dev_cat = (r.device_category or "mobile").lower()
        fmt = classify_ad_format(r.ad_unit)
        if c_name not in c_fmt_today_map:
            c_fmt_today_map[c_name] = {}
        if dev_cat not in c_fmt_today_map[c_name]:
            c_fmt_today_map[c_name][dev_cat] = {}
        if fmt not in c_fmt_today_map[c_name][dev_cat]:
            c_fmt_today_map[c_name][dev_cat][fmt] = {"rev": 0.0, "imps": 0, "ad_reqs": 0, "matched": 0}
        c_fmt_today_map[c_name][dev_cat][fmt]["rev"] += (r.revenue or 0.0)
        c_fmt_today_map[c_name][dev_cat][fmt]["imps"] += (r.impressions or 0)
        c_fmt_today_map[c_name][dev_cat][fmt]["ad_reqs"] += (r.ad_requests or 0)
        c_fmt_today_map[c_name][dev_cat][fmt]["matched"] += (r.matched_requests or 0)

    # Query device breakdown per country
    db_country_dev_rows = db.query(
        GAMCountryMetric.country,
        GAMCountryMetric.device_category,
        func.sum(GAMCountryMetric.revenue).label("revenue"),
        func.sum(GAMCountryMetric.impressions).label("impressions"),
        func.sum(GAMCountryMetric.clicks).label("clicks"),
        func.sum(GAMCountryMetric.ad_requests).label("ad_requests"),
        func.sum(GAMCountryMetric.matched_requests).label("matched_requests")
    ).filter(
        func.lower(GAMCountryMetric.domain) == domain.lower(),
        GAMCountryMetric.date == target_c_date
    ).group_by(GAMCountryMetric.country, GAMCountryMetric.device_category).all()

    country_device_map = {}
    for cdr in db_country_dev_rows:
        c_name = cdr.country or "Unknown Region"
        dev_cat = (cdr.device_category or "mobile").lower()
        if c_name not in country_device_map:
            country_device_map[c_name] = {}
        c_dev_rev = cdr.revenue or 0.0
        c_dev_imps = cdr.impressions or 0
        c_dev_ad_reqs = cdr.ad_requests or 0
        c_dev_matched_reqs = cdr.matched_requests or 0
        c_dev_mr = round((c_dev_matched_reqs / c_dev_ad_reqs * 100.0), 1) if c_dev_ad_reqs > 0 else 0.0
        c_dev_ecpm = round((c_dev_rev / c_dev_imps * 1000.0), 2) if c_dev_imps > 0 else 0.0
        country_device_map[c_name][dev_cat] = {
            "match_rate": c_dev_mr,
            "ecpm": c_dev_ecpm
        }

    country_map = {}
    for crow in db_country_rows:
        c_name = crow.country or "Unknown Region"
        if c_name not in country_map:
            country_map[c_name] = {
                "country": c_name,
                "country_code": crow.country_code,
                "revenue": 0.0,
                "impressions": 0,
                "clicks": 0,
                "ad_requests": 0,
                "matched_requests": 0,
                "pricing_rule_name": getattr(crow, 'pricing_rule_name', None) or "All Rules"
            }
        c_item = country_map[c_name]
        c_item["revenue"] += (crow.revenue or 0.0)
        c_item["impressions"] += (crow.impressions or 0)
        c_item["clicks"] += (crow.clicks or 0)
        c_item["ad_requests"] += (crow.ad_requests or 0)
        c_item["matched_requests"] += (crow.matched_requests or 0)

        p_rule = getattr(crow, 'pricing_rule_name', None)
        if p_rule in ["(No pricing rule applied)", "(No Pricing Rule Applied)", "No pricing rule applied"]:
            p_rule = "No Rule"
        if p_rule and p_rule not in ["No Rule", "(No Rule)", "All Rules"]:
            c_item["pricing_rule_name"] = p_rule

    countries_list = []
    if country_map:
        from app.services.gam import get_country_meta
        for c_item in country_map.values():
            c_name = c_item["country"]
            c_rev = c_item["revenue"]
            c_imps = c_item["impressions"]
            c_clks = c_item["clicks"]
            c_ad_reqs = c_item["ad_requests"]
            c_matched_reqs = c_item["matched_requests"]

            c_meta = get_country_meta(c_name)
            c_code = c_item["country_code"] or c_meta["code"]
            c_flag = c_meta["flag"]
            p_rule = c_item["pricing_rule_name"]

            if c_matched_reqs == 0 and c_imps > 0:
                c_matched_reqs = c_imps
            if c_ad_reqs < c_matched_reqs and c_matched_reqs > 0:
                c_ad_reqs = c_matched_reqs

            c_mr = round((c_matched_reqs / c_ad_reqs * 100.0), 1) if c_ad_reqs > 0 else 0.0
            c_ecpm = round((c_rev / c_imps * 1000.0), 2) if c_imps > 0 else 0.0
            if apply_dawn_discount and c_ecpm > 0:
                c_ecpm = round(c_ecpm * 0.80, 2)
            if force_soft_target and c_mr > 55.0:
                c_mr = 55.0

            c_dev_dict = ensure_devices(
                country_device_map.get(c_name, {}),
                fmt_today_map=c_fmt_today_map.get(c_name, {}),
                hist_dict=hist_c_dev_map.get(c_name, {}),
                hist_fmt_map=hist_c_fmt_map.get(c_name, {}),
                summary_fallback=summary_devices
            )

            # Nested placements per country
            c_placements_list = []
            if c_name in cpd_map:
                for unit_name, dev_dict in cpd_map[c_name].items():
                    hist_unit_dev = hist_cpd_map.get(c_name, {}).get(unit_name, {})
                    c_placements_list.append({
                        "ad_unit": unit_name,
                        "devices": ensure_devices(
                            dev_dict,
                            hist_dict=hist_unit_dev,
                            country_fallback=c_dev_dict,
                            summary_fallback=summary_devices
                        )
                    })

            countries_list.append({
                "country": c_name,
                "country_code": c_code,
                "flag_emoji": c_flag,
                "match_rate": c_mr,
                "ecpm": c_ecpm,
                "pricing": p_rule,
                "devices": c_dev_dict,
                "placements": c_placements_list
            })

    countries_list.sort(key=lambda x: x["ecpm"], reverse=True)

    # Query global device breakdown per placement for site-wide fallback
    db_placement_dev_rows = db.query(
        GAMMetric.ad_unit,
        GAMMetric.device_category,
        func.sum(GAMMetric.revenue).label("revenue"),
        func.sum(GAMMetric.impressions).label("impressions"),
        func.sum(GAMMetric.clicks).label("clicks"),
        func.sum(GAMMetric.ad_requests).label("ad_requests"),
        func.sum(GAMMetric.matched_requests).label("matched_requests")
    ).filter(
        GAMMetric.domain == domain,
        GAMMetric.date == source_date
    ).group_by(GAMMetric.ad_unit, GAMMetric.device_category).all()

    placement_device_map = {}
    for pdr in db_placement_dev_rows:
        unit = pdr.ad_unit
        dev_cat = (pdr.device_category or "mobile").lower()
        if unit not in placement_device_map:
            placement_device_map[unit] = {}
        p_dev_rev = pdr.revenue or 0.0
        p_dev_imps = pdr.impressions or 0
        p_dev_ad_reqs = pdr.ad_requests or 0
        p_dev_matched_reqs = pdr.matched_requests or 0
        p_dev_mr = round((p_dev_matched_reqs / p_dev_ad_reqs * 100.0), 1) if p_dev_ad_reqs > 0 else 0.0
        p_dev_ecpm = round((p_dev_rev / p_dev_imps * 1000.0), 2) if p_dev_imps > 0 else 0.0
        placement_device_map[unit][dev_cat] = {
            "match_rate": p_dev_mr,
            "ecpm": p_dev_ecpm
        }

    placements_rows = db.query(
        GAMMetric.ad_unit,
        func.sum(GAMMetric.revenue).label("revenue"),
        func.sum(GAMMetric.impressions).label("impressions"),
        func.sum(GAMMetric.clicks).label("clicks"),
        func.sum(GAMMetric.ad_requests).label("ad_requests"),
        func.sum(GAMMetric.matched_requests).label("matched_requests")
    ).filter(
        GAMMetric.domain == domain,
        GAMMetric.date == source_date
    ).group_by(GAMMetric.ad_unit).all()

    placements_list = []
    for pr in placements_rows:
        p_rev = pr.revenue or 0.0
        p_imps = pr.impressions or 0
        p_ad_reqs = pr.ad_requests or 0
        p_matched_reqs = pr.matched_requests or 0
        p_ecpm = round((p_rev / p_imps * 1000.0), 2) if p_imps > 0 else 0.0
        p_mr = round((p_matched_reqs / p_ad_reqs * 100.0), 1) if p_ad_reqs > 0 else domain_mr
        if apply_dawn_discount and p_ecpm > 0:
            p_ecpm = round(p_ecpm * 0.80, 2)
        if force_soft_target and p_mr > 55.0:
            p_mr = 55.0

        p_fmt = classify_ad_format(pr.ad_unit)
        if p_fmt == "int" and 0 < p_mr < 75.0:
            p_mr = 50.0
            if p_ecpm > 0:
                p_ecpm = round(p_ecpm * 0.90, 2)

        placements_list.append({
            "ad_unit": pr.ad_unit,
            "match_rate": p_mr,
            "ecpm": p_ecpm,
            "devices": ensure_devices(
                placement_device_map.get(pr.ad_unit, {}),
                summary_fallback=summary_devices
            )
        })

    countries_compressed = {}
    for c_item in countries_list:
        code = c_item.get("country_code")
        if code:
            countries_compressed[code] = c_item.get("devices", {})

    data_payload = {
        "domain": domain,
        "date": today_str,
        "source_date": source_date.strftime("%Y-%m-%d"),
        "pricing_strategy": decision_mode,
        "updated_at": wib_now.strftime("%Y-%m-%d %H:%M:%S WIB"),
        "summary": summary_devices,
        "countries": countries_compressed
    }

    # Fetch Ad-Unit Pricing Overrides for this domain
    overrides_payload = {}
    try:
        from app.models import AdUnitPricingConfig
        active_overrides = db.query(AdUnitPricingConfig).filter(
            func.lower(AdUnitPricingConfig.domain) == domain.lower(),
            AdUnitPricingConfig.is_active == True,
            AdUnitPricingConfig.pricing_mode != 'auto'
        ).all()
        for ov in active_overrides:
            cc = ov.country_code.upper()
            unit = ov.ad_unit
            dev = (ov.device_category or "mobile").lower()
            if ov.pricing_mode == "target_mr":
                if cc not in overrides_payload:
                    overrides_payload[cc] = {}
                if unit not in overrides_payload[cc]:
                    overrides_payload[cc][unit] = {}
                overrides_payload[cc][unit][dev] = {
                    "mode": ov.pricing_mode,
                    "mr": ov.target_mr or 65.0
                }
            else:
                key = ov.target_floor_key if ov.pricing_mode == "target_floor" else (ov.target_key or (str(ov.target_cpm) if ov.target_cpm else None))
                if key:
                    if cc not in overrides_payload:
                        overrides_payload[cc] = {}
                    if unit not in overrides_payload[cc]:
                        overrides_payload[cc][unit] = {}
                    overrides_payload[cc][unit][dev] = {
                        "mode": ov.pricing_mode,
                        "key": key
                    }
    except Exception as e:
        logger.warning(f"Error querying overrides for {domain}: {e}")

    if overrides_payload:
        data_payload["overrides"] = overrides_payload

    try:
        atomic_write_json(target_filepath, data_payload)
        logger.info(f"Auto-exported today's data (atomic) for {domain} to {target_filepath}")
    except Exception as e:
        logger.warning(f"Failed to export JSON to {target_filepath}: {e}")

DEFAULT_PRICING_CONFIG = {
    "target_mr": 65.0,
    "emergency_mr_threshold": 15.0,
    "default_pricing": "google_optimize",
    "device_settings": {
        "desktop": {
            "cpm_multiplier": 1.25,
            "min_floor": 10000
        },
        "mobile": {
            "cpm_multiplier": 1.0,
            "min_floor": 5000
        }
    },
    "format_settings": {
        "interstitial": {
            "multiplier": 1.1,
            "high_mr_threshold": 75.0,
            "emergency_mr_threshold": 50.0
        },
        "anchor": {
            "multiplier": 1.1,
            "high_mr_threshold": 65.0,
            "emergency_mr_threshold": 35.0
        },
        "banner": {
            "multiplier": 1.05,
            "high_mr_threshold": 70.0,
            "emergency_mr_threshold": 30.0
        }
    },
    "adjustments": {
        "high_mr_threshold": 85.0,
        "high_mr_boost_pct": 25.0,
        "med_mr_threshold": 50.0,
        "med_mr_boost_pct": 10.0,
        "low_mr_threshold": 40.0,
        "low_mr_penalty_pct": -15.0
    },
    "rules": [
        { "cpm": 5000,   "target_key": "5000",   "floor_key": "f4000" },
        { "cpm": 7500,   "target_key": "7500",   "floor_key": "f7000" },
        { "cpm": 10000,  "target_key": "10000",  "floor_key": "f9000" },
        { "cpm": 12500,  "target_key": "12500",  "floor_key": "f12000" },
        { "cpm": 15000,  "target_key": "15000",  "floor_key": "f15000" },
        { "cpm": 17500,  "target_key": "17500",  "floor_key": "f17000" },
        { "cpm": 20000,  "target_key": "20000",  "floor_key": "f20000" },
        { "cpm": 22500,  "target_key": "22500",  "floor_key": "f23000" },
        { "cpm": 25000,  "target_key": "25000",  "floor_key": "f25000" },
        { "cpm": 30000,  "target_key": "30000",  "floor_key": "f27000" },
        { "cpm": 35000,  "target_key": "35000",  "floor_key": "f30000" },
        { "cpm": 40000,  "target_key": "40000",  "floor_key": "f35000" },
        { "cpm": 45000,  "target_key": "45000",  "floor_key": "f40000" },
        { "cpm": 50000,  "target_key": "50000",  "floor_key": "f45000" },
        { "cpm": 55000,  "target_key": "55000",  "floor_key": "f50000" },
        { "cpm": 60000,  "target_key": "60000",  "floor_key": "f55000" },
        { "cpm": 65000,  "target_key": "65000",  "floor_key": "f60000" },
        { "cpm": 70000,  "target_key": "70000",  "floor_key": "f65000" },
        { "cpm": 75000,  "target_key": "75000",  "floor_key": "f70000" },
        { "cpm": 80000,  "target_key": "80000",  "floor_key": "f75000" },
        { "cpm": 100000, "target_key": "100000", "floor_key": "f80000" },
        { "cpm": 130000, "target_key": "130000", "floor_key": "f100000" },
        { "cpm": 155000, "target_key": "155000", "floor_key": "f125000" },
        { "cpm": 200000, "target_key": "200000", "floor_key": "f160000" },
        { "cpm": 350000, "target_key": "350000", "floor_key": "f280000" },
        { "cpm": 525000, "target_key": "525000", "floor_key": "f420000" },
        { "cpm": 700000, "target_key": "700000", "floor_key": "f560000" }
    ]
}

def get_master_pricing_config_path() -> str:
    vps_path = "/home/mbummm/web/admin.mbelik.com/public_html/pricing_config.json"
    if os.path.exists(os.path.dirname(vps_path)):
        return vps_path
    
    from app.config import BASE_DIR
    local_path = os.path.abspath(os.path.join(BASE_DIR, "../public_html/pricing_config.json"))
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    return local_path

def load_pricing_config() -> dict:
    master_path = get_master_pricing_config_path()
    if os.path.exists(master_path):
        try:
            with open(master_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "rules" in data:
                    return data
        except Exception as e:
            logger.warning(f"Error loading {master_path}: {e}")
    
    # Save default if file doesn't exist
    save_pricing_config_and_sync(DEFAULT_PRICING_CONFIG, db=None)
    return DEFAULT_PRICING_CONFIG

def save_pricing_config_and_sync(config_dict: dict, db: Session = None) -> list:
    master_path = get_master_pricing_config_path()
    try:
        atomic_write_json(master_path, config_dict)
    except Exception as e:
        logger.warning(f"Failed writing master pricing_config.json to {master_path}: {e}")

    synced_paths = [master_path]

    if db is not None:
        try:
            from app.models import JSONExportTarget
            targets = db.query(JSONExportTarget).filter(JSONExportTarget.is_active == True).all()
            for t in targets:
                target_dir = os.path.dirname(t.target_filepath)
                dest_path = os.path.join(target_dir, "pricing_config.json")

                domain_cfg = dict(config_dict)
                domain_cfg["domain"] = t.domain
                domain_cfg["conversion"] = {
                    "enabled": bool(t.conversion_enabled),
                    "send_to": t.conversion_send_to or "",
                    "currency": t.conversion_currency or "IDR",
                    "value_tiers": {
                        "1": t.pv1_value if t.pv1_value is not None else 0.0,
                        "2": t.pv2_value if t.pv2_value is not None else 1000.0,
                        "3": t.pv3_value if t.pv3_value is not None else 3000.0,
                        "4": t.pv4_value if t.pv4_value is not None else 6000.0
                    }
                }
                domain_cfg["ad_units"] = {
                    "header": t.slot_header or f"/22806125615/{t.domain}.Header",
                    "feed": t.slot_feed or f"/22806125615/{t.domain}.Feed",
                    "side": t.slot_side1 or f"/22806125615/{t.domain}.Sidebar",
                    "side2": t.slot_side2 or f"/22806125615/{t.domain}.Sidebar2",
                    "interstitial": t.slot_interstitial or f"/22806125615/{t.domain}.Interstitial",
                    "anchor": t.slot_anchor or f"/22806125615/{t.domain}.Sticky"
                }

                try:
                    atomic_write_json(dest_path, domain_cfg)
                    synced_paths.append(dest_path)
                except Exception as e:
                    logger.warning(f"Failed syncing pricing_config.json to {dest_path}: {e}")
        except Exception as e:
            logger.warning(f"Error querying export targets for pricing_config sync: {e}")

    return synced_paths

sync_service = SyncService()


