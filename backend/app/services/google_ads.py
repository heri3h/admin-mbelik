import logging
import random
from datetime import datetime, timedelta, date
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

class GoogleAdsService:
    @property
    def use_mock(self) -> bool:
        return bool(settings.USE_MOCK_DATA)

    def fetch_daily_metrics(self, start_date: date, end_date: date, customer_ids: List[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch daily metrics for all configured Google Ads Customer IDs.
        """
        if self.use_mock:
            return self._generate_mock_data(start_date, end_date, customer_ids=customer_ids)
        
        try:
            return self._fetch_live_google_ads_data(start_date, end_date, customer_ids=customer_ids)
        except Exception as e:
            logger.error(f"Failed to fetch live Google Ads data ({e}). Falling back to mock data.")
            return self._generate_mock_data(start_date, end_date, customer_ids=customer_ids)

    def _fetch_live_google_ads_data(self, start_date: date, end_date: date, customer_ids: List[str] = None) -> List[Dict[str, Any]]:
        from google.ads.googleads.client import GoogleAdsClient
        from google.ads.googleads.errors import GoogleAdsException

        credentials = {
            "developer_token": settings.GOOGLE_ADS_DEVELOPER_TOKEN,
            "client_id": settings.GOOGLE_ADS_CLIENT_ID,
            "client_secret": settings.GOOGLE_ADS_CLIENT_SECRET,
            "refresh_token": settings.GOOGLE_ADS_REFRESH_TOKEN,
            "use_proto_plus": True
        }
        if settings.GOOGLE_ADS_LOGIN_CUSTOMER_ID:
            credentials["login_customer_id"] = settings.GOOGLE_ADS_LOGIN_CUSTOMER_ID.replace("-", "")

        googleads_client = GoogleAdsClient.load_from_dict(credentials)
        ga_service = googleads_client.get_service("GoogleAdsService")

        formatted_start = start_date.strftime("%Y-%m-%d")
        formatted_end = end_date.strftime("%Y-%m-%d")

        query = f"""
            SELECT
                segments.date,
                customer.id,
                customer.descriptive_name,
                campaign.name,
                metrics.cost_micros,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.average_cpc
            FROM campaign
            WHERE segments.date BETWEEN '{formatted_start}' AND '{formatted_end}'
        """

        results = []
        cids = customer_ids or settings.customer_ids_list
        if not cids:
            cids = ["default"]

        for cid in cids:
            clean_cid = cid.replace("-", "")
            try:
                stream = ga_service.search_stream(customer_id=clean_cid, query=query)
                for batch in stream:
                    for row in batch.results:
                        cost = row.metrics.cost_micros / 1000000.0 if row.metrics.cost_micros else 0.0
                        cpc = row.metrics.average_cpc / 1000000.0 if row.metrics.average_cpc else 0.0
                        ctr = row.metrics.ctr * 100.0 if row.metrics.ctr else 0.0
                        
                        row_date = datetime.strptime(row.segments.date, "%Y-%m-%d").date()
                        results.append({
                            "date": row_date,
                            "customer_id": cid,
                            "account_name": row.customer.descriptive_name or f"Account-{cid}",
                            "campaign_name": row.campaign.name or "General Campaign",
                            "spend": round(cost, 2),
                            "impressions": int(row.metrics.impressions),
                            "clicks": int(row.metrics.clicks),
                            "cpc": round(cpc, 2),
                            "ctr": round(ctr, 2)
                        })
            except GoogleAdsException as ex:
                logger.error(f"Google Ads API Error for Customer ID {cid}: {ex}")
                raise RuntimeError(f"Google Ads Customer ID {cid} Error: {ex.failure.errors[0].message if ex.failure.errors else ex}")

        return results

    def _generate_mock_data(self, start_date: date, end_date: date, customer_ids: List[str] = None) -> List[Dict[str, Any]]:
        results = []
        if customer_ids:
            accounts = [
                {"id": cid, "name": f"Google Ads ({cid})", "campaigns": ["Campaign General", "Campaign Performance"]}
                for cid in customer_ids
            ]
        else:
            accounts = [
                {"id": "102-394-8812", "name": "Google Ads - E-Commerce ID", "campaigns": ["Search - Promo Megasale", "Display - Retargeting", "Performance Max - All Products"]},
                {"id": "551-902-1143", "name": "Google Ads - Tech Portal ID", "campaigns": ["Search - Tech Keywords", "YouTube - Video Branding"]},
                {"id": "782-119-4450", "name": "Google Ads - Media Network", "campaigns": ["Search - Breaking News", "Discovery - News Feed"]}
            ]

        curr_date = start_date
        while curr_date <= end_date:
            day_factor = 1.2 if curr_date.weekday() in [0, 1, 2] else 0.95
            
            for acc in accounts:
                for camp in acc["campaigns"]:
                    seed = hash(f"{curr_date.isoformat()}-{acc['id']}-{camp}")
                    rng = random.Random(seed)
                    
                    base_spend = rng.uniform(400000, 1800000) * day_factor
                    cpc = rng.uniform(1500, 4500)
                    clicks = int(base_spend / cpc) if cpc > 0 else rng.randint(100, 500)
                    ctr = rng.uniform(2.5, 6.8)
                    impressions = int((clicks / (ctr / 100))) if ctr > 0 else clicks * 25
                    
                    results.append({
                        "date": curr_date,
                        "customer_id": acc["id"],
                        "account_name": acc["name"],
                        "campaign_name": camp,
                        "spend": round(base_spend, 2),
                        "impressions": impressions,
                        "clicks": clicks,
                        "cpc": round(cpc, 2),
                        "ctr": round(ctr, 2)
                    })
            curr_date += timedelta(days=1)
            
        return results

google_ads_service = GoogleAdsService()
