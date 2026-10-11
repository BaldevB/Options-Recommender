    # Sector Filter
    sector_options = [
        "All AI Leaders (40+ Tickers)",
        "AI NeoClouds & GPU Compute",
        "AI Optical Interconnect & Photonics",
        "AI Memory & Storage (HBM)",
        "AI Chips & Semiconductors",
        "AI Hyperscalers & Big Tech",
        "AI Enterprise Software & Cyber",
        "AI Hardware & Data Center Infra",
        "Mega-Cap Tech (Mag 7)",
        "Market & Sector ETFs",
    ]
    chosen_sector = st.sidebar.selectbox("Target Sector", sector_options)

    # Minimum Confidence Filter
    min_conf_pct = st.sidebar.slider(
        "Minimum Confidence Score (%)",
        min_value=25,
        max_value=70,
        value=35,
        step=5,
        help="Filters out weak or unconfirmed setups. 35%+ requires strong alignment."
    )

    direction_filter = st.sidebar.selectbox(
        "Direction Filter",
        ["All Directions", "Bullish Only (Calls / Bull Spreads)", "Bearish Only (Puts / Bear Spreads)"]
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🛡️ **Position Sizing Calculator**")
    account_equity = st.sidebar.number_input("Account Equity ($)", min_value=1000.0, value=10000.0, step=1000.0)
    risk_pct = st.sidebar.slider("Max Risk per Trade (%)", min_value=0.25, max_value=3.0, value=1.0, step=0.25) / 100.0

    # Build Config
    cfg = AppConfig()
    cfg.risk.account_equity = float(account_equity)
    cfg.risk.max_risk_pct = float(risk_pct)

    # Resolve Universe
    if chosen_sector == "All AI Leaders (40+ Tickers)":
        tickers_to_scan = AI_STOCKS_UNIVERSE
    elif chosen_sector == "AI NeoClouds & GPU Compute":
        tickers_to_scan = AI_STOCKS_CATEGORIES["AI NeoClouds & GPU Compute"]
    elif chosen_sector == "AI Optical Interconnect & Photonics":
        tickers_to_scan = AI_STOCKS_CATEGORIES["AI Optical Interconnect & Photonics"]
    elif chosen_sector == "AI Memory & Storage (HBM)":
        tickers_to_scan = AI_STOCKS_CATEGORIES["AI Memory & Storage (HBM)"]
    elif chosen_sector == "AI Chips & Semiconductors":
        tickers_to_scan = AI_STOCKS_CATEGORIES["AI Chips & Semiconductors"]
    elif chosen_sector == "AI Hyperscalers & Big Tech":
        tickers_to_scan = AI_STOCKS_CATEGORIES["AI Hyperscalers & Platforms"]
    elif chosen_sector == "AI Enterprise Software & Cyber":
        tickers_to_scan = AI_STOCKS_CATEGORIES["AI Enterprise Software & Cyber"]
    elif chosen_sector == "AI Hardware & Data Center Infra":
        tickers_to_scan = AI_STOCKS_CATEGORIES["AI Hardware & Data Center Infra"]
    elif chosen_sector == "Mega-Cap Tech (Mag 7)":
        tickers_to_scan = WATCHLIST_CATEGORIES["Mega-Cap Tech (Mag 7)"]
    elif chosen_sector == "Market & Sector ETFs":
        tickers_to_scan = WATCHLIST_CATEGORIES["Market & Sector ETFs"]
    else:
        tickers_to_scan = AI_STOCKS_UNIVERSE
