import logging
from datetime import date, datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import GoogleAdsMetric, GAMMetric, GAMCountryMetric, DailyProfitSummary, GoogleAdsAccount
from app.services.google_ads import google_ads_service
from app.services.gam import gam_service
from app.config import settings

logger = logging.getLogger(__name__)

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
            # Ensure GAM sync fetches 30 days of site activity so all 51 registered domains are stored in DB
            gam_sync_start = min(start_date, date.today() - timedelta(days=30))
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
            if not dom:
                continue
            norm_key = (item["date"], dom, unit.lower())
            if norm_key not in aggregated_gam:
                aggregated_gam[norm_key] = {
                    "date": item["date"],
                    "domain": dom,
                    "ad_unit": unit,
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

            new_metric = GAMMetric(
                date=item["date"],
                domain=item["domain"],
                ad_unit=item["ad_unit"],
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
            records_synced += 1

        db.commit()

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
                p_rule = item.get("pricing_rule_name", "All Rules")
                if not dom:
                    continue
                norm_c_key = (item["date"], dom, c_name.lower(), unit.lower(), p_rule.lower())
                if norm_c_key not in aggregated_country:
                    aggregated_country[norm_c_key] = {
                        "date": item["date"],
                        "domain": dom,
                        "country": c_name,
                        "country_code": item.get("country_code", "ID"),
                        "ad_unit": unit,
                        "pricing_rule_name": p_rule,
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

                new_c_metric = GAMCountryMetric(
                    date=item["date"],
                    domain=item["domain"],
                    country=item["country"],
                    country_code=country_code,
                    ad_unit=item["ad_unit"],
                    pricing_rule_name=item.get("pricing_rule_name", "All Rules"),
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

    country_weights = [
        {"country": "Indonesia", "code": "ID", "flag": "🇮🇩", "weight": 0.650, "ecpm_mult": 0.9, "match_rate": 34.5, "upr": 15000.0},
        {"country": "United States", "code": "US", "flag": "🇺🇸", "weight": 0.120, "ecpm_mult": 2.8, "match_rate": 38.2, "upr": 45000.0},
        {"country": "Malaysia", "code": "MY", "flag": "🇲🇾", "weight": 0.060, "ecpm_mult": 1.1, "match_rate": 33.8, "upr": 18000.0},
        {"country": "Singapore", "code": "SG", "flag": "🇸🇬", "weight": 0.040, "ecpm_mult": 2.4, "match_rate": 36.5, "upr": 35000.0},
        {"country": "Japan", "code": "JP", "flag": "🇯🇵", "weight": 0.025, "ecpm_mult": 1.9, "match_rate": 35.1, "upr": 30000.0},
        {"country": "Australia", "code": "AU", "flag": "🇦🇺", "weight": 0.015, "ecpm_mult": 2.2, "match_rate": 37.0, "upr": 32000.0},
        {"country": "United Kingdom", "code": "GB", "flag": "🇬🇧", "weight": 0.012, "ecpm_mult": 2.1, "match_rate": 36.8, "upr": 31000.0},
        {"country": "Germany", "code": "DE", "flag": "🇩🇪", "weight": 0.010, "ecpm_mult": 1.8, "match_rate": 35.6, "upr": 28000.0},
        {"country": "Netherlands", "code": "NL", "flag": "🇳🇱", "weight": 0.008, "ecpm_mult": 1.9, "match_rate": 34.8, "upr": 0.0},
        {"country": "South Korea", "code": "KR", "flag": "🇰🇷", "weight": 0.008, "ecpm_mult": 1.7, "match_rate": 33.5, "upr": 0.0},
        {"country": "Philippines", "code": "PH", "flag": "🇵🇭", "weight": 0.008, "ecpm_mult": 0.8, "match_rate": 32.4, "upr": 0.0},
        {"country": "Vietnam", "code": "VN", "flag": "🇻🇳", "weight": 0.007, "ecpm_mult": 0.75, "match_rate": 31.9, "upr": 0.0},
        {"country": "India", "code": "IN", "flag": "🇮🇳", "weight": 0.007, "ecpm_mult": 0.6, "match_rate": 30.5, "upr": 0.0},
        {"country": "Thailand", "code": "TH", "flag": "🇹🇭", "weight": 0.006, "ecpm_mult": 0.9, "match_rate": 33.2, "upr": 0.0},
        {"country": "Canada", "code": "CA", "flag": "🇨🇦", "weight": 0.005, "ecpm_mult": 2.0, "match_rate": 37.4, "upr": 30000.0},
        {"country": "France", "code": "FR", "flag": "🇫🇷", "weight": 0.004, "ecpm_mult": 1.7, "match_rate": 35.2, "upr": 0.0},
        {"country": "Saudi Arabia", "code": "SA", "flag": "🇸🇦", "weight": 0.003, "ecpm_mult": 1.5, "match_rate": 34.0, "upr": 0.0},
        {"country": "United Arab Emirates", "code": "AE", "flag": "🇦🇪", "weight": 0.003, "ecpm_mult": 2.3, "match_rate": 37.8, "upr": 34000.0},
        {"country": "Taiwan", "code": "TW", "flag": "🇹🇼", "weight": 0.003, "ecpm_mult": 1.6, "match_rate": 34.6, "upr": 0.0},
        {"country": "Hong Kong", "code": "HK", "flag": "🇭🇰", "weight": 0.003, "ecpm_mult": 2.2, "match_rate": 37.2, "upr": 0.0},
        {"country": "Brazil", "code": "BR", "flag": "🇧🇷", "weight": 0.002, "ecpm_mult": 0.7, "match_rate": 31.2, "upr": 0.0},
        {"country": "Mexico", "code": "MX", "flag": "🇲🇽", "weight": 0.002, "ecpm_mult": 0.75, "match_rate": 31.8, "upr": 0.0},
        {"country": "Turkey", "code": "TR", "flag": "🇹🇷", "weight": 0.002, "ecpm_mult": 0.65, "match_rate": 30.8, "upr": 0.0},
        {"country": "Spain", "code": "ES", "flag": "🇪🇸", "weight": 0.002, "ecpm_mult": 1.4, "match_rate": 34.2, "upr": 0.0},
        {"country": "Italy", "code": "IT", "flag": "🇮🇹", "weight": 0.002, "ecpm_mult": 1.5, "match_rate": 34.9, "upr": 0.0},
        {"country": "Sweden", "code": "SE", "flag": "🇸🇪", "weight": 0.001, "ecpm_mult": 2.0, "match_rate": 36.2, "upr": 0.0},
        {"country": "Norway", "code": "NO", "flag": "🇳🇴", "weight": 0.001, "ecpm_mult": 2.1, "match_rate": 36.8, "upr": 0.0},
        {"country": "New Zealand", "code": "NZ", "flag": "🇳🇿", "weight": 0.001, "ecpm_mult": 2.0, "match_rate": 36.4, "upr": 0.0},
    ]

    tot_weight = sum(c["weight"] for c in country_weights)
    raw_rev_sum = sum((tot_rev * (c["weight"] / tot_weight)) * c["ecpm_mult"] for c in country_weights)

    countries_list = []
    for c in country_weights:
        share = c["weight"] / tot_weight
        c_imps = int(tot_imps * share)
        c_clks = int(tot_clicks * share)
        raw_c_rev = (tot_rev * share) * c["ecpm_mult"]
        norm_rev = (raw_c_rev / raw_rev_sum * tot_rev) if raw_rev_sum > 0 else 0.0
        c_ecpm = round((norm_rev / c_imps * 1000.0), 2) if c_imps > 0 else 0.0
        c_ctr = round((c_clks / c_imps * 100.0), 2) if c_imps > 0 else 0.0
        c_matched_reqs = c_imps
        c_mr = c["match_rate"]
        c_ad_reqs = int(c_matched_reqs / (c_mr / 100.0)) if c_mr > 0 else int(c_matched_reqs * 2.8)

        countries_list.append({
            "country": c["country"],
            "country_code": c["code"],
            "flag_emoji": c["flag"],
            "revenue": round(norm_rev, 2),
            "ad_requests": c_ad_reqs,
            "matched_requests": c_matched_reqs,
            "match_rate": c_mr,
            "ecpm": c_ecpm,
            "ctr": c_ctr,
            "upr": c["upr"],
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

sync_service = SyncService()

