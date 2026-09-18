from pydantic import BaseModel
from datetime import date as DateType, datetime
from typing import List, Optional, Any

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True

# Dashboard Schemas
class SummaryMetrics(BaseModel):
    total_spend: float
    total_revenue: float
    net_profit: float
    roi: float
    profit_margin: float
    period_start: str
    period_end: str
    currency: str = "IDR"
    last_synced_at: Optional[str] = None
    spend_change_pct: Optional[float] = None
    revenue_change_pct: Optional[float] = None
    profit_change_pct: Optional[float] = None
    roi_change_pct: Optional[float] = None
    comparison_period_label: Optional[str] = None



class DailyTrendItem(BaseModel):
    date: str
    spend: float
    revenue: float
    profit: float
    roi: float
    margin: float

class AccountBreakdownItem(BaseModel):
    customer_id: str
    account_name: str
    total_spend: float
    impressions: int
    clicks: int
    cpc: float
    ctr: float
    campaign_count: int
    spend_change_pct: Optional[float] = None
    comparison_period_label: Optional[str] = None

class CampaignBreakdownItem(BaseModel):
    customer_id: str
    account_name: str
    campaign_name: str
    total_spend: float
    impressions: int
    clicks: int
    cpc: float
    ctr: float

class SiteBreakdownItem(BaseModel):
    domain: str
    total_revenue: float
    total_spend: float = 0.0
    net_profit: float = 0.0
    roi: float = 0.0
    profit_margin: float = 0.0
    ad_requests: int = 0
    matched_requests: int = 0
    match_rate: float = 0.0
    impressions: int = 0
    clicks: int = 0
    ecpm: float = 0.0
    ad_unit_count: int = 1
    assigned_customer_ids: List[str] = []
    revenue_change_pct: Optional[float] = None
    spend_change_pct: Optional[float] = None
    profit_change_pct: Optional[float] = None
    roi_change_pct: Optional[float] = None
    comparison_period_label: Optional[str] = None
    has_auto_export: bool = False

class PlacementBreakdownItem(BaseModel):
    domain: str
    ad_unit: str
    total_revenue: float
    impressions: int
    clicks: int
    ecpm: float
    ad_requests: int = 0
    matched_requests: int = 0
    match_rate: float = 0.0
    ctr: float = 0.0
    pricing_rule_name: Optional[str] = "All Rules"
    revenue_change_pct: Optional[float] = None
    ecpm_change_pct: Optional[float] = None
    comparison_period_label: Optional[str] = None

class CountryBreakdownItem(BaseModel):
    country: str
    country_code: str
    flag_emoji: str = "🌐"
    spend: float
    revenue: float
    net_profit: float
    roi: float
    ecpm: float
    ad_requests: int = 0
    matched_requests: int = 0
    match_rate: float
    ctr: float
    impressions: int
    clicks: int
    upr: Optional[float] = 0.0
    pricing_rule_name: Optional[str] = "All Rules"
    rpm: float = 0.0

class SyncResponse(BaseModel):
    status: str
    message: str
    records_synced: int
    sync_date_start: str
    sync_date_end: str
    is_mock_data: bool

class SettingsStatusResponse(BaseModel):
    use_mock_data: bool
    google_ads_configured: bool
    gam_configured: bool
    configured_customer_ids: List[str]
    gam_network_code: Optional[str]
    missing_fields: List[str] = []
    currency: str = "IDR"

# Google Ads Account Management Schemas
class GoogleAdsAccountCreate(BaseModel):
    customer_id: str
    account_name: Optional[str] = None
    assigned_domain: Optional[str] = None

class GoogleAdsAccountUpdate(BaseModel):
    account_name: Optional[str] = None
    assigned_domain: Optional[str] = None

class GoogleAdsAccountResponse(BaseModel):
    id: int
    customer_id: str
    account_name: Optional[str] = None
    assigned_domain: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# JSON Export Target Management Schemas
class JSONExportTargetBase(BaseModel):
    domain: str
    target_filepath: str
    start_hour: int = 10
    end_hour: int = 23
    is_active: bool = True

    # Conversion Tracking Settings
    conversion_enabled: bool = True
    conversion_send_to: Optional[str] = None
    conversion_currency: str = "IDR"
    pv1_value: float = 0.0
    pv2_value: float = 1000.0
    pv3_value: float = 3000.0
    pv4_value: float = 6000.0

    # GAM Ad Unit Slot Paths
    slot_header: Optional[str] = None
    slot_feed: Optional[str] = None
    slot_side1: Optional[str] = None
    slot_side2: Optional[str] = None
    slot_interstitial: Optional[str] = None
    slot_anchor: Optional[str] = None

class JSONExportTargetCreate(JSONExportTargetBase):
    pass

class JSONExportTargetUpdate(BaseModel):
    domain: Optional[str] = None
    target_filepath: Optional[str] = None
    start_hour: Optional[int] = None
    end_hour: Optional[int] = None
    is_active: Optional[bool] = None

    conversion_enabled: Optional[bool] = None
    conversion_send_to: Optional[str] = None
    conversion_currency: Optional[str] = None
    pv1_value: Optional[float] = None
    pv2_value: Optional[float] = None
    pv3_value: Optional[float] = None
    pv4_value: Optional[float] = None

    slot_header: Optional[str] = None
    slot_feed: Optional[str] = None
    slot_side1: Optional[str] = None
    slot_side2: Optional[str] = None
    slot_interstitial: Optional[str] = None
    slot_anchor: Optional[str] = None

class JSONExportTargetResponse(JSONExportTargetBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Pricing Config Schemas
class PricingRuleSchema(BaseModel):
    cpm: int
    target_key: str
    floor_key: str

class PricingAdjustmentsSchema(BaseModel):
    high_mr_threshold: Optional[float] = 85.0
    high_mr_boost_pct: Optional[float] = 25.0
    med_mr_threshold: Optional[float] = 70.0
    med_mr_boost_pct: Optional[float] = 10.0
    low_mr_threshold: Optional[float] = 50.0
    low_mr_penalty_pct: Optional[float] = -15.0

class PricingConfigSchema(BaseModel):
    target_mr: float = 65.0
    default_pricing: str = "google_optimize"
    device_settings: Optional[dict] = None
    adjustments: Optional[PricingAdjustmentsSchema] = None
    rules: List[PricingRuleSchema]



