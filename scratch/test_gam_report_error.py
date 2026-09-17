import sys
import os
from datetime import date, timedelta
from googleads import ad_manager, oauth2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.config import settings, BASE_DIR
from app.services.gam import LOCKED_PRIMARY_GAM_COLUMNS

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

print("Testing GAM Report Job with DEVICE_CATEGORY_NAME...")
report_job_query = {
    'dimensions': ['DATE', 'DEVICE_CATEGORY_NAME', 'SITE_NAME'],
    'columns': LOCKED_PRIMARY_GAM_COLUMNS,
    'dateRangeType': 'CUSTOM_DATE',
    'startDate': {'year': yesterday.year, 'month': yesterday.month, 'day': yesterday.day},
    'endDate': {'year': yesterday.year, 'month': yesterday.month, 'day': yesterday.day},
    'timeZoneType': 'TIME_ZONE_OF_NETWORK'
}

try:
    report_job = {'reportQuery': report_job_query}
    res = report_service.runReportJob(report_job)
    print(f"Success! Job ID: {res['id']}")
except Exception as e:
    print(f"FAILED with error: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting GAM Report Job with DEVICE_CATEGORY_NAME & COUNTRY_NAME...")
report_job_query2 = {
    'dimensions': ['DATE', 'COUNTRY_NAME', 'DEVICE_CATEGORY_NAME', 'SITE_NAME'],
    'columns': LOCKED_PRIMARY_GAM_COLUMNS,
    'dateRangeType': 'CUSTOM_DATE',
    'startDate': {'year': yesterday.year, 'month': yesterday.month, 'day': yesterday.day},
    'endDate': {'year': yesterday.year, 'month': yesterday.month, 'day': yesterday.day},
    'timeZoneType': 'TIME_ZONE_OF_NETWORK'
}

try:
    report_job2 = {'reportQuery': report_job_query2}
    res2 = report_service.runReportJob(report_job2)
    print(f"Success 2! Job ID: {res2['id']}")
except Exception as e:
    print(f"FAILED 2 with error: {e}")
