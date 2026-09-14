import sys
import os
import gzip
import csv
import requests
from datetime import date, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.config import settings, BASE_DIR

def debug_gam_targeting():
    print("=" * 60)
    print("=== INSPEKSI CUSTOM TARGETING ('domain') & PAGE_URL IN GAM API ===")
    print("=" * 60)
    
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

    today = date.today()
    start = today - timedelta(days=7)

    # Let's test dimension sets specifically for page url & targeting
    dims_to_test = [
        ['DATE', 'AD_EXCHANGE_URL_NAME', 'AD_UNIT_NAME'],
        ['DATE', 'CUSTOM_TARGETING_VALUE_PAIR', 'AD_UNIT_NAME'],
        ['DATE', 'DOMAIN_NAME', 'AD_UNIT_NAME'],
        ['DATE', 'AD_UNIT_NAME']
    ]

    cols = [
        'AD_EXCHANGE_LINE_ITEM_LEVEL_REVENUE',
        'AD_EXCHANGE_LINE_ITEM_LEVEL_IMPRESSIONS',
        'AD_EXCHANGE_LINE_ITEM_LEVEL_CLICKS'
    ]

    for dims in dims_to_test:
        try:
            print(f"\n--- Testing Dims: {dims} ---")
            report_job = {
                'reportQuery': {
                    'dimensions': dims,
                    'columns': cols,
                    'dateRangeType': 'CUSTOM_DATE',
                    'startDate': {'year': start.year, 'month': start.month, 'day': start.day},
                    'endDate': {'year': today.year, 'month': today.month, 'day': today.day}
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

            print(f"SUCCESS! Dims {dims} returned {len(reader)} rows.")
            if reader:
                print("CSV Headers:", list(reader[0].keys()))
                print("Sample Row #1:", dict(reader[0]))
                if len(reader) > 1:
                    print("Sample Row #2:", dict(reader[1]))
            break
        except Exception as e:
            print(f"Dims {dims} failed: {e}")

if __name__ == "__main__":
    debug_gam_targeting()
