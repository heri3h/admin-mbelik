import logging
import random
import os
import time
from datetime import datetime, timedelta, date, timezone
from typing import List, Dict, Any
import unicodedata
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

def normalize_canonical_domain(raw_domain: str) -> str:
    if not raw_domain:
        return "mbelik.com"
    d = raw_domain.strip().lower()
    if "gemol" in d:
        return "play.gemol.me"
    if "skuy" in d:
        return "dpr.skuy.me"
    if "nubmaster" in d:
        return "2b.nubmaster.com"
    if "spotgames" in d:
        return "spotgames.top"
    if "polpasulsa" in d:
        return "polpasulsa.com"
    if "baleq" in d:
        return "baleq.me"
    if "henden" in d:
        return "henden.top"
    if "ugames" in d or "zse" in d:
        return "zse.ugames.top"
    if "mbelik" in d:
        return "mbelik.com"
    return d

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

    # Exact full ad unit exceptions
    EXACT_MAP = {
        "gm feed": "gemol.me",
        "gm side": "gemol.me",
        "gm side 2": "gemol.me",
        "gm-side-v2": "gemol.me",
        "gm-side-2-v2": "gemol.me",
    }
    if unit_lower in EXACT_MAP:
        return EXACT_MAP[unit_lower]

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
        ('gml', 'gemol.me'),
        ('play', 'play.gemol.me'),
        ('gm', 'play.gemol.me'),
        ('gemol', 'gemol.me'),
        ('skuy', 'skuy.me'),
        ('dpr', 'dpr.skuy.me'),
        ('nub', 'nub.skuy.me'),
        ('nmas', 'nub.skuy.me'),
        ('xdr', 'xdr.nubmaster.com'),
        ('spotgames', 'spotgames.top'),
        ('spot', 'spotgames.top'),
        ('sg', 'spotgames.top'),
        ('2b', '2b.nubmaster.com'),
        ('nubmaster', '2b.nubmaster.com'),
        ('alt', 'alt.polpasulsa.com'),
        ('polpasulsa', 'polpasulsa.com'),
        ('polpa', 'polpasulsa.com'),
        ('pol', 'polpasulsa.com'),
        ('pas', 'polpasulsa.com'),
        ('enew', 'enew.spotgames.top'),
        ('yay', 'yay.spotgames.top'),
        ('glee', 'glee.mbelik.com'),
        ('baleq', 'baleq.me'),
        ('blq', 'baleq.me'),
        ('hndn', 'henden.top'),
        ('henden', 'henden.top'),
        ('zse', 'zse.ugames.top'),
        ('ugames', 'zse.ugames.top'),
        ('vinn', 'mbelik.com'),
        ('mko', 'mbelik.com'),
        ('pow', 'mbelik.com'),
        ('wew', 'mbelik.com'),
        ('mvp', 'mbelik.com'),
        ('ses', 'mbelik.com'),
        ('gg', 'mbelik.com'),
        ('dwnld', 'mbelik.com'),
        ('mbelik', 'mbelik.com'),
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

def parse_device_category(raw_val: str) -> str:
    if not raw_val:
        return "mobile"
    val = raw_val.strip().lower()
    if "desktop" in val or "computer" in val:
        return "desktop"
    return "mobile"

