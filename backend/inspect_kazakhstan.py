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
    print("🔬 INSPEKSI KAZAKHSTAN (KZ) - play.gemol.me (YESTERDAY)")
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

    combos = [
        {
            "name": "Country Combo 1: DATE + COUNTRY_NAME + SITE_NAME + AD_UNIT_NAME",
            "dims": ['DATE', 'COUNTRY_NAME', 'SITE_NAME', 'AD_UNIT_NAME'],
            "cols": [
                'AD_EXCHANGE_LINE_ITEM_LEVEL_IMPRESSIONS',
                'AD_EXCHANGE_LINE_ITEM_LEVEL_REVENUE',
                'AD_EXCHANGE_LINE_ITEM_LEVEL_CLICKS',
                'AD_EXCHANGE_TOTAL_REQUESTS',
                'AD_EXCHANGE_RESPONSES_SERVED'
            ]
        },
        {
            "name": "Country Combo 2: DATE + COUNTRY_NAME + AD_UNIT_NAME",
            "dims": ['DATE', 'COUNTRY_NAME', 'AD_UNIT_NAME'],
            "cols": [
                'AD_EXCHANGE_LINE_ITEM_LEVEL_IMPRESSIONS',
                'AD_EXCHANGE_LINE_ITEM_LEVEL_REVENUE',
                'AD_EXCHANGE_LINE_ITEM_LEVEL_CLICKS',
                'AD_EXCHANGE_TOTAL_REQUESTS',
                'AD_EXCHANGE_RESPONSES_SERVED'
            ]
        }
    ]

    for combo in combos:
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
                if ('DATE' in line_up or 'COUNTRY' in line_up or 'UNIT' in line_up or 'SITE' in line_up) and ('IMPRESSION' in line_up or 'SERVED' in line_up or 'REQUEST' in line_up or 'COLUMN' in line_up):
                    header_idx = idx
                    break

            reader = list(csv.DictReader(lines[header_idx:]))
            print(f"✅ SUKSES! Total {len(reader)} baris ditarik.\n")

            # Filter for Kazakhstan and gemol/play
            filtered_rows = []
            for row in reader:
                r_str = json.dumps(row).lower()
                is_kazakhstan = "kazakhstan" in r_str or "kz" in r_str
                is_gemol = "gemol" in r_str or "play" in r_str
                
                if is_kazakhstan or is_gemol or len(reader) < 20:
                    filtered_rows.append(row)

            # Sort by AD_UNIT_NAME
            def get_unit(r):
                for k, v in r.items():
                    if k and 'AD_UNIT' in k.upper() and v:
                        return str(v).strip().lower()
                return ""

            sorted_rows = sorted(filtered_rows, key=get_unit)

            print(f"📌 HASIL FILTER & SORT BY ADUNIT (Kazakhstan / play.gemol.me - Total {len(sorted_rows)} baris):")
            print("=" * 100)
            
            for idx, r in enumerate(sorted_rows, 1):
                print(f"[{idx}] {json.dumps(r, indent=2)}")

            print("=" * 100 + "\n")

        except Exception as e:
            print(f"❌ FAULT: {e}\n")

if __name__ == "__main__":
    main()
