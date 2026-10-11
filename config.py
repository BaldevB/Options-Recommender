"""Configuration module for Options Suggester.

Enhanced with:
- Dedicated 0DTE (Zero Days To Expiration) High-Velocity Universe (SPY, QQQ, IWM, NVDA, TSLA, etc.)
- Dedicated AI Stock Ecosystem (40+ tickers across 7 sub-sectors)
- Dedicated Commodities & Natural Resources Universe (Precious Metals, Energy, Copper, Agriculture, Uranium)
- Dedicated High-Risk & Speculative Trade Setups (MSTR, COIN, ASTS, IONQ, etc.) with Uncapped Sizing
- Multi-timeframe trend alignment thresholds
- Volume confirmation settings
- Earnings blackout window configuration
- Strict delta targeting (0.30 - 0.55 for core, 0.15 - 0.28 for high-risk, 0.40 - 0.55 for 0DTE scalps)
- Position sizing parameters with risk allocation
- Implied Volatility threshold for debit spread alternatives
- Rich categorized watchlists (100+ liquid US equities and ETFs)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


# Predefined Categorized Watchlists for Quick Sector Analysis
WATCHLIST_CATEGORIES: Dict[str, List[str]] = {
    "Mega-Cap Tech": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA"],
    "Semiconductors": ["NVDA", "AMD", "AVGO", "QCOM", "TXN", "INTC", "MU", "ARM", "TSM"],
    "Commodities & Metals": ["GLD", "SLV", "GDX", "USO", "UNG", "FCX", "COPX", "CCJ", "DBA", "NEM"],
    "Financials": ["JPM", "BAC", "WFC", "GS", "MS", "V", "MA", "PYPL"],
    "Consumer & Retail": ["COST", "WMT", "TGT", "NKE", "SBUX", "MCD", "HD"],
    "Healthcare & Biotech": ["LLY", "JNJ", "PFE", "UNH", "ABBV", "MRK", "AMGN"],
    "Energy & Industrials": ["XOM", "CVX", "COP", "CAT", "GE", "BA", "DE"],
    "Index ETFs": ["SPY", "QQQ", "IWM", "DIA", "SMH", "XLF", "XLE"]
}

# Dedicated Commodities & Natural Resources Ecosystem (Liquid ETFs & Top Producers)
COMMODITIES_CATEGORIES: Dict[str, List[str]] = {
    "Precious Metals & Miners": [
        "GLD", "SLV", "GDX", "GDXJ", "NEM", "GOLD"
    ],
    "Energy, Crude & Natural Gas": [
        "USO", "UNG", "XLE", "XOM", "CVX", "OXY"
    ],
    "Industrial Metals, Copper & Materials": [
        "FCX", "COPX", "CPER", "SCCO", "CLF", "NUE", "ALB"
    ],
    "Agriculture & Fertilizers": [
        "DBA", "WEAT", "CORN", "MOS", "CF"
    ],
    "Uranium & Nuclear Fuel": [
        "CCJ", "URA", "NXE"
    ]
}

# Flattened Commodities Universe for scanning
COMMODITIES_UNIVERSE: List[str] = list(dict.fromkeys(
    ticker for tickers in COMMODITIES_CATEGORIES.values() for ticker in tickers
))

# Dedicated AI Stock Ecosystem (40+ Leaders across 7 Segments)
AI_STOCKS_CATEGORIES: Dict[str, List[str]] = {
    "AI Chips & Semiconductors": [
        "NVDA", "AMD", "AVGO", "TSM", "ARM", "MRVL", "MU", "QCOM"
    ],
    "AI NeoClouds & GPU Compute": [
        "NBIS", "CORZ", "APLD", "IREN", "WULF", "HUT"
    ],
    "AI Optical Interconnect & Photonics": [
        "COHR", "LITE", "AAOI", "FN", "CIEN", "GLW", "POET"
    ],
    "AI Memory & Storage (HBM)": [
        "MU", "WDC", "STX", "LRCX", "AMAT"
    ],
    "AI Hyperscalers & Big Tech": [
        "MSFT", "GOOGL", "AMZN", "META", "AAPL"
    ],
    "AI Enterprise Software & Cyber": [
        "PLTR", "CRWD", "NOW", "SNOW", "ORCL", "NET"
    ],
    "AI Hardware & Data Center Infra": [
        "VRT", "DELL", "ANET", "SMCI"
    ]
}

# Flattened AI Stocks Universe for scanning
AI_STOCKS_UNIVERSE: List[str] = list(dict.fromkeys(
    ticker for tickers in AI_STOCKS_CATEGORIES.values() for ticker in tickers
))

# Dedicated High-Risk / High-Beta / Speculative Stocks Universe
HIGH_RISK_CATEGORIES: Dict[str, List[str]] = {
    "Crypto-Beta & AI Miners": [
        "MSTR", "COIN", "MARA", "CLSK", "RIOT", "CIFR"
    ],
    "Speculative Tech & Quantum": [
        "ASTS", "IONQ", "RGTI", "QBTS", "SOUN", "PLUG"
    ],
    "High-Vol Fintech & Squeeze Growth": [
        "CVNA", "SMCI", "UPST", "AFRM", "DJT", "RDDT", "OPEN"
    ],
    "0DTE Index & High-Beta Scalps": [
        "SPY", "QQQ", "IWM", "NVDA", "TSLA", "AMD"
    ]
}

# Flattened High-Risk Universe
HIGH_RISK_UNIVERSE: List[str] = list(dict.fromkeys(
    ticker for tickers in HIGH_RISK_CATEGORIES.values() for ticker in tickers
))

# Dedicated 0DTE High-Velocity Universe (Highest Intraday Options Volume)
ZERO_DTE_UNIVERSE: List[str] = [
    "SPY", "QQQ", "IWM", "NVDA", "TSLA", "AAPL", "AMD", "META", "AMZN", "MSFT"
]

# Flattened list of all unique tickers across standard watchlist & commodities
EXPANDED_WATCHLIST: List[str] = list(dict.fromkeys(
    [ticker for tickers in WATCHLIST_CATEGORIES.values() for ticker in tickers] +
    COMMODITIES_UNIVERSE
))


@dataclass
class TechnicalConfig:
    """Technical indicators configuration with volume & MTF confirmation."""
    rsi_period: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    sma_short: int = 20
    sma_long: int = 50
    volume_ma_period: int = 20
    volume_confirmation_threshold: float = 1.0  # At least 1.0x average volume for strong signals
    volume_confirmation_ratio: float = 1.0      # Alias
    # Multi-timeframe trend check: Weekly SMA-10 (intermediate trend)
    weekly_trend_period: int = 10


@dataclass
class EarningsConfig:
    """Earnings calendar blackout parameters."""
    blackout_days: int = 8      # Strict blackout: block trades if earnings <= 8 days away
    warning_days: int = 14     # Warning banner: flag elevated IV risk if earnings <= 14 days


@dataclass
class OptionsFilterConfig:
    """Options contract filtering and delta targeting parameters."""
    # Target Delta bounds: 0.30 - 0.55 delta sweet spot
    min_delta: float = 0.30
    max_delta: float = 0.55
    target_delta: float = 0.42  # Optimal strike delta centering
    # Expiration cycle: 14 to 45 Days to Expiration (DTE)
    min_dte: int = 14
    max_dte: int = 45
    # Liquidity filters
    min_open_interest: int = 100
    min_volume: int = 25
    max_spread_pct_of_mid: float = 0.10  # Max 10% bid-ask spread
    min_bid: float = 0.10               # Eliminate worthless contracts
    # Implied Volatility threshold to trigger Debit Spread suggestion
    elevated_iv_threshold: float = 45.0  # 45% IV
    top_n_suggestions: int = 5
    risk_free_rate: float = 0.045        # Risk-free interest rate (4.5%)


@dataclass
class HighRiskOptionsFilterConfig:
    """Screening filters for aggressive, asymmetric high-risk trade setups."""
    min_dte: int = 7
    max_dte: int = 28
    min_open_interest: int = 50
    min_volume: int = 15
    max_spread_pct_of_mid: float = 0.18
    min_bid: float = 0.05
    # Out-of-the-money (OTM) asymmetric delta range: 0.15 to 0.28 delta
    min_delta: float = 0.15
    max_delta: float = 0.28
    target_delta: float = 0.22
    # Uncapped risk budget (None uses standard trade risk allocation without arbitrary caps)
    speculative_risk_pct: Optional[float] = None
    min_risk_reward_ratio: float = 2.5   # Minimum 2.5:1 R:R for lotto spreads
    risk_free_rate: float = 0.045        # Risk-free interest rate (4.5%)


@dataclass
class ZeroDteOptionsFilterConfig:
    """Screening filters for ultra-high velocity 0DTE (same-day / next-session) options."""
    min_dte: int = 0
    max_dte: int = 1
    # Scalp sweet-spot (ATM momentum scalp): ~0.45 to 0.55 Delta
    target_scalp_delta: float = 0.50
    min_scalp_delta: float = 0.38
    max_scalp_delta: float = 0.58
    # Lotto moonshot sweet-spot (OTM gamma convexity): ~0.15 to 0.28 Delta
    target_lotto_delta: float = 0.20
    min_lotto_delta: float = 0.12
    max_lotto_delta: float = 0.28
    # Liquidity filters (0DTE demands high volume)
    min_volume: int = 50
    min_open_interest: int = 50
    max_spread_pct_of_mid: float = 0.20
    min_bid: float = 0.05
    # Uncapped risk budget (None uses standard trade risk allocation without arbitrary caps)
    speculative_risk_pct: Optional[float] = None
    min_risk_reward_ratio: float = 3.0   # Minimum 3:1 R:R for 0DTE lotto spreads
    risk_free_rate: float = 0.045


@dataclass
class RiskManagementConfig:
    """Position sizing and risk parameters."""
    account_equity: float = 10000.0  # Default nominal account size ($)
    max_risk_pct: float = 0.01       # 1% max capital risk per trade
    stop_loss_pct: float = 0.50      # Practical stop loss at 50% option premium loss


@dataclass
class SignalWeights:
    """Weights and confidence classification thresholds."""
    momentum_weight: float = 0.60
    sentiment_weight: float = 0.40
    # Confidence tier boundaries (High / Medium / Low)
    high_confidence_thresh: float = 0.45
    medium_confidence_thresh: float = 0.25
    low_confidence_thresh: float = 0.15


@dataclass
class AppConfig:
    """Master application configuration."""
    default_watchlist: List[str] = field(default_factory=lambda: EXPANDED_WATCHLIST[:12])
    all_supported_watchlist: List[str] = field(default_factory=lambda: EXPANDED_WATCHLIST)
    watchlist_categories: Dict[str, List[str]] = field(default_factory=lambda: WATCHLIST_CATEGORIES)
    commodities_categories: Dict[str, List[str]] = field(default_factory=lambda: COMMODITIES_CATEGORIES)
    commodities_universe: List[str] = field(default_factory=lambda: COMMODITIES_UNIVERSE)
    ai_stocks_categories: Dict[str, List[str]] = field(default_factory=lambda: AI_STOCKS_CATEGORIES)
    ai_stocks_universe: List[str] = field(default_factory=lambda: AI_STOCKS_UNIVERSE)
    high_risk_categories: Dict[str, List[str]] = field(default_factory=lambda: HIGH_RISK_CATEGORIES)
    high_risk_universe: List[str] = field(default_factory=lambda: HIGH_RISK_UNIVERSE)
    zero_dte_universe: List[str] = field(default_factory=lambda: ZERO_DTE_UNIVERSE)
    technicals: TechnicalConfig = field(default_factory=TechnicalConfig)
    earnings: EarningsConfig = field(default_factory=EarningsConfig)
    options_filter: OptionsFilterConfig = field(default_factory=OptionsFilterConfig)
    high_risk_filter: HighRiskOptionsFilterConfig = field(default_factory=HighRiskOptionsFilterConfig)
    zero_dte_filter: ZeroDteOptionsFilterConfig = field(default_factory=ZeroDteOptionsFilterConfig)
    risk: RiskManagementConfig = field(default_factory=RiskManagementConfig)
    weights: SignalWeights = field(default_factory=SignalWeights)
    history_period: str = "6mo"
    news_limit: int = 10
    cache_ttl_seconds: int = 900  # 15 minutes TTL for market data caching
    disclaimer: str = (
        "⚠️ DISCLAIMER: This tool is strictly for informational and educational purposes only. "
        "It does NOT constitute financial advice, investment advice, or an offer or recommendation "
        "to buy or sell any security or option contract. Options involve significant risk and are not "
        "suitable for all investors. Trade at your own risk."
    )


# Global default configuration instances
DEFAULT_CONFIG = AppConfig()
HIGH_RISK_FILTER_CONFIG = DEFAULT_CONFIG.high_risk_filter
ZERO_DTE_FILTER_CONFIG = DEFAULT_CONFIG.zero_dte_filter
