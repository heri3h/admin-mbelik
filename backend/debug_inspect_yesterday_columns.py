import sys
import os
import gzip
import csv
import requests
from datetime import date, timedelta, datetime, timezone

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.config import settings, BASE_DIR

WIB = timezone(timedelta(hours=7))

def debug_inspect_columns():
    wib_now = datetime.now(WIB)
    today = wib_now.date()
    yesterday = today - timedelta(days=1)

    print("=" * 70)
    print(f"=== INSPEKSI REVENUE GAM DALAM WAKTU WIB (GMT+7) ===")
    print(f"-> WIB Today     : {today}")
    print(f"-> WIB Yesterday : {yesterday}")
    print("=" * 70)

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

    column_sets_to_test = [
        ("AD_EXCHANGE_LINE_ITEM_LEVEL", [
            'AD_EXCHANGE_LINE_ITEM_LEVEL_REVENUE',
            'AD_EXCHANGE_LINE_ITEM_LEVEL_IMPRESSIONS',
            'AD_EXCHANGE_LINE_ITEM_LEVEL_CLICKS'
        ])
    ]

    dims = ['DATE', 'SITE_NAME']

    for label, cols in column_sets_to_test:
        try:
            print(f"\nMenguji Revenue GAM untuk WIB Yesterday ({yesterday}):")
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

            raw_micros = 0.0
            for r in reader:
                for k, v in r.items():
                    if k and 'REVENUE' in k.upper() and v:
                        try:
                            raw_micros += float(v)
                        except ValueError:
                            pass

            gross_idr = raw_micros / 1000000.0
            net_idr = gross_idr * 0.92

            print(f" -> Gross GAM Console (11 Sept) : Rp {gross_idr:,.2f}")
            print(f" -> Net Dashboard (-8%)          : Rp {net_idr:,.2f}")

        except Exception as e:
            print(f" -> Gagal: {e}")

if __name__ == "__main__":
    debug_inspect_columns()
