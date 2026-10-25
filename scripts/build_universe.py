import json
import io
import urllib.request
import pandas as pd

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as r:
        return pd.read_html(io.StringIO(r.read().decode('utf-8')))[0]

print("Fetching S&P indices from Wikipedia...")
sp500 = fetch('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
sp400 = fetch('https://en.wikipedia.org/wiki/List_of_S%26P_400_companies')
sp600 = fetch('https://en.wikipedia.org/wiki/List_of_S%26P_600_companies')

gics_map = {
    'Information Technology': 'technology',
    'Health Care': 'healthcare',
    'Financials': 'financials',
    'Consumer Discretionary': 'consumer_discretionary',
    'Consumer Staples': 'consumer_staples',
    'Communication Services': 'communication_services',
    'Industrials': 'industrials',
    'Energy': 'energy',
    'Materials': 'materials',
    'Real Estate': 'real_estate',
    'Utilities': 'utilities',
}

mega_caps = {
    'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'GOOG', 'AMZN', 'META', 'TSLA', 'BRK-B', 'BRK.B',
    'LLY', 'AVGO', 'JPM', 'WMT', 'V', 'UNH', 'MA', 'PG', 'JNJ', 'COST', 'HD', 'ABBV',
    'BAC', 'CRM', 'NFLX', 'AMD', 'CVX', 'XOM', 'ORCL', 'KO', 'PEP', 'ADBE', 'TMO',
    'WFC', 'CSCO', 'QCOM', 'IBM', 'TXN', 'GE', 'CAT', 'PM', 'MS', 'GS', 'DIS', 'INTC'
}

seen = set()
universe = []

# S&P 500
for _, row in sp500.iterrows():
    sym = str(row['Symbol']).strip().replace('.', '-')
    if sym in seen or not sym:
        continue
    seen.add(sym)
    name = str(row['Security']).strip()
    if sym == 'NVDA':
        name = 'NVIDIA Corporation'
    gics = str(row['GICS Sector']).strip()
    sec = gics_map.get(gics, 'technology')
    tier = 'mega' if sym in mega_caps else 'large'
    universe.append({'symbol': sym, 'name': name, 'sector': sec, 'market_cap_tier': tier})

print(f"Added {len(universe)} S&P 500 stocks")

# S&P 400
for _, row in sp400.iterrows():
    sym = str(row['Symbol']).strip().replace('.', '-')
    if sym in seen or not sym:
        continue
    seen.add(sym)
    name = str(row['Security']).strip()
    gics = str(row['GICS Sector']).strip()
    sec = gics_map.get(gics, 'industrials')
    universe.append({'symbol': sym, 'name': name, 'sector': sec, 'market_cap_tier': 'mid'})

print(f"Total after S&P 400: {len(universe)}")

# Dedicated AI / Speculative stocks
ai_specialty_stocks = [
    ('ASTS', 'AST SpaceMobile Inc.', 'small'),
    ('PLTR', 'Palantir Technologies Inc.', 'large'),
    ('SMCI', 'Super Micro Computer Inc.', 'large'),
    ('IONQ', 'IonQ Inc.', 'small'),
    ('RGTI', 'Rigetti Computing Inc.', 'small'),
    ('QBTS', 'D-Wave Quantum Inc.', 'small'),
    ('SOUN', 'SoundHound AI Inc.', 'small'),
    ('BBAI', 'BigBear.ai Holdings Inc.', 'small'),
    ('MSTR', 'MicroStrategy Incorporated', 'large'),
    ('COIN', 'Coinbase Global Inc.', 'large'),
    ('MARA', 'MARA Holdings Inc.', 'small'),
    ('CLSK', 'CleanSpark Inc.', 'small'),
    ('RIOT', 'Riot Platforms Inc.', 'small'),
    ('CIFR', 'Cipher Mining Inc.', 'small'),
    ('NBIS', 'Nebius Group N.V.', 'mid'),
    ('CORZ', 'Core Scientific Inc.', 'mid'),
    ('APLD', 'Applied Digital Corporation', 'small'),
    ('IREN', 'Iris Energy Limited', 'small'),
    ('WULF', 'TeraWulf Inc.', 'small'),
    ('HUT', 'Hut 8 Corp.', 'small'),
    ('COHR', 'Coherent Corp.', 'mid'),
    ('LITE', 'Lumentum Holdings Inc.', 'mid'),
    ('AAOI', 'Applied Optoelectronics Inc.', 'small'),
    ('FN', 'Fabrinet', 'mid'),
    ('POET', 'POET Technologies Inc.', 'small'),
    ('VRT', 'Vertiv Holdings Co', 'large'),
    ('SYM', 'Symbotic Inc.', 'mid'),
    ('PATH', 'UiPath Inc.', 'mid'),
    ('TEM', 'Tempus AI Inc.', 'mid'),
    ('UPST', 'Upstart Holdings Inc.', 'small'),
    ('RDDT', 'Reddit Inc.', 'mid'),
    ('DJT', 'Trump Media & Technology Group Corp.', 'small'),
    ('OPEN', 'Opendoor Technologies Inc.', 'small'),
    ('CVNA', 'Carvana Co.', 'mid'),
    ('AFRM', 'Affirm Holdings Inc.', 'mid'),
    ('ARM', 'Arm Holdings plc', 'large'),
    ('TSM', 'Taiwan Semiconductor Manufacturing Co.', 'mega'),
]

for sym, name, tier in ai_specialty_stocks:
    if sym in seen:
        continue
    seen.add(sym)
    universe.append({'symbol': sym, 'name': name, 'sector': 'ai_specialty', 'market_cap_tier': tier})

print(f"Total after AI & Specialty: {len(universe)}")

# S&P 600 stocks until target of 1100
target_total = 1100
for _, row in sp600.iterrows():
    if len(universe) >= target_total:
        break
    sym = str(row['Symbol']).strip().replace('.', '-')
    if sym in seen or not sym:
        continue
    seen.add(sym)
    name = str(row['Security']).strip()
    gics = str(row['GICS Sector']).strip()
    sec = gics_map.get(gics, 'industrials')
    universe.append({'symbol': sym, 'name': name, 'sector': sec, 'market_cap_tier': 'small'})

print(f"Final universe size: {len(universe)}")

header = '''"""Comprehensive US Stock Universe Catalog.

Covers 1,000+ liquid US equities across 11 GICS sectors and AI/Specialty,
including S&P 500, S&P 400 MidCap, liquid small caps, and high-growth AI/Crypto leaders.
"""

from typing import Dict, List, Optional

# Supported sector categories mapping slug to human-readable name
STOCK_SECTORS: Dict[str, str] = {
    "technology": "Technology",
    "healthcare": "Healthcare",
    "financials": "Financials",
    "consumer_discretionary": "Consumer Discretionary",
    "consumer_staples": "Consumer Staples",
    "communication_services": "Communication Services",
    "industrials": "Industrials",
    "energy": "Energy",
    "materials": "Materials",
    "real_estate": "Real Estate",
    "utilities": "Utilities",
    "ai_specialty": "AI & Specialty",
}

# 1,000+ US Stock Universe Catalog
STOCK_UNIVERSE: List[Dict[str, str]] = '''

body = json.dumps(universe, indent=4)

footer = '''

# Lookup index by uppercase symbol
_STOCK_MAP: Dict[str, Dict[str, str]] = {item["symbol"].upper(): item for item in STOCK_UNIVERSE}
# Also index with dot variation (e.g. BRK.B -> BRK-B)
for item in STOCK_UNIVERSE:
    if "-" in item["symbol"]:
        _STOCK_MAP[item["symbol"].replace("-", ".").upper()] = item


def get_stock_universe(sector: Optional[str] = None) -> List[Dict[str, str]]:
    """Retrieve the stock universe, optionally filtered by sector.

    Args:
        sector: Optional sector identifier or display name (case-insensitive).
                If None or 'all', returns the complete catalog.

    Returns:
        List of stock metadata dictionaries.
    """
    if not sector or sector.strip().lower() == "all":
        return [dict(item) for item in STOCK_UNIVERSE]

    query = sector.strip().lower().replace(" ", "_").replace("&", "and")
    alias_map = {
        "information_technology": "technology",
        "tech": "technology",
        "health_care": "healthcare",
        "health": "healthcare",
        "financial": "financials",
        "finance": "financials",
        "discretionary": "consumer_discretionary",
        "staples": "consumer_staples",
        "communication": "communication_services",
        "comms": "communication_services",
        "telecom": "communication_services",
        "industrial": "industrials",
        "material": "materials",
        "utility": "utilities",
        "reit": "real_estate",
        "reits": "real_estate",
        "ai": "ai_specialty",
        "ai_and_specialty": "ai_specialty",
        "specialty": "ai_specialty",
    }
    target_sector = alias_map.get(query, query)

    return [
        dict(item)
        for item in STOCK_UNIVERSE
        if item["sector"].lower() == target_sector
        or item["sector"].lower().replace("_", " ") == sector.strip().lower()
        or STOCK_SECTORS.get(item["sector"], "").lower() == sector.strip().lower()
    ]


def get_stock_metadata(symbol: str) -> Optional[Dict[str, str]]:
    """Lookup stock metadata by ticker symbol.

    Args:
        symbol: The ticker symbol (case-insensitive).

    Returns:
        Dict with keys {'symbol', 'name', 'sector', 'market_cap_tier'} or None if not found.
    """
    if not symbol or not isinstance(symbol, str):
        return None
    sym = symbol.strip().upper()
    match = _STOCK_MAP.get(sym)
    if not match:
        match = _STOCK_MAP.get(sym.replace(".", "-"))
    if not match:
        match = _STOCK_MAP.get(sym.replace("-", "."))
    return dict(match) if match else None
'''

with open('data/stock_universe.py', 'w', encoding='utf-8') as f:
    f.write(header + body + footer)

print("Generated data/stock_universe.py successfully!")
