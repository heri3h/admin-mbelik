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
        
        return self._fetch_live_google_ads_data(start_date, end_date, customer_ids=customer_ids)

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
            except Exception as ex:
                err_str = str(ex)
                logger.error(f"Google Ads API Error for Customer ID {cid}: {err_str}")
                if "invalid_grant" in err_str.lower():
                    raise RuntimeError("Google Ads API Auth Error: Refresh Token is expired or revoked. Please update GOOGLE_ADS_REFRESH_TOKEN in .env.")
                raise RuntimeError(f"Google Ads Customer ID {cid} Error: {err_str}")

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

    def fetch_country_metrics(self, start_date: date, end_date: date, customer_ids: List[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch daily country breakdown metrics for configured Google Ads Customer IDs.
        Adds +11% PPN tax to cost.
        """
        if self.use_mock:
            return self._generate_mock_country_data(start_date, end_date, customer_ids=customer_ids)
        
        return self._fetch_live_google_ads_country_data(start_date, end_date, customer_ids=customer_ids)

    def _fetch_live_google_ads_country_data(self, start_date: date, end_date: date, customer_ids: List[str] = None) -> List[Dict[str, Any]]:
        from google.ads.googleads.client import GoogleAdsClient
        from google.ads.googleads.errors import GoogleAdsException
        from app.services.gam import get_country_meta

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

        cids = customer_ids or settings.customer_ids_list
        if not cids:
            cids = ["default"]

        # 1. Fetch official country mapping from geo_target_constant API for all 219+ countries
        geo_map = getattr(self, '_geo_cache', None)
        if not geo_map:
            geo_map = {}
            try:
                sample_cid = cids[0].replace("-", "")
                query_geo = """
                    SELECT
                        geo_target_constant.id,
                        geo_target_constant.name,
                        geo_target_constant.country_code
                    FROM geo_target_constant
                    WHERE geo_target_constant.status = 'ENABLED'
                """
                stream_geo = ga_service.search_stream(customer_id=sample_cid, query=query_geo)
                for batch in stream_geo:
                    for row in batch.results:
                        g = row.geo_target_constant
                        code = str(g.country_code).upper() if g.country_code else ""
                        c_meta = get_country_meta(code or g.name)
                        geo_map[g.id] = {
                            "country": str(g.name),
                            "code": c_meta.get("code") or code or "XX"
                        }
                self._geo_cache = geo_map
            except Exception as e:
                logger.warning(f"Failed loading geo_target_constant map: {e}")

        formatted_start = start_date.strftime("%Y-%m-%d")
        formatted_end = end_date.strftime("%Y-%m-%d")

        query = f"""
            SELECT
                segments.date,
                customer.id,
                user_location_view.country_criterion_id,
                metrics.cost_micros,
                metrics.impressions,
                metrics.clicks
            FROM user_location_view
            WHERE segments.date BETWEEN '{formatted_start}' AND '{formatted_end}'
        """

        results = []
        for cid in cids:
            clean_cid = cid.replace("-", "")
            try:
                stream = ga_service.search_stream(customer_id=clean_cid, query=query)
                for batch in stream:
                    for row in batch.results:
                        cost = row.metrics.cost_micros / 1000000.0 if row.metrics.cost_micros else 0.0
                        crit_id = getattr(row.user_location_view, 'country_criterion_id', None)
                        
                        meta = geo_map.get(crit_id)
                        if not meta:
                            c_meta = get_country_meta("Unknown")
                            meta = {"country": f"Location #{crit_id}", "code": c_meta.get("code", "XX")}

                        row_date = datetime.strptime(row.segments.date, "%Y-%m-%d").date()
                        results.append({
                            "date": row_date,
                            "customer_id": cid,
                            "country": meta["country"],
                            "country_code": meta["code"],
                            "spend": round(cost, 2),  # Raw spend, +11% tax applied during sync
                            "impressions": int(row.metrics.impressions),
                            "clicks": int(row.metrics.clicks)
                        })
            except Exception as ex:
                err_str = str(ex)
                logger.error(f"Google Ads API Error for Customer ID {cid}: {err_str}")
                if "invalid_grant" in err_str.lower():
                    raise RuntimeError("Google Ads API Auth Error: Refresh Token is expired or revoked. Please update GOOGLE_ADS_REFRESH_TOKEN in .env.")
                raise RuntimeError(f"Google Ads Customer ID {cid} Error: {err_str}")

        return results


    def _generate_mock_country_data(self, start_date: date, end_date: date, customer_ids: List[str] = None) -> List[Dict[str, Any]]:
        results = []
        cids = customer_ids or (settings.customer_ids_list if settings.customer_ids_list else ["102-394-8812", "551-902-1143"])

        countries_distribution = [
            {"country": "Indonesia", "code": "ID", "weight": 0.65, "cpc_mult": 1.0},
            {"country": "United States", "code": "US", "weight": 0.15, "cpc_mult": 3.2},
            {"country": "Malaysia", "code": "MY", "weight": 0.08, "cpc_mult": 1.2},
            {"country": "Singapore", "code": "SG", "weight": 0.05, "cpc_mult": 2.5},
            {"country": "Japan", "code": "JP", "weight": 0.03, "cpc_mult": 2.1},
            {"country": "Australia", "code": "AU", "weight": 0.02, "cpc_mult": 2.4},
            {"country": "Kazakhstan", "code": "KZ", "weight": 0.02, "cpc_mult": 1.1}
        ]

        curr_date = start_date
        while curr_date <= end_date:
            for cid in cids:
                seed = hash(f"{curr_date.isoformat()}-{cid}-country")
                rng = random.Random(seed)
                total_day_spend = rng.uniform(800000, 2500000)

                for c in countries_distribution:
                    c_spend = total_day_spend * c["weight"]
                    cpc = rng.uniform(1500, 3500) * c["cpc_mult"]
                    clicks = max(1, int(c_spend / cpc))
                    imps = clicks * rng.randint(15, 35)

                    results.append({
                        "date": curr_date,
                        "customer_id": cid,
                        "country": c["country"],
                        "country_code": c["code"],
                        "spend": round(c_spend, 2), # Raw spend, +11% tax applied during sync
                        "impressions": imps,
                        "clicks": clicks
                    })
            curr_date += timedelta(days=1)

        return results

google_ads_service = GoogleAdsService()

