from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from app.config import settings
from app.database import get_db
from app.models import DailyProfitSummary, GoogleAdsMetric, GAMMetric, GAMCountryMetric, GoogleAdsCountryMetric, User, GoogleAdsAccount, JSONExportTarget

from app.schemas import (
    SummaryMetrics, DailyTrendItem, AccountBreakdownItem, CampaignBreakdownItem,
    SiteBreakdownItem, PlacementBreakdownItem, CountryBreakdownItem
)
from app.services.auth import get_current_user
from app.services.sync import sync_service, _sync_lock
from app.services.gam import gam_service, get_country_meta

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

# WIB Timezone (GMT+7)
WIB = timezone(timedelta(hours=7))

SPEND_HOURLY_WEIGHTS = [
    0.020, 0.015, 0.010, 0.010, 0.010, 0.015,  # 00:00 - 05:00
    0.025, 0.035, 0.045, 0.050, 0.055, 0.060,  # 06:00 - 11:00
    0.065, 0.065, 0.060, 0.060, 0.065, 0.070,  # 12:00 - 17:00
    0.075, 0.070, 0.060, 0.050, 0.035, 0.025   # 18:00 - 23:00
]

REVENUE_HOURLY_WEIGHTS = [
    0.012, 0.008, 0.006, 0.006, 0.007, 0.011,  # 00:00 - 05:00 (lower night eCPM yield)
    0.020, 0.032, 0.045, 0.052, 0.058, 0.064,  # 06:00 - 11:00
    0.072, 0.074, 0.070, 0.068, 0.072, 0.078,  # 12:00 - 17:00 (higher afternoon eCPM yield)
    0.082, 0.075, 0.062, 0.048, 0.030, 0.016   # 18:00 - 23:00 (peak evening yield)
]

HOURLY_WEIGHTS = SPEND_HOURLY_WEIGHTS

def get_wib_today() -> date:
    return datetime.now(WIB).date()

def parse_date_range(start_date: Optional[str], end_date: Optional[str]):
    today = get_wib_today()
    if not start_date:
        d_start = today - timedelta(days=6)  # Default last 7 days in WIB
    else:
        d_start = datetime.strptime(start_date, "%Y-%m-%d").date()

    if not end_date:
        d_end = today
    else:
        d_end = datetime.strptime(end_date, "%Y-%m-%d").date()

    return d_start, d_end

import threading

def _run_bg_sync(start_date: date, end_date: date):
    if not _sync_lock.acquire(blocking=False):
        return  # Another sync is already running, skip duplicate
    try:
        from app.database import SessionLocal
        bg_db = SessionLocal()
        try:
            sync_service.sync_range(bg_db, start_date, end_date)
        finally:
            bg_db.close()
    except Exception as e:
        print(f"Background sync notice: {e}")
    finally:
        _sync_lock.release()

def ensure_data_synced(db: Session, start_date: date, end_date: date):
    try:
        min_c_date = db.query(func.min(GAMCountryMetric.date)).filter(
            GAMCountryMetric.date >= start_date,
            GAMCountryMetric.date <= end_date
        ).scalar()
        max_c_date = db.query(func.max(GAMCountryMetric.date)).filter(
            GAMCountryMetric.date >= start_date,
            GAMCountryMetric.date <= end_date
        ).scalar()
        
        if not min_c_date or min_c_date > start_date or max_c_date < end_date:
            threading.Thread(target=_run_bg_sync, args=(start_date, end_date), daemon=True).start()
        else:
            latest_sync = db.query(func.max(GAMMetric.synced_at)).filter(
                GAMMetric.date >= start_date,
                GAMMetric.date <= end_date
            ).scalar()
            if not latest_sync or (datetime.utcnow() - latest_sync).total_seconds() > 600:
                threading.Thread(target=_run_bg_sync, args=(start_date, end_date), daemon=True).start()
    except Exception as e:
        db.rollback()
        logger.warning(f"ensure_data_synced notice: {e}")

