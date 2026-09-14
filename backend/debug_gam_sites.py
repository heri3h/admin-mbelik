import sys
import os
import gzip
import csv
import requests
from datetime import date, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.config import settings, BASE_DIR

def debug_gam_sites():
    print("=" * 60)
    print("=== MENCARI DIMENSI NAMA SITUS / DOMAIN ASLI DARI GAM API ===")
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

    # List of site/domain dimensions to test
    site_dims_to_test = [
        ['DATE', 'AD_EXCHANGE_SITE_NAME'],
        ['DATE', 'AD_EXCHANGE_URL_NAME'],
        ['DATE', 'DOMAIN_NAME'],
        ['DATE', 'SITE_NAME'],
        ['DATE', 'AD_EXCHANGE_CHANNEL_NAME'],
        ['DATE', 'AD_UNIT_TOP_LEVEL_NAME']
    ]

    cols = [
        'AD_EXCHANGE_LINE_ITEM_LEVEL_REVENUE',
        'AD_EXCHANGE_LINE_ITEM_LEVEL_IMPRESSIONS',
        'AD_EXCHANGE_LINE_ITEM_LEVEL_CLICKS'
    ]

    for dims in site_dims_to_test:
        try:
            print(f"\nMenguji Dimensi Situs: {dims}")
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

            print(f"✅ SUKSES! Dimensi {dims} mengembalikan {len(reader)} baris.")
            if reader:
                print("Header Kolom:", list(reader[0].keys()))
                print("Contoh 3 Baris Data:")
                for idx, r in enumerate(reader[:3]):
                    print(f" Baris #{idx+1}:", dict(r))
        except Exception as e:
            print(f"❌ Dimensi {dims} tidak didukung/gagal: {e}")

if __name__ == "__main__":
    debug_gam_sites()
