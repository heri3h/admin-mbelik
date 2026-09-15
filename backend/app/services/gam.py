import logging
import random
import os
import time
from datetime import datetime, timedelta, date, timezone
from typing import List, Dict, Any
from app.config import settings, BASE_DIR

logger = logging.getLogger(__name__)

# WIB Timezone (GMT+7)
WIB = timezone(timedelta(hours=7))

# ==============================================================================
# STRICTLY LOCKED GAM API AD EXCHANGE COLUMN SET (DO NOT ALTER OR MODIFY)
# Matches exact 5 Ad Exchange metrics: Impressions, Revenue, Clicks, Total Requests, Responses Served
# ==============================================================================
LOCKED_PRIMARY_GAM_COLUMNS = [
    'AD_EXCHANGE_LINE_ITEM_LEVEL_IMPRESSIONS',
    'AD_EXCHANGE_LINE_ITEM_LEVEL_REVENUE',
    'AD_EXCHANGE_LINE_ITEM_LEVEL_CLICKS',
    'AD_EXCHANGE_TOTAL_REQUESTS',
    'AD_EXCHANGE_RESPONSES_SERVED'
]

import re

def parse_gam_date(v_str: Any, default_date: date) -> date:
    if not v_str:
        return default_date
    clean_v = str(v_str).strip().split('T')[0].split(' ')[0]
    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y/%m/%d", "%d-%m-%Y"]:
        try:
            return datetime.strptime(clean_v, fmt).date()
        except ValueError:
            pass
    return default_date

def extract_domain_from_row(row: Dict[str, str], ad_unit: str = "") -> str:
    """
    Extract site domain directly from GAM API response row:
    1. Dimension.SITE_NAME / AD_EXCHANGE_URL_NAME / DOMAIN_NAME / URL_NAME
    2. CUSTOM_TARGETING_VALUE_PAIR
    3. Known domain matching in ad_unit string
    4. Custom SITE_MAPPING in .env
    5. Built-in token prefix mapping
    6. Fallback domain
    """
    for k, v in row.items():
        if not k or not v:
            continue
        k_up = k.upper()
        v_str = str(v).strip()

        if any(kw in k_up for kw in ['URL', 'DOMAIN', 'SITE', 'HOST']) and 'DATE' not in k_up and 'UNIT' not in k_up and 'ID' not in k_up and 'TYPE' not in k_up and 'STATUS' not in k_up and v_str:
            clean_val = v_str.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0].strip().lower()
            if clean_val and clean_val not in ["all domains", "-", "none", "null", "unknown", "standard ad unit"]:
                return clean_val

        # Check custom targeting (e.g. setTargeting('domain', currentDomain))
        if any(kw in k_up for kw in ['TARGETING', 'CUSTOM', 'KEY_VALUE']) and v_str:
            v_lower = v_str.lower()
            match = re.search(r'domain\s*[:=]\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', v_lower)
            if match:
                clean_val = match.group(1).replace('www.', '').strip()
                if clean_val and clean_val not in ["all domains", "-", "none", "null", "unknown"]:
                    return clean_val
            if 'domain=' in v_lower or 'domain:' in v_lower:
                val = v_lower.split('domain=')[-1].split(';')[0].split(',')[0].strip()
                clean_val = val.replace('www.', '').strip()
                if clean_val and clean_val not in ["all domains", "-", "none", "null", "unknown"]:
                    return clean_val

    unit_str = ad_unit.strip() if ad_unit else ""
    unit_lower = unit_str.lower()

    # Check known domain names directly in ad_unit string
    for known_dom in ["spotgames.top", "2b.nubmaster.com", "baleq.me", "dpr.skuy.me", "polpasulsa.com", "play.gemol.me", "gemol.me"]:
        if known_dom in unit_lower:
            return known_dom

    # Check custom SITE_MAPPING in .env
    site_mapping = getattr(settings, "SITE_MAPPING_DICT", {})
    for prefix, mapped_domain in site_mapping.items():
        if prefix.lower() in unit_lower:
            return mapped_domain.lower().strip()

    # Built-in tokenized prefix mappings
    DEFAULT_PREFIX_MAP = [
        ('gemol', 'play.gemol.me'),
        ('gm', 'play.gemol.me'),
        ('spotgames', 'spotgames.top'),
        ('spot', 'spotgames.top'),
        ('sg', 'spotgames.top'),
        ('2b', '2b.nubmaster.com'),
        ('nubmaster', '2b.nubmaster.com'),
        ('baleq', 'baleq.me'),
        ('blq', 'baleq.me'),
        ('dpr', 'dpr.skuy.me'),
        ('skuy', 'dpr.skuy.me'),
        ('polpasulsa', 'polpasulsa.com'),
        ('pol', 'polpasulsa.com'),
        ('pas', 'polpasulsa.com'),
    ]

    tokens = [t for t in re.split(r'[^a-z0-9.]+', unit_lower) if t]
    for pref, dom in DEFAULT_PREFIX_MAP:
        if pref in tokens:
            return dom

    for pref, dom in DEFAULT_PREFIX_MAP:
        if len(pref) >= 3 and pref in unit_lower:
            return dom

    # General TLD domain regex extraction from ad_unit string
    domain_match = re.search(r'([a-zA-Z0-9-]+\.(?:com|top|me|skuy\.me|nubmaster\.com|id|net|org|co\.id|xyz|site|info|online|tech|app|io|cc|vip|store|shop|biz|pro|asia|club|live|news|space|work|media|digital))', unit_lower)
    if domain_match:
        return domain_match.group(1).lower()

    # Underscore domain regex extraction (e.g., site_com, site_id, site_co_id)
    und_match = re.search(r'([a-zA-Z0-9-]+)_(com|top|me|id|net|org|xyz|site|info)(?:_|$)', unit_lower)
    if und_match:
        return f"{und_match.group(1)}.{und_match.group(2)}".lower()

    if ' > ' in unit_str:
        first_part = unit_str.split(' > ')[0].strip().lower()
        if first_part and first_part not in ["all", "global", "root", "standard ad unit"]:
            return first_part.replace(' ', '-')

    if '/' in unit_str and not unit_str.startswith('http'):
        parts = [p.strip() for p in unit_str.split('/') if p.strip()]
        if len(parts) > 1:
            site_candidate = parts[0] if parts[0].lower() not in ["all", "global", "root"] else parts[1]
            return site_candidate.lower().replace(' ', '-')

    if '.' in unit_str and not unit_str.startswith('.'):
        for p in unit_str.split():
            if '.' in p and not p.endswith('.'):
                return p.strip().lower()

    return "mbelik.com"