COUNTRY_NAME_TO_CODE = {
    "afghanistan": "AF",
    "albania": "AL",
    "algeria": "DZ",
    "american samoa": "AS",
    "andorra": "AD",
    "angola": "AO",
    "anguilla": "AI",
    "antarctica": "AQ",
    "antigua and barbuda": "AG",
    "argentina": "AR",
    "armenia": "AM",
    "aruba": "AW",
    "australia": "AU",
    "austria": "AT",
    "azerbaijan": "AZ",
    "bahamas": "BS",
    "the bahamas": "BS",
    "bahrain": "BH",
    "bangladesh": "BD",
    "barbados": "BB",
    "belarus": "BY",
    "belgium": "BE",
    "belize": "BZ",
    "benin": "BJ",
    "bermuda": "BM",
    "bhutan": "BT",
    "bolivia": "BO",
    "bosnia and herzegovina": "BA",
    "botswana": "BW",
    "brazil": "BR",
    "british virgin islands": "VG",
    "brunei": "BN",
    "brunei darussalam": "BN",
    "bulgaria": "BG",
    "burkina faso": "BF",
    "burundi": "BI",
    "cabo verde": "CV",
    "cape verde": "CV",
    "cambodia": "KH",
    "cameroon": "CM",
    "canada": "CA",
    "cayman islands": "KY",
    "central african republic": "CF",
    "chad": "TD",
    "chile": "CL",
    "china": "CN",
    "colombia": "CO",
    "comoros": "KM",
    "congo": "CG",
    "democratic republic of the congo": "CD",
    "republic of the congo": "CG",
    "costa rica": "CR",
    "croatia": "HR",
    "cuba": "CU",
    "curacao": "CW",
    "cyprus": "CY",
    "czechia": "CZ",
    "czech republic": "CZ",
    "denmark": "DK",
    "djibouti": "DJ",
    "dominica": "DM",
    "dominican republic": "DO",
    "ecuador": "EC",
    "egypt": "EG",
    "el salvador": "SV",
    "equatorial guinea": "GQ",
    "eritrea": "ER",
    "estonia": "EE",
    "eswatini": "SZ",
    "swaziland": "SZ",
    "ethiopia": "ET",
    "falkland islands": "FK",
    "falkland islands (islas malvinas)": "FK",
    "faroe islands": "FO",
    "fiji": "FJ",
    "finland": "FI",
    "france": "FR",
    "french guiana": "GF",
    "french polynesia": "PF",
    "gabon": "GA",
    "gambia": "GM",
    "the gambia": "GM",
    "georgia": "GE",
    "germany": "DE",
    "ghana": "GH",
    "gibraltar": "GI",
    "greece": "GR",
    "greenland": "GL",
    "grenada": "GD",
    "guadeloupe": "GP",
    "guam": "GU",
    "guatemala": "GT",
    "guernsey": "GG",
    "guinea": "GN",
    "guinea-bissau": "GW",
    "guyana": "GY",
    "haiti": "HT",
    "honduras": "HN",
    "hong kong": "HK",
    "hungary": "HU",
    "iceland": "IS",
    "india": "IN",
    "indonesia": "ID",
    "iran": "IR",
    "iraq": "IQ",
    "ireland": "IE",
    "isle of man": "IM",
    "israel": "IL",
    "italy": "IT",
    "ivory coast": "CI",
    "côte d'ivoire": "CI",
    "cote d'ivoire": "CI",
    "jamaica": "JM",
    "japan": "JP",
    "jersey": "JE",
    "jordan": "JO",
    "kazakhstan": "KZ",
    "kenya": "KE",
    "kiribati": "KI",
    "kosovo": "XK",
    "kuwait": "KW",
    "kyrgyzstan": "KG",
    "laos": "LA",
    "latvia": "LV",
    "lebanon": "LB",
    "lesotho": "LS",
    "liberia": "LR",
    "libya": "LY",
    "liechtenstein": "LI",
    "lithuania": "LT",
    "luxembourg": "LU",
    "macao": "MO",
    "macau": "MO",
    "madagascar": "MG",
    "malawi": "MW",
    "malaysia": "MY",
    "maldives": "MV",
    "mali": "ML",
    "malta": "MT",
    "marshall islands": "MH",
    "martinique": "MQ",
    "mauritania": "MR",
    "mauritius": "MU",
    "mayotte": "YT",
    "mexico": "MX",
    "micronesia": "FM",
    "moldova": "MD",
    "monaco": "MC",
    "mongolia": "MN",
    "montenegro": "ME",
    "montserrat": "MS",
    "morocco": "MA",
    "mozambique": "MZ",
    "myanmar": "MM",
    "namibia": "NA",
    "nauru": "NR",
    "nepal": "NP",
    "netherlands": "NL",
    "new caledonia": "NC",
    "new zealand": "NZ",
    "nicaragua": "NI",
    "niger": "NE",
    "nigeria": "NG",
    "north macedonia": "MK",
    "northern mariana islands": "MP",
    "norway": "NO",
    "oman": "OM",
    "pakistan": "PK",
    "palau": "PW",
    "palestine": "PS",
    "panama": "PA",
    "papua new guinea": "PG",
    "paraguay": "PY",
    "peru": "PE",
    "philippines": "PH",
    "poland": "PL",
    "portugal": "PT",
    "puerto rico": "PR",
    "qatar": "QA",
    "reunion": "RE",
    "romania": "RO",
    "russia": "RU",
    "russian federation": "RU",
    "rwanda": "RW",
    "saint lucia": "LC",
    "saint vincent and the grenadines": "VC",
    "samoa": "WS",
    "san marino": "SM",
    "sao tome and principe": "ST",
    "saudi arabia": "SA",
    "senegal": "SN",
    "serbia": "RS",
    "seychelles": "SC",
    "sierra leone": "SL",
    "singapore": "SG",
    "sint maarten": "SX",
    "slovakia": "SK",
    "slovenia": "SI",
    "solomon islands": "SB",
    "somalia": "SO",
    "south africa": "ZA",
    "south korea": "KR",
    "korea, republic of": "KR",
    "korea": "KR",
    "south sudan": "SS",
    "spain": "ES",
    "sri lanka": "LK",
    "sudan": "SD",
    "suriname": "SR",
    "sweden": "SE",
    "switzerland": "CH",
    "syria": "SY",
    "taiwan": "TW",
    "tajikistan": "TJ",
    "tanzania": "TZ",
    "thailand": "TH",
    "timor-leste": "TL",
    "togo": "TG",
    "tonga": "TO",
    "trinidad and tobago": "TT",
    "tunisia": "TN",
    "turkey": "TR",
    "türkiye": "TR",
    "turkiye": "TR",
    "turkmenistan": "TM",
    "turks and caicos islands": "TC",
    "tuvalu": "TV",
    "uganda": "UG",
    "ukraine": "UA",
    "united arab emirates": "AE",
    "uae": "AE",
    "united kingdom": "GB",
    "great britain": "GB",
    "uk": "GB",
    "united states": "US",
    "united states of america": "US",
    "usa": "US",
    "us": "US",
    "uruguay": "UY",
    "uzbekistan": "UZ",
    "vanuatu": "VU",
    "venezuela": "VE",
    "vietnam": "VN",
    "western sahara": "EH",
    "yemen": "YE",
    "zambia": "ZM",
    "zimbabwe": "ZW",
    "others": "XX",
    "unknown region": "XX",
}