@router.get("/summary", response_model=SummaryMetrics)
def get_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    device: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    d_start, d_end = parse_date_range(start_date, end_date)
    ensure_data_synced(db, d_start, d_end)

    dev_filter = device.lower().strip() if device and device.lower().strip() != "all" else None

    tot_spend_raw = db.query(func.sum(GoogleAdsMetric.spend)).filter(
        GoogleAdsMetric.date >= d_start, GoogleAdsMetric.date <= d_end
    ).scalar() or 0.0

    gam_q = db.query(func.sum(GAMMetric.revenue)).filter(
        GAMMetric.date >= d_start, GAMMetric.date <= d_end
    )
    if dev_filter:
        gam_q = gam_q.filter(GAMMetric.device_category == dev_filter)
    tot_revenue = gam_q.scalar() or 0.0

    if dev_filter:
        tot_all_imps = db.query(func.sum(GAMMetric.impressions)).filter(
            GAMMetric.date >= d_start, GAMMetric.date <= d_end
        ).scalar() or 0
        tot_dev_imps = db.query(func.sum(GAMMetric.impressions)).filter(
            GAMMetric.date >= d_start, GAMMetric.date <= d_end,
            GAMMetric.device_category == dev_filter
        ).scalar() or 0
        ratio = (tot_dev_imps / tot_all_imps) if tot_all_imps > 0 else 0.5
        tot_spend = tot_spend_raw * ratio
    else:
        tot_spend = tot_spend_raw

    net_profit = tot_revenue - tot_spend
    roi = (tot_revenue / tot_spend * 100.0) if tot_spend > 0 else 0.0
    profit_margin = (net_profit / tot_revenue * 100.0) if tot_revenue > 0 else 0.0

    # Calculate Previous Period metrics for Day-over-Day or Period-over-Period comparison
    wib_now = datetime.now(WIB)
    wib_today = wib_now.date()

    if d_start == d_end:
        prev_date = d_start - timedelta(days=1)
        prev_day_spend_raw = db.query(func.sum(GoogleAdsMetric.spend)).filter(GoogleAdsMetric.date == prev_date).scalar() or 0.0
        
        prev_gam_q = db.query(func.sum(GAMMetric.revenue)).filter(GAMMetric.date == prev_date)
        if dev_filter:
            prev_gam_q = prev_gam_q.filter(GAMMetric.device_category == dev_filter)
        prev_day_revenue = prev_gam_q.scalar() or 0.0

        if dev_filter:
            prev_all_imps = db.query(func.sum(GAMMetric.impressions)).filter(GAMMetric.date == prev_date).scalar() or 0
            prev_dev_imps = db.query(func.sum(GAMMetric.impressions)).filter(
                GAMMetric.date == prev_date, GAMMetric.device_category == dev_filter
            ).scalar() or 0
            prev_ratio = (prev_dev_imps / prev_all_imps) if prev_all_imps > 0 else 0.5
            prev_day_spend = prev_day_spend_raw * prev_ratio
        else:
            prev_day_spend = prev_day_spend_raw

        if d_start == wib_today:
            curr_h = wib_now.hour
            active_spend_sum = sum(SPEND_HOURLY_WEIGHTS[:curr_h + 1]) if curr_h >= 0 else 1.0
            active_rev_sum = sum(REVENUE_HOURLY_WEIGHTS[:curr_h + 1]) if curr_h >= 0 else 1.0
            if active_spend_sum <= 0:
                active_spend_sum = 1.0
            if active_rev_sum <= 0:
                active_rev_sum = 1.0

            prev_spend = prev_day_spend * active_spend_sum
            prev_revenue = prev_day_revenue * active_rev_sum
            comp_label = "vs yesterday same time"
        else:
            prev_spend = prev_day_spend
            prev_revenue = prev_day_revenue
            comp_label = "vs yesterday"
    else:
        days_count = (d_end - d_start).days + 1
        prev_start = d_start - timedelta(days=days_count)
        prev_end = d_start - timedelta(days=1)

        prev_spend_raw = db.query(func.sum(GoogleAdsMetric.spend)).filter(
            GoogleAdsMetric.date >= prev_start, GoogleAdsMetric.date <= prev_end
        ).scalar() or 0.0

        prev_gam_q = db.query(func.sum(GAMMetric.revenue)).filter(
            GAMMetric.date >= prev_start, GAMMetric.date <= prev_end
        )
        if dev_filter:
            prev_gam_q = prev_gam_q.filter(GAMMetric.device_category == dev_filter)
        prev_revenue = prev_gam_q.scalar() or 0.0

        if dev_filter:
            prev_all_imps = db.query(func.sum(GAMMetric.impressions)).filter(
                GAMMetric.date >= prev_start, GAMMetric.date <= prev_end
            ).scalar() or 0
            prev_dev_imps = db.query(func.sum(GAMMetric.impressions)).filter(
                GAMMetric.date >= prev_start, GAMMetric.date <= prev_end,
                GAMMetric.device_category == dev_filter
            ).scalar() or 0
            prev_ratio = (prev_dev_imps / prev_all_imps) if prev_all_imps > 0 else 0.5
            prev_spend = prev_spend_raw * prev_ratio
        else:
            prev_spend = prev_spend_raw

        comp_label = f"vs previous {days_count} days"

    prev_profit = prev_revenue - prev_spend
    prev_roi = (prev_revenue / prev_spend * 100.0) if prev_spend > 0 else 0.0

    def calc_pct_change(curr, prev):
        if prev > 0:
            return round(((curr - prev) / prev) * 100.0, 1)
        elif prev < 0:
            return round(((curr - prev) / abs(prev)) * 100.0, 1)
        elif curr > 0:
            return 100.0
        else:
            return 0.0

    spend_change_pct = calc_pct_change(tot_spend, prev_spend)
    revenue_change_pct = calc_pct_change(tot_revenue, prev_revenue)
    profit_change_pct = calc_pct_change(net_profit, prev_profit)
    roi_change_pct = round(roi - prev_roi, 1)

    last_sync_utc = db.query(func.max(GAMMetric.synced_at)).scalar()
    if not last_sync_utc:
        last_sync_utc = db.query(func.max(GoogleAdsMetric.synced_at)).scalar()

    if last_sync_utc:
        last_sync_wib = last_sync_utc + timedelta(hours=7)
        last_synced_str = last_sync_wib.strftime("%d %b %Y, %H:%M WIB")
    else:
        last_synced_str = datetime.now(WIB).strftime("%d %b %Y, %H:%M WIB")

    return SummaryMetrics(
        total_spend=round(tot_spend, 2),
        total_revenue=round(tot_revenue, 2),
        net_profit=round(net_profit, 2),
        roi=round(roi, 2),
        profit_margin=round(profit_margin, 2),
        period_start=d_start.strftime("%Y-%m-%d"),
        period_end=d_end.strftime("%Y-%m-%d"),
        currency=settings.CURRENCY,
        last_synced_at=last_synced_str,
        spend_change_pct=spend_change_pct,
        revenue_change_pct=revenue_change_pct,
        profit_change_pct=profit_change_pct,
        roi_change_pct=roi_change_pct,
        comparison_period_label=comp_label
    )

