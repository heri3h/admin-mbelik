import sys
import os
import gzip
import csv
import requests
from datetime import date, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.config import settings, BASE_DIR

def debug_list_all_domains():
    print("=" * 70)
    print("=== MENDAGANGKAN SELURUH DOMAIN / SITUS DARI GAM API ===")
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
    today = date.today()
    start = today - timedelta(days=30)  # Check last 30 days to capture all active sites

    all_found_domains = set()

    # 1. Check SITE_NAME
    try:
        job = {
            'reportQuery': {
                'dimensions': ['DATE', 'SITE_NAME'],
                'columns': ['AD_EXCHANGE_LINE_ITEM_LEVEL_REVENUE', 'AD_EXCHANGE_LINE_ITEM_LEVEL_IMPRESSIONS'],
                'dateRangeType': 'CUSTOM_DATE',
                'startDate': {'year': start.year, 'month': start.month, 'day': start.day},
                'endDate': {'year': today.year, 'month': today.month, 'day': today.day}
            }
        }
        job = report_service.runReportJob(job)
        job_id = job['id']
        while True:
            st = report_service.getReportJobStatus(job_id)
            if st == 'COMPLETED': break
            elif st == 'FAILED': raise Exception("Report Job Failed")

        url = report_service.getReportDownloadUrlWithOptions(job_id, 'CSV_DUMP')
        text = gzip.decompress(requests.get(url).content).decode('utf-8-sig', errors='ignore')
        reader = csv.DictReader([l for l in text.splitlines() if l.strip()])
        site_name_doms = set()
        for r in reader:
            for k, v in r.items():
                if k and 'SITE' in k.upper() and 'DATE' not in k.upper() and v:
                    val = str(v).replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0].strip().lower()
                    if val and val not in ["all domains", "-", "none", "null"]:
                        site_name_doms.add(val)
        print(f"\n1. SITE_NAME (Last 30 days) -> Found {len(site_name_doms)} domains:")
        for d in sorted(list(site_name_doms)):
            print(f"   - {d}")
        all_found_domains.update(site_name_doms)
    except Exception as e:
        print(f"SITE_NAME failed: {e}")

    # 2. Check CUSTOM_TARGETING_VALUE_PAIR
    try:
        job = {
            'reportQuery': {
                'dimensions': ['DATE', 'CUSTOM_TARGETING_VALUE_PAIR'],
                'columns': ['AD_EXCHANGE_LINE_ITEM_LEVEL_REVENUE', 'AD_EXCHANGE_LINE_ITEM_LEVEL_IMPRESSIONS'],
                'dateRangeType': 'CUSTOM_DATE',
                'startDate': {'year': start.year, 'month': start.month, 'day': start.day},
                'endDate': {'year': today.year, 'month': today.month, 'day': today.day}
            }
        }
        job = report_service.runReportJob(job)
        job_id = job['id']
        while True:
            st = report_service.getReportJobStatus(job_id)
            if st == 'COMPLETED': break
            elif st == 'FAILED': raise Exception("Report Job Failed")

        url = report_service.getReportDownloadUrlWithOptions(job_id, 'CSV_DUMP')
        text = gzip.decompress(requests.get(url).content).decode('utf-8-sig', errors='ignore')
        reader = csv.DictReader([l for l in text.splitlines() if l.strip()])
        custom_target_doms = set()
        import re
        for r in reader:
            for k, v in r.items():
                if k and 'TARGETING' in k.upper() and v:
                    match = re.search(r'domain\s*[:=]\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', str(v).lower())
                    if match:
                        custom_target_doms.add(match.group(1).replace('www.', '').strip())
        print(f"\n2. CUSTOM_TARGETING_VALUE_PAIR -> Found {len(custom_target_doms)} domains:")
        for d in sorted(list(custom_target_doms)):
            print(f"   - {d}")
        all_found_domains.update(custom_target_doms)
    except Exception as e:
        print(f"CUSTOM_TARGETING failed: {e}")

    # 3. Check AD_UNIT_NAME
    try:
        from app.services.gam import extract_domain_from_row
        job = {
            'reportQuery': {
                'dimensions': ['DATE', 'AD_UNIT_NAME'],
                'columns': ['AD_EXCHANGE_LINE_ITEM_LEVEL_REVENUE', 'AD_EXCHANGE_LINE_ITEM_LEVEL_IMPRESSIONS'],
                'dateRangeType': 'CUSTOM_DATE',
                'startDate': {'year': start.year, 'month': start.month, 'day': start.day},
                'endDate': {'year': today.year, 'month': today.month, 'day': today.day}
            }
        }
        job = report_service.runReportJob(job)
        job_id = job['id']
        while True:
            st = report_service.getReportJobStatus(job_id)
            if st == 'COMPLETED': break
            elif st == 'FAILED': raise Exception("Report Job Failed")

        url = report_service.getReportDownloadUrlWithOptions(job_id, 'CSV_DUMP')
        text = gzip.decompress(requests.get(url).content).decode('utf-8-sig', errors='ignore')
        reader = csv.DictReader([l for l in text.splitlines() if l.strip()])
        adunit_doms = set()
        for r in reader:
            ad_u = r.get('Dimension.AD_UNIT_NAME') or r.get('AD_UNIT_NAME') or ''
            dom = extract_domain_from_row(r, ad_u)
            if dom and dom != 'mbelik.com':
                adunit_doms.add(dom)
        print(f"\n3. AD_UNIT_NAME -> Found {len(adunit_doms)} domains:")
        for d in sorted(list(adunit_doms)):
            print(f"   - {d}")
        all_found_domains.update(adunit_doms)
    except Exception as e:
        print(f"AD_UNIT_NAME failed: {e}")

    print("\n" + "=" * 70)
    print(f"TOTAL DOMAIN UNIK DITEMUKAN DARI SELURUH API: {len(all_found_domains)}")
    print("Daftar Total Domain:")
    for d in sorted(list(all_found_domains)):
        print(f" -> {d}")
    print("=" * 70)

if __name__ == "__main__":
    debug_list_all_domains()