def _normalize_country_str(s: str) -> str:
    if not s:
        return ""
    nfd = unicodedata.normalize("NFD", s)
    stripped = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return stripped.lower().strip()


def get_country_meta(country_name: str) -> dict:
    if not country_name:
        return {"code": "ID", "flag": "🇮🇩"}
    
    raw = country_name.strip()
    norm_key = _normalize_country_str(raw)

    if len(raw) == 2 and raw.isalpha() and raw.upper() != "XX":
        code = raw.upper()
        flag = chr(127397 + ord(code[0])) + chr(127397 + ord(code[1]))
        return {"code": code, "flag": flag}

    # 1. Exact match on normalized string
    for c_name, code in COUNTRY_NAME_TO_CODE.items():
        if _normalize_country_str(c_name) == norm_key:
            if code == "XX":
                return {"code": "XX", "flag": "🌐"}
            flag = chr(127397 + ord(code[0])) + chr(127397 + ord(code[1]))
            return {"code": code, "flag": flag}

    # 2. Substring match on normalized string
    for c_name, code in COUNTRY_NAME_TO_CODE.items():
        norm_c_name = _normalize_country_str(c_name)
        if len(norm_c_name) >= 3 and (norm_c_name in norm_key or norm_key in norm_c_name):
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
                    ['DATE', 'DEVICE_CATEGORY_NAME', 'AD_UNIT_NAME'],
                    ['DATE', 'DEVICE_CATEGORY_NAME', 'SITE_NAME', 'AD_UNIT_NAME'],
                    ['DATE', 'DEVICE_CATEGORY_NAME', 'SITE_NAME'],
                    ['DATE', 'DEVICE_CATEGORY_NAME', 'DOMAIN_NAME'],
                    ['DATE', 'DEVICE_CATEGORY_NAME']
                ],
                'column_sets': [
                    LOCKED_PRIMARY_GAM_COLUMNS,
                    [
                        'TOTAL_LINE_ITEM_LEVEL_CPM_AND_CPC_REVENUE',
                        'TOTAL_LINE_ITEM_LEVEL_IMPRESSIONS',
                        'TOTAL_LINE_ITEM_LEVEL_CLICKS',
                        'TOTAL_LINE_ITEM_LEVEL_WITHOUT_CPD_AVERAGE_ECPM'
                    ]
                ]
            },
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
                                    if pricing_rule in ["(No pricing rule applied)", "(No Pricing Rule Applied)", "No pricing rule applied"]:
                                        pricing_rule = "No Rule"
                                    break

                            match_rate = (matched_requests / ad_requests * 100.0) if ad_requests > 0 else 0.0

                            device_cat = "mobile"
                            for k, v in row.items():
                                if k and ('DEVICE' in k.upper() or 'CATEGORY' in k.upper() or 'PLATFORM' in k.upper()) and v:
                                    device_cat = parse_device_category(v)
                                    break

                            key = (row_date, domain, ad_unit, pricing_rule, device_cat)
                            if key not in aggregated_results:
                                aggregated_results[key] = {
                                    "date": row_date,
                                    "domain": domain,
                                    "ad_unit": ad_unit,
                                    "pricing_rule_name": pricing_rule,
                                    "device_category": device_cat,
                                    "revenue": revenue,
                                    "impressions": impressions,
                                    "ecpm": round(ecpm, 2),
                                    "clicks": clicks,
                                    "ad_requests": ad_requests,
                                    "matched_requests": matched_requests,
                                    "match_rate": round(match_rate, 2)
                                }
                            else:
                                curr = aggregated_results[key]
                                curr["revenue"] += revenue
                                curr["impressions"] += impressions
                                curr["clicks"] += clicks
                                curr["ad_requests"] += ad_requests
                                curr["matched_requests"] += matched_requests
                                curr["ecpm"] = round((curr["revenue"] / curr["impressions"]) * 1000.0, 2) if curr["impressions"] > 0 else 0.0
                                curr["match_rate"] = round((curr["matched_requests"] / curr["ad_requests"]) * 100.0, 2) if curr["ad_requests"] > 0 else 0.0

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
            final_rows = list(aggregated_results.values())
            for item in final_rows:
                item["revenue"] = round(item["revenue"], 2)
            return final_rows

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
                    ['DATE', 'COUNTRY_NAME', 'DEVICE_CATEGORY_NAME', 'AD_UNIT_NAME'],
                    ['DATE', 'COUNTRY_NAME', 'DEVICE_CATEGORY_NAME', 'SITE_NAME', 'AD_UNIT_NAME'],
                    ['DATE', 'COUNTRY_NAME', 'DEVICE_CATEGORY_NAME', 'SITE_NAME'],
                    ['DATE', 'COUNTRY_NAME', 'DEVICE_CATEGORY_NAME']
                ],
                'column_sets': [
                    LOCKED_PRIMARY_GAM_COLUMNS,
                    [
                        'TOTAL_LINE_ITEM_LEVEL_CPM_AND_CPC_REVENUE',
                        'TOTAL_LINE_ITEM_LEVEL_IMPRESSIONS',
                        'TOTAL_LINE_ITEM_LEVEL_CLICKS',
                        'TOTAL_LINE_ITEM_LEVEL_WITHOUT_CPD_AVERAGE_ECPM'
                    ]
                ]
            },
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
                                    if pricing_rule in ["(No pricing rule applied)", "(No Pricing Rule Applied)", "No pricing rule applied"]:
                                        pricing_rule = "No Rule"
                                    break

                            clean_ad_unit = ad_unit or "Standard Ad Unit"
                            domain = extract_domain_from_row(row, clean_ad_unit)
                            c_meta = get_country_meta(country)

                            device_cat = "mobile"
                            for k, v in row.items():
                                if k and ('DEVICE' in k.upper() or 'CATEGORY' in k.upper() or 'PLATFORM' in k.upper()) and v:
                                    device_cat = parse_device_category(v)
                                    break

                            dc_key = (row_date, domain, country, clean_ad_unit, pricing_rule, device_cat)

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
                                    "device_category": device_cat,
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

