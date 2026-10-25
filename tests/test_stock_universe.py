import pytest
from data.stock_universe import (
    STOCK_SECTORS,
    STOCK_UNIVERSE,
    get_stock_universe,
    get_stock_metadata,
)


def test_stock_universe_contains_over_1000_stocks():
    universe = get_stock_universe()
    assert len(universe) >= 1000, f"Expected at least 1000 stocks, got {len(universe)}"
    assert len(STOCK_UNIVERSE) >= 1000


def test_stock_universe_item_structure():
    universe = get_stock_universe()
    required_keys = {"symbol", "name", "sector", "market_cap_tier"}
    for item in universe:
        assert required_keys.issubset(item.keys()), f"Item missing keys: {item}"
        assert isinstance(item["symbol"], str) and len(item["symbol"]) > 0
        assert isinstance(item["name"], str) and len(item["name"]) > 0
        assert isinstance(item["sector"], str) and len(item["sector"]) > 0
        assert isinstance(item["market_cap_tier"], str) and len(item["market_cap_tier"]) > 0


def test_stock_universe_no_duplicates():
    universe = get_stock_universe()
    symbols = [item["symbol"].upper() for item in universe]
    unique_symbols = set(symbols)
    assert len(symbols) == len(unique_symbols), (
        f"Duplicate symbols found: {len(symbols) - len(unique_symbols)} duplicates"
    )


def test_stock_universe_sector_filtering():
    tech_stocks = get_stock_universe("technology")
    assert len(tech_stocks) > 0, "Expected non-empty list for technology sector"
    for stock in tech_stocks:
        assert stock["sector"].lower() == "technology"

    # Verify filtering with different case
    tech_stocks_upper = get_stock_universe("Technology")
    assert len(tech_stocks_upper) == len(tech_stocks)

    # Verify all sectors in STOCK_SECTORS have coverage
    for sector_key in STOCK_SECTORS.keys():
        sector_stocks = get_stock_universe(sector_key)
        assert len(sector_stocks) > 0, f"Expected stocks for sector '{sector_key}'"


def test_get_stock_metadata_found():
    nvda = get_stock_metadata("NVDA")
    assert nvda is not None
    assert nvda["symbol"] == "NVDA"
    assert "NVIDIA" in nvda["name"]
    assert nvda["sector"] == "technology"
    assert nvda["market_cap_tier"] == "mega"

    # Case insensitivity test
    nvda_lower = get_stock_metadata("nvda")
    assert nvda_lower is not None
    assert nvda_lower["symbol"] == "NVDA"


def test_get_stock_metadata_not_found():
    result = get_stock_metadata("UNKNOWN")
    assert result is None

    result_empty = get_stock_metadata("")
    assert result_empty is None


def test_package_level_exports():
    import data
    assert hasattr(data, "STOCK_SECTORS")
    assert hasattr(data, "STOCK_UNIVERSE")
    assert hasattr(data, "get_stock_universe")
    assert hasattr(data, "get_stock_metadata")
