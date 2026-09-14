import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.config import settings, BASE_DIR

def check_network_timezone():
    print("=" * 60)
    print("=== INSPEKSI TIMEZONE JARINGAN GAM (AD MANAGER) ===")
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

    network_service = client.GetService('NetworkService', version='v202602')

    try:
        net = network_service.getCurrentNetwork()
        print("Network Code    :", getattr(net, 'networkCode', 'N/A'))
        print("Network Name    :", getattr(net, 'displayName', 'N/A'))
        print("Time Zone GAM   :", getattr(net, 'timeZone', 'N/A'))
        print("Currency Code   :", getattr(net, 'currencyCode', 'N/A'))
    except Exception as e:
        print("Error fetching network settings:", e)

if __name__ == "__main__":
    check_network_timezone()