COUNTRY_NAME_TO_CODE = {
    "indonesia": "ID",
    "united states": "US",
    "united states of america": "US",
    "usa": "US",
    "us": "US",
    "malaysia": "MY",
    "singapore": "SG",
    "japan": "JP",
    "australia": "AU",
    "united kingdom": "GB",
    "great britain": "GB",
    "uk": "GB",
    "germany": "DE",
    "france": "FR",
    "india": "IN",
    "canada": "CA",
    "brazil": "BR",
    "philippines": "PH",
    "vietnam": "VN",
    "thailand": "TH",
    "taiwan": "TW",
    "south korea": "KR",
    "korea, republic of": "KR",
    "korea": "KR",
    "netherlands": "NL",
    "spain": "ES",
    "mexico": "MX",
    "turkey": "TR",
    "türkiye": "TR",
    "italy": "IT",
    "saudi arabia": "SA",
    "united arab emirates": "AE",
    "uae": "AE",
    "egypt": "EG",
    "hong kong": "HK",
    "poland": "PL",
    "nigeria": "NG",
    "colombia": "CO",
    "pakistan": "PK",
    "argentina": "AR",
    "algeria": "DZ",
    "iraq": "IQ",
    "morocco": "MA",
    "chile": "CL",
    "peru": "PE",
    "romania": "RO",
    "czechia": "CZ",
    "czech republic": "CZ",
    "ukraine": "UA",
    "south africa": "ZA",
    "switzerland": "CH",
    "sweden": "SE",
    "norway": "NO",
    "belgium": "BE",
    "austria": "AT",
    "greece": "GR",
    "portugal": "PT",
    "new zealand": "NZ",
    "israel": "IL",
    "ireland": "IE",
    "finland": "FI",
    "denmark": "DK",
    "hungary": "HU",
    "bangladesh": "BD",
    "sri lanka": "LK",
    "nepal": "NP",
    "cambodia": "KH",
    "laos": "LA",
    "myanmar": "MM",
    "mongolia": "MN",
    "macao": "MO",
    "macau": "MO",
    "kuwait": "KW",
    "qatar": "QA",
    "oman": "OM",
    "bahrain": "BH",
    "jordan": "JO",
    "lebanon": "LB",
    "croatia": "HR",
    "serbia": "RS",
    "slovakia": "SK",
    "slovenia": "SI",
    "bulgaria": "BG",
    "lithuania": "LT",
    "latvia": "LV",
    "estonia": "EE",
    "cyprus": "CY",
    "malta": "MT",
    "luxembourg": "LU",
    "iceland": "IS",
    "ecuador": "EC",
    "bolivia": "BO",
    "paraguay": "PY",
    "uruguay": "UY",
    "venezuela": "VE",
    "costa rica": "CR",
    "panama": "PA",
    "dominican republic": "DO",
    "guatemala": "GT",
    "honduras": "HN",
    "el salvador": "SV",
    "nicaragua": "NI",
    "puerto rico": "PR",
    "jamaica": "JM",
    "trinidad and tobago": "TT",
    "kenya": "KE",
    "ghana": "GH",
    "ethiopia": "ET",
    "tanzania": "TZ",
    "uganda": "UG",
    "senegal": "SN",
    "ivory coast": "CI",
    "côte d'ivoire": "CI",
    "cameroon": "CM",
    "angola": "AO",
    "tunisia": "TN",
    "libya": "LY",
    "sudan": "SD",
    "zambia": "ZM",
    "zimbabwe": "ZW",
    "kazakhstan": "KZ",
    "uzbekistan": "UZ",
    "azerbaijan": "AZ",
    "georgia": "GE",
    "armenia": "AM",
    "belarus": "BY",
    "moldova": "MD",
    "albania": "AL",
    "north macedonia": "MK",
    "bosnia and herzegovina": "BA",
    "montenegro": "ME",
    "others": "XX",
    "unknown region": "XX",
}

def get_country_meta(country_name: str) -> dict:
    if not country_name:
        return {"code": "ID", "flag": "🇮🇩"}
    
    raw = country_name.strip()
    key = raw.lower()

    if len(raw) == 2 and raw.isalpha():
        code = raw.upper()
        flag = chr(127397 + ord(code[0])) + chr(127397 + ord(code[1]))
        return {"code": code, "flag": flag}

    if key in COUNTRY_NAME_TO_CODE:
        code = COUNTRY_NAME_TO_CODE[key]
        if code == "XX":
            return {"code": "XX", "flag": "🌐"}
        flag = chr(127397 + ord(code[0])) + chr(127397 + ord(code[1]))
        return {"code": code, "flag": flag}

    for c_name, code in COUNTRY_NAME_TO_CODE.items():
        if len(c_name) >= 4 and (c_name in key or key in c_name):
            if code == "XX":
                return {"code": "XX", "flag": "🌐"}
            flag = chr(127397 + ord(code[0])) + chr(127397 + ord(code[1]))
            return {"code": code, "flag": flag}

    return {"code": "XX", "flag": "🌐"}

