import os
import json
import logging
from datetime import date, datetime, timedelta


from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import GoogleAdsMetric, GAMMetric, GAMCountryMetric, GoogleAdsCountryMetric, DailyProfitSummary, GoogleAdsAccount

from app.services.google_ads import google_ads_service
from app.services.gam import gam_service
from app.config import settings

import threading

logger = logging.getLogger(__name__)

_sync_lock = threading.Lock()

class SyncService:
    def sync_range(self, db: Session, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Pull Google Ads & GAM metrics for start_date to end_date, update DB cache tables,
        apply +11% tax on Google Ads spend and -8% deduction on GAM AdX revenue,
        and calculate daily profit summaries.
        """
        messages = []
        gads_data = []
        gam_data = []

        try:
            from app.database import Base, engine
            import app.models
            Base.metadata.create_all(bind=engine)
        except Exception as e:
            logger.warning(f"Sync table creation notice: {e}")

        try:
            db_accounts = db.query(GoogleAdsAccount).all()
        except Exception:
            db.rollback()
            db_accounts = []

        cids = [acc.customer_id for acc in db_accounts] if db_accounts else None

        try:
            gads_data = google_ads_service.fetch_daily_metrics(start_date, end_date, customer_ids=cids)
        except Exception as e:
            err_msg = str(e)
            logger.error(f"Google Ads API Error: {err_msg}")
            if "test accounts" in err_msg.lower():
                messages.append("Google Ads: Developer Token masih level Test Account. Ajukan Basic Access di Google Ads API Center untuk akses akun live.")
            else:
                messages.append(f"Google Ads API Error: {err_msg}")

        try:
            gam_sync_start = start_date
            gam_data = gam_service.fetch_daily_metrics(gam_sync_start, end_date)
        except Exception as e:
            err_msg = str(e)
            logger.error(f"GAM API Error: {err_msg}")
            messages.append(f"GAM API Error: {err_msg}")

        records_synced = 0

        # 1. Deduplicate & Upsert Google Ads metrics (Apply +11% tax adjustment)
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

            existing = db.query(GoogleAdsMetric).filter(
                GoogleAdsMetric.date == item["date"],
                GoogleAdsMetric.customer_id == item["customer_id"],
                GoogleAdsMetric.campaign_name == item["campaign_name"]
            ).first()

            if existing:
                existing.account_name = item["account_name"]
                existing.spend = adj_spend
                existing.impressions = imps
                existing.clicks = clicks
                existing.cpc = adj_cpc
                existing.ctr = ctr
                existing.synced_at = datetime.utcnow()
            else:
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
                    synced_at=datetime.utcnow()
                )
                db.add(new_metric)
            records_synced += 1

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"GoogleAdsMetric commit notice: {e}")

        # 1b. Deduplicate & Upsert Google Ads Country metrics (Apply +11% tax adjustment)

        try:
            gads_country_data = google_ads_service.fetch_country_metrics(start_date, end_date, customer_ids=cids)
            db.query(GoogleAdsCountryMetric).filter(
                GoogleAdsCountryMetric.date >= start_date,
                GoogleAdsCountryMetric.date <= end_date
            ).delete(synchronize_session=False)
            db.commit()

            aggregated_gads_country = {}
            for item in gads_country_data:
                key = (item["date"], item["customer_id"], item["country"])
                if key not in aggregated_gads_country:
                    aggregated_gads_country[key] = {
                        "date": item["date"],
                        "customer_id": item["customer_id"],
                        "country": item["country"],
                        "country_code": item.get("country_code", "ID"),
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
                    spend=adj_spend,
                    impressions=item["impressions"],
                    clicks=item["clicks"],
                    synced_at=datetime.utcnow()
                )
                db.add(new_c_gads)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Sync Google Ads Country Metrics notice: {e}")

        # 2. Delete stale GAM metrics for target sync range and insert fresh live GAM API data
        db.query(GAMMetric).filter(
            GAMMetric.date >= gam_sync_start,
            GAMMetric.date <= end_date
        ).delete(synchronize_session=False)
        db.commit()


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

        for item in aggregated_gam.values():
            raw_rev = item.get("revenue", 0.0)
            adj_rev = round(raw_rev * 0.92, 2)  # Deducts 8% fee
            imps = item.get("impressions", 0)
            clicks = item.get("clicks", 0)
            adj_ecpm = round((adj_rev / imps) * 1000.0, 2) if imps > 0 else 0.0

            ad_reqs = item.get("ad_requests", 0)
            matched_reqs = item.get("matched_requests", 0)
            mr = (matched_reqs / ad_reqs * 100.0) if ad_reqs > 0 else 0.0

            try:
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
                    synced_at=datetime.utcnow()
                )
                db.add(new_metric)
                db.commit()
                records_synced += 1
            except Exception as e:
                db.rollback()

        # 3. Delete stale GAM country metrics for target sync range and insert fresh live GAM country data
        try:
            gam_country_data = gam_service.fetch_country_metrics(start_date, end_date)
            
            db.query(GAMCountryMetric).filter(
                GAMCountryMetric.date >= start_date,
                GAMCountryMetric.date <= end_date
            ).delete(synchronize_session=False)
            db.commit()

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

                try:
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
                        synced_at=datetime.utcnow()
                    )
                    db.add(new_c_metric)
                    db.commit()
                except Exception as e:
                    db.rollback()
        except Exception as e:
            db.rollback()
            logger.warning(f"Sync GAM Country Metrics notice: {e}")

        # 3. Calculate daily profit summaries per date in the range
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
                summary.synced_at = datetime.utcnow()
            else:
                summary = DailyProfitSummary(
                    date=curr_date,
                    total_spend=round(gads_spend, 2),
                    total_revenue=round(gam_rev, 2),
                    net_profit=round(net_profit, 2),
                    roi=round(roi, 2),
                    profit_margin=round(margin, 2),
                    synced_at=datetime.utcnow()
                )
                db.add(summary)

            curr_date += timedelta(days=1)

        db.commit()

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
        message_str = " | ".join(messages) if messages else f"Berhasil menyinkronkan data dari {start_date} hingga {end_date}"

        return {
            "status": status_str,
            "message": message_str,
            "records_synced": records_synced,
            "sync_date_start": start_date.strftime("%Y-%m-%d"),
            "sync_date_end": end_date.strftime("%Y-%m-%d"),
            "is_mock_data": google_ads_service.use_mock or gam_service.use_mock
        }

def export_site_today_json(
    db: Session,
    domain: str = "spotgames.top",
    target_filepath: str = "/home/mbummm/web/spotgames.top/public_html/current_pricing.json",
    start_hour: int = 10,
    end_hour: int = 23,
    force: bool = False
):
    import os
    import json
    from datetime import timezone

    WIB = timezone(timedelta(hours=7))
    wib_now = datetime.now(WIB)
    current_hour = wib_now.hour

    # Jam operasional auto-export: Pukul 10:00 pagi s/d 23:00 malam WIB
    if not force and not (start_hour <= current_hour <= end_hour):
        logger.info(f"Auto-export JSON untuk {domain} dilewati (di luar jam operasional {start_hour}:00 - {end_hour}:00 WIB). Jam saat ini: {wib_now.strftime('%H:%M WIB')}")
        return

    today_date = wib_now.date()
    today_str = today_date.strftime("%Y-%m-%d")

    # Fetch GAM metrics for domain today
    gam_row = db.query(
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

    # Query real GAM country metrics from DB for the specified domain
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
        GAMCountryMetric.date == today_date
    ).group_by(GAMCountryMetric.country, GAMCountryMetric.country_code, GAMCountryMetric.pricing_rule_name).all()

    if not db_country_rows:
        latest_c_date = db.query(func.max(GAMCountryMetric.date)).filter(
            func.lower(GAMCountryMetric.domain) == domain.lower()
        ).scalar()
        if latest_c_date:
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
            c_ctr = round((c_clks / c_imps * 100.0), 2) if c_imps > 0 else 0.0

            countries_list.append({
                "country": c_name,
                "country_code": c_code,
                "flag_emoji": c_flag,
                "revenue": round(c_rev, 2),
                "ad_requests": int(c_ad_reqs),
                "matched_requests": int(c_matched_reqs),
                "match_rate": c_mr,
                "ecpm": c_ecpm,
                "ctr": c_ctr,
                "pricing": p_rule,
                "rpm": c_ecpm
            })

    countries_list.sort(key=lambda x: x["revenue"], reverse=True)

    placements_rows = db.query(
        GAMMetric.ad_unit,
        func.sum(GAMMetric.revenue).label("revenue"),
        func.sum(GAMMetric.impressions).label("impressions"),
        func.sum(GAMMetric.clicks).label("clicks"),
        func.sum(GAMMetric.ad_requests).label("ad_requests"),
        func.sum(GAMMetric.matched_requests).label("matched_requests")
    ).filter(
        GAMMetric.domain == domain,
        GAMMetric.date == today_date
    ).group_by(GAMMetric.ad_unit).all()

    placements_list = []
    for pr in placements_rows:
        p_rev = pr.revenue or 0.0
        p_imps = pr.impressions or 0
        p_clks = pr.clicks or 0
        p_ad_reqs = pr.ad_requests or 0
        p_matched_reqs = pr.matched_requests or 0
        p_ecpm = round((p_rev / p_imps * 1000.0), 2) if p_imps > 0 else 0.0
        p_mr = round((p_matched_reqs / p_ad_reqs * 100.0), 1) if p_ad_reqs > 0 else domain_mr

        placements_list.append({
            "ad_unit": pr.ad_unit,
            "revenue": round(p_rev, 2),
            "ad_requests": p_ad_reqs,
            "matched_requests": p_matched_reqs,
            "match_rate": p_mr,
            "ecpm": p_ecpm,
            "clicks": p_clks
        })

    data_payload = {
        "domain": domain,
        "date": today_str,
        "updated_at": wib_now.strftime("%Y-%m-%d %H:%M:%S WIB"),
        "summary": {
            "total_revenue": round(tot_rev, 2),
            "total_impressions": tot_imps,
            "total_clicks": tot_clicks,
            "ad_requests": tot_ad_reqs,
            "matched_requests": tot_matched_reqs,
            "match_rate": domain_mr,
            "ecpm": ecpm
        },
        "countries": countries_list,
        "placements": placements_list
    }

    try:
        os.makedirs(os.path.dirname(target_filepath), exist_ok=True)
        with open(target_filepath, "w", encoding="utf-8") as f:
            json.dump(data_payload, f, indent=2, ensure_ascii=False)
        try:
            os.chmod(target_filepath, 0o666)
        except Exception:
            pass
        logger.info(f"Auto-exported today's data for {domain} to {target_filepath}")
    except Exception as e:
        logger.warning(f"Failed to export JSON to {target_filepath}: {e}")

DEFAULT_PRICING_CONFIG = {
    "target_mr": 65.0,
    "default_pricing": "google_optimize",
    "adjustments": {
        "high_mr_threshold": 85.0,
        "high_mr_boost_pct": 25.0,
        "med_mr_threshold": 70.0,
        "med_mr_boost_pct": 10.0,
        "low_mr_threshold": 50.0,
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
        { "cpm": 70000,  "target_key": "70000",  "floor_key": "f60000" },
        { "cpm": 75000,  "target_key": "75000",  "floor_key": "f60000" },
        { "cpm": 80000,  "target_key": "80000",  "floor_key": "f60000" },
        { "cpm": 100000, "target_key": "100000", "floor_key": "f60000" },
        { "cpm": 130000, "target_key": "130000", "floor_key": "f60000" },
        { "cpm": 155000, "target_key": "155000", "floor_key": "f60000" }
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
    import json
    master_path = get_master_pricing_config_path()
    os.makedirs(os.path.dirname(master_path), exist_ok=True)
    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2, ensure_ascii=False)
    try:
        os.chmod(master_path, 0o666)
    except Exception:
        pass

    synced_paths = [master_path]

    if db is not None:
        try:
            from app.models import JSONExportTarget
            targets = db.query(JSONExportTarget).filter(JSONExportTarget.is_active == True).all()
            for t in targets:
                target_dir = os.path.dirname(t.target_filepath)
                dest_path = os.path.join(target_dir, "pricing_config.json")
                if dest_path != master_path and dest_path not in synced_paths:
                    try:
                        os.makedirs(target_dir, exist_ok=True)
                        with open(dest_path, "w", encoding="utf-8") as f:
                            json.dump(config_dict, f, indent=2, ensure_ascii=False)
                        try:
                            os.chmod(dest_path, 0o666)
                        except Exception:
                            pass
                        synced_paths.append(dest_path)
                    except Exception as e:
                        logger.warning(f"Failed syncing pricing_config.json to {dest_path}: {e}")
        except Exception as e:
            logger.warning(f"Error querying export targets for pricing_config sync: {e}")

    return synced_paths

sync_service = SyncService()


