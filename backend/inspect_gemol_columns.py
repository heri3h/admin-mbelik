import sys
import os
import csv
import json
import gzip
import requests
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings, BASE_DIR
from googleads import ad_manager, oauth2

def main():
    print("==========================================================================")
    print("🔬 INSPEKSI DETAIL SELURUH KOLOM GAM API: play.gemol.me (YESTERDAY)")
    print("==========================================================================\n")

    json_path = settings.GAM_JSON_KEY_FILE_PATH
    if json_path and not os.path.isabs(json_path):
        json_path = os.path.join(BASE_DIR, json_path)
    
    if json_path and os.path.exists(json_path):
        oauth2_client = oauth2.GoogleServiceAccountClient(
            json_path,
            scope='https://www.googleapis.com/auth/admanager'
        )
        client = ad_manager.AdManagerClient(
            oauth2_client,
            settings.GAM_APPLICATION_NAME,
            settings.GAM_NETWORK_CODE
        )
    else:
        oauth2_client = oauth2.GoogleRefreshTokenClient(
            settings.GAM_CLIENT_ID,
            settings.GAM_CLIENT_SECRET,
            settings.GAM_REFRESH_TOKEN
        )
        client = ad_manager.AdManagerClient(
            oauth2_client,
            settings.GAM_APPLICATION_NAME,
            settings.GAM_NETWORK_CODE
        )

    report_service = client.GetService('ReportService', version='v202602')

    yesterday = date.today() - timedelta(days=1)
    print(f"📅 Tanggal Kemarin: {yesterday}\n")

    # Candidate column sets to test against GAM API
    test_combos = [
        {
            "name": "Combo 1: AdX Total Requests & Responses Served",
            "dims": ['DATE', 'SITE_NAME', 'AD_UNIT_NAME'],
            "cols": [
                'AD_EXCHANGE_LINE_ITEM_LEVEL_IMPRESSIONS',
                'AD_EXCHANGE_LINE_ITEM_LEVEL_REVENUE',
                'AD_EXCHANGE_LINE_ITEM_LEVEL_CLICKS',
                'AD_EXCHANGE_TOTAL_REQUESTS',
                'AD_EXCHANGE_RESPONSES_SERVED'
            ]
        },
        {
            "name": "Combo 2: AdX Requests per Ad Unit",
            "dims": ['DATE', 'AD_UNIT_NAME'],
            "cols": [
                'AD_EXCHANGE_LINE_ITEM_LEVEL_IMPRESSIONS',
                'AD_EXCHANGE_LINE_ITEM_LEVEL_REVENUE',
                'AD_EXCHANGE_LINE_ITEM_LEVEL_CLICKS',
                'AD_EXCHANGE_TOTAL_REQUESTS',
                'AD_EXCHANGE_RESPONSES_SERVED'
            ]
        },
        {
            "name": "Combo 3: Total Code Served & Unfilled Impressions",
            "dims": ['DATE', 'AD_UNIT_NAME'],
            "cols": [
                'TOTAL_CODE_SERVED_COUNT',
                'TOTAL_INVENTORY_LEVEL_UNFILLED_IMPRESSIONS',
                'TOTAL_INVENTORY_LEVEL_IMPRESSIONS'
            ]
        },
        {
            "name": "Combo 4: Site Level Requests & Responses",
            "dims": ['DATE', 'SITE_NAME'],
            "cols": [
                'AD_EXCHANGE_LINE_ITEM_LEVEL_IMPRESSIONS',
                'AD_EXCHANGE_LINE_ITEM_LEVEL_REVENUE',
                'AD_EXCHANGE_TOTAL_REQUESTS',
                'AD_EXCHANGE_RESPONSES_SERVED'
            ]
        }
    ]

    for combo in test_combos:
        print(f"--- 🧪 Menguji {combo['name']} ---")
        try:
            report_job_query = {
                'dimensions': combo['dims'],
                'columns': combo['cols'],
                'dateRangeType': 'CUSTOM_DATE',
                'startDate': {'year': yesterday.year, 'month': yesterday.month, 'day': yesterday.day},
                'endDate': {'year': yesterday.year, 'month': yesterday.month, 'day': yesterday.day},
                'timeZoneType': 'TIME_ZONE_OF_NETWORK'
            }

            report_job = {'reportQuery': report_job_query}
            report_job = report_service.runReportJob(report_job)
            report_job_id = report_job['id']

            attempts = 0
            while attempts < 15:
                status = report_service.getReportJobStatus(report_job_id)
                if status == 'COMPLETED':
                    break
                elif status == 'FAILED':
                    raise Exception("Job Failed")
                import time
                time.sleep(1)
                attempts += 1

            report_download_url = report_service.getReportDownloadUrlWithOptions(report_job_id, 'CSV_DUMP')
            res = requests.get(report_download_url)
            content_bytes = res.content
            if content_bytes.startswith(b'\x1f\x8b'):
                content_bytes = gzip.decompress(content_bytes)

            csv_text = content_bytes.decode('utf-8-sig', errors='ignore')
            lines = [l for l in csv_text.splitlines() if l.strip()]

            header_idx = 0
            for idx, line in enumerate(lines):
                line_up = line.upper()
                if ('DATE' in line_up or 'UNIT' in line_up or 'SITE' in line_up) and ('IMPRESSION' in line_up or 'SERVED' in line_up or 'REQUEST' in line_up or 'COLUMN' in line_up):
                    header_idx = idx
                    break

            reader = list(csv.DictReader(lines[header_idx:]))
            print(f"✅ SUKSES! Mengembalikan {len(reader)} baris.")
            if reader:
                print("   [CSV HEADERS]:", list(reader[0].keys()))
                print("   [BARIS DATA MATCHING 'gemol' / 'play']: ")
                gemol_found = False
                for r in reader:
                    r_str = json.dumps(r).lower()
                    if "gemol" in r_str or "play" in r_str or len(reader) < 5:
                        print("   ->", json.dumps(r, indent=2))
                        gemol_found = True
                if not gemol_found:
                    print("   [SAMPEL 2 BARIS PERTAMA]:")
                    for r in reader[:2]:
                        print("   ->", json.dumps(r, indent=2))
            print("\n")
        except Exception as e:
            print(f"❌ FAULT: {e}\n")

if __name__ == "__main__":
    main()