class GAMService:
    @property
    def use_mock(self) -> bool:
        return bool(settings.USE_MOCK_DATA)

    def fetch_daily_metrics(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        Fetch daily metrics for GAM / AdX.
        """
        if self.use_mock:
            return self._generate_mock_data(start_date, end_date)

        try:
            return self._fetch_live_gam_data(start_date, end_date)
        except Exception as e:
            logger.error(f"Failed to fetch live GAM data: {e}")
            return []

    def _fetch_ad_requests_pass(self, report_service, start_date: date, end_date: date) -> Dict[Any, int]:
        """
        Pass 2 of Dual Query API: Fetch inventory metrics per (date, ad_unit) or (date, site)
        from standard GAM Inventory Report.
        """
        requests_map = {}
        req_dim_sets = [
            ['DATE', 'AD_UNIT_NAME'],
            ['DATE', 'SITE_NAME']
        ]
        req_col_sets = [
            ['AD_EXCHANGE_TOTAL_REQUESTS', 'AD_EXCHANGE_RESPONSES_SERVED', 'AD_EXCHANGE_LINE_ITEM_LEVEL_IMPRESSIONS'],
            ['AD_EXCHANGE_TOTAL_REQUESTS', 'AD_EXCHANGE_RESPONSES_SERVED'],
            ['TOTAL_CODE_SERVED_COUNT', 'TOTAL_INVENTORY_LEVEL_UNFILLED_IMPRESSIONS', 'TOTAL_INVENTORY_LEVEL_IMPRESSIONS'],
            ['TOTAL_CODE_SERVED_COUNT', 'TOTAL_INVENTORY_LEVEL_IMPRESSIONS'],
            ['TOTAL_INVENTORY_LEVEL_UNFILLED_IMPRESSIONS', 'TOTAL_INVENTORY_LEVEL_IMPRESSIONS'],
            ['TOTAL_CODE_SERVED_COUNT'],
            ['TOTAL_LINE_ITEM_LEVEL_IMPRESSIONS', 'TOTAL_LINE_ITEM_LEVEL_CLICKS']
        ]

        for dims in req_dim_sets:
            successful = False
            for cols in req_col_sets:
                try:
                    report_job = {
                        'reportQuery': {
                            'dimensions': dims,
                            'columns': cols,
                            'dateRangeType': 'CUSTOM_DATE',
                            'startDate': {'year': start_date.year, 'month': start_date.month, 'day': start_date.day},
                            'endDate': {'year': end_date.year, 'month': end_date.month, 'day': end_date.day},
                            'timeZoneType': 'TIME_ZONE_OF_NETWORK'
                        }
                    }
                    report_job = report_service.runReportJob(report_job)
                    report_job_id = report_job['id']

                    attempts = 0
                    while attempts < 15:
                        job_status = report_service.getReportJobStatus(report_job_id)
                        if job_status == 'COMPLETED':
                            break
                        elif job_status == 'FAILED':
                            raise Exception("Pass 2 Job Failed")
                        time.sleep(1)
                        attempts += 1

                    if attempts >= 15:
                        raise Exception("Pass 2 Job Timed Out")

                    report_download_url = report_service.getReportDownloadUrlWithOptions(report_job_id, 'CSV_DUMP')
                    import requests
                    import csv
                    import gzip

                    res = requests.get(report_download_url)
                    content_bytes = res.content
                    if content_bytes.startswith(b'\x1f\x8b'):
                        content_bytes = gzip.decompress(content_bytes)

                    csv_text = content_bytes.decode('utf-8-sig', errors='ignore')
                    lines = [line for line in csv_text.splitlines() if line.strip()]

                    header_idx = 0
                    for idx, line in enumerate(lines):
                        line_up = line.upper()
                        if ('DATE' in line_up or 'UNIT' in line_up or 'SITE' in line_up) and ('IMPRESSION' in line_up or 'SERVED' in line_up or 'REQUEST' in line_up or 'COLUMN' in line_up):
                            header_idx = idx
                            break

                    reader = csv.DictReader(lines[header_idx:])
                    for row in reader:
                        r_date = start_date
                        unit_or_site = ""
                        code_served = 0
                        unfilled_imps = 0
                        filled_imps = 0

                        for k, v in row.items():
                            if not k or not v:
                                continue
                            k_up = k.upper()
                            v_str = str(v).strip()
                            if 'DATE' in k_up:
                                r_date = parse_gam_date(v_str, start_date)
                            elif 'UNIT' in k_up or 'SITE' in k_up:
                                unit_or_site = v_str.lower()
                            elif ('INVENTORY_LEVEL_AD_REQUESTS' in k_up or 'CODE_SERVED' in k_up or 'TOTAL_REQUESTS' in k_up or 'AD_REQUESTS' in k_up) and 'IMPRESSION' not in k_up:
                                try:
                                    code_served = int(float(v_str))
                                except ValueError:
                                    pass
                            elif 'UNFILLED' in k_up:
                                try:
                                    unfilled_imps = int(float(v_str))
                                except ValueError:
                                    pass
                            elif 'IMPRESSION' in k_up or 'MATCHED' in k_up:
                                try:
                                    filled_imps = int(float(v_str))
                                except ValueError:
                                    pass

                        req_val = 0
                        if code_served > 0:
                            req_val = code_served
                        elif unfilled_imps > 0:
                            req_val = filled_imps + unfilled_imps
                        else:
                            req_val = filled_imps

                        if req_val > 0:
                            if unit_or_site:
                                requests_map[(r_date, unit_or_site)] = req_val
                                clean_unit = unit_or_site.split('(')[0].replace('http://', '').replace('https://', '').replace('www.', '').strip().lower()
                                if clean_unit:
                                    requests_map[(r_date, clean_unit)] = req_val

                            dom = extract_domain_from_row(row, unit_or_site)
                            if dom:
                                requests_map[(r_date, dom)] = requests_map.get((r_date, dom), 0) + req_val

                    if requests_map:
                        successful = True
                        logger.info(f"Pass 2 successfully retrieved inventory requests: {len(requests_map)} keys")
                        break
                except Exception as e:
                    logger.info(f"Pass 2 requests query dims={dims} cols={cols} notice: {e}")
            if successful:
                break

        return requests_map

    def _fetch_live_gam_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        from googleads import ad_manager, oauth2

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

        # Dual Query API Pass 2: Fetch real GAM inventory Ad Requests per ad unit / site
        requests_map = {}
        try:
            requests_map = self._fetch_ad_requests_pass(report_service, start_date, end_date)
            logger.info(f"Dual Query Pass 2 retrieved {len(requests_map)} inventory request entries from GAM")
        except Exception as e:
            logger.warning(f"Dual Query Pass 2 notice: {e}")

        query_configs = [
            {
                'dimension_sets': [
                    ['DATE', 'SITE_NAME', 'UNIFIED_PRICING_RULE_NAME', 'AD_UNIT_NAME'],
                    ['DATE', 'UNIFIED_PRICING_RULE_NAME', 'AD_UNIT_NAME'],
                    ['DATE', 'SITE_NAME', 'AD_UNIT_NAME'],
                    ['DATE', 'SITE_NAME'],
                    ['DATE', 'DOMAIN_NAME', 'AD_UNIT_NAME'],
                    ['DATE', 'DOMAIN_NAME'],
                    ['DATE', 'CUSTOM_TARGETING_VALUE_PAIR', 'AD_UNIT_NAME'],
                    ['DATE', 'CUSTOM_TARGETING_VALUE_PAIR'],
                    ['DATE', 'PLATFORM_NAME', 'SITE_NAME'],
                    ['DATE', 'AD_UNIT_NAME'],
                    ['DATE']
                ],
                'column_sets': [
                    LOCKED_PRIMARY_GAM_COLUMNS,
                    [
                        'AD_EXCHANGE_LINE_ITEM_LEVEL_REVENUE',
                        'AD_EXCHANGE_LINE_ITEM_LEVEL_IMPRESSIONS',
                        'AD_EXCHANGE_LINE_ITEM_LEVEL_CLICKS',
                        'AD_EXCHANGE_LINE_ITEM_LEVEL_WITHOUT_CPD_AVERAGE_ECPM'
                    ],
                    [
                        'TOTAL_LINE_ITEM_LEVEL_CPM_AND_CPC_REVENUE',
                        'TOTAL_LINE_ITEM_LEVEL_IMPRESSIONS',
                        'TOTAL_LINE_ITEM_LEVEL_CLICKS',
                        'TOTAL_LINE_ITEM_LEVEL_WITHOUT_CPD_AVERAGE_ECPM'
                    ],
                    [
                        'AD_EXCHANGE_REVENUE',
                        'AD_EXCHANGE_IMPRESSIONS',
                        'AD_EXCHANGE_CLICKS',
                        'AD_EXCHANGE_AVERAGE_ECPM'
                    ]
                ]
            }
        ]

        last_error = None
        aggregated_results = {}
        seen_domains_per_date = set()

        for config in query_configs:
            successful_config = False
            r_type = config.get('reportType', 'HISTORICAL')
            for dims in config['dimension_sets']:
                successful_dim = False
                for cols in config['column_sets']:
                    try:
                        report_job_query = {
                            'dimensions': dims,
                            'columns': cols,
                            'dateRangeType': 'CUSTOM_DATE',
                            'startDate': {'year': start_date.year, 'month': start_date.month, 'day': start_date.day},
                            'endDate': {'year': end_date.year, 'month': end_date.month, 'day': end_date.day},
                            'timeZoneType': 'TIME_ZONE_OF_NETWORK'
                        }

                        report_job = {'reportQuery': report_job_query}
                        report_job = report_service.runReportJob(report_job)
                        report_job_id = report_job['id']
                        
                        attempts = 0
                        while attempts < 30:
                            job_status = report_service.getReportJobStatus(report_job_id)
                            if job_status == 'COMPLETED':
                                break
                            elif job_status == 'FAILED':
                                raise Exception("GAM Report Job Failed")
                            time.sleep(1)
                            attempts += 1

                        if attempts >= 30:
                            raise Exception("GAM Report Job Timed Out after 30s")

                        export_format = 'CSV_DUMP'
                        report_download_url = report_service.getReportDownloadUrlWithOptions(
                            report_job_id, export_format
                        )
                        
                        import requests
                        import csv
                        import gzip

                        res = requests.get(report_download_url)
                        content_bytes = res.content
                        if content_bytes.startswith(b'\x1f\x8b'):
                            content_bytes = gzip.decompress(content_bytes)

                        csv_text = content_bytes.decode('utf-8-sig', errors='ignore')
                        lines = [line for line in csv_text.splitlines() if line.strip()]
                        
                        header_idx = 0
                        for idx, line in enumerate(lines):
                            line_up = line.upper()
                            if ('DATE' in line_up or 'SITE' in line_up or 'DOMAIN' in line_up or 'COUNTRY' in line_up or 'URL' in line_up or 'TAG' in line_up) and ('REVENUE' in line_up or 'IMPRESSION' in line_up or 'REQUEST' in line_up or 'COLUMN' in line_up or 'DIMENSION' in line_up):
                                header_idx = idx
                                break

                        reader = csv.DictReader(lines[header_idx:])
                        found_any_row = False
                        
                        for row in reader:
                            # 1. Parse Date
                            row_date = start_date
                            for k, v in row.items():
                                if k and 'DATE' in k.upper() and v:
                                    row_date = parse_gam_date(v, start_date)
                                    break

                            # 2. Parse Ad Unit Name
                            ad_unit = ""
                            for k, v in row.items():
                                if k and ('AD_UNIT' in k.upper() or 'TAG' in k.upper()) and v:
                                    ad_unit = v.strip()
                                    break
                            
                            if not ad_unit:
                                ad_unit = "Standard Ad Unit"

                            # 3. Parse Site Domain (Using SITE_NAME / CUSTOM_TARGETING / AD_EXCHANGE_URL)
                            domain = extract_domain_from_row(row, ad_unit)

                            domain_date_key = (row_date, domain)
                            is_new_domain = domain_date_key not in seen_domains_per_date

                            # 4. Parse Impressions (AD_EXCHANGE_LINE_ITEM_LEVEL_IMPRESSIONS)
                            impressions = 0
                            for k, v in row.items():
                                if k and 'AD_EXCHANGE_LINE_ITEM_LEVEL_IMPRESSIONS' in k.upper() and v:
                                    try:
                                        impressions = int(float(v))
                                        break
                                    except ValueError:
                                        pass
                            if impressions == 0:
                                for k, v in row.items():
                                    if k and 'IMPRESSIONS' in k.upper() and v:
                                        try:
                                            impressions = int(float(v))
                                            break
                                        except ValueError:
                                            pass

                            # 5. Parse Clicks (AD_EXCHANGE_LINE_ITEM_LEVEL_CLICKS)
                            clicks = 0
                            for k, v in row.items():
                                if k and 'AD_EXCHANGE_LINE_ITEM_LEVEL_CLICKS' in k.upper() and v:
                                    try:
                                        clicks = int(float(v))
                                        break
                                    except ValueError:
                                        pass
                            if clicks == 0:
                                for k, v in row.items():
                                    if k and 'CLICKS' in k.upper() and v:
                                        try:
                                            clicks = int(float(v))
                                            break
                                        except ValueError:
                                            pass

                            # 6. Parse Revenue (AD_EXCHANGE_LINE_ITEM_LEVEL_REVENUE)
                            raw_rev = 0.0
                            for k, v in row.items():
                                if k and 'AD_EXCHANGE_LINE_ITEM_LEVEL_REVENUE' in k.upper() and v:
                                    try:
                                        val = float(v)
                                        if val > 0:
                                            raw_rev = val
                                            break
                                    except ValueError:
                                        pass

                            if raw_rev == 0.0:
                                for k, v in row.items():
                                    if k and ('REVENUE' in k.upper() or 'EARNINGS' in k.upper()) and v:
                                        try:
                                            val = float(v)
                                            if val > 0:
                                                raw_rev = val
                                                break
                                        except ValueError:
                                            pass

                            # GAM API ALWAYS returns revenue in microamounts (1,000,000 micros = 1 currency unit)
                            revenue = (raw_rev / 1000000.0) if raw_rev > 0 else 0.0

                            # Calculate precise eCPM (eCPM = Revenue / Impressions * 1000)
                            if impressions > 0 and revenue > 0:
                                ecpm = (revenue / impressions) * 1000.0
                            else:
                                raw_ecpm = 0.0
                                for k, v in row.items():
                                    if k and 'ECPM' in k.upper() and v:
                                        try:
                                            raw_ecpm = float(v)
                                            if raw_ecpm > 0:
                                                break
                                        except ValueError:
                                            pass
                                ecpm = (raw_ecpm / 1000000.0) if raw_ecpm > 0 else 0.0

                            # 7. Parse Total Requests & Unfilled Impressions / Matched Requests
                            matched_requests = impressions
                            ad_requests = 0
                            unfilled_impressions = 0

                            for k, v in row.items():
                                if not k or not v:
                                    continue
                                k_up = k.upper()
                                try:
                                    val_num = int(float(v))
                                    if ('CODE_SERVED' in k_up or 'TOTAL_REQUESTS' in k_up or 'AD_REQUESTS' in k_up) and 'IMPRESSION' not in k_up:
                                        if val_num > ad_requests:
                                            ad_requests = val_num
                                    elif 'UNFILLED' in k_up:
                                        if val_num > unfilled_impressions:
                                            unfilled_impressions = val_num
                                    elif 'MATCHED' in k_up or 'RESPONSES_SERVED' in k_up:
                                        if val_num > matched_requests:
                                            matched_requests = val_num
                                except ValueError:
                                    pass

                            if ad_requests == 0 and unfilled_impressions > 0:
                                ad_requests = matched_requests + unfilled_impressions

                            if ad_requests == 0:
                                unit_raw_key = (row_date, ad_unit.lower().strip())
                                unit_clean_key = (row_date, ad_unit.lower().strip().split('(')[0].strip())
                                dom_key = (row_date, domain.lower().strip())

                                if unit_raw_key in requests_map and requests_map[unit_raw_key] > 0:
                                    ad_requests = requests_map[unit_raw_key]
                                elif unit_clean_key in requests_map and requests_map[unit_clean_key] > 0:
                                    ad_requests = requests_map[unit_clean_key]
                                elif dom_key in requests_map and requests_map[dom_key] > 0:
                                    ad_requests = requests_map[dom_key]
                                else:
                                    ad_requests = matched_requests

                            if ad_requests < matched_requests:
                                ad_requests = matched_requests

                            pricing_rule = "All Rules"
                            for k, v in row.items():
                                if k and ('PRICING_RULE' in k.upper() or 'RULE_NAME' in k.upper()) and v:
                                    pricing_rule = v.strip()
                                    break

                            match_rate = (matched_requests / ad_requests * 100.0) if ad_requests > 0 else 0.0

                            key = (row_date, domain, ad_unit, pricing_rule)
                            if is_new_domain or key not in aggregated_results or revenue > aggregated_results[key]["revenue"]:
                                aggregated_results[key] = {
                                    "date": row_date,
                                    "domain": domain,
                                    "ad_unit": ad_unit,
                                    "pricing_rule_name": pricing_rule,
                                    "revenue": round(revenue, 2),
                                    "impressions": impressions,
                                    "ecpm": round(ecpm, 2),
                                    "clicks": clicks,
                                    "ad_requests": ad_requests,
                                    "matched_requests": matched_requests,
                                    "match_rate": round(match_rate, 2)
                                }
                                seen_domains_per_date.add(domain_date_key)

                            found_any_row = True

                        if found_any_row:
                            successful_dim = True
                            successful_config = True
                            break

                    except Exception as e:
                        last_error = e
                        logger.warning(f"GAM combination r_type={r_type} dims={dims} cols={cols} failed: {e}")

                if successful_dim:
                    logger.info(f"Dim set {dims} completed. Current total domains parsed: {len(seen_domains_per_date)}")
                    break

            if successful_config:
                logger.info(f"Query config r_type={r_type} completed successfully.")
                break

        if aggregated_results:
            logger.info(f"Successfully fetched {len(aggregated_results)} aggregated rows covering {len(seen_domains_per_date)} date-domain pairs from GAM API")
            return list(aggregated_results.values())

        if last_error:
            raise last_error
        return []

    def _generate_mock_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        results = []
        domains = ["spotgames.top", "dpr.skuy.me", "mbelik.com", "2b.nubmaster.com", "baleq.me", "polpasulsa.com"]
        try:
            from app.database import SessionLocal
            from app.models import GoogleAdsAccount
            db = SessionLocal()
            accs = db.query(GoogleAdsAccount.assigned_domain).distinct().all()
            db.close()
            db_doms = [a[0] for a in accs if a[0] and a[0] != "All / Unassigned"]
            if db_doms:
                domains = list(set(domains + db_doms))
        except Exception:
            pass

        units_config = [
            {"name": "Header_Responsive", "base_rev": 1400000, "base_imp": 85000},
            {"name": "InArticle_AdX", "base_rev": 2100000, "base_imp": 120000},
            {"name": "Sidebar_300x600", "base_rev": 950000, "base_imp": 50000}
        ]

        curr_date = start_date
        while curr_date <= end_date:
            multiplier = 1.35 + (0.1 * (curr_date.day % 5))

            for dom in domains:
                for unit in units_config:
                    seed = hash(f"{curr_date.isoformat()}-{dom}-{unit['name']}")
                    rng = random.Random(seed)

                    revenue = unit["base_rev"] * multiplier * rng.uniform(0.9, 1.25)
                    impressions = int(unit["base_imp"] * multiplier * rng.uniform(0.85, 1.15))
                    ecpm = (revenue / impressions * 1000) if impressions > 0 else rng.uniform(15000, 35000)
                    clicks = int(impressions * rng.uniform(0.008, 0.025))

                    ad_requests = int(impressions * rng.uniform(2.6, 3.2))
                    matched_requests = int(impressions * rng.uniform(0.95, 1.05))
                    match_rate = (matched_requests / ad_requests) * 100.0 if ad_requests > 0 else 34.5

                    p_rule = "DFLT GML kz" if dom == "play.gemol.me" else "DFLT GML"
                    results.append({
                        "date": curr_date,
                        "domain": dom,
                        "ad_unit": unit["name"],
                        "pricing_rule_name": p_rule,
                        "revenue": round(revenue, 2),
                        "impressions": impressions,
                        "ecpm": round(ecpm, 2),
                        "clicks": clicks,
                        "ad_requests": ad_requests,
                        "matched_requests": matched_requests,
                        "match_rate": round(match_rate, 2)
                    })
            curr_date += timedelta(days=1)

        return results

    def fetch_country_metrics(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        Fetch GAM metrics with COUNTRY_NAME dimension for exact per-country performance.
        """
        if self.use_mock:
            return self._generate_mock_country_data(start_date, end_date)

        try:
            return self._fetch_live_gam_country_data(start_date, end_date)
        except Exception as e:
            logger.error(f"Failed to fetch live GAM country data: {e}")
            return []

    def _fetch_live_gam_country_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        from googleads import ad_manager, oauth2

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

        # Dual Query API Pass 2: Fetch real GAM inventory Ad Requests per ad unit / site
        requests_map = {}
        try:
            requests_map = self._fetch_ad_requests_pass(report_service, start_date, end_date)
        except Exception as e:
            logger.warning(f"Country Dual Query Pass 2 notice: {e}")

        query_configs = [
            {
                'dimension_sets': [
                    ['DATE', 'COUNTRY_NAME', 'UNIFIED_PRICING_RULE_NAME', 'SITE_NAME', 'AD_UNIT_NAME'],
                    ['DATE', 'COUNTRY_NAME', 'SITE_NAME', 'AD_UNIT_NAME'],
                    ['DATE', 'COUNTRY_NAME', 'UNIFIED_PRICING_RULE_NAME', 'SITE_NAME'],
                    ['DATE', 'COUNTRY_NAME', 'SITE_NAME'],
                    ['DATE', 'COUNTRY_NAME', 'UNIFIED_PRICING_RULE_NAME', 'AD_UNIT_NAME'],
                    ['DATE', 'COUNTRY_NAME', 'UNIFIED_PRICING_RULE_NAME'],
                    ['DATE', 'COUNTRY_NAME', 'AD_UNIT_NAME'],
                    ['DATE', 'COUNTRY_NAME', 'CUSTOM_TARGETING_VALUE_PAIR', 'AD_UNIT_NAME'],
                    ['DATE', 'COUNTRY_NAME', 'CUSTOM_TARGETING_VALUE_PAIR'],
                    ['DATE', 'COUNTRY_NAME']
                ],
                'column_sets': [
                    LOCKED_PRIMARY_GAM_COLUMNS,
                    [
                        'AD_EXCHANGE_LINE_ITEM_LEVEL_REVENUE',
                        'AD_EXCHANGE_LINE_ITEM_LEVEL_IMPRESSIONS',
                        'AD_EXCHANGE_LINE_ITEM_LEVEL_CLICKS',
                        'AD_EXCHANGE_LINE_ITEM_LEVEL_WITHOUT_CPD_AVERAGE_ECPM'
                    ],
                    [
                        'TOTAL_LINE_ITEM_LEVEL_CPM_AND_CPC_REVENUE',
                        'TOTAL_LINE_ITEM_LEVEL_IMPRESSIONS',
                        'TOTAL_LINE_ITEM_LEVEL_CLICKS',
                        'TOTAL_LINE_ITEM_LEVEL_WITHOUT_CPD_AVERAGE_ECPM'
                    ],
                    [
                        'AD_EXCHANGE_REVENUE',
                        'AD_EXCHANGE_IMPRESSIONS',
                        'AD_EXCHANGE_CLICKS',
                        'AD_EXCHANGE_AVERAGE_ECPM'
                    ]
                ]
            }
        ]

        last_error = None
        results = []

        for config in query_configs:
            successful_config = False
            r_type = config.get('reportType', 'HISTORICAL')
            for dims in config['dimension_sets']:
                successful_dim = False
                for cols in config['column_sets']:
                    try:
                        report_job_query = {
                            'dimensions': dims,
                            'columns': cols,
                            'dateRangeType': 'CUSTOM_DATE',
                            'startDate': {'year': start_date.year, 'month': start_date.month, 'day': start_date.day},
                            'endDate': {'year': end_date.year, 'month': end_date.month, 'day': end_date.day},
                            'timeZoneType': 'TIME_ZONE_OF_NETWORK'
                        }

                        report_job = {'reportQuery': report_job_query}
                        report_job = report_service.runReportJob(report_job)
                        report_job_id = report_job['id']

                        attempts = 0
                        while attempts < 30:
                            job_status = report_service.getReportJobStatus(report_job_id)
                            if job_status == 'COMPLETED':
                                break
                            elif job_status == 'FAILED':
                                raise Exception("GAM Country Report Job Failed")
                            time.sleep(1)
                            attempts += 1

                        if attempts >= 30:
                            raise Exception("GAM Country Report Job Timed Out after 30s")

                        report_download_url = report_service.getReportDownloadUrlWithOptions(
                            report_job_id, 'CSV_DUMP'
                        )

                        import requests
                        import csv
                        import gzip

                        res = requests.get(report_download_url)
                        content_bytes = res.content
                        if content_bytes.startswith(b'\x1f\x8b'):
                            content_bytes = gzip.decompress(content_bytes)

                        csv_text = content_bytes.decode('utf-8-sig', errors='ignore')
                        lines = [line for line in csv_text.splitlines() if line.strip()]

                        header_idx = 0
                        for idx, line in enumerate(lines):
                            line_up = line.upper()
                            if ('DATE' in line_up or 'SITE' in line_up or 'DOMAIN' in line_up or 'COUNTRY' in line_up or 'URL' in line_up or 'TAG' in line_up) and ('REVENUE' in line_up or 'IMPRESSION' in line_up or 'REQUEST' in line_up or 'COLUMN' in line_up or 'DIMENSION' in line_up):
                                header_idx = idx
                                break

                        reader = csv.DictReader(lines[header_idx:])
                        found_any_row = False
                        aggregated_country_results = {}

                        for row in reader:
                            row_date = start_date
                            for k, v in row.items():
                                if k and 'DATE' in k.upper() and v:
                                    row_date = parse_gam_date(v, start_date)
                                    break

                            country = "Indonesia"
                            for k, v in row.items():
                                if k and 'COUNTRY' in k.upper() and v:
                                    country = v.strip()
                                    break

                            ad_unit = ""
                            for k, v in row.items():
                                if k and ('AD_UNIT' in k.upper() or 'TAG' in k.upper()) and v:
                                    ad_unit = v.strip()
                                    break

                            pricing_rule = "All Rules"
                            for k, v in row.items():
                                if k and ('PRICING_RULE' in k.upper() or 'RULE_NAME' in k.upper()) and v:
                                    pricing_rule = v.strip()
                                    break

                            clean_ad_unit = ad_unit or "Standard Ad Unit"
                            domain = extract_domain_from_row(row, clean_ad_unit)
                            c_meta = get_country_meta(country)

                            dc_key = (row_date, domain, country, clean_ad_unit, pricing_rule)

                            impressions = 0
                            for k, v in row.items():
                                if k and 'IMPRESSIONS' in k.upper() and v:
                                    try:
                                        impressions = int(float(v))
                                        break
                                    except ValueError:
                                        pass

                            clicks = 0
                            for k, v in row.items():
                                if k and 'CLICKS' in k.upper() and v:
                                    try:
                                        clicks = int(float(v))
                                        break
                                    except ValueError:
                                        pass

                            raw_rev = 0.0
                            for k, v in row.items():
                                if k and ('REVENUE' in k.upper() or 'EARNINGS' in k.upper()) and v:
                                    try:
                                        raw_rev += float(v)
                                    except ValueError:
                                        pass

                            revenue = (raw_rev / 1000000.0) if raw_rev > 0 else 0.0

                            matched_requests = impressions
                            ad_requests = 0
                            unfilled_impressions = 0

                            for k, v in row.items():
                                if not k or not v:
                                    continue
                                k_up = k.upper()
                                try:
                                    val_num = int(float(v))
                                    if ('CODE_SERVED' in k_up or 'TOTAL_REQUESTS' in k_up or 'AD_REQUESTS' in k_up) and 'IMPRESSION' not in k_up:
                                        if val_num > ad_requests:
                                            ad_requests = val_num
                                    elif 'UNFILLED' in k_up:
                                        if val_num > unfilled_impressions:
                                            unfilled_impressions = val_num
                                    elif 'MATCHED' in k_up or 'RESPONSES_SERVED' in k_up:
                                        if val_num > matched_requests:
                                            matched_requests = val_num
                                except ValueError:
                                    pass

                            if ad_requests == 0:
                                unit_raw_key = (row_date, clean_ad_unit.lower().strip())
                                unit_clean_key = (row_date, clean_ad_unit.lower().strip().split('(')[0].strip())
                                if unit_raw_key in requests_map and requests_map[unit_raw_key] > 0:
                                    ad_requests = requests_map[unit_raw_key]
                                elif unit_clean_key in requests_map and requests_map[unit_clean_key] > 0:
                                    ad_requests = requests_map[unit_clean_key]
                                else:
                                    ad_requests = matched_requests

                            if ad_requests < matched_requests:
                                ad_requests = matched_requests

                            if dc_key not in aggregated_country_results:
                                aggregated_country_results[dc_key] = {
                                    "date": row_date,
                                    "domain": domain,
                                    "country": country,
                                    "country_code": c_meta["code"],
                                    "ad_unit": clean_ad_unit,
                                    "pricing_rule_name": pricing_rule,
                                    "revenue": revenue,
                                    "impressions": impressions,
                                    "clicks": clicks,
                                    "ad_requests": ad_requests,
                                    "matched_requests": matched_requests,
                                }
                            else:
                                item = aggregated_country_results[dc_key]
                                item["revenue"] += revenue
                                item["impressions"] += impressions
                                item["clicks"] += clicks
                                item["ad_requests"] += ad_requests
                                item["matched_requests"] += matched_requests

                            found_any_row = True

                        if found_any_row:
                            results = []
                            for item in aggregated_country_results.values():
                                rev = item["revenue"]
                                imps = item["impressions"]
                                reqs = item["ad_requests"]
                                matched = item["matched_requests"]
                                if reqs < matched:
                                    reqs = matched
                                    item["ad_requests"] = reqs
                                item["ecpm"] = round((rev / imps * 1000.0), 2) if imps > 0 else 0.0
                                item["match_rate"] = round((matched / reqs * 100.0), 2) if reqs > 0 else 0.0
                                item["revenue"] = round(rev, 2)
                                results.append(item)
                            successful_dim = True
                            successful_config = True
                            break

                    except Exception as e:
                        last_error = e

                if successful_dim:
                    logger.info(f"Country Dim set {dims} completed. Total country records: {len(results)}")
                    break

            if successful_config:
                logger.info(f"Country Query config r_type={r_type} completed successfully.")
                break

        if results:
            return results

        if last_error:
            raise last_error
        return []

    def _generate_mock_country_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        results = []
        domains = ["spotgames.top", "dpr.skuy.me", "mbelik.com", "2b.nubmaster.com", "baleq.me", "polpasulsa.com", "play.gemol.me"]
        country_configs = [
            {"country": "Indonesia", "code": "ID", "weight": 0.65, "ecpm": 18000, "rule": "DFLT GML"},
            {"country": "Kazakhstan", "code": "KZ", "weight": 0.12, "ecpm": 26000, "rule": "DFLT GML kz"},
            {"country": "United States", "code": "US", "weight": 0.08, "ecpm": 48000, "rule": "DFLT GML T1"},
            {"country": "Malaysia", "code": "MY", "weight": 0.05, "ecpm": 22000, "rule": "DFLT GML T2"},
            {"country": "Singapore", "code": "SG", "weight": 0.05, "ecpm": 38000, "rule": "DFLT GML T2"},
            {"country": "Japan", "code": "JP", "weight": 0.03, "ecpm": 32000, "rule": "DFLT GML T1"},
            {"country": "Australia", "code": "AU", "weight": 0.02, "ecpm": 35000, "rule": "DFLT GML T1"}
        ]
        units = ["Header_Responsive", "InArticle_Native", "Mobile_Sticky_Bottom", "Sidebar_300x600"]

        curr = start_date
        while curr <= end_date:
            for dom in domains:
                for c in country_configs:
                    for unit in units:
                        seed = hash(f"{curr.isoformat()}-{dom}-{c['country']}-{unit}")
                        rng = random.Random(seed)
                        base_rev = 150000 * c["weight"] * rng.uniform(0.8, 1.3)
                        imps = int(base_rev / c["ecpm"] * 1000) if c["ecpm"] > 0 else 1000
                        clks = int(imps * rng.uniform(0.01, 0.03))
                        ad_reqs = int(imps * rng.uniform(2.5, 3.2))
                        match_reqs = imps
                        mr = (match_reqs / ad_reqs * 100.0) if ad_reqs > 0 else 34.5
                        p_rule = c.get("rule", "DFLT GML")
                        if dom == "play.gemol.me" and c["code"] == "KZ":
                            p_rule = "DFLT GML kz"

                        results.append({
                            "date": curr,
                            "domain": dom,
                            "country": c["country"],
                            "country_code": c.get("code", "ID"),
                            "ad_unit": unit,
                            "pricing_rule_name": p_rule,
                            "revenue": round(base_rev, 2),
                            "impressions": imps,
                            "ecpm": round(c["ecpm"], 2),
                            "clicks": clks,
                            "ad_requests": ad_reqs,
                            "matched_requests": match_reqs,
                            "match_rate": round(mr, 2)
                        })
            curr += timedelta(days=1)
        return results

    def fetch_registered_sites(self) -> List[str]:
        """
        Query GAM SiteService, InventoryService, and CustomTargetingService with
        StatementBuilder pagination loop (page_size=500, start_index += 500)
        to retrieve 100% of all registered site domains in the GAM network across all pages.
        """
        if self.use_mock:
            return []

        try:
            from googleads import ad_manager, oauth2
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

            found_domains = set()
            page_size = 500

            # 1. Fetch via SiteService with StatementBuilder pagination loop
            try:
                site_service = client.GetService('SiteService', version='v202602')
                statement_builder = ad_manager.StatementBuilder(version='v202602')
                start_index = 0
                while True:
                    statement_builder.offset = start_index
                    statement_builder.limit = page_size
                    response = statement_builder.ToStatement()

                    page = site_service.getSitesByStatement(response)
                    results = getattr(page, 'results', None) or (page.get('results') if isinstance(page, dict) else None)
                    if not results:
                        break

                    for site in results:
                        s_name = getattr(site, 'name', '') or (site.get('name') if isinstance(site, dict) else '') or ''
                        s_url = getattr(site, 'url', '') or (site.get('url') if isinstance(site, dict) else '') or ''
                        for raw in [s_url, s_name]:
                            if raw:
                                dom = raw.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0].strip().lower()
                                if dom and '.' in dom and dom not in ["all domains", "-", "none", "null", "unknown"]:
                                    found_domains.add(dom)

                    if len(results) < page_size:
                        break
                    start_index += page_size
            except Exception as e:
                logger.warning(f"SiteService pagination loop notice: {e}")

            # 2. Fetch via InventoryService (Ad Units) with StatementBuilder pagination loop
            try:
                inventory_service = client.GetService('InventoryService', version='v202602')
                statement_builder = ad_manager.StatementBuilder(version='v202602')
                start_index = 0
                while True:
                    statement_builder.offset = start_index
                    statement_builder.limit = page_size
                    response = statement_builder.ToStatement()

                    page = inventory_service.getAdUnitsByStatement(response)
                    results = getattr(page, 'results', None) or (page.get('results') if isinstance(page, dict) else None)
                    if not results:
                        break

                    for unit in results:
                        unit_name = getattr(unit, 'name', '') or (unit.get('name') if isinstance(unit, dict) else '') or ''
                        dom = extract_domain_from_row({}, unit_name)
                        if dom and '.' in dom and dom not in ["all domains", "-", "none", "null", "unknown", "mbelik.com"]:
                            found_domains.add(dom)

                    if len(results) < page_size:
                        break
                    start_index += page_size
            except Exception as e:
                logger.warning(f"InventoryService pagination loop notice: {e}")

            # 3. Fetch via CustomTargetingService (Custom Targeting Values) with StatementBuilder pagination loop
            try:
                custom_service = client.GetService('CustomTargetingService', version='v202602')
                statement_builder = ad_manager.StatementBuilder(version='v202602')
                start_index = 0
                while True:
                    statement_builder.offset = start_index
                    statement_builder.limit = page_size
                    response = statement_builder.ToStatement()

                    page = custom_service.getCustomTargetingValuesByStatement(response)
                    results = getattr(page, 'results', None) or (page.get('results') if isinstance(page, dict) else None)
                    if not results:
                        break

                    for val_item in results:
                        val_name = getattr(val_item, 'name', '') or getattr(val_item, 'displayName', '') or (val_item.get('name') if isinstance(val_item, dict) else '') or ''
                        if val_name:
                            clean_val = val_name.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0].strip().lower()
                            if clean_val and '.' in clean_val and clean_val not in ["all domains", "-", "none", "null", "unknown"]:
                                found_domains.add(clean_val)

                    if len(results) < page_size:
                        break
                    start_index += page_size
            except Exception as e:
                logger.warning(f"CustomTargetingService pagination loop notice: {e}")

            logger.info(f"StatementBuilder pagination loop fetched {len(found_domains)} registered sites: {sorted(list(found_domains))}")
            return sorted(list(found_domains))
        except Exception as e:
            logger.warning(f"StatementBuilder pagination fetch notice: {e}")
            return []

gam_service = GAMService()

