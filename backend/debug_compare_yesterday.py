import sys
import os
import gzip
import csv
import requests
from datetime import date, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.config import settings, BASE_DIR
from app.database import SessionLocal
from app.models import GAMMetric, DailyProfitSummary

def compare_yesterday():
    today = date.today()
    yesterday = today - timedelta(days=1)

    print("=" * 65)
    print(f"=== PERBANDINGAN DATA EARNING GAM (YESTERDAY: {yesterday}) ===")
    print("=" * 65)

    # 1. Check DB Cache
    db = SessionLocal()
    try:
        summary = db.query(DailyProfitSummary).filter(DailyProfitSummary.date == yesterday).first()
        db_rev = summary.total_revenue if summary else 0.0
        print(f"1. Earning di Database Dashboard (Setelah Potongan -8%) : Rp {db_rev:,.2f}")
    finally:
        db.close()

    # 2. Fetch Raw GAM API Data
    from googleads import ad_manager, oauth2

    json_path = settings.GAM_JSON_KEY_FILE_PATH
    if json_path and not os.path.isabs(json_path):
        json_path = os.path.join(BASE_DIR, json_path)

    oauth2_client = oauth2.GoogleServiceAccountClient(
        json_path,
        scope='https://www.googleapis.com/auth/admanager'
    )
    client = ad_manager.AdManagerClient(
        oauth2_client,
        settings.GAM_APPLICATION_NAME,
        settings.GAM_NETWORK_CODE
    )

    report_service = client.GetService('ReportService', version='v202602')

    dims = ['DATE', 'SITE_NAME']
    cols = [
        'AD_EXCHANGE_LINE_ITEM_LEVEL_REVENUE',
        'AD_EXCHANGE_LINE_ITEM_LEVEL_IMPRESSIONS',
        'AD_EXCHANGE_LINE_ITEM_LEVEL_CLICKS'
    ]

    try:
        report_job = {
            'reportQuery': {
                'dimensions': dims,
                'columns': cols,
                'dateRangeType': 'CUSTOM_DATE',
                'startDate': {'year': yesterday.year, 'month': yesterday.month, 'day': yesterday.day},
                'endDate': {'year': yesterday.year, 'month': yesterday.month, 'day': yesterday.day}
            }
        }

        report_job = report_service.runReportJob(report_job)
        report_job_id = report_job['id']

        while True:
            status = report_service.getReportJobStatus(report_job_id)
            if status == 'COMPLETED':
                break
            elif status == 'FAILED':
                raise Exception("Report Job Failed")

        url = report_service.getReportDownloadUrlWithOptions(report_job_id, 'CSV_DUMP')
        res = requests.get(url)
        content = res.content
        if content.startswith(b'\x1f\x8b'):
            content = gzip.decompress(content)

        text = content.decode('utf-8-sig', errors='ignore')
        lines = [l for l in text.splitlines() if l.strip()]
        reader = list(csv.DictReader(lines))

        raw_micros_total = 0.0
        for r in reader:
            for k, v in r.items():
                if k and 'REVENUE' in k.upper() and v:
                    try:
                        raw_micros_total += float(v)
                    except ValueError:
                        pass

        raw_gross_idr = raw_micros_total / 1000000.0
        adj_net_idr = raw_gross_idr * 0.92

        print(f"2. Earning Kotor Mentah dari GAM Console (Gross GAM)      : Rp {raw_gross_idr:,.2f}")
        print(f"3. Earning Bersih Setelah Dikurangi 8% (Net Dashboard)   : Rp {adj_net_idr:,.2f}")
        print("-" * 65)

    except Exception as e:
        print("Error fetching GAM data:", e)

if __name__ == "__main__":
    compare_yesterday()
