import os
import json
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Dict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE_PATH = os.path.join(BASE_DIR, ".env")

class Settings(BaseSettings):
    PORT: int = 8000
    SECRET_KEY: str = "supersecretjwtkey_change_me_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    DATABASE_URL: str = "sqlite:///./ad_analytics.db"
    
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    
    CURRENCY: str = "IDR"
    USE_MOCK_DATA: bool = True
    
    # Optional Site/Subdomain Custom Mapping (JSON string in .env)
    # Example: SITE_MAPPING='{"gg": "mbelik.com", "blq": "sub.mbelik.com"}'
    SITE_MAPPING: Optional[str] = None
    
    # Google Ads API Credentials
    GOOGLE_ADS_DEVELOPER_TOKEN: Optional[str] = None
    GOOGLE_ADS_CLIENT_ID: Optional[str] = None
    GOOGLE_ADS_CLIENT_SECRET: Optional[str] = None
    GOOGLE_ADS_REFRESH_TOKEN: Optional[str] = None
    GOOGLE_ADS_CUSTOMER_IDS: Optional[str] = None  # Comma separated
    GOOGLE_ADS_LOGIN_CUSTOMER_ID: Optional[str] = None

    # Google Ad Manager API Credentials
    GAM_NETWORK_CODE: Optional[str] = None
    GAM_APPLICATION_NAME: str = "AdAnalyticsDashboard"
    GAM_JSON_KEY_FILE_PATH: Optional[str] = "./gam_service_account.json"
    GAM_CLIENT_ID: Optional[str] = None
    GAM_CLIENT_SECRET: Optional[str] = None
    GAM_REFRESH_TOKEN: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH if os.path.exists(ENV_FILE_PATH) else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def SITE_MAPPING_DICT(self) -> Dict[str, str]:
        if not self.SITE_MAPPING:
            return {}
        try:
            return json.loads(self.SITE_MAPPING)
        except Exception:
            return {}

    @property
    def customer_ids_list(self) -> List[str]:
        if not self.GOOGLE_ADS_CUSTOMER_IDS:
            return []
        return [cid.strip() for cid in self.GOOGLE_ADS_CUSTOMER_IDS.split(",") if cid.strip()]

    def is_placeholder(self, val: Optional[str]) -> bool:
        if not val:
            return True
        v = val.strip().lower()
        return "your_" in v or "xxx_" in v or "change_me" in v

    @property
    def is_google_ads_configured(self) -> bool:
        return bool(
            self.GOOGLE_ADS_DEVELOPER_TOKEN and not self.is_placeholder(self.GOOGLE_ADS_DEVELOPER_TOKEN)
            and self.GOOGLE_ADS_CLIENT_ID and not self.is_placeholder(self.GOOGLE_ADS_CLIENT_ID)
            and self.GOOGLE_ADS_CLIENT_SECRET and not self.is_placeholder(self.GOOGLE_ADS_CLIENT_SECRET)
            and self.GOOGLE_ADS_REFRESH_TOKEN and not self.is_placeholder(self.GOOGLE_ADS_REFRESH_TOKEN)
            and self.GOOGLE_ADS_CUSTOMER_IDS and not self.is_placeholder(self.GOOGLE_ADS_CUSTOMER_IDS)
        )

    @property
    def is_gam_configured(self) -> bool:
        if not self.GAM_NETWORK_CODE or self.is_placeholder(self.GAM_NETWORK_CODE):
            return False
        
        json_path = self.GAM_JSON_KEY_FILE_PATH
        if json_path and not os.path.isabs(json_path):
            json_path = os.path.join(BASE_DIR, json_path)
            
        has_json = bool(json_path and os.path.exists(json_path))
        has_oauth = bool(
            self.GAM_CLIENT_ID and not self.is_placeholder(self.GAM_CLIENT_ID)
            and self.GAM_CLIENT_SECRET and not self.is_placeholder(self.GAM_CLIENT_SECRET)
            and self.GAM_REFRESH_TOKEN and not self.is_placeholder(self.GAM_REFRESH_TOKEN)
        )
        return has_json or has_oauth

settings = Settings()
