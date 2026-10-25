"""Comprehensive US Stock Universe Catalog.

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
STOCK_UNIVERSE: List[Dict[str, str]] = [
    {
        "symbol": "MMM",
        "name": "3M",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "AOS",
        "name": "A. O. Smith",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ABT",
        "name": "Abbott Laboratories",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ABBV",
        "name": "AbbVie",
        "sector": "healthcare",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "ACN",
        "name": "Accenture",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ADBE",
        "name": "Adobe Inc.",
        "sector": "technology",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "AMD",
        "name": "Advanced Micro Devices",
        "sector": "technology",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "AES",
        "name": "AES Corporation",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "AFL",
        "name": "Aflac",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "A",
        "name": "Agilent Technologies",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "APD",
        "name": "Air Products",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ABNB",
        "name": "Airbnb",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "AKAM",
        "name": "Akamai Technologies",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ALB",
        "name": "Albemarle Corporation",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ARE",
        "name": "Alexandria Real Estate Equities",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ALGN",
        "name": "Align Technology",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ALLE",
        "name": "Allegion",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "LNT",
        "name": "Alliant Energy",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ALL",
        "name": "Allstate",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "GOOGL",
        "name": "Alphabet Inc. (Class A)",
        "sector": "communication_services",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "GOOG",
        "name": "Alphabet Inc. (Class C)",
        "sector": "communication_services",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "MO",
        "name": "Altria",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "AMZN",
        "name": "Amazon",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "AMCR",
        "name": "Amcor",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "AEE",
        "name": "Ameren",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "AEP",
        "name": "American Electric Power",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "AXP",
        "name": "American Express",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "AIG",
        "name": "American International Group",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "AMT",
        "name": "American Tower",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "AWK",
        "name": "American Water Works",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "AMP",
        "name": "Ameriprise Financial",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "AME",
        "name": "Ametek",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "AMGN",
        "name": "Amgen",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "APH",
        "name": "Amphenol",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ADI",
        "name": "Analog Devices",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "AON",
        "name": "Aon plc",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "APA",
        "name": "APA Corporation",
        "sector": "energy",
        "market_cap_tier": "large"
    },
    {
        "symbol": "APO",
        "name": "Apollo Global Management",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "sector": "technology",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "AMAT",
        "name": "Applied Materials",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "APP",
        "name": "AppLovin",
        "sector": "communication_services",
        "market_cap_tier": "large"
    },
    {
        "symbol": "APTV",
        "name": "Aptiv",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ACGL",
        "name": "Arch Capital Group",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ADM",
        "name": "Archer Daniels Midland",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ARES",
        "name": "Ares Management",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ANET",
        "name": "Arista Networks",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "AJG",
        "name": "Arthur J. Gallagher & Co.",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "AIZ",
        "name": "Assurant",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "T",
        "name": "AT&T",
        "sector": "communication_services",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ATO",
        "name": "Atmos Energy",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ADSK",
        "name": "Autodesk",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ADP",
        "name": "Automatic Data Processing",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "AZO",
        "name": "AutoZone",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "AVY",
        "name": "Avery Dennison",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "AXON",
        "name": "Axon Enterprise",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "BKR",
        "name": "Baker Hughes",
        "sector": "energy",
        "market_cap_tier": "large"
    },
    {
        "symbol": "BALL",
        "name": "Ball Corporation",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "BAC",
        "name": "Bank of America",
        "sector": "financials",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "BAX",
        "name": "Baxter International",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "BDX",
        "name": "Becton Dickinson",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "BRK-B",
        "name": "Berkshire Hathaway",
        "sector": "financials",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "BBY",
        "name": "Best Buy",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TECH",
        "name": "Bio-Techne",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "BIIB",
        "name": "Biogen",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "BLK",
        "name": "BlackRock",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "BX",
        "name": "Blackstone Inc.",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "XYZ",
        "name": "Block, Inc.",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "BE",
        "name": "Bloom Energy",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "BNY",
        "name": "BNY Mellon",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "BA",
        "name": "Boeing",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "BKNG",
        "name": "Booking Holdings",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "BSX",
        "name": "Boston Scientific",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "BMY",
        "name": "Bristol Myers Squibb",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "AVGO",
        "name": "Broadcom",
        "sector": "technology",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "BR",
        "name": "Broadridge Financial Solutions",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "BRO",
        "name": "Brown & Brown",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "BF-B",
        "name": "Brown\u2013Forman",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "BG",
        "name": "Bunge Global",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "BXP",
        "name": "BXP, Inc.",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CHRW",
        "name": "C.H. Robinson",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CDNS",
        "name": "Cadence Design Systems",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CPT",
        "name": "Camden Property Trust",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "COF",
        "name": "Capital One",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CAH",
        "name": "Cardinal Health",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CCL",
        "name": "Carnival Corporation",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CARR",
        "name": "Carrier Global",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CVNA",
        "name": "Carvana",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CASY",
        "name": "Casey's",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CAT",
        "name": "Caterpillar Inc.",
        "sector": "industrials",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "CBOE",
        "name": "Cboe Global Markets",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CBRE",
        "name": "CBRE Group",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CDW",
        "name": "CDW Corporation",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "COR",
        "name": "Cencora",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CNC",
        "name": "Centene Corporation",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CNP",
        "name": "CenterPoint Energy",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CF",
        "name": "CF Industries",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CRL",
        "name": "Charles River Laboratories",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "SCHW",
        "name": "Charles Schwab Corporation",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CHTR",
        "name": "Charter Communications",
        "sector": "communication_services",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CVX",
        "name": "Chevron Corporation",
        "sector": "energy",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "CMG",
        "name": "Chipotle Mexican Grill",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CB",
        "name": "Chubb Limited",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CHD",
        "name": "Church & Dwight",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CIEN",
        "name": "Ciena",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CI",
        "name": "Cigna",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CINF",
        "name": "Cincinnati Financial",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CTAS",
        "name": "Cintas",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CSCO",
        "name": "Cisco",
        "sector": "technology",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "C",
        "name": "Citigroup",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CFG",
        "name": "Citizens Financial Group",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CLX",
        "name": "Clorox",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CME",
        "name": "CME Group",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CMS",
        "name": "CMS Energy",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "KO",
        "name": "Coca-Cola Company (The)",
        "sector": "consumer_staples",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "CTSH",
        "name": "Cognizant",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "COHR",
        "name": "Coherent Corp.",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "COIN",
        "name": "Coinbase",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CL",
        "name": "Colgate-Palmolive",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CMCSA",
        "name": "Comcast",
        "sector": "communication_services",
        "market_cap_tier": "large"
    },
    {
        "symbol": "FIX",
        "name": "Comfort Systems USA",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "COP",
        "name": "ConocoPhillips",
        "sector": "energy",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ED",
        "name": "Consolidated Edison",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "STZ",
        "name": "Constellation Brands",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CEG",
        "name": "Constellation Energy",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "COO",
        "name": "Cooper Companies (The)",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CPRT",
        "name": "Copart",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "GLW",
        "name": "Corning Inc.",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CPAY",
        "name": "Corpay",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CSGP",
        "name": "CoStar Group",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "COST",
        "name": "Costco",
        "sector": "consumer_staples",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "CRH",
        "name": "CRH plc",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CRWD",
        "name": "CrowdStrike",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CCI",
        "name": "Crown Castle",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CSX",
        "name": "CSX Corporation",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CMI",
        "name": "Cummins",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CVS",
        "name": "CVS Health",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "DHR",
        "name": "Danaher Corporation",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "DRI",
        "name": "Darden Restaurants",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "DDOG",
        "name": "Datadog",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "DVA",
        "name": "DaVita",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "DECK",
        "name": "Deckers Brands",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "DE",
        "name": "Deere & Company",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "DELL",
        "name": "Dell Technologies",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "DAL",
        "name": "Delta Air Lines",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "DVN",
        "name": "Devon Energy",
        "sector": "energy",
        "market_cap_tier": "large"
    },
    {
        "symbol": "DXCM",
        "name": "Dexcom",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "FANG",
        "name": "Diamondback Energy",
        "sector": "energy",
        "market_cap_tier": "large"
    },
    {
        "symbol": "DLR",
        "name": "Digital Realty",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "DG",
        "name": "Dollar General",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "DLTR",
        "name": "Dollar Tree",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "D",
        "name": "Dominion Energy",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "DPZ",
        "name": "Domino's",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "DASH",
        "name": "DoorDash",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "DOV",
        "name": "Dover Corporation",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "DOW",
        "name": "Dow Inc.",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "DHI",
        "name": "D. R. Horton",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "DTE",
        "name": "DTE Energy",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "DUK",
        "name": "Duke Energy",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "DD",
        "name": "DuPont",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ETN",
        "name": "Eaton Corporation",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "EBAY",
        "name": "eBay Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ECHO",
        "name": "EchoStar",
        "sector": "communication_services",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ECL",
        "name": "Ecolab",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "EIX",
        "name": "Edison International",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "EW",
        "name": "Edwards Lifesciences",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ELV",
        "name": "Elevance Health",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "EME",
        "name": "Emcor",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "EMR",
        "name": "Emerson Electric",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ETR",
        "name": "Entergy",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "EOG",
        "name": "EOG Resources",
        "sector": "energy",
        "market_cap_tier": "large"
    },
    {
        "symbol": "EQT",
        "name": "EQT Corporation",
        "sector": "energy",
        "market_cap_tier": "large"
    },
    {
        "symbol": "EFX",
        "name": "Equifax",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "EQIX",
        "name": "Equinix",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ERIE",
        "name": "Erie Indemnity",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ESS",
        "name": "Essex Property Trust",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "EL",
        "name": "Est\u00e9e Lauder Companies (The)",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "EG",
        "name": "Everest Group",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "EVRG",
        "name": "Evergy",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "P",
        "name": "Everpure",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ES",
        "name": "Eversource Energy",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "EXC",
        "name": "Exelon",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "EXE",
        "name": "Expand Energy",
        "sector": "energy",
        "market_cap_tier": "large"
    },
    {
        "symbol": "EXPE",
        "name": "Expedia Group",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "EXPD",
        "name": "Expeditors International",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "EXR",
        "name": "Extra Space Storage",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "XOM",
        "name": "ExxonMobil",
        "sector": "energy",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "FFIV",
        "name": "F5, Inc.",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "FDS",
        "name": "FactSet",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "FICO",
        "name": "Fair Isaac",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "FAST",
        "name": "Fastenal",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "FRT",
        "name": "Federal Realty Investment Trust",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "FDX",
        "name": "FedEx",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "FDXF",
        "name": "FedEx Freight",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "FERG",
        "name": "Ferguson Enterprises",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "FIS",
        "name": "Fidelity National Information Services",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "FITB",
        "name": "Fifth Third Bancorp",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "FSLR",
        "name": "First Solar",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "FE",
        "name": "FirstEnergy",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "FISV",
        "name": "Fiserv",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "FLEX",
        "name": "Flex Ltd.",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "F",
        "name": "Ford Motor Company",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "FTNT",
        "name": "Fortinet",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "FTV",
        "name": "Fortive",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "FOXA",
        "name": "Fox Corporation (Class A)",
        "sector": "communication_services",
        "market_cap_tier": "large"
    },
    {
        "symbol": "FOX",
        "name": "Fox Corporation (Class B)",
        "sector": "communication_services",
        "market_cap_tier": "large"
    },
    {
        "symbol": "BEN",
        "name": "Franklin Resources",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "FCX",
        "name": "Freeport-McMoRan",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "GRMN",
        "name": "Garmin",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "IT",
        "name": "Gartner",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "GE",
        "name": "GE Aerospace",
        "sector": "industrials",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "GEHC",
        "name": "GE HealthCare",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "GEV",
        "name": "GE Vernova",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "GEN",
        "name": "Gen Digital",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "GNRC",
        "name": "Generac",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "GD",
        "name": "General Dynamics",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "GIS",
        "name": "General Mills",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "GM",
        "name": "General Motors",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "GPC",
        "name": "Genuine Parts Company",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "GILD",
        "name": "Gilead Sciences",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "GPN",
        "name": "Global Payments",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "GL",
        "name": "Globe Life",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "GDDY",
        "name": "GoDaddy",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "GS",
        "name": "Goldman Sachs",
        "sector": "financials",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "HAL",
        "name": "Halliburton",
        "sector": "energy",
        "market_cap_tier": "large"
    },
    {
        "symbol": "HIG",
        "name": "Hartford (The)",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "HAS",
        "name": "Hasbro",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "HCA",
        "name": "HCA Healthcare",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "DOC",
        "name": "Healthpeak Properties",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "HSIC",
        "name": "Henry Schein",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "HSY",
        "name": "Hershey Company (The)",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "HPE",
        "name": "Hewlett Packard Enterprise",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "HLT",
        "name": "Hilton Worldwide",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "HD",
        "name": "Home Depot (The)",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "HONA",
        "name": "Honeywell Aerospace",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "HON",
        "name": "Honeywell Technologies",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "HRL",
        "name": "Hormel Foods",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "HST",
        "name": "Host Hotels & Resorts",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "HWM",
        "name": "Howmet Aerospace",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "HPQ",
        "name": "HP Inc.",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "HUBB",
        "name": "Hubbell Incorporated",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "HUM",
        "name": "Humana",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "HBAN",
        "name": "Huntington Bancshares",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "HII",
        "name": "Huntington Ingalls Industries",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "IBM",
        "name": "IBM",
        "sector": "technology",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "IEX",
        "name": "IDEX Corporation",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "IDXX",
        "name": "Idexx Laboratories",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ITW",
        "name": "Illinois Tool Works",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ILMN",
        "name": "Illumina, Inc.",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "INCY",
        "name": "Incyte",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "IR",
        "name": "Ingersoll Rand",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PODD",
        "name": "Insulet Corporation",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "INTC",
        "name": "Intel",
        "sector": "technology",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "IBKR",
        "name": "Interactive Brokers",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ICE",
        "name": "Intercontinental Exchange",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "IFF",
        "name": "International Flavors & Fragrances",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "IP",
        "name": "International Paper",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "INTU",
        "name": "Intuit",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ISRG",
        "name": "Intuitive Surgical",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "IVZ",
        "name": "Invesco",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "INVH",
        "name": "Invitation Homes",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "IQV",
        "name": "IQVIA",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "IRM",
        "name": "Iron Mountain",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "JBHT",
        "name": "J.B. Hunt",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "JBL",
        "name": "Jabil",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "JKHY",
        "name": "Jack Henry & Associates",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "J",
        "name": "Jacobs Solutions",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "JNJ",
        "name": "Johnson & Johnson",
        "sector": "healthcare",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "JCI",
        "name": "Johnson Controls",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "JPM",
        "name": "JPMorgan Chase",
        "sector": "financials",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "KVUE",
        "name": "Kenvue",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "KDP",
        "name": "Keurig Dr Pepper",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "KEY",
        "name": "KeyCorp",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "KEYS",
        "name": "Keysight Technologies",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "KMB",
        "name": "Kimberly-Clark",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "KIM",
        "name": "Kimco Realty",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "KMI",
        "name": "Kinder Morgan",
        "sector": "energy",
        "market_cap_tier": "large"
    },
    {
        "symbol": "KKR",
        "name": "KKR & Co.",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "KLAC",
        "name": "KLA Corporation",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "KHC",
        "name": "Kraft Heinz",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "KR",
        "name": "Kroger",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "LHX",
        "name": "L3Harris",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "LH",
        "name": "Labcorp",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "LRCX",
        "name": "Lam Research",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "LVS",
        "name": "Las Vegas Sands",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "LDOS",
        "name": "Leidos",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "LEN",
        "name": "Lennar",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "LII",
        "name": "Lennox International",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "LLY",
        "name": "Lilly (Eli)",
        "sector": "healthcare",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "LIN",
        "name": "Linde plc",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "LYV",
        "name": "Live Nation Entertainment",
        "sector": "communication_services",
        "market_cap_tier": "large"
    },
    {
        "symbol": "LMT",
        "name": "Lockheed Martin",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "L",
        "name": "Loews Corporation",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "LOW",
        "name": "Lowe's",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "LULU",
        "name": "Lululemon Athletica",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "LITE",
        "name": "Lumentum",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "LYB",
        "name": "LyondellBasell",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MTB",
        "name": "M&T Bank",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MPC",
        "name": "Marathon Petroleum",
        "sector": "energy",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MAR",
        "name": "Marriott International",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MRSH",
        "name": "Marsh McLennan",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MLM",
        "name": "Martin Marietta Materials",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MRVL",
        "name": "Marvell Technology",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MAS",
        "name": "Masco",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MA",
        "name": "Mastercard",
        "sector": "financials",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "MKC",
        "name": "McCormick & Company",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MCD",
        "name": "McDonald's",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MCK",
        "name": "McKesson",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MDT",
        "name": "Medtronic",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MRK",
        "name": "Merck & Co.",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "META",
        "name": "Meta Platforms",
        "sector": "communication_services",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "MET",
        "name": "MetLife",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MTD",
        "name": "Mettler Toledo",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MGM",
        "name": "MGM Resorts",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MCHP",
        "name": "Microchip Technology",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MU",
        "name": "Micron Technology",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MSFT",
        "name": "Microsoft",
        "sector": "technology",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "MAA",
        "name": "Mid-America Apartment Communities",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MRNA",
        "name": "Moderna",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MDLZ",
        "name": "Mondelez International",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MPWR",
        "name": "Monolithic Power Systems",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MNST",
        "name": "Monster Beverage",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MCO",
        "name": "Moody's Corporation",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MS",
        "name": "Morgan Stanley",
        "sector": "financials",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "MOS",
        "name": "Mosaic Company (The)",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MSI",
        "name": "Motorola Solutions",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MSCI",
        "name": "MSCI",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "NDAQ",
        "name": "Nasdaq, Inc.",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "NTAP",
        "name": "NetApp",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "NFLX",
        "name": "Netflix",
        "sector": "communication_services",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "NEM",
        "name": "Newmont",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "NWSA",
        "name": "News Corp (Class A)",
        "sector": "communication_services",
        "market_cap_tier": "large"
    },
    {
        "symbol": "NWS",
        "name": "News Corp (Class B)",
        "sector": "communication_services",
        "market_cap_tier": "large"
    },
    {
        "symbol": "NEE",
        "name": "NextEra Energy",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "NKE",
        "name": "Nike, Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "NI",
        "name": "NiSource",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "NDSN",
        "name": "Nordson Corporation",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "NSC",
        "name": "Norfolk Southern",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "NTRS",
        "name": "Northern Trust",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "NOC",
        "name": "Northrop Grumman",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "NCLH",
        "name": "Norwegian Cruise Line Holdings",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "NRG",
        "name": "NRG Energy",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "NUE",
        "name": "Nucor",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "NVDA",
        "name": "NVIDIA Corporation",
        "sector": "technology",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "NVR",
        "name": "NVR, Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "NXPI",
        "name": "NXP Semiconductors",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ORLY",
        "name": "O'Reilly Automotive",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "OXY",
        "name": "Occidental Petroleum",
        "sector": "energy",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ODFL",
        "name": "Old Dominion",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "OMC",
        "name": "Omnicom Group",
        "sector": "communication_services",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ON",
        "name": "ON Semiconductor",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "OKE",
        "name": "Oneok",
        "sector": "energy",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ORCL",
        "name": "Oracle Corporation",
        "sector": "technology",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "OTIS",
        "name": "Otis Worldwide",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PCAR",
        "name": "Paccar",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PKG",
        "name": "Packaging Corporation of America",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PLTR",
        "name": "Palantir Technologies",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PANW",
        "name": "Palo Alto Networks",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PH",
        "name": "Parker Hannifin",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PAYX",
        "name": "Paychex",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PYPL",
        "name": "PayPal",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PNR",
        "name": "Pentair",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PEP",
        "name": "PepsiCo",
        "sector": "consumer_staples",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "PFE",
        "name": "Pfizer",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PCG",
        "name": "PG&E Corporation",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PM",
        "name": "Philip Morris International",
        "sector": "consumer_staples",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "PSX",
        "name": "Phillips 66",
        "sector": "energy",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PNW",
        "name": "Pinnacle West Capital",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PNC",
        "name": "PNC Financial Services",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PPG",
        "name": "PPG Industries",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PPL",
        "name": "PPL Corporation",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PFG",
        "name": "Principal Financial Group",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PG",
        "name": "Procter & Gamble",
        "sector": "consumer_staples",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "PGR",
        "name": "Progressive Corporation",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PLD",
        "name": "Prologis",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PRU",
        "name": "Prudential Financial",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PEG",
        "name": "Public Service Enterprise Group",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PTC",
        "name": "PTC Inc.",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PSA",
        "name": "Public Storage",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PHM",
        "name": "PulteGroup",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "PWR",
        "name": "Quanta Services",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "QCOM",
        "name": "Qualcomm",
        "sector": "technology",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "DGX",
        "name": "Quest Diagnostics",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "Q",
        "name": "Qnity Electronics",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "RL",
        "name": "Ralph Lauren Corporation",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "RJF",
        "name": "Raymond James Financial",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "RDDT",
        "name": "Reddit",
        "sector": "communication_services",
        "market_cap_tier": "large"
    },
    {
        "symbol": "RTX",
        "name": "RTX Corporation",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "O",
        "name": "Realty Income",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "REG",
        "name": "Regency Centers",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "REGN",
        "name": "Regeneron Pharmaceuticals",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "RF",
        "name": "Regions Financial Corporation",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "RSG",
        "name": "Republic Services",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "RMD",
        "name": "ResMed",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "RVTY",
        "name": "Revvity",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "HOOD",
        "name": "Robinhood Markets",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ROK",
        "name": "Rockwell Automation",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ROL",
        "name": "Rollins, Inc.",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ROP",
        "name": "Roper Technologies",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ROST",
        "name": "Ross Stores",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "RCL",
        "name": "Royal Caribbean Group",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "SPGI",
        "name": "S&P Global",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "CRM",
        "name": "Salesforce",
        "sector": "technology",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "SNDK",
        "name": "Sandisk",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "SBAC",
        "name": "SBA Communications",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "SLB",
        "name": "Schlumberger",
        "sector": "energy",
        "market_cap_tier": "large"
    },
    {
        "symbol": "STX",
        "name": "Seagate Technology",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "SRE",
        "name": "Sempra",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "NOW",
        "name": "ServiceNow",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "SHW",
        "name": "Sherwin-Williams",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "SPG",
        "name": "Simon Property Group",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "SKYD",
        "name": "Skydance Corporation",
        "sector": "communication_services",
        "market_cap_tier": "large"
    },
    {
        "symbol": "SWKS",
        "name": "Skyworks Solutions",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "SJM",
        "name": "J.M. Smucker Company (The)",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "SW",
        "name": "Smurfit Westrock",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "SNA",
        "name": "Snap-on",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "SOLV",
        "name": "Solventum",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "SO",
        "name": "Southern Company",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "LUV",
        "name": "Southwest Airlines",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "SWK",
        "name": "Stanley Black & Decker",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "SBUX",
        "name": "Starbucks",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "STT",
        "name": "State Street Corporation",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "STLD",
        "name": "Steel Dynamics",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "STE",
        "name": "Steris",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "SYK",
        "name": "Stryker Corporation",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "SMCI",
        "name": "Supermicro",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "SYF",
        "name": "Synchrony Financial",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "SNPS",
        "name": "Synopsys",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "SYY",
        "name": "Sysco",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TMUS",
        "name": "T-Mobile US",
        "sector": "communication_services",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TROW",
        "name": "T. Rowe Price",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TTWO",
        "name": "Take-Two Interactive",
        "sector": "communication_services",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TPR",
        "name": "Tapestry, Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TRGP",
        "name": "Targa Resources",
        "sector": "energy",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TGT",
        "name": "Target Corporation",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TEL",
        "name": "TE Connectivity",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TDY",
        "name": "Teledyne Technologies",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TER",
        "name": "Teradyne",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TSLA",
        "name": "Tesla, Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "TXN",
        "name": "Texas Instruments",
        "sector": "technology",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "TPL",
        "name": "Texas Pacific Land Corporation",
        "sector": "energy",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TXT",
        "name": "Textron",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TMO",
        "name": "Thermo Fisher Scientific",
        "sector": "healthcare",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "TJX",
        "name": "TJX Companies",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TKO",
        "name": "TKO Group Holdings",
        "sector": "communication_services",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TSCO",
        "name": "Tractor Supply",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TT",
        "name": "Trane Technologies",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TDG",
        "name": "TransDigm Group",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TRV",
        "name": "Travelers Companies (The)",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TRMB",
        "name": "Trimble Inc.",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TFC",
        "name": "Truist Financial",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TWLO",
        "name": "Twilio",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TYL",
        "name": "Tyler Technologies",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TSN",
        "name": "Tyson Foods",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "USB",
        "name": "U.S. Bancorp",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "UBER",
        "name": "Uber",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "UDR",
        "name": "UDR, Inc.",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ULTA",
        "name": "Ulta Beauty",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "UNP",
        "name": "Union Pacific Corporation",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "UAL",
        "name": "United Airlines Holdings",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "UPS",
        "name": "United Parcel Service",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "URI",
        "name": "United Rentals",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "UNH",
        "name": "UnitedHealth Group",
        "sector": "healthcare",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "UHS",
        "name": "Universal Health Services",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "VLO",
        "name": "Valero Energy",
        "sector": "energy",
        "market_cap_tier": "large"
    },
    {
        "symbol": "VEEV",
        "name": "Veeva Systems",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "VTR",
        "name": "Ventas",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "VLTO",
        "name": "Veralto",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "VRSN",
        "name": "Verisign",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "VRSK",
        "name": "Verisk Analytics",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "VZ",
        "name": "Verizon",
        "sector": "communication_services",
        "market_cap_tier": "large"
    },
    {
        "symbol": "VRTX",
        "name": "Vertex Pharmaceuticals",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "VRT",
        "name": "Vertiv",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "VTRS",
        "name": "Viatris",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "VICI",
        "name": "Vici Properties",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "V",
        "name": "Visa Inc.",
        "sector": "financials",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "VST",
        "name": "Vistra Corp.",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "VMRK",
        "name": "Vivmark Residential",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "VMC",
        "name": "Vulcan Materials Company",
        "sector": "materials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "VYLR",
        "name": "Vylor",
        "sector": "consumer_staples",
        "market_cap_tier": "large"
    },
    {
        "symbol": "WRB",
        "name": "W. R. Berkley Corporation",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "GWW",
        "name": "W. W. Grainger",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "WAB",
        "name": "Wabtec",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "WMT",
        "name": "Walmart",
        "sector": "consumer_staples",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "DIS",
        "name": "Walt Disney Company (The)",
        "sector": "communication_services",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "WM",
        "name": "Waste Management",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "WAT",
        "name": "Waters Corporation",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "WEC",
        "name": "WEC Energy Group",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "WFC",
        "name": "Wells Fargo",
        "sector": "financials",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "WELL",
        "name": "Welltower",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "WST",
        "name": "West Pharmaceutical Services",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "WDC",
        "name": "Western Digital",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "WY",
        "name": "Weyerhaeuser",
        "sector": "real_estate",
        "market_cap_tier": "large"
    },
    {
        "symbol": "WSM",
        "name": "Williams-Sonoma, Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "WMB",
        "name": "Williams Companies",
        "sector": "energy",
        "market_cap_tier": "large"
    },
    {
        "symbol": "WTW",
        "name": "Willis Towers Watson",
        "sector": "financials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "WDAY",
        "name": "Workday, Inc.",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "WYNN",
        "name": "Wynn Resorts",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "XEL",
        "name": "Xcel Energy",
        "sector": "utilities",
        "market_cap_tier": "large"
    },
    {
        "symbol": "XYL",
        "name": "Xylem Inc.",
        "sector": "industrials",
        "market_cap_tier": "large"
    },
    {
        "symbol": "YUM",
        "name": "Yum! Brands",
        "sector": "consumer_discretionary",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ZBRA",
        "name": "Zebra Technologies",
        "sector": "technology",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ZBH",
        "name": "Zimmer Biomet",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "ZTS",
        "name": "Zoetis",
        "sector": "healthcare",
        "market_cap_tier": "large"
    },
    {
        "symbol": "AA",
        "name": "Alcoa",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "AAL",
        "name": "American Airlines Group",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "AAON",
        "name": "AAON",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ACI",
        "name": "Albertsons",
        "sector": "consumer_staples",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ACM",
        "name": "AECOM",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ADC",
        "name": "Agree Realty",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "AEIS",
        "name": "Advanced Energy",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "AFG",
        "name": "American Financial Group",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "AGCO",
        "name": "AGCO",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "AGNC",
        "name": "AGNC Investment",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "AHR",
        "name": "American Healthcare REIT",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "AIT",
        "name": "Applied Industrial Technologies",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ALGM",
        "name": "Allegro MicroSystems",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ALK",
        "name": "Alaska Air Group",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ALLY",
        "name": "Ally Financial",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ALSN",
        "name": "Allison Transmission",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ALV",
        "name": "Autoliv",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "AM",
        "name": "Antero Midstream",
        "sector": "energy",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "AMG",
        "name": "Affiliated Managers Group",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "AMH",
        "name": "American Homes 4 Rent",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "AMKR",
        "name": "Amkor Technology",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "AN",
        "name": "AutoNation",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ANF",
        "name": "Abercrombie & Fitch",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "APG",
        "name": "APi Group",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "APPF",
        "name": "AppFolio",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "AR",
        "name": "Antero Resources",
        "sector": "energy",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ARMK",
        "name": "Aramark",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ARW",
        "name": "Arrow Electronics",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ARWR",
        "name": "Arrowhead Pharmaceuticals",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ASB",
        "name": "Associated Bank",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ASH",
        "name": "Ashland Global",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ATI",
        "name": "ATI Inc.",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ATR",
        "name": "AptarGroup",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "AVAV",
        "name": "AeroVironment",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "AVNT",
        "name": "Avient",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "AVT",
        "name": "Avnet",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "AVTR",
        "name": "Avantor",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "AXTA",
        "name": "Axalta",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "AYI",
        "name": "Acuity Brands",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "BAH",
        "name": "Booz Allen Hamilton",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "BBWI",
        "name": "Bath & Body Works, Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "BC",
        "name": "Brunswick",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "BCO",
        "name": "Brink's",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "BDC",
        "name": "Belden Inc.",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "BHF",
        "name": "Brighthouse Financial",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "BILL",
        "name": "Bill Holdings",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "BIO",
        "name": "Bio-Rad Laboratories",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "BJ",
        "name": "BJ's Wholesale Club",
        "sector": "consumer_staples",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "BKH",
        "name": "Black Hills Corporation",
        "sector": "utilities",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "BMRN",
        "name": "BioMarin Pharmaceutical",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "BRKR",
        "name": "Bruker",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "BROS",
        "name": "Dutch Bros Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "BRX",
        "name": "Brixmor Property Group",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "BSY",
        "name": "Bentley Systems",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "BTSG",
        "name": "BrightSpring Health Services",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "BURL",
        "name": "Burlington Stores",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "BWA",
        "name": "BorgWarner",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "BWXT",
        "name": "BWX Technologies",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "BYD",
        "name": "Boyd Gaming",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CACI",
        "name": "CACI International",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CAR",
        "name": "Avis Budget Group",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CART",
        "name": "Maplebear Inc.",
        "sector": "consumer_staples",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CAVA",
        "name": "Cava Group",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CBSH",
        "name": "Commerce Bancshares",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CBT",
        "name": "Cabot Corp",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CCK",
        "name": "Crown Holdings",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CDE",
        "name": "Coeur Mining",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CDP",
        "name": "COPT Defense Properties",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CELH",
        "name": "Celsius Holdings",
        "sector": "consumer_staples",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CFR",
        "name": "Frost Bank",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CG",
        "name": "Carlyle Group (The)",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CGNX",
        "name": "Cognex",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CHDN",
        "name": "Churchill Downs Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CHE",
        "name": "Chemed Corp.",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CHH",
        "name": "Choice Hotels",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CHRD",
        "name": "Chord Energy",
        "sector": "energy",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CHWY",
        "name": "Chewy",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CLF",
        "name": "Cleveland-Cliffs",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CLH",
        "name": "Clean Harbors",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CMC",
        "name": "Commercial Metals",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CNH",
        "name": "CNH Industrial",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CNM",
        "name": "Core & Main",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CNO",
        "name": "CNO Financial Group",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CNX",
        "name": "CNX Resources",
        "sector": "energy",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "COKE",
        "name": "Coca-Cola Consolidated",
        "sector": "consumer_staples",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "COLB",
        "name": "Columbia Banking System",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "COLM",
        "name": "Columbia Sportswear",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CORT",
        "name": "Corcept Therapeutics",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CR",
        "name": "Crane",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CRBG",
        "name": "Corebridge Financial",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CROX",
        "name": "Crocs",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CRS",
        "name": "Carpenter Technology",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CRUS",
        "name": "Cirrus Logic",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CSL",
        "name": "Carlisle Companies",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CTRE",
        "name": "CareTrust REIT",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CTVA",
        "name": "Corteva",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CUBE",
        "name": "CubeSmart",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CUZ",
        "name": "Cousins Properties",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CVLT",
        "name": "CommVault Systems",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CW",
        "name": "Curtiss-Wright",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CXT",
        "name": "Crane NXT",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CYTK",
        "name": "Cytokinetics",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "DAR",
        "name": "Darling Ingredients",
        "sector": "consumer_staples",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "DBX",
        "name": "Dropbox",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "DCI",
        "name": "Donaldson Company",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "DINO",
        "name": "HF Sinclair",
        "sector": "energy",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "DKS",
        "name": "Dick's Sporting Goods",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "DLB",
        "name": "Dolby",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "DOCN",
        "name": "DigitalOcean",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "DOCS",
        "name": "Doximity",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "DOCU",
        "name": "Docusign",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "DT",
        "name": "Dynatrace",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "DTM",
        "name": "DT Midstream",
        "sector": "energy",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "DUOL",
        "name": "Duolingo",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "DY",
        "name": "Dycom Industries",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "EAT",
        "name": "Brinker International",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "EEFT",
        "name": "Euronet Worldwide",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "EGP",
        "name": "EastGroup Properties",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "EHC",
        "name": "Encompass Health",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ELAN",
        "name": "Elanco",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ELF",
        "name": "e.l.f. Beauty",
        "sector": "consumer_staples",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ELS",
        "name": "Equity Lifestyle Properties",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ENS",
        "name": "EnerSys",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ENSG",
        "name": "Ensign Group",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ENTG",
        "name": "Entegris",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "EPR",
        "name": "EPR Properties",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "EQH",
        "name": "Equitable Holdings",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ESAB",
        "name": "ESAB",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ESNT",
        "name": "Essent Group Ltd.",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "EVR",
        "name": "Evercore",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "EWBC",
        "name": "East West Bancorp",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "EXEL",
        "name": "Exelixis",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "EXLS",
        "name": "EXL Service",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "EXP",
        "name": "Eagle Materials",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "EXPO",
        "name": "Exponent, Inc.",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "FAF",
        "name": "First American Financial Corporation",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "FBIN",
        "name": "Fortune Brands Innovations",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "FCFS",
        "name": "FirstCash",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "FCN",
        "name": "FTI Consulting",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "FFIN",
        "name": "First Financial Bankshares",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "FHI",
        "name": "Federated Hermes",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "FHN",
        "name": "First Horizon",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "FIVE",
        "name": "Five Below",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "FLG",
        "name": "Flagstar Bank",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "FLR",
        "name": "Fluor",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "FLS",
        "name": "Flowserve",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "FN",
        "name": "Fabrinet",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "FNB",
        "name": "FNB Corporation",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "FND",
        "name": "Floor & Decor",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "FNF",
        "name": "Fidelity National Financial",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "FORM",
        "name": "FormFactor, Inc.",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "FOUR",
        "name": "Shift4",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "FR",
        "name": "First Industrial Realty Trust",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "FTI",
        "name": "TechnipFMC",
        "sector": "energy",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "G",
        "name": "Genpact",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "GAP",
        "name": "Gap Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "GATX",
        "name": "GATX",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "GBCI",
        "name": "Glacier Bancorp",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "GEF",
        "name": "Greif, Inc.",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "GGG",
        "name": "Graco Inc.",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "GHC",
        "name": "Graham Holdings",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "GLPI",
        "name": "Gaming and Leisure Properties",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "GME",
        "name": "GameStop",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "GMED",
        "name": "Globus Medical",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "GNTX",
        "name": "Gentex",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "GPK",
        "name": "Graphic Packaging",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "GWRE",
        "name": "Guidewire Software",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "GXO",
        "name": "GXO Logistics",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "H",
        "name": "Hyatt",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "HAE",
        "name": "Haemonetics",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "HALO",
        "name": "Halozyme",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "HGV",
        "name": "Hilton Grand Vacations",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "HIMS",
        "name": "Hims & Hers Health",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "HL",
        "name": "Hecla Mining",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "HLI",
        "name": "Houlihan Lokey",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "HLNE",
        "name": "Hamilton Lane",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "HOG",
        "name": "Harley-Davidson",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "HOMB",
        "name": "Home BancShares",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "HQY",
        "name": "HealthEquity",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "HR",
        "name": "Healthcare Realty Trust",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "HRB",
        "name": "H&R Block",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "HUBS",
        "name": "HubSpot",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "HWC",
        "name": "Hancock Whitney",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "HXL",
        "name": "Hexcel",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "IBOC",
        "name": "Intl Bancshares Corp",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "IDA",
        "name": "Idacorp",
        "sector": "utilities",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "IDCC",
        "name": "InterDigital",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "IESC",
        "name": "IES Holdings",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "INGR",
        "name": "Ingredion",
        "sector": "consumer_staples",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "IPGP",
        "name": "IPG Photonics",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "IRT",
        "name": "Independence Realty Trust",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ITT",
        "name": "ITT Inc.",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "JAZZ",
        "name": "Jazz Pharmaceuticals",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "JEF",
        "name": "Jefferies",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "JLL",
        "name": "Jones Lang LaSalle",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "KBH",
        "name": "KB Home",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "KBR",
        "name": "KBR, Inc.",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "KD",
        "name": "Kyndryl",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "KEX",
        "name": "Kirby Corporation",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "KNF",
        "name": "Knife River Corporation",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "KNSL",
        "name": "Kinsale Capital Group",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "KNX",
        "name": "Knight-Swift",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "KRC",
        "name": "Kilroy Realty Corp",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "KRG",
        "name": "Kite Realty Group Trust",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "KRYS",
        "name": "Krystal Biotech",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "KTOS",
        "name": "Kratos Defense & Security Solutions",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "LAD",
        "name": "Lithia Motors",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "LAMR",
        "name": "Lamar Advertising Company",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "LEA",
        "name": "Lear",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "LECO",
        "name": "Lincoln Electric",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "LFUS",
        "name": "Littelfuse",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "LIVN",
        "name": "LivaNova",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "LNTH",
        "name": "Lantheus Holdings",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "LOPE",
        "name": "Grand Canyon Education",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "LPX",
        "name": "Louisiana-Pacific",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "LSCC",
        "name": "Lattice Semiconductor",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "LSTR",
        "name": "Landstar System",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "M",
        "name": "Macy's",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "MANH",
        "name": "Manhattan Associates",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "MAT",
        "name": "Mattel",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "MEDP",
        "name": "Medpace",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "MIDD",
        "name": "Middleby",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "MKSI",
        "name": "MKS Instruments",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "MLI",
        "name": "Mueller Industries",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "MMS",
        "name": "Maximus Inc.",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "MOG-A",
        "name": "Moog Inc.",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "MOH",
        "name": "Molina Healthcare",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "MORN",
        "name": "Morningstar, Inc.",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "MP",
        "name": "MP Materials",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "MSA",
        "name": "MSA Safety",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "MSM",
        "name": "MSC Industrial Direct",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "MTDR",
        "name": "Matador Resources",
        "sector": "energy",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "MTG",
        "name": "MGIC Investment Corporation",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "MTN",
        "name": "Vail Resorts",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "MTSI",
        "name": "MACOM Technology Solutions",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "MTZ",
        "name": "MasTec",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "MUR",
        "name": "Murphy Oil",
        "sector": "energy",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "MUSA",
        "name": "Murphy USA",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "MZTI",
        "name": "The Marzetti Company",
        "sector": "consumer_staples",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "NBIX",
        "name": "Neurocrine Biosciences",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "NEU",
        "name": "NewMarket Corporation",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "NFG",
        "name": "National Fuel Gas",
        "sector": "utilities",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "NJR",
        "name": "New Jersey Resources",
        "sector": "utilities",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "NLY",
        "name": "Annaly Capital Management",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "NNN",
        "name": "NNN Reit",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "NOV",
        "name": "NOV Inc.",
        "sector": "energy",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "NOVT",
        "name": "Novanta",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "NTNX",
        "name": "Nutanix",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "NVST",
        "name": "Envista Holdings",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "NVT",
        "name": "nVent Electric plc",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "NWE",
        "name": "NorthWestern Energy",
        "sector": "utilities",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "NXST",
        "name": "Nexstar Media Group",
        "sector": "communication_services",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "NXT",
        "name": "Nextpower",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "NYT",
        "name": "New York Times Company",
        "sector": "communication_services",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "OC",
        "name": "Owens Corning",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "OGE",
        "name": "OGE Energy",
        "sector": "utilities",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "OGS",
        "name": "One Gas",
        "sector": "utilities",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "OHI",
        "name": "Omega Healthcare Investors",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "OKTA",
        "name": "Okta, Inc.",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "OLED",
        "name": "Universal Display",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "OLLI",
        "name": "Ollie's Bargain Outlet",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ONB",
        "name": "Old National Bank",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ONTO",
        "name": "Onto Innovation",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "OPCH",
        "name": "Option Care Health",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ORA",
        "name": "Ormat Technologies",
        "sector": "utilities",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ORI",
        "name": "Old Republic International",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "OSK",
        "name": "Oshkosh",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "OVV",
        "name": "Ovintiv",
        "sector": "energy",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "OZK",
        "name": "Bank OZK",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "PAG",
        "name": "Penske Automotive Group",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "PATH",
        "name": "UiPath",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "PB",
        "name": "Prosperity Bancshares",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "PBF",
        "name": "PBF Energy",
        "sector": "energy",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "PCTY",
        "name": "Paylocity",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "PEGA",
        "name": "Pegasystems",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "PEN",
        "name": "Penumbra, Inc.",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "PFGC",
        "name": "Performance Food Group",
        "sector": "consumer_staples",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "PII",
        "name": "Polaris",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "PINS",
        "name": "Pinterest",
        "sector": "communication_services",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "PK",
        "name": "Park Hotels & Resorts",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "PLNT",
        "name": "Planet Fitness",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "PNFP",
        "name": "Pinnacle Financial Partners",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "POR",
        "name": "Portland General Electric",
        "sector": "utilities",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "POST",
        "name": "Post Holdings",
        "sector": "consumer_staples",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "PPC",
        "name": "Pilgrim's Pride",
        "sector": "consumer_staples",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "PR",
        "name": "Permian Resources",
        "sector": "energy",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "PRI",
        "name": "Primerica",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "PSN",
        "name": "Parsons Corporation",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "PVH",
        "name": "PVH Corp.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "QLYS",
        "name": "Qualys",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "R",
        "name": "Ryder",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "RBA",
        "name": "RB Global",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "RBC",
        "name": "RBC Bearings",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "REXR",
        "name": "Rexford Industrial Realty",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "RGA",
        "name": "Reinsurance Group of America",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "RGEN",
        "name": "Repligen",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "RGLD",
        "name": "Royal Gold",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "RH",
        "name": "RH",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "RLI",
        "name": "RLI Corp.",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "RMBS",
        "name": "Rambus",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "RNR",
        "name": "RenaissanceRe",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ROIV",
        "name": "Roivant Sciences",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ROKU",
        "name": "Roku, Inc.",
        "sector": "communication_services",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "RPM",
        "name": "RPM International",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "RRC",
        "name": "Range Resources",
        "sector": "energy",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "RRX",
        "name": "Regal Rexnord",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "RS",
        "name": "Reliance, Inc.",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "RYAN",
        "name": "Ryan Specialty",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "RYN",
        "name": "Rayonier",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SAIA",
        "name": "Saia",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SAIC",
        "name": "Science Applications Intl Corp",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SANM",
        "name": "Sanmina Corporation",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SARO",
        "name": "StandardAero",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SBRA",
        "name": "Sabra Health Care REIT",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SCI",
        "name": "Service Corp Intl",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SEIC",
        "name": "SEI Investments Company",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SF",
        "name": "Stifel",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SFM",
        "name": "Sprouts Farmers Market",
        "sector": "consumer_staples",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SGI",
        "name": "Somnigroup International",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SHC",
        "name": "Sotera Health",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SIGI",
        "name": "Selective Insurance Group",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SIRI",
        "name": "SiriusXM",
        "sector": "communication_services",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SITM",
        "name": "SiTime",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SLAB",
        "name": "Silicon Labs",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SLGN",
        "name": "Silgan Holdings",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SLM",
        "name": "SLM Corp",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SMG",
        "name": "Scotts Miracle-Gro Company",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SMTC",
        "name": "Semtech",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SN",
        "name": "SharkNinja",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SNX",
        "name": "TD Synnex",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SOLS",
        "name": "Solstice Advanced Materials",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SON",
        "name": "Sonoco",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SPXC",
        "name": "SPX Technologies",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SR",
        "name": "Spire",
        "sector": "utilities",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SSB",
        "name": "South State Bank",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SSD",
        "name": "Simpson Manufacturing",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ST",
        "name": "Sensata Technologies",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "STAG",
        "name": "STAG Industrial",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "STRL",
        "name": "Sterling Infrastructure",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "STWD",
        "name": "Starwood Property Trust",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SUI",
        "name": "Sun Communities",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SWX",
        "name": "Southwest Gas Corp",
        "sector": "utilities",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "SYNA",
        "name": "Synaptics",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "TCBI",
        "name": "Texas Capital Bancshares",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "TEX",
        "name": "Terex",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "THC",
        "name": "Tenet Health",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "THG",
        "name": "Hanover Insurance",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "THO",
        "name": "Thor Industries",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "TKR",
        "name": "Timken",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "TLN",
        "name": "Talen Energy",
        "sector": "utilities",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "TNL",
        "name": "Travel + Leisure Co.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "TOL",
        "name": "Toll Brothers",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "TOST",
        "name": "Toast, Inc.",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "TREX",
        "name": "Trex",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "TRU",
        "name": "TransUnion",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "TTC",
        "name": "Toro",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "TTEK",
        "name": "Tetra Tech",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "TTMI",
        "name": "TTM Technologies",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "TXNM",
        "name": "TXNM Energy",
        "sector": "utilities",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "TXRH",
        "name": "Texas Roadhouse",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "UBSI",
        "name": "United Bankshares",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "UFPI",
        "name": "UFP Industries",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "UGI",
        "name": "UGI Corp",
        "sector": "utilities",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ULS",
        "name": "UL Solutions",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "UMBF",
        "name": "UMB Financial Corp.",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "UNM",
        "name": "Unum",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "USFD",
        "name": "US Foods",
        "sector": "consumer_staples",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "UTHR",
        "name": "United Therapeutics",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "VAL",
        "name": "Valaris",
        "sector": "energy",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "VC",
        "name": "Visteon",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "VFC",
        "name": "VF Corporation",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "VIAV",
        "name": "Viavi Solutions",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "VICR",
        "name": "Vicor Corporation",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "VLY",
        "name": "Valley Bank",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "VMI",
        "name": "Valmont Industries",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "VNO",
        "name": "Vornado Realty Trust",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "VNOM",
        "name": "Viper Energy",
        "sector": "energy",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "VNT",
        "name": "Vontier",
        "sector": "technology",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "VOYA",
        "name": "Voya Financial",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "VVV",
        "name": "Valvoline",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "WAL",
        "name": "Western Alliance Bancorporation",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "WCC",
        "name": "WESCO International",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "WEX",
        "name": "WEX Inc.",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "WFRD",
        "name": "Weatherford International",
        "sector": "energy",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "WH",
        "name": "Wyndham Hotels & Resorts",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "WHR",
        "name": "Whirlpool Corporation",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "WING",
        "name": "Wingstop",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "WLK",
        "name": "Westlake Corporation",
        "sector": "materials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "WMG",
        "name": "Warner Music Group",
        "sector": "communication_services",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "WMS",
        "name": "Advanced Drainage Systems",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "WPC",
        "name": "W. P. Carey",
        "sector": "real_estate",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "WSO",
        "name": "Watsco",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "WTFC",
        "name": "Wintrust Financial",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "WTRG",
        "name": "Essential Utilities",
        "sector": "utilities",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "WTS",
        "name": "Watts Water Technologies",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "WWD",
        "name": "Woodward, Inc.",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "XPO",
        "name": "XPO, Inc.",
        "sector": "industrials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "XRAY",
        "name": "Dentsply Sirona",
        "sector": "healthcare",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "YETI",
        "name": "Yeti Holdings",
        "sector": "consumer_discretionary",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ZION",
        "name": "Zions Bancorporation",
        "sector": "financials",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ASTS",
        "name": "AST SpaceMobile Inc.",
        "sector": "ai_specialty",
        "market_cap_tier": "small"
    },
    {
        "symbol": "IONQ",
        "name": "IonQ Inc.",
        "sector": "ai_specialty",
        "market_cap_tier": "small"
    },
    {
        "symbol": "RGTI",
        "name": "Rigetti Computing Inc.",
        "sector": "ai_specialty",
        "market_cap_tier": "small"
    },
    {
        "symbol": "QBTS",
        "name": "D-Wave Quantum Inc.",
        "sector": "ai_specialty",
        "market_cap_tier": "small"
    },
    {
        "symbol": "SOUN",
        "name": "SoundHound AI Inc.",
        "sector": "ai_specialty",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BBAI",
        "name": "BigBear.ai Holdings Inc.",
        "sector": "ai_specialty",
        "market_cap_tier": "small"
    },
    {
        "symbol": "MSTR",
        "name": "MicroStrategy Incorporated",
        "sector": "ai_specialty",
        "market_cap_tier": "large"
    },
    {
        "symbol": "MARA",
        "name": "MARA Holdings Inc.",
        "sector": "ai_specialty",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CLSK",
        "name": "CleanSpark Inc.",
        "sector": "ai_specialty",
        "market_cap_tier": "small"
    },
    {
        "symbol": "RIOT",
        "name": "Riot Platforms Inc.",
        "sector": "ai_specialty",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CIFR",
        "name": "Cipher Mining Inc.",
        "sector": "ai_specialty",
        "market_cap_tier": "small"
    },
    {
        "symbol": "NBIS",
        "name": "Nebius Group N.V.",
        "sector": "ai_specialty",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "CORZ",
        "name": "Core Scientific Inc.",
        "sector": "ai_specialty",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "APLD",
        "name": "Applied Digital Corporation",
        "sector": "ai_specialty",
        "market_cap_tier": "small"
    },
    {
        "symbol": "IREN",
        "name": "Iris Energy Limited",
        "sector": "ai_specialty",
        "market_cap_tier": "small"
    },
    {
        "symbol": "WULF",
        "name": "TeraWulf Inc.",
        "sector": "ai_specialty",
        "market_cap_tier": "small"
    },
    {
        "symbol": "HUT",
        "name": "Hut 8 Corp.",
        "sector": "ai_specialty",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AAOI",
        "name": "Applied Optoelectronics Inc.",
        "sector": "ai_specialty",
        "market_cap_tier": "small"
    },
    {
        "symbol": "POET",
        "name": "POET Technologies Inc.",
        "sector": "ai_specialty",
        "market_cap_tier": "small"
    },
    {
        "symbol": "SYM",
        "name": "Symbotic Inc.",
        "sector": "ai_specialty",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "TEM",
        "name": "Tempus AI Inc.",
        "sector": "ai_specialty",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "UPST",
        "name": "Upstart Holdings Inc.",
        "sector": "ai_specialty",
        "market_cap_tier": "small"
    },
    {
        "symbol": "DJT",
        "name": "Trump Media & Technology Group Corp.",
        "sector": "ai_specialty",
        "market_cap_tier": "small"
    },
    {
        "symbol": "OPEN",
        "name": "Opendoor Technologies Inc.",
        "sector": "ai_specialty",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AFRM",
        "name": "Affirm Holdings Inc.",
        "sector": "ai_specialty",
        "market_cap_tier": "mid"
    },
    {
        "symbol": "ARM",
        "name": "Arm Holdings plc",
        "sector": "ai_specialty",
        "market_cap_tier": "large"
    },
    {
        "symbol": "TSM",
        "name": "Taiwan Semiconductor Manufacturing Co.",
        "sector": "ai_specialty",
        "market_cap_tier": "mega"
    },
    {
        "symbol": "AAMI",
        "name": "Acadian Asset Management Inc.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AAP",
        "name": "Advance Auto Parts, Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AAT",
        "name": "American Assets Trust",
        "sector": "real_estate",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ABCB",
        "name": "Ameris Bancorp",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ABG",
        "name": "Asbury Automotive Group",
        "sector": "consumer_discretionary",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ABM",
        "name": "ABM Industries, Inc.",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ABR",
        "name": "Arbor Realty Trust",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ACA",
        "name": "Arcosa, Inc.",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ACAD",
        "name": "Acadia Pharmaceuticals",
        "sector": "healthcare",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ACHC",
        "name": "Acadia Healthcare",
        "sector": "healthcare",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ACIW",
        "name": "ACI Worldwide",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ACLS",
        "name": "Axcelis Technologies, Inc.",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ACMR",
        "name": "ACM Research, Inc.",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ACT",
        "name": "Enact Holdings, Inc.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ADAM",
        "name": "Adamas Trust, Inc.",
        "sector": "real_estate",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ADEA",
        "name": "Adeia, Inc.",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ADIG",
        "name": "ADI Global Distribution",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ADMA",
        "name": "ADMA Biologics, Inc.",
        "sector": "healthcare",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ADNT",
        "name": "Adient",
        "sector": "consumer_discretionary",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ADT",
        "name": "ADT Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ADUS",
        "name": "Addus HomeCare Corp.",
        "sector": "healthcare",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AEO",
        "name": "American Eagle Outfitters",
        "sector": "consumer_discretionary",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AESI",
        "name": "Atlas Energy Solutions, Inc.",
        "sector": "energy",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AGNT",
        "name": "eXp World Holdings, Inc.",
        "sector": "real_estate",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AGO",
        "name": "Assured Guaranty Ltd.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AGX",
        "name": "Argan, Inc.",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AGYS",
        "name": "Agilysys, Inc.",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AHCO",
        "name": "AdaptHealth Corp.",
        "sector": "healthcare",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AIN",
        "name": "Albany International Corp.",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AIR",
        "name": "AAR Corp.",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AKR",
        "name": "Acadia Realty Trust",
        "sector": "real_estate",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ALG",
        "name": "Alamo Group",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ALGT",
        "name": "Allegiant Travel Company",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ALHC",
        "name": "Alignment Healthcare, Inc.",
        "sector": "healthcare",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ALKS",
        "name": "Alkermes plc",
        "sector": "healthcare",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ALRM",
        "name": "Alarm.Com, Inc.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AMN",
        "name": "Amn Healthcare Services, Inc.",
        "sector": "healthcare",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AMPH",
        "name": "Amphstar Pharmaceuticals, Inc.",
        "sector": "healthcare",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AMR",
        "name": "Alpha Metallurgical Resources, Inc.",
        "sector": "materials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AMRX",
        "name": "Amneal Pharmaceuticals",
        "sector": "healthcare",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AMSF",
        "name": "Amerisafe, Inc.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AMTM",
        "name": "Amentum",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ANDE",
        "name": "The Andersons, Inc.",
        "sector": "consumer_staples",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ANIP",
        "name": "ANI Pharmaceuticals, Inc.",
        "sector": "healthcare",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AORT",
        "name": "Artivion",
        "sector": "healthcare",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AOSL",
        "name": "Alpha and Omega Semiconductor, Ltd.",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "APAM",
        "name": "Artisan Partners Asset Management, Inc.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "APLE",
        "name": "Apple Hospitality REIT, Inc.",
        "sector": "real_estate",
        "market_cap_tier": "small"
    },
    {
        "symbol": "APOG",
        "name": "Apogee Enterprises, Inc.",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ARCB",
        "name": "ArcBest Corp.",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ARLO",
        "name": "Arlo Technologies",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AROC",
        "name": "Archrock, Inc.",
        "sector": "energy",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ARR",
        "name": "Armour Residential REIT",
        "sector": "real_estate",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ASO",
        "name": "Academy Sports + Outdoors",
        "sector": "consumer_discretionary",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ASTE",
        "name": "Astec Industries, Inc.",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ASTH",
        "name": "Astrana Health, Inc.",
        "sector": "healthcare",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ATEN",
        "name": "A10 Networks, Inc.",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ATMU",
        "name": "Atmus Filtration Technologies Inc.",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AUB",
        "name": "Atlantic Union Bankshares, Corp.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AVA",
        "name": "Avista Corporation",
        "sector": "utilities",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AWI",
        "name": "Armstrong World Industries, Inc.",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AWR",
        "name": "American States Water Company",
        "sector": "utilities",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AX",
        "name": "Axos Financial, Inc.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AZTA",
        "name": "Azenta, Inc.",
        "sector": "healthcare",
        "market_cap_tier": "small"
    },
    {
        "symbol": "AZZ",
        "name": "AZZ, Inc.",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BANC",
        "name": "Banc Of California, Inc.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BANF",
        "name": "Bancfirst Corp",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BANR",
        "name": "Banner Corporation",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BBT",
        "name": "Beacon Financial Corp.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BCC",
        "name": "Boise Cascade",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BCPC",
        "name": "Balchem Corporation",
        "sector": "materials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BFAM",
        "name": "Bright Horizons Family Solutions Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BFH",
        "name": "Bread Financial Holdings, Inc.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BFS",
        "name": "Saul Centers, Inc.",
        "sector": "real_estate",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BGC",
        "name": "BGC Group, Inc.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BHE",
        "name": "Benchmark Electronics, Inc.",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BJRI",
        "name": "BJ's Restaurants, Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BKE",
        "name": "The Buckle, Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BKU",
        "name": "BankUnited, Inc.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BL",
        "name": "BlackLine Systems, Inc.",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BLFS",
        "name": "BioLife Solutions, Inc.",
        "sector": "healthcare",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BLKB",
        "name": "Blackbaud",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BMI",
        "name": "Badger Meter, Inc.",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BNL",
        "name": "Broadstone Net Lease, Inc.",
        "sector": "real_estate",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BOH",
        "name": "Bank of Hawaii",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BOOT",
        "name": "Boot Barn Holdings, Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BOX",
        "name": "Box, Inc.",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BRC",
        "name": "Brady Corporation",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BTU",
        "name": "Peabody Energy, Inc.",
        "sector": "energy",
        "market_cap_tier": "small"
    },
    {
        "symbol": "BXMT",
        "name": "Blackstone Mortgage Trust, Inc.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CACC",
        "name": "Credit Acceptance",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CAG",
        "name": "Conagra Brands",
        "sector": "consumer_staples",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CAKE",
        "name": "The Cheesecake Factory, Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CALM",
        "name": "Cal-Maine Foods, Inc.",
        "sector": "consumer_staples",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CALX",
        "name": "Calix",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CALY",
        "name": "Callaway Golf Company",
        "sector": "consumer_discretionary",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CARG",
        "name": "CarGurus",
        "sector": "communication_services",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CASH",
        "name": "Pathward Financial, Inc.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CATY",
        "name": "Cathay General Bancorp",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CBRL",
        "name": "Cracker Barrel",
        "sector": "consumer_discretionary",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CBU",
        "name": "Community Bank System, Inc.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CC",
        "name": "Chemours",
        "sector": "materials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CCOI",
        "name": "Cogent Communications Holdings, Inc.",
        "sector": "communication_services",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CCS",
        "name": "Century Communities, Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CE",
        "name": "Celanese",
        "sector": "materials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CENT",
        "name": "Central Garden & Pet Company",
        "sector": "consumer_staples",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CENTA",
        "name": "Central Garden & Pet Company (Class A)",
        "sector": "consumer_staples",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CENX",
        "name": "Century Aluminum Company",
        "sector": "materials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CERT",
        "name": "Certara, Inc.",
        "sector": "healthcare",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CFFN",
        "name": "Capitol Federal Savings Bank",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CHCO",
        "name": "City Holding Company",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CHEF",
        "name": "Chefs' Warehouse, Inc.",
        "sector": "consumer_staples",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CNK",
        "name": "Cinemark Holdings, Inc.",
        "sector": "communication_services",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CNMD",
        "name": "CONMED Corporation",
        "sector": "healthcare",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CNR",
        "name": "Core Natural Resources, Inc.",
        "sector": "energy",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CNS",
        "name": "Cohen & Steers, Inc.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CNXC",
        "name": "Concentrix",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CNXN",
        "name": "PC Connection, Inc.",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "COCO",
        "name": "The Vita Coco Company",
        "sector": "consumer_staples",
        "market_cap_tier": "small"
    },
    {
        "symbol": "COHU",
        "name": "Cohu, Inc.",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "COLL",
        "name": "Collegium Pharmaceutical, Inc.",
        "sector": "healthcare",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CON",
        "name": "Concentra Group Holdings Parent, Inc.",
        "sector": "healthcare",
        "market_cap_tier": "small"
    },
    {
        "symbol": "COTY",
        "name": "Coty",
        "sector": "consumer_staples",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CPB",
        "name": "The Campbell's Company",
        "sector": "consumer_staples",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CPF",
        "name": "Central Pacific Financial Corp.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CPK",
        "name": "Chesapeake Utilities Corp.",
        "sector": "utilities",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CRC",
        "name": "California Resources Corporation",
        "sector": "energy",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CRGY",
        "name": "Crescent Energy Company",
        "sector": "energy",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CRI",
        "name": "Carter's, Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CRK",
        "name": "Comstock Resources, Inc.",
        "sector": "energy",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CRSR",
        "name": "Corsair Gaming",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CRVL",
        "name": "CorVel Corporation",
        "sector": "healthcare",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CSR",
        "name": "Centerspace Trust",
        "sector": "real_estate",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CSW",
        "name": "CSW Industrials, Inc.",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CTS",
        "name": "CTS Corporation",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CUBI",
        "name": "Customers Bancorp, Inc.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CURB",
        "name": "Curbline Properties Corp.",
        "sector": "real_estate",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CVBF",
        "name": "CVB Financial Corp.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CVCO",
        "name": "Cavco Industries, Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CVI",
        "name": "CVR Energy, Inc.",
        "sector": "energy",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CVSA",
        "name": "Covista Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CWEN",
        "name": "Clearway Energy, Inc. (Class C)",
        "sector": "utilities",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CWEN-A",
        "name": "Clearway Energy, Inc. (Class A)",
        "sector": "utilities",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CWK",
        "name": "Cushman & Wakefield plc",
        "sector": "real_estate",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CWST",
        "name": "Casella Waste Systems, Inc.",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CWT",
        "name": "California Water Service Group",
        "sector": "utilities",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CXM",
        "name": "Sprinklr, Inc.",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CXW",
        "name": "CoreCivic",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "CZR",
        "name": "Caesars Entertainment",
        "sector": "consumer_discretionary",
        "market_cap_tier": "small"
    },
    {
        "symbol": "DAN",
        "name": "Dana Incorporated",
        "sector": "consumer_discretionary",
        "market_cap_tier": "small"
    },
    {
        "symbol": "DAVE",
        "name": "Dave, Inc.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "DBD",
        "name": "Diebold Nixdorf",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "DCH",
        "name": "Dauch Corporation",
        "sector": "consumer_discretionary",
        "market_cap_tier": "small"
    },
    {
        "symbol": "DCOM",
        "name": "Dime Community Bancshares, Inc.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "DEA",
        "name": "Easterly Government Properties, Inc.",
        "sector": "real_estate",
        "market_cap_tier": "small"
    },
    {
        "symbol": "DEI",
        "name": "Douglas Emmett",
        "sector": "real_estate",
        "market_cap_tier": "small"
    },
    {
        "symbol": "DFH",
        "name": "Dream Finders Homes, Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "small"
    },
    {
        "symbol": "DFIN",
        "name": "Donnelley Financial Solutions, Inc.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "DGII",
        "name": "Digi International Inc.",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "DIOD",
        "name": "Diodes Incorporated",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "DLX",
        "name": "Deluxe Corporation",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "DMC",
        "name": "Del Monte Corporation",
        "sector": "consumer_staples",
        "market_cap_tier": "small"
    },
    {
        "symbol": "DNOW",
        "name": "NOW Inc",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "DORM",
        "name": "Dorman Products, Inc.",
        "sector": "consumer_discretionary",
        "market_cap_tier": "small"
    },
    {
        "symbol": "DRH",
        "name": "DiamondRock Hospitality Company",
        "sector": "real_estate",
        "market_cap_tier": "small"
    },
    {
        "symbol": "DV",
        "name": "DoubleVerify Holdings Inc.",
        "sector": "communication_services",
        "market_cap_tier": "small"
    },
    {
        "symbol": "DXC",
        "name": "DXC Technology",
        "sector": "technology",
        "market_cap_tier": "small"
    },
    {
        "symbol": "DXPE",
        "name": "DXP Enterprises, Inc.",
        "sector": "industrials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "EBC",
        "name": "Eastern Bankshares, Inc.",
        "sector": "financials",
        "market_cap_tier": "small"
    },
    {
        "symbol": "ECG",
        "name": "Everus Construction Group, Inc.",
        "sector": "industrials",
        "market_cap_tier": "small"
    }
]

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
