"""Listed-company search backed by NSE's public equity master list."""
from __future__ import annotations
import csv, hashlib, io, time
from typing import Any
from urllib.request import Request, urlopen

NSE_EQUITY_MASTER_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
CACHE_TTL_SECONDS = 24 * 60 * 60
MAX_RESULTS = 20
FALLBACK_COMPANIES = [
    {"symbol": "RELIANCE", "company_name": "Reliance Industries Limited", "series": "EQ", "isin": "INE002A01018"},
    {"symbol": "TATAMOTORS", "company_name": "Tata Motors Limited", "series": "EQ", "isin": "INE155A01022"},
    {"symbol": "INFY", "company_name": "Infosys Limited", "series": "EQ", "isin": "INE009A01021"},
    {"symbol": "ITC", "company_name": "ITC Limited", "series": "EQ", "isin": "INE154A01025"},
]
_catalogue: list[dict[str, str]] | None = None
_catalogue_loaded_at = 0.0
_catalogue_source = "NSE equity master list"
_catalogue_error: str | None = None
PUBLIC_NOTE = "Listing identity was sourced from the NSE equity master list. The remaining assessment fields are a synthetic ideal borrower profile generated for the classroom demo, not actual company financials, banking records, GST data or credit-bureau information."

def _ideal_demo_profile(symbol: str) -> dict[str, Any]:
    """Create stable, optimistic synthetic inputs for a selected NSE company."""
    seed = int(hashlib.sha256(symbol.encode("utf-8")).hexdigest()[:8], 16)
    revenue = 150_000_000 + (seed % 851) * 1_000_000
    ebitda = round(revenue * (0.15 + ((seed >> 8) % 6) / 100), 2)
    net_profit = round(revenue * (0.08 + ((seed >> 12) % 5) / 100), 2)
    total_assets = round(revenue * (1.0 + ((seed >> 16) % 31) / 100), 2)
    current_assets = round(revenue * (0.36 + ((seed >> 20) % 10) / 100), 2)
    current_liabilities = round(current_assets / (1.65 + ((seed >> 24) % 25) / 100), 2)
    net_worth = round(total_assets * (0.56 + ((seed >> 4) % 12) / 100), 2)
    existing_debt = round(total_assets * (0.18 + ((seed >> 10) % 10) / 100), 2)
    interest = round(existing_debt * (0.075 + ((seed >> 14) % 20) / 1000), 2)
    cash_balance = round(current_assets * (0.22 + ((seed >> 18) % 10) / 100), 2)
    monthly_inflows = round(revenue / 12 * 0.95, 2)
    return {"business_age": 8 + (seed % 18), "employees": 80 + ((seed >> 5) % 420), "revenue": revenue, "ebitda": ebitda, "net_profit": net_profit, "total_assets": total_assets, "current_assets": current_assets, "current_liabilities": current_liabilities, "total_liabilities": round(total_assets - net_worth, 2), "net_worth": net_worth, "existing_debt": existing_debt, "annual_interest_expense": interest, "cash_balance": cash_balance, "accounts_receivable": round(revenue * 0.10, 2), "inventory": round(revenue * 0.08, 2), "accounts_payable": round(revenue * 0.065, 2), "existing_loans": existing_debt, "monthly_emi": round(ebitda * 0.025, 2), "previous_defaults": 0, "credit_history_years": 7 + (seed % 10), "active_loans": 1 + ((seed >> 9) % 2), "credit_utilization": round(0.22 + ((seed >> 13) % 16) / 100, 2), "payment_history": round(0.97 + ((seed >> 17) % 3) / 100, 2), "avg_monthly_balance": round(cash_balance * 0.56, 2), "monthly_inflows": monthly_inflows, "monthly_outflows": round(monthly_inflows * 0.76, 2), "bounced_payments": 0, "banking_relationship_years": 6 + (seed % 8)}

def _normalise(row: dict[str, str]) -> dict[str, str] | None:
    row = {str(key).strip(): (value or "") for key, value in row.items()}
    symbol, name = row.get("SYMBOL", "").strip().upper(), row.get("NAME OF COMPANY", "").strip()
    series, isin = row.get("SERIES", "").strip().upper(), row.get("ISIN NUMBER", "").strip().upper()
    if not symbol or not name or series in {"", "SM", "ST"}: return None
    return {"symbol": symbol, "company_name": name, "series": series, "isin": isin}

def _download_catalogue() -> list[dict[str, str]]:
    request = Request(NSE_EQUITY_MASTER_URL, headers={"User-Agent": "CredLens academic project contact: local-demo", "Accept": "text/csv,*/*;q=0.8"})
    with urlopen(request, timeout=12) as response: payload = response.read().decode("utf-8-sig")
    records = [item for row in csv.DictReader(io.StringIO(payload)) if (item := _normalise(row))]
    if len(records) < 100: raise ValueError("NSE equity master list returned too few usable records")
    return sorted(records, key=lambda item: (item["company_name"].casefold(), item["symbol"]))

def _load_catalogue(force_refresh: bool = False) -> list[dict[str, str]]:
    global _catalogue, _catalogue_loaded_at, _catalogue_source, _catalogue_error
    if _catalogue is not None and time.time() - _catalogue_loaded_at < CACHE_TTL_SECONDS and not force_refresh: return _catalogue
    try:
        _catalogue, _catalogue_loaded_at = _download_catalogue(), time.time()
        _catalogue_source, _catalogue_error = "NSE equity master list", None
    except Exception as error:
        if _catalogue is None: _catalogue = FALLBACK_COMPANIES.copy()
        _catalogue_source, _catalogue_error = "Offline fallback catalogue", type(error).__name__
    return _catalogue

def catalogue_status() -> dict[str, Any]:
    records = _load_catalogue()
    return {"source": _catalogue_source, "count": len(records), "updated_at": int(_catalogue_loaded_at) if _catalogue_loaded_at else None, "degraded": _catalogue_source != "NSE equity master list", "error": _catalogue_error}

def search_companies(query: str, refresh: bool = False) -> list[dict[str, Any]]:
    query = query.strip().casefold()
    if len(query) < 2: return []
    tokens, matches = [token for token in query.split() if token], []
    for item in _load_catalogue(force_refresh=refresh):
        if all(token in f"{item['company_name']} {item['symbol']}".casefold() for token in tokens):
            matches.append({"id": f"nse:{item['symbol']}", "company_name": item["company_name"], "symbol": item["symbol"], "series": item["series"], "isin": item["isin"], "industry": "Listed company", "location": "India", "listed": True})
            if len(matches) >= MAX_RESULTS: break
    return matches

def get_company(company_id: str) -> dict[str, Any] | None:
    if not company_id.startswith("nse:"): return None
    symbol = company_id.removeprefix("nse:").strip().upper()
    for item in _load_catalogue():
        if item["symbol"] == symbol:
            profile = {"id": f"nse:{item['symbol']}", "company_name": item["company_name"], "industry": "Listed company", "location": "India", "ownership_type": "Public Limited", "business_type": "Listed company", "listed": True, "symbol": item["symbol"], "series": item["series"], "isin": item["isin"], "source": _catalogue_source, "source_note": PUBLIC_NOTE, "demo_profile": True}
            profile.update(_ideal_demo_profile(symbol))
            return profile
    return None

