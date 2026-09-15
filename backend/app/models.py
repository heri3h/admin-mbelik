from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, UniqueConstraint, Boolean
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class GoogleAdsMetric(Base):
    __tablename__ = "google_ads_metrics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True, nullable=False)
    customer_id = Column(String(50), index=True, nullable=False)
    account_name = Column(String(100), nullable=False)
    campaign_name = Column(String(150), nullable=False)
    spend = Column(Float, default=0.0)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    cpc = Column(Float, default=0.0)
    ctr = Column(Float, default=0.0)
    synced_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('date', 'customer_id', 'campaign_name', name='_date_customer_campaign_uc'),
    )

class GAMMetric(Base):
    __tablename__ = "gam_metrics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True, nullable=False)
    domain = Column(String(100), index=True, nullable=False)
    ad_unit = Column(String(150), nullable=False)
    revenue = Column(Float, default=0.0)
    impressions = Column(Integer, default=0)
    ecpm = Column(Float, default=0.0)
    clicks = Column(Integer, default=0)
    match_rate = Column(Float, default=0.0)
    ad_requests = Column(Integer, default=0)
    matched_requests = Column(Integer, default=0)
    pricing_rule_name = Column(String(150), nullable=True, default="All Rules")
    synced_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('date', 'domain', 'ad_unit', 'pricing_rule_name', name='_date_domain_adunit_pricing_uc'),
    )

class DailyProfitSummary(Base):
    __tablename__ = "daily_profit_summaries"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    total_spend = Column(Float, default=0.0)
    total_revenue = Column(Float, default=0.0)
    net_profit = Column(Float, default=0.0)
    roi = Column(Float, default=0.0)
    profit_margin = Column(Float, default=0.0)
    synced_at = Column(DateTime, default=datetime.utcnow)

class GoogleAdsAccount(Base):
    __tablename__ = "google_ads_accounts"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(50), unique=True, index=True, nullable=False)
    account_name = Column(String(100), nullable=True)
    assigned_domain = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class JSONExportTarget(Base):
    __tablename__ = "json_export_targets"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(100), nullable=False, index=True)
    target_filepath = Column(String(255), nullable=False)
    start_hour = Column(Integer, default=10)
    end_hour = Column(Integer, default=23)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class GAMCountryMetric(Base):
    __tablename__ = "gam_country_metrics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True, nullable=False)
    domain = Column(String(100), index=True, nullable=False)
    country = Column(String(100), index=True, nullable=False)
    country_code = Column(String(10), nullable=True)
    ad_unit = Column(String(150), nullable=True, default="")
    revenue = Column(Float, default=0.0)
    impressions = Column(Integer, default=0)
    ecpm = Column(Float, default=0.0)
    clicks = Column(Integer, default=0)
    match_rate = Column(Float, default=0.0)
    ad_requests = Column(Integer, default=0)
    matched_requests = Column(Integer, default=0)
    pricing_rule_name = Column(String(150), nullable=True, default="All Rules")
    synced_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('date', 'domain', 'country', 'ad_unit', 'pricing_rule_name', name='_date_domain_country_adunit_pricing_uc'),
    )



