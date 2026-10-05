import sys
from datetime import date
from app.config import settings
from app.services.google_ads import google_ads_service
from google.ads.googleads.client import GoogleAdsClient

credentials = {
    'developer_token': settings.GOOGLE_ADS_DEVELOPER_TOKEN,
    'client_id': settings.GOOGLE_ADS_CLIENT_ID,
    'client_secret': settings.GOOGLE_ADS_CLIENT_SECRET,
    'refresh_token': settings.GOOGLE_ADS_REFRESH_TOKEN,
    'use_proto_plus': True,
    'login_customer_id': '4400151880'
}

googleads_client = GoogleAdsClient.load_from_dict(credentials)
ga_service = googleads_client.get_service('GoogleAdsService')
device_enum = googleads_client.enums.DeviceEnum

all_cids = google_ads_service._get_effective_cids(ga_service)

query = """
    SELECT
        segments.date,
        segments.device,
        customer.id,
        metrics.cost_micros,
        metrics.impressions,
        metrics.clicks
    FROM campaign
    WHERE segments.date = '2026-09-30'
"""

device_spend = {'mobile': 0.0, 'desktop': 0.0, 'tablet': 0.0, 'other': 0.0}
device_clicks = {'mobile': 0, 'desktop': 0, 'tablet': 0, 'other': 0}
device_imps = {'mobile': 0, 'desktop': 0, 'tablet': 0, 'other': 0}

for cid in all_cids:
    clean_cid = cid.replace('-', '')
    try:
        stream = google_ads_service._search_stream_with_retry(ga_service, clean_cid, query)
        if not stream:
            continue
        for batch in stream:
            for row in batch.results:
                dev_raw = int(row.segments.device)
                dev_name = device_enum(dev_raw).name if callable(device_enum) else str(dev_raw)
                
                cost = row.metrics.cost_micros / 1000000.0 if row.metrics.cost_micros else 0.0
                imps = int(row.metrics.impressions) if row.metrics.impressions else 0
                clks = int(row.metrics.clicks) if row.metrics.clicks else 0

                cat = 'mobile' if dev_name in ['MOBILE', 'HIGH_END_MOBILE'] else ('desktop' if dev_name == 'DESKTOP' else ('tablet' if dev_name == 'TABLET' else 'other'))
                device_spend[cat] += cost
                device_clicks[cat] += clks
                device_imps[cat] += imps
    except Exception as e:
        pass

total_raw = sum(device_spend.values())
total_tax = total_raw * 1.11

print("=" * 65)
print("     DEBUG GOOGLE ADS SPEND BY DEVICE (YESTERDAY: 2026-09-30)")
print("=" * 65)
print(f"📱 MOBILE SPEND  : Rp {device_spend['mobile']:>12,.2f}  |  +11% PPN: Rp {device_spend['mobile']*1.11:>12,.2f}  |  Clicks: {device_clicks['mobile']:>6,}  |  Imps: {device_imps['mobile']:>8,}")
print(f"💻 DESKTOP SPEND : Rp {device_spend['desktop']:>12,.2f}  |  +11% PPN: Rp {device_spend['desktop']*1.11:>12,.2f}  |  Clicks: {device_clicks['desktop']:>6,}  |  Imps: {device_imps['desktop']:>8,}")
print(f"📱 TABLET SPEND  : Rp {device_spend['tablet']:>12,.2f}  |  +11% PPN: Rp {device_spend['tablet']*1.11:>12,.2f}  |  Clicks: {device_clicks['tablet']:>6,}  |  Imps: {device_imps['tablet']:>8,}")
print("-" * 65)
print(f"💰 TOTAL SPEND   : Rp {total_raw:>12,.2f}  |  +11% PPN: Rp {total_tax:>12,.2f}  |  Clicks: {sum(device_clicks.values()):>6,}  |  Imps: {sum(device_imps.values()):>8,}")
print("=" * 65)