@router.get("/trend", response_model=List[DailyTrendItem])
def get_daily_trend(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    device: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    d_start, d_end = parse_date_range(start_date, end_date)
    ensure_data_synced(db, d_start, d_end)

    dev_filter = device.lower().strip() if device and device.lower().strip() != "all" else None

    # Intraday Hourly Trend Breakdown for Single Day filters (Today or Yesterday) in WIB (GMT+7)
    if d_start == d_end:
        tot_spend_raw = db.query(func.sum(GoogleAdsMetric.spend)).filter(
            GoogleAdsMetric.date == d_start
        ).scalar() or 0.0

        gam_q = db.query(func.sum(GAMMetric.revenue)).filter(GAMMetric.date == d_start)
        if dev_filter:
            gam_q = gam_q.filter(GAMMetric.device_category == dev_filter)
        tot_revenue = gam_q.scalar() or 0.0

        if dev_filter:
            tot_all_rev = db.query(func.sum(GAMMetric.revenue)).filter(GAMMetric.date == d_start).scalar() or 0.0
            ratio = (tot_revenue / tot_all_rev) if tot_all_rev > 0 else 0.5
            tot_spend = tot_spend_raw * ratio
        else:
            tot_spend = tot_spend_raw

        wib_now = datetime.now(WIB)
        is_today = (d_start == wib_now.date())
        current_hour = wib_now.hour if is_today else 23

        active_spend_sum = sum(SPEND_HOURLY_WEIGHTS[:current_hour + 1]) if current_hour >= 0 else 1.0
        if active_spend_sum <= 0:
            active_spend_sum = 1.0

        active_rev_sum = sum(REVENUE_HOURLY_WEIGHTS[:current_hour + 1]) if current_hour >= 0 else 1.0
        if active_rev_sum <= 0:
            active_rev_sum = 1.0

        result = []
        for h in range(24):
            hour_str = f"{h:02d}:00"
            if h <= current_hour:
                spend_factor = SPEND_HOURLY_WEIGHTS[h] / active_spend_sum
                rev_factor = REVENUE_HOURLY_WEIGHTS[h] / active_rev_sum
                h_spend = round(tot_spend * spend_factor, 2)
                h_revenue = round(tot_revenue * rev_factor, 2)
                h_profit = round(h_revenue - h_spend, 2)
                h_roi = round((h_revenue / h_spend * 100.0), 2) if h_spend > 0 else 0.0
                h_margin = round((h_profit / h_revenue * 100.0), 2) if h_revenue > 0 else 0.0
            else:
                h_spend = 0.0
                h_revenue = 0.0
                h_profit = 0.0
                h_roi = 0.0
                h_margin = 0.0

            result.append(DailyTrendItem(
                date=hour_str,
                spend=h_spend,
                revenue=h_revenue,
                profit=h_profit,
                roi=h_roi,
                margin=h_margin
            ))
        return result

    # Standard Multi-day Trend Breakdown (Bulk GROUP BY date query)
    ads_rows = db.query(
        GoogleAdsMetric.date,
        func.sum(GoogleAdsMetric.spend).label("spend")
    ).filter(
        GoogleAdsMetric.date >= d_start,
        GoogleAdsMetric.date <= d_end
    ).group_by(GoogleAdsMetric.date).all()
    spend_map = {r.date: r.spend or 0.0 for r in ads_rows}

    gam_q = db.query(
        GAMMetric.date,
        func.sum(GAMMetric.revenue).label("revenue")
    ).filter(
        GAMMetric.date >= d_start,
        GAMMetric.date <= d_end
    )
    if dev_filter:
        gam_q = gam_q.filter(GAMMetric.device_category == dev_filter)
    gam_rows = gam_q.group_by(GAMMetric.date).all()
    rev_map = {r.date: r.revenue or 0.0 for r in gam_rows}

    result = []
    curr_date = d_start
    while curr_date <= d_end:
        day_spend = spend_map.get(curr_date, 0.0)
        day_revenue = rev_map.get(curr_date, 0.0)

        day_profit = day_revenue - day_spend
        day_roi = (day_revenue / day_spend * 100.0) if day_spend > 0 else 0.0
        day_margin = (day_profit / day_revenue * 100.0) if day_revenue > 0 else 0.0

        result.append(DailyTrendItem(
            date=curr_date.strftime("%Y-%m-%d"),
            spend=round(day_spend, 2),
            revenue=round(day_revenue, 2),
            profit=round(day_profit, 2),
            roi=round(day_roi, 2),
            margin=round(day_margin, 2)
        ))
        curr_date += timedelta(days=1)
    return result

@router.get("/accounts", response_model=List[AccountBreakdownItem])
def get_accounts_breakdown(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    device: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    d_start, d_end = parse_date_range(start_date, end_date)
    ensure_data_synced(db, d_start, d_end)

    dev_filter = device.lower().strip() if device and device.lower().strip() != "all" else None

    num_days = (d_end - d_start).days + 1
    prev_end = d_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=num_days - 1)

    wib_now = datetime.now(WIB)
    is_today_only = (d_start == d_end == wib_now.date())
    current_hour = wib_now.hour if is_today_only else 23
    intraday_factor = sum(HOURLY_WEIGHTS[:current_hour + 1]) if is_today_only else 1.0

    comp_label = "vs yesterday same time" if is_today_only else ("vs yesterday" if num_days == 1 else f"vs previous {num_days} days")

    cid_to_domain_map = {
        acc.customer_id: acc.assigned_domain
        for acc in db.query(GoogleAdsAccount).all() if acc.assigned_domain
    }

    prev_spend_rows = db.query(
        GoogleAdsMetric.customer_id,
        func.sum(GoogleAdsMetric.spend).label("spend")
    ).filter(
        GoogleAdsMetric.date >= prev_start,
        GoogleAdsMetric.date <= prev_end
    ).group_by(GoogleAdsMetric.customer_id).all()

    prev_spend_map = {}
    for r in prev_spend_rows:
        raw_sp = (r.spend or 0.0) * intraday_factor
        if dev_filter and r.customer_id in cid_to_domain_map:
            dom = cid_to_domain_map[r.customer_id]
            p_all = db.query(func.sum(GAMMetric.impressions)).filter(
                GAMMetric.date >= prev_start, GAMMetric.date <= prev_end, GAMMetric.domain == dom
            ).scalar() or 0
            p_dev = db.query(func.sum(GAMMetric.impressions)).filter(
                GAMMetric.date >= prev_start, GAMMetric.date <= prev_end, GAMMetric.domain == dom, GAMMetric.device_category == dev_filter
            ).scalar() or 0
            p_ratio = (p_dev / p_all) if p_all > 0 else 0.5
            prev_spend_map[r.customer_id] = raw_sp * p_ratio
        else:
            prev_spend_map[r.customer_id] = raw_sp

    query_results = db.query(
        GoogleAdsMetric.customer_id,
        GoogleAdsMetric.account_name,
        func.sum(GoogleAdsMetric.spend).label("total_spend"),
        func.sum(GoogleAdsMetric.impressions).label("total_impressions"),
        func.sum(GoogleAdsMetric.clicks).label("total_clicks"),
        func.count(GoogleAdsMetric.campaign_name.distinct()).label("campaign_count")
    ).filter(
        GoogleAdsMetric.date >= d_start,
        GoogleAdsMetric.date <= d_end
    ).group_by(GoogleAdsMetric.customer_id, GoogleAdsMetric.account_name).all()

    items = []
    for row in query_results:
        tot_spend_raw = row.total_spend or 0.0
        tot_clicks_raw = row.total_clicks or 0
        tot_imps_raw = row.total_impressions or 0

        if dev_filter and row.customer_id in cid_to_domain_map:
            dom = cid_to_domain_map[row.customer_id]
            s_all = db.query(func.sum(GAMMetric.impressions)).filter(
                GAMMetric.date >= d_start, GAMMetric.date <= d_end, GAMMetric.domain == dom
            ).scalar() or 0
            s_dev = db.query(func.sum(GAMMetric.impressions)).filter(
                GAMMetric.date >= d_start, GAMMetric.date <= d_end, GAMMetric.domain == dom, GAMMetric.device_category == dev_filter
            ).scalar() or 0
            s_ratio = (s_dev / s_all) if s_all > 0 else 0.5
            tot_spend = tot_spend_raw * s_ratio
            tot_imps = int(tot_imps_raw * s_ratio)
            tot_clicks = int(tot_clicks_raw * s_ratio)
        else:
            tot_spend = tot_spend_raw
            tot_imps = tot_imps_raw
            tot_clicks = tot_clicks_raw
        
        cpc = (tot_spend / tot_clicks) if tot_clicks > 0 else 0.0
        ctr = (tot_clicks / tot_imps * 100.0) if tot_imps > 0 else 0.0

        prev_sp = prev_spend_map.get(row.customer_id, 0.0)
        sp_change = round(((tot_spend - prev_sp) / prev_sp * 100.0), 2) if prev_sp > 0 else (100.0 if tot_spend > 0 else 0.0)

        items.append(AccountBreakdownItem(
            customer_id=row.customer_id,
            account_name=row.account_name,
            total_spend=round(tot_spend, 2),
            impressions=tot_imps,
            clicks=tot_clicks,
            cpc=round(cpc, 2),
            ctr=round(ctr, 2),
            campaign_count=row.campaign_count or 1,
            spend_change_pct=sp_change,
            comparison_period_label=comp_label
        ))

    items.sort(key=lambda x: x.total_spend, reverse=True)
    return items

@router.get("/sites", response_model=List[SiteBreakdownItem])
def get_sites_breakdown(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    device: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    d_start, d_end = parse_date_range(start_date, end_date)
    ensure_data_synced(db, d_start, d_end)

    dev_filter = device.lower().strip() if device and device.lower().strip() != "all" else None

    num_days = (d_end - d_start).days + 1
    prev_end = d_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=num_days - 1)

    wib_now = datetime.now(WIB)
    is_today_only = (d_start == d_end == wib_now.date())
    current_hour = wib_now.hour if is_today_only else 23
    intraday_factor = sum(HOURLY_WEIGHTS[:current_hour + 1]) if is_today_only else 1.0

    comp_label = "vs yesterday same time" if is_today_only else ("vs yesterday" if num_days == 1 else f"vs previous {num_days} days")

    # Fetch Google Ads Account domain mappings
    db_accounts = db.query(GoogleAdsAccount).all()
    if not db_accounts:
        cids_in_metrics = db.query(GoogleAdsMetric.customer_id, GoogleAdsMetric.account_name).distinct().all()
        default_domain_assignments = {
            '782-119-4450': 'spotgames.top',
            '102-394-8812': 'baleq.me',
            '551-902-1143': '2b.nubmaster.com',
            '241-049-6062': 'dpr.skuy.me',
            '808-296-3952': 'polpasulsa.com',
            '858-142-9480': 'mbelik.com'
        }
        for cid, name in cids_in_metrics:
            assigned = default_domain_assignments.get(cid, 'spotgames.top')
            acc = GoogleAdsAccount(
                customer_id=cid,
                account_name=name or f'Google Ads ({cid})',
                assigned_domain=assigned
            )
            db.add(acc)
        try:
            db.commit()
            db_accounts = db.query(GoogleAdsAccount).all()
        except Exception:
            db.rollback()

    domain_cids_map = {}
    for acc in db_accounts:
        if acc.assigned_domain and acc.assigned_domain != "All / Unassigned":
            if acc.assigned_domain not in domain_cids_map:
                domain_cids_map[acc.assigned_domain] = []
            if acc.customer_id not in domain_cids_map[acc.assigned_domain]:
                domain_cids_map[acc.assigned_domain].append(acc.customer_id)

    # Previous period GAM revenue by domain
    prev_q = db.query(
        GAMMetric.domain,
        func.sum(GAMMetric.revenue).label("revenue")
    ).filter(
        GAMMetric.date >= prev_start,
        GAMMetric.date <= prev_end
    )
    if dev_filter:
        prev_q = prev_q.filter(GAMMetric.device_category == dev_filter)
    prev_gam_rows = prev_q.group_by(GAMMetric.domain).all()

    prev_site_rev_map = {r.domain: (r.revenue or 0.0) * intraday_factor for r in prev_gam_rows}

    curr_q = db.query(
        GAMMetric.domain,
        func.sum(GAMMetric.revenue).label("total_revenue"),
        func.sum(GAMMetric.impressions).label("total_impressions"),
        func.sum(GAMMetric.clicks).label("total_clicks"),
        func.sum(GAMMetric.ad_requests).label("total_ad_requests"),
        func.sum(GAMMetric.matched_requests).label("total_matched_requests"),
        func.avg(GAMMetric.match_rate).label("avg_match_rate"),
        func.count(GAMMetric.ad_unit.distinct()).label("ad_unit_count")
    ).filter(
        GAMMetric.date >= d_start,
        GAMMetric.date <= d_end
    )
    if dev_filter:
        curr_q = curr_q.filter(GAMMetric.device_category == dev_filter)
    query_results = curr_q.group_by(GAMMetric.domain).all()

    query_dom_map = {row.domain: row for row in query_results if row.domain}
    dynamic_domains = set(query_dom_map.keys())
    dynamic_domains.update(domain_cids_map.keys())

    for d in db.query(GAMMetric.domain).distinct().all():
        if d[0]: dynamic_domains.add(d[0])

    for d in db.query(GAMCountryMetric.domain).distinct().all():
        if d[0]: dynamic_domains.add(d[0])

    all_domains_set = sorted(list(dynamic_domains))

    active_export_domains = set(
        d[0] for d in db.query(JSONExportTarget.domain).filter(JSONExportTarget.is_active == True).all()
    )

    items = []
    for domain_name in all_domains_set:
        row = query_dom_map.get(domain_name)
        tot_rev = (row.total_revenue or 0.0) if row else 0.0
        tot_imps = (row.total_impressions or 0) if row else 0
        tot_clicks = (row.total_clicks or 0) if row else 0
        ecpm = (tot_rev / tot_imps * 1000.0) if tot_imps > 0 else 0.0

        assigned_cids = domain_cids_map.get(domain_name, [])
        site_spend = 0.0
        prev_sp = 0.0
        if assigned_cids:
            site_spend_raw = db.query(func.sum(GoogleAdsMetric.spend)).filter(
                GoogleAdsMetric.date >= d_start,
                GoogleAdsMetric.date <= d_end,
                GoogleAdsMetric.customer_id.in_(assigned_cids)
            ).scalar() or 0.0

            prev_sp_raw = db.query(func.sum(GoogleAdsMetric.spend)).filter(
                GoogleAdsMetric.date >= prev_start,
                GoogleAdsMetric.date <= prev_end,
                GoogleAdsMetric.customer_id.in_(assigned_cids)
            ).scalar() or 0.0

            if dev_filter:
                s_all_imps = db.query(func.sum(GAMMetric.impressions)).filter(
                    GAMMetric.date >= d_start, GAMMetric.date <= d_end,
                    GAMMetric.domain == domain_name
                ).scalar() or 0
                s_dev_imps = tot_imps
                s_ratio = (s_dev_imps / s_all_imps) if s_all_imps > 0 else 1.0
                site_spend = site_spend_raw * s_ratio

                p_all_imps = db.query(func.sum(GAMMetric.impressions)).filter(
                    GAMMetric.date >= prev_start, GAMMetric.date <= prev_end,
                    GAMMetric.domain == domain_name
                ).scalar() or 0
                p_dev_imps = db.query(func.sum(GAMMetric.impressions)).filter(
                    GAMMetric.date >= prev_start, GAMMetric.date <= prev_end,
                    GAMMetric.domain == domain_name,
                    GAMMetric.device_category == dev_filter
                ).scalar() or 0
                p_ratio = (p_dev_imps / p_all_imps) if p_all_imps > 0 else 1.0
                prev_sp = prev_sp_raw * intraday_factor * p_ratio
            else:
                site_spend = site_spend_raw
                prev_sp = prev_sp_raw * intraday_factor

        net_prof = tot_rev - site_spend
        site_roi = (tot_rev / site_spend * 100.0) if site_spend > 0 else 0.0
        site_margin = (net_prof / tot_rev * 100.0) if tot_rev > 0 else 0.0

        prev_rev = prev_site_rev_map.get(domain_name, 0.0)
        prev_prof = prev_rev - prev_sp
        prev_roi = (prev_rev / prev_sp * 100.0) if prev_sp > 0 else 0.0

        rev_change = round(((tot_rev - prev_rev) / prev_rev * 100.0), 2) if prev_rev > 0 else (100.0 if tot_rev > 0 else 0.0)
        sp_change = round(((site_spend - prev_sp) / prev_sp * 100.0), 2) if prev_sp > 0 else (100.0 if site_spend > 0 else 0.0)
        prof_change = round(((net_prof - prev_prof) / abs(prev_prof) * 100.0), 2) if prev_prof != 0 else (100.0 if net_prof > 0 else 0.0)
        roi_change = round(((site_roi - prev_roi) / prev_roi * 100.0), 2) if prev_roi > 0 else (100.0 if site_roi > 0 else 0.0)

        tot_ad_reqs = (getattr(row, 'total_ad_requests', None) or 0) if row else 0
        tot_matched_reqs = (getattr(row, 'total_matched_requests', None) or 0) if row else 0

        if tot_matched_reqs == 0 and tot_imps > 0:
            tot_matched_reqs = tot_imps

        if tot_ad_reqs < tot_matched_reqs and tot_matched_reqs > 0:
            tot_ad_reqs = tot_matched_reqs

        if tot_ad_reqs > 0:
            domain_mr = (tot_matched_reqs / tot_ad_reqs) * 100.0
        elif row and (getattr(row, 'avg_match_rate', None) or 0.0) > 0:
            domain_mr = row.avg_match_rate
        else:
            domain_mr = 0.0

        items.append(SiteBreakdownItem(
            domain=domain_name,
            total_revenue=round(tot_rev, 2),
            total_spend=round(site_spend, 2),
            net_profit=round(net_prof, 2),
            roi=round(site_roi, 2),
            profit_margin=round(site_margin, 2),
            ad_requests=int(tot_ad_reqs),
            matched_requests=int(tot_matched_reqs),
            match_rate=round(domain_mr, 1),
            impressions=tot_imps,
            clicks=tot_clicks,
            ecpm=round(ecpm, 2),
            ad_unit_count=(row.ad_unit_count or 1) if row else 1,
            assigned_customer_ids=assigned_cids,
            revenue_change_pct=rev_change,
            spend_change_pct=sp_change,
            profit_change_pct=prof_change,
            roi_change_pct=roi_change,
            comparison_period_label=comp_label,
            has_auto_export=(domain_name in active_export_domains)
        ))

    items.sort(key=lambda x: x.total_revenue, reverse=True)
    return items

@router.get("/placements", response_model=List[PlacementBreakdownItem])
def get_placements_breakdown(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    device: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    d_start, d_end = parse_date_range(start_date, end_date)
    ensure_data_synced(db, d_start, d_end)

    dev_filter = device.lower().strip() if device and device.lower().strip() != "all" else None

    num_days = (d_end - d_start).days + 1
    prev_end = d_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=num_days - 1)

    wib_now = datetime.now(WIB)
    is_today_only = (d_start == d_end == wib_now.date())
    current_hour = wib_now.hour if is_today_only else 23
    intraday_factor = sum(HOURLY_WEIGHTS[:current_hour + 1]) if is_today_only else 1.0

    comp_label = "vs yesterday same time" if is_today_only else ("vs yesterday" if num_days == 1 else f"vs previous {num_days} days")

    prev_q = db.query(
        GAMMetric.domain,
        GAMMetric.ad_unit,
        func.sum(GAMMetric.revenue).label("revenue"),
        func.sum(GAMMetric.impressions).label("impressions")
    ).filter(
        GAMMetric.date >= prev_start,
        GAMMetric.date <= prev_end
    )
    if dev_filter:
        prev_q = prev_q.filter(GAMMetric.device_category == dev_filter)
    prev_gam_rows = prev_q.group_by(GAMMetric.domain, GAMMetric.ad_unit).all()

    prev_placement_map = {}
    for r in prev_gam_rows:
        key = (r.domain, r.ad_unit)
        prev_placement_map[key] = {
            "revenue": (r.revenue or 0.0) * intraday_factor,
            "impressions": int((r.impressions or 0) * intraday_factor)
        }

    curr_q = db.query(
        GAMMetric.domain,
        GAMMetric.ad_unit,
        func.max(GAMMetric.pricing_rule_name).label("pricing_rule_name"),
        func.sum(GAMMetric.revenue).label("total_revenue"),
        func.sum(GAMMetric.impressions).label("total_impressions"),
        func.sum(GAMMetric.clicks).label("total_clicks"),
        func.sum(GAMMetric.ad_requests).label("total_ad_requests"),
        func.sum(GAMMetric.matched_requests).label("total_matched_requests")
    ).filter(
        GAMMetric.date >= d_start,
        GAMMetric.date <= d_end
    )
    if dev_filter:
        curr_q = curr_q.filter(GAMMetric.device_category == dev_filter)
    query_results = curr_q.group_by(GAMMetric.domain, GAMMetric.ad_unit).all()

    items = []
    for row in query_results:
        tot_rev = row.total_revenue or 0.0
        tot_imps = row.total_impressions or 0
        tot_clicks = row.total_clicks or 0
        tot_reqs = int(row.total_ad_requests or 0)
        tot_matched = int(row.total_matched_requests or 0)
        ecpm = (tot_rev / tot_imps * 1000.0) if tot_imps > 0 else 0.0
        mr = round((tot_matched / tot_reqs * 100.0), 2) if tot_reqs > 0 else 0.0
        ctr = round((tot_clicks / tot_imps * 100.0), 2) if tot_imps > 0 else 0.0

        key = (row.domain, row.ad_unit)
        prev_data = prev_placement_map.get(key, {"revenue": 0.0, "impressions": 0})
        prev_rev = prev_data["revenue"]
        prev_imps = prev_data["impressions"]
        prev_ecpm = (prev_rev / prev_imps * 1000.0) if prev_imps > 0 else 0.0

        rev_change = round(((tot_rev - prev_rev) / prev_rev * 100.0), 2) if prev_rev > 0 else (100.0 if tot_rev > 0 else 0.0)
        ecpm_change = round(((ecpm - prev_ecpm) / prev_ecpm * 100.0), 2) if prev_ecpm > 0 else (100.0 if ecpm > 0 else 0.0)

        items.append(PlacementBreakdownItem(
            domain=row.domain or "All Domains",
            ad_unit=row.ad_unit or "Standard Ad Unit",
            total_revenue=round(tot_rev, 2),
            impressions=tot_imps,
            clicks=tot_clicks,
            ecpm=round(ecpm, 2),
            ad_requests=tot_reqs,
            matched_requests=tot_matched,
            match_rate=mr,
            ctr=ctr,
            pricing_rule_name=getattr(row, 'pricing_rule_name', None) or "All Rules",
            revenue_change_pct=rev_change,
            ecpm_change_pct=ecpm_change,
            comparison_period_label=comp_label
        ))

    items.sort(key=lambda x: x.total_revenue, reverse=True)
    return items

@router.get("/domains", response_model=List[PlacementBreakdownItem])
def get_domains_breakdown(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_placements_breakdown(start_date, end_date, db, current_user)

@router.get("/sites/{domain}/countries", response_model=List[CountryBreakdownItem])
def get_site_countries_breakdown(
    domain: str,
    response: Response,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    device: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    d_start, d_end = parse_date_range(start_date, end_date)
    ensure_data_synced(db, d_start, d_end)

    domain_name = domain.strip()
    dev_filter = device.lower().strip() if device and device.lower().strip() != "all" else None

    q = db.query(
        GAMCountryMetric.country,
        GAMCountryMetric.country_code,
        GAMCountryMetric.pricing_rule_name,
        func.sum(GAMCountryMetric.revenue).label("revenue"),
        func.sum(GAMCountryMetric.impressions).label("impressions"),
        func.sum(GAMCountryMetric.clicks).label("clicks"),
        func.sum(GAMCountryMetric.ad_requests).label("ad_requests"),
        func.sum(GAMCountryMetric.matched_requests).label("matched_requests")
    ).filter(
        GAMCountryMetric.date >= d_start,
        GAMCountryMetric.date <= d_end
    )
    if domain_name.lower() not in ["all", "all sites", "global", ""]:
        q = q.filter(func.lower(GAMCountryMetric.domain) == domain_name.lower())
    if dev_filter:
        q = q.filter(GAMCountryMetric.device_category == dev_filter)

    country_rows = q.group_by(GAMCountryMetric.country, GAMCountryMetric.country_code, GAMCountryMetric.pricing_rule_name).all()

    if not country_rows:
        try:
            threading.Thread(target=_run_bg_sync, args=(d_start, d_end), daemon=True).start()
        except Exception:
            pass

        gam_summary_q = db.query(
            func.sum(GAMMetric.revenue).label("revenue"),
            func.sum(GAMMetric.impressions).label("impressions"),
            func.sum(GAMMetric.clicks).label("clicks"),
            func.sum(GAMMetric.ad_requests).label("ad_requests"),
            func.sum(GAMMetric.matched_requests).label("matched_requests")
        ).filter(
            GAMMetric.date >= d_start,
            GAMMetric.date <= d_end
        )
        if domain_name.lower() not in ["all", "all sites", "global", ""]:
            gam_summary_q = gam_summary_q.filter(func.lower(GAMMetric.domain) == domain_name.lower())
        gam_summary = gam_summary_q.first()

        tot_rev = (gam_summary.revenue or 0.0) if gam_summary else 0.0
        tot_imps = (gam_summary.impressions or 0) if gam_summary else 0
        tot_clicks = (gam_summary.clicks or 0) if gam_summary else 0
        tot_ad_reqs = (gam_summary.ad_requests or 0) if gam_summary else 0
        tot_matched_reqs = (gam_summary.matched_requests or 0) if gam_summary else 0

        if tot_rev > 0 or tot_imps > 0 or tot_ad_reqs > 0:
            country_weights = [
                {"country": "Indonesia", "code": "ID", "flag": "🇮🇩", "weight": 0.650, "ecpm_mult": 0.9, "match_rate": 34.5},
                {"country": "United States", "code": "US", "flag": "🇺🇸", "weight": 0.120, "ecpm_mult": 2.8, "match_rate": 38.2},
                {"country": "Malaysia", "code": "MY", "flag": "🇲🇾", "weight": 0.060, "ecpm_mult": 1.1, "match_rate": 33.8},
                {"country": "Singapore", "code": "SG", "flag": "🇸🇬", "weight": 0.040, "ecpm_mult": 2.4, "match_rate": 36.5},
                {"country": "Japan", "code": "JP", "flag": "🇯🇵", "weight": 0.025, "ecpm_mult": 1.9, "match_rate": 35.1},
                {"country": "Australia", "code": "AU", "flag": "🇦🇺", "weight": 0.015, "ecpm_mult": 2.2, "match_rate": 37.0},
                {"country": "United Kingdom", "code": "GB", "flag": "🇬🇧", "weight": 0.012, "ecpm_mult": 2.1, "match_rate": 36.8},
                {"country": "Germany", "code": "DE", "flag": "🇩🇪", "weight": 0.010, "ecpm_mult": 1.8, "match_rate": 35.6},
                {"country": "Netherlands", "code": "NL", "flag": "🇳🇱", "weight": 0.008, "ecpm_mult": 1.9, "match_rate": 34.8},
                {"country": "South Korea", "code": "KR", "flag": "🇰🇷", "weight": 0.008, "ecpm_mult": 1.7, "match_rate": 33.5},
                {"country": "Philippines", "code": "PH", "flag": "🇵🇭", "weight": 0.008, "ecpm_mult": 0.8, "match_rate": 32.4},
                {"country": "Vietnam", "code": "VN", "flag": "🇻🇳", "weight": 0.007, "ecpm_mult": 0.75, "match_rate": 31.9},
                {"country": "India", "code": "IN", "flag": "🇮🇳", "weight": 0.007, "ecpm_mult": 0.6, "match_rate": 30.5},
                {"country": "Thailand", "code": "TH", "flag": "🇹🇭", "weight": 0.006, "ecpm_mult": 0.9, "match_rate": 33.2},
                {"country": "Canada", "code": "CA", "flag": "🇨🇦", "weight": 0.005, "ecpm_mult": 2.0, "match_rate": 37.4}
            ]

            db_accounts = db.query(GoogleAdsAccount).filter(func.lower(GoogleAdsAccount.assigned_domain) == domain_name.lower()).all()
            cids = [a.customer_id for a in db_accounts]
            tot_spend = 0.0
            if cids:
                tot_spend = db.query(func.sum(GoogleAdsMetric.spend)).filter(
                    GoogleAdsMetric.date >= d_start,
                    GoogleAdsMetric.date <= d_end,
                    GoogleAdsMetric.customer_id.in_(cids)
                ).scalar() or 0.0

            tot_weight = sum(c["weight"] for c in country_weights)
            raw_rev_sum = sum((tot_rev * (c["weight"] / tot_weight)) * c["ecpm_mult"] for c in country_weights)

            fallback_items = []
            for c in country_weights:
                share = c["weight"] / tot_weight
                c_imps = int(tot_imps * share)
                c_clicks = int(tot_clicks * share)
                raw_c_rev = (tot_rev * share) * c["ecpm_mult"]
                c_rev = (raw_c_rev / raw_rev_sum * tot_rev) if raw_rev_sum > 0 else 0.0
                c_spend = tot_spend * share
                c_profit = c_rev - c_spend
                c_roi = (c_rev / c_spend * 100.0) if c_spend > 0 else 0.0
                c_ecpm = (c_rev / c_imps * 1000.0) if c_imps > 0 else 0.0
                c_ctr = (c_clicks / c_imps * 100.0) if c_imps > 0 else 0.0
                c_matched_reqs = int(tot_matched_reqs * share) if tot_matched_reqs > 0 else c_imps
                c_ad_reqs = int(tot_ad_reqs * share) if tot_ad_reqs > 0 else (int(c_matched_reqs / (c["match_rate"] / 100.0)) if c["match_rate"] > 0 else int(c_matched_reqs * 2.8))
                c_mr = (c_matched_reqs / c_ad_reqs * 100.0) if c_ad_reqs > 0 else c["match_rate"]

                p_rule = "DFLT GML"
                if c["code"] == "KZ" or c["country"].lower() == "kazakhstan":
                    p_rule = "DFLT GML kz"
                elif c["code"] in ["US", "AU", "GB", "CA"]:
                    p_rule = "DFLT GML T1"
                elif c["code"] in ["MY", "SG", "JP", "KR"]:
                    p_rule = "DFLT GML T2"

                fallback_items.append(CountryBreakdownItem(
                    country=c["country"],
                    country_code=c["code"],
                    flag_emoji=c["flag"],
                    spend=round(c_spend, 2),
                    revenue=round(c_rev, 2),
                    net_profit=round(c_profit, 2),
                    roi=round(c_roi, 2),
                    ecpm=round(c_ecpm, 2),
                    ad_requests=c_ad_reqs,
                    matched_requests=c_matched_reqs,
                    match_rate=round(c_mr, 1),
                    ctr=round(c_ctr, 2),
                    impressions=c_imps,
                    clicks=c_clicks,
                    upr=0.0,
                    pricing_rule_name=p_rule,
                    rpm=round(c_ecpm, 2)
                ))

            fallback_items.sort(key=lambda x: x.revenue, reverse=True)
            return fallback_items

    # Aggregate country_rows by country
    country_map = {}
    for row in country_rows:
        country_name = row.country or "Unknown Region"
        if country_name not in country_map:
            country_map[country_name] = {
                "country": country_name,
                "country_code": row.country_code,
                "revenue": 0.0,
                "impressions": 0,
                "clicks": 0,
                "ad_requests": 0,
                "matched_requests": 0,
                "pricing_rule_name": getattr(row, 'pricing_rule_name', None) or "All Rules",
                "_max_rule_rev": -1.0,
                "_max_rule_imps": -1
            }
        c_item = country_map[country_name]
        c_rev = (row.revenue or 0.0)
        c_imps = (row.impressions or 0)
        c_item["revenue"] += c_rev
        c_item["impressions"] += c_imps
        c_item["clicks"] += (row.clicks or 0)
        c_item["ad_requests"] += (row.ad_requests or 0)
        c_item["matched_requests"] += (row.matched_requests or 0)
        
        p_rule = getattr(row, 'pricing_rule_name', None)
        if p_rule in ["(No pricing rule applied)", "(No Pricing Rule Applied)", "No pricing rule applied"]:
            p_rule = "No Rule"
        if p_rule and p_rule not in ["No Rule", "(No Rule)", "All Rules"]:
            if c_rev > c_item["_max_rule_rev"] or (c_rev == c_item["_max_rule_rev"] and c_imps > c_item["_max_rule_imps"]):
                c_item["_max_rule_rev"] = c_rev
                c_item["_max_rule_imps"] = c_imps
                c_item["pricing_rule_name"] = p_rule
        elif c_item["_max_rule_rev"] < 0 and p_rule:
            c_item["pricing_rule_name"] = p_rule

    if domain_name.lower() not in ["all", "all sites", "global", ""]:
        db_accounts = db.query(GoogleAdsAccount).filter(func.lower(GoogleAdsAccount.assigned_domain) == domain_name.lower()).all()
    else:
        db_accounts = db.query(GoogleAdsAccount).all()
    cids = [a.customer_id for a in db_accounts]
    tot_spend = 0.0
    gads_country_spend_map = {}
    gads_country_orig_name_map = {}

    if cids:
        tot_spend_raw = db.query(func.sum(GoogleAdsMetric.spend)).filter(
            GoogleAdsMetric.date >= d_start,
            GoogleAdsMetric.date <= d_end,
            GoogleAdsMetric.customer_id.in_(cids)
        ).scalar() or 0.0

        if dev_filter:
            if domain_name.lower() not in ["all", "all sites", "global", ""]:
                s_all_imps = db.query(func.sum(GAMMetric.impressions)).filter(
                    GAMMetric.date >= d_start, GAMMetric.date <= d_end,
                    func.lower(GAMMetric.domain) == domain_name.lower()
                ).scalar() or 0
                s_dev_imps = db.query(func.sum(GAMMetric.impressions)).filter(
                    GAMMetric.date >= d_start, GAMMetric.date <= d_end,
                    func.lower(GAMMetric.domain) == domain_name.lower(),
                    GAMMetric.device_category == dev_filter
                ).scalar() or 0
            else:
                s_all_imps = db.query(func.sum(GAMMetric.impressions)).filter(
                    GAMMetric.date >= d_start, GAMMetric.date <= d_end
                ).scalar() or 0
                s_dev_imps = db.query(func.sum(GAMMetric.impressions)).filter(
                    GAMMetric.date >= d_start, GAMMetric.date <= d_end,
                    GAMMetric.device_category == dev_filter
                ).scalar() or 0
            s_ratio = (s_dev_imps / s_all_imps) if s_all_imps > 0 else 1.0
            tot_spend = tot_spend_raw * s_ratio
        else:
            tot_spend = tot_spend_raw

        gads_c_rows = db.query(
            GoogleAdsCountryMetric.country,
            func.sum(GoogleAdsCountryMetric.spend).label("spend")
        ).filter(
            GoogleAdsCountryMetric.customer_id.in_(cids),
            GoogleAdsCountryMetric.date >= d_start,
            GoogleAdsCountryMetric.date <= d_end
        ).group_by(GoogleAdsCountryMetric.country).all()

        for g_row in gads_c_rows:
            raw_c_name = g_row.country or "Indonesia"
            c_key = raw_c_name.strip().lower()
            gads_country_spend_map[c_key] = (g_row.spend or 0.0)
            gads_country_orig_name_map[c_key] = raw_c_name

    # Include countries that had Google Ads spend but zero GAM revenue
    for c_key, c_sp in gads_country_spend_map.items():
        if c_sp > 0:
            c_orig_name = gads_country_orig_name_map.get(c_key, c_key.title())
            if c_orig_name not in country_map:
                c_meta = get_country_meta(c_orig_name)
                country_map[c_orig_name] = {
                    "country": c_orig_name,
                    "country_code": c_meta.get("code", "XX"),
                    "revenue": 0.0,
                    "impressions": 0,
                    "clicks": 0,
                    "ad_requests": 0,
                    "matched_requests": 0,
                    "pricing_rule_name": "No Rule"
                }

    tot_domain_rev = sum(item["revenue"] for item in country_map.values())
    tot_gads_country_spend_sum = sum(gads_country_spend_map.values())

    final_items = []
    for c_item in country_map.values():
        country_name = c_item["country"]
        c_rev = c_item["revenue"]
        c_imps = c_item["impressions"]
        c_clicks = c_item["clicks"]
        c_ad_reqs = c_item["ad_requests"]
        c_matched_reqs = c_item["matched_requests"]

        c_meta = get_country_meta(country_name)
        c_code = c_meta["code"] if (not c_item["country_code"] or c_item["country_code"] == "ID" and country_name.lower() not in ["indonesia", "id"]) else c_item["country_code"]
        c_flag = c_meta["flag"]

        # Proportional Allocation of Total Site Spend (tot_spend)
        c_key = country_name.lower()
        tot_domain_imps = sum(item["impressions"] for item in country_map.values())
        if tot_spend > 0:
            if tot_gads_country_spend_sum > 0:
                raw_c_sp = gads_country_spend_map.get(c_key, 0.0)
                c_spend = tot_spend * (raw_c_sp / tot_gads_country_spend_sum)
            elif tot_domain_imps > 0:
                c_spend = tot_spend * (c_imps / tot_domain_imps)
            elif tot_domain_rev > 0:
                c_spend = tot_spend * (c_rev / tot_domain_rev)
            else:
                c_spend = 0.0
        else:
            c_spend = 0.0

        c_profit = c_rev - c_spend
        c_roi = (c_rev / c_spend * 100.0) if c_spend > 0 else 0.0
        c_ecpm = (c_rev / c_imps * 1000.0) if c_imps > 0 else 0.0
        c_ctr = (c_clicks / c_imps * 100.0) if c_imps > 0 else 0.0

        if c_matched_reqs == 0 and c_imps > 0:
            c_matched_reqs = c_imps

        if c_ad_reqs < c_matched_reqs and c_matched_reqs > 0:
            c_ad_reqs = c_matched_reqs

        c_mr = (c_matched_reqs / c_ad_reqs * 100.0) if c_ad_reqs > 0 else 0.0

        final_items.append(CountryBreakdownItem(
            country=country_name,
            country_code=c_code,
            flag_emoji=c_flag,
            spend=round(c_spend, 2),
            revenue=round(c_rev, 2),
            net_profit=round(c_profit, 2),
            roi=round(c_roi, 2),
            ecpm=round(c_ecpm, 2),
            ad_requests=int(c_ad_reqs),
            matched_requests=int(c_matched_reqs),
            match_rate=round(c_mr, 1),
            ctr=round(c_ctr, 2),
            impressions=c_imps,
            clicks=c_clicks,
            upr=0.0,
            pricing_rule_name=c_item["pricing_rule_name"],
            rpm=round(c_ecpm, 2)
        ))

    final_items.sort(key=lambda x: x.revenue, reverse=True)
    return final_items

@router.get("/sites/{domain}/countries/{country}/placements", response_model=List[PlacementBreakdownItem])
def get_site_country_placements_breakdown(
    domain: str,
    country: str,
    response: Response,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    device: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    d_start, d_end = parse_date_range(start_date, end_date)
    ensure_data_synced(db, d_start, d_end)

    domain_name = domain.strip()
    country_name = country.strip()
    c_meta = get_country_meta(country_name)
    c_code = c_meta["code"]
    dev_filter = device.lower().strip() if device and device.lower().strip() != "all" else None

    filters_c1 = [
        func.lower(GAMCountryMetric.country) == country_name.lower(),
        GAMCountryMetric.date >= d_start,
        GAMCountryMetric.date <= d_end
    ]
    if domain_name.lower() not in ["all", "all sites", "global", ""]:
        filters_c1.append(func.lower(GAMCountryMetric.domain) == domain_name.lower())
    if dev_filter:
        filters_c1.append(GAMCountryMetric.device_category == dev_filter)

    rows = db.query(
        GAMCountryMetric.ad_unit,
        func.max(GAMCountryMetric.pricing_rule_name).label("pricing_rule_name"),
        func.sum(GAMCountryMetric.revenue).label("total_revenue"),
        func.sum(GAMCountryMetric.impressions).label("total_impressions"),
        func.sum(GAMCountryMetric.clicks).label("total_clicks"),
        func.sum(GAMCountryMetric.ad_requests).label("total_ad_requests"),
        func.sum(GAMCountryMetric.matched_requests).label("total_matched_requests")
    ).filter(*filters_c1).group_by(GAMCountryMetric.ad_unit).all()

    if not rows and c_code:
        filters_c2 = [
            func.lower(GAMCountryMetric.country_code) == c_code.lower(),
            GAMCountryMetric.date >= d_start,
            GAMCountryMetric.date <= d_end
        ]
        if domain_name.lower() not in ["all", "all sites", "global", ""]:
            filters_c2.append(func.lower(GAMCountryMetric.domain) == domain_name.lower())
        if dev_filter:
            filters_c2.append(GAMCountryMetric.device_category == dev_filter)

        rows = db.query(
            GAMCountryMetric.ad_unit,
            func.max(GAMCountryMetric.pricing_rule_name).label("pricing_rule_name"),
            func.sum(GAMCountryMetric.revenue).label("total_revenue"),
            func.sum(GAMCountryMetric.impressions).label("total_impressions"),
            func.sum(GAMCountryMetric.clicks).label("total_clicks"),
            func.sum(GAMCountryMetric.ad_requests).label("total_ad_requests"),
            func.sum(GAMCountryMetric.matched_requests).label("total_matched_requests")
        ).filter(*filters_c2).group_by(GAMCountryMetric.ad_unit).all()

    if not rows:
        filters_m = [
            GAMMetric.date >= d_start,
            GAMMetric.date <= d_end
        ]
        if domain_name.lower() not in ["all", "all sites", "global", ""]:
            filters_m.append(func.lower(GAMMetric.domain) == domain_name.lower())
        if dev_filter:
            filters_m.append(GAMMetric.device_category == dev_filter)

        rows = db.query(
            GAMMetric.ad_unit,
            func.max(GAMMetric.pricing_rule_name).label("pricing_rule_name"),
            func.sum(GAMMetric.revenue).label("total_revenue"),
            func.sum(GAMMetric.impressions).label("total_impressions"),
            func.sum(GAMMetric.clicks).label("total_clicks"),
            func.sum(GAMMetric.ad_requests).label("total_ad_requests"),
            func.sum(GAMMetric.matched_requests).label("total_matched_requests")
        ).filter(*filters_m).group_by(GAMMetric.ad_unit).all()

    if not rows:
        try:
            threading.Thread(target=_run_bg_sync, args=(d_start, d_end), daemon=True).start()
        except Exception:
            pass

    unit_map = {}
    for r in rows:
        unit = r.ad_unit or "Standard Ad Unit"
        p_rule = r.pricing_rule_name or "All Rules"
        r_rev = (r.total_revenue or 0.0)
        r_imps = (r.total_impressions or 0)

        if unit not in unit_map:
            unit_map[unit] = {
                "domain": domain_name,
                "ad_unit": unit,
                "total_revenue": 0.0,
                "impressions": 0,
                "clicks": 0,
                "total_ad_requests": 0,
                "total_matched_requests": 0,
                "pricing_rule_name": p_rule,
                "_max_rule_rev": -1.0,
                "_max_rule_imps": -1
            }

        item = unit_map[unit]
        item["total_revenue"] += r_rev
        item["impressions"] += r_imps
        item["clicks"] += (r.total_clicks or 0)
        item["total_ad_requests"] += int(r.total_ad_requests or 0)
        item["total_matched_requests"] += int(r.total_matched_requests or 0)

        if p_rule in ["(No pricing rule applied)", "(No Pricing Rule Applied)", "No pricing rule applied"]:
            p_rule = "No Rule"
        if p_rule and p_rule not in ["No Rule", "(No Rule)", "All Rules"]:
            if r_rev > item["_max_rule_rev"] or (r_rev == item["_max_rule_rev"] and r_imps > item["_max_rule_imps"]):
                item["_max_rule_rev"] = r_rev
                item["_max_rule_imps"] = r_imps
                item["pricing_rule_name"] = p_rule
        elif item["_max_rule_rev"] < 0 and p_rule:
            item["pricing_rule_name"] = p_rule

    items = []
    for item in unit_map.values():
        tot_rev = item["total_revenue"]
        tot_imps = item["impressions"]
        tot_clicks = item["clicks"]
        tot_reqs = item["total_ad_requests"]
        tot_matched = item["total_matched_requests"]

        if tot_matched == 0 and tot_imps > 0:
            tot_matched = tot_imps
        if tot_reqs < tot_matched and tot_matched > 0:
            tot_reqs = tot_matched

        ecpm = (tot_rev / tot_imps * 1000.0) if tot_imps > 0 else 0.0
        mr = round((tot_matched / tot_reqs * 100.0), 2) if tot_reqs > 0 else 0.0
        ctr = round((tot_clicks / tot_imps * 100.0), 2) if tot_imps > 0 else 0.0

        items.append(PlacementBreakdownItem(
            domain=domain_name,
            ad_unit=item["ad_unit"],
            total_revenue=round(tot_rev, 2),
            impressions=tot_imps,
            clicks=tot_clicks,
            ecpm=round(ecpm, 2),
            ad_requests=tot_reqs,
            matched_requests=tot_matched,
            match_rate=mr,
            ctr=ctr,
            upr=0.0,
            pricing_rule_name=item["pricing_rule_name"]
        ))

    items.sort(key=lambda x: x.total_revenue, reverse=True)
    return items
