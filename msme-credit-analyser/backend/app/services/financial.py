from typing import Any

def div(a: float, b: float) -> float:
    return round(a / b, 3) if b else 0.0

def ratios(x: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cur = div(x['current_assets'], x['current_liabilities'])
    quick = div(x['current_assets'] - x['inventory'], x['current_liabilities'])
    de = div(x['existing_debt'], x['net_worth'])
    da = div(x['total_liabilities'], x['total_assets'])
    icr = div(x['ebitda'], x['annual_interest_expense'])
    npm = div(x['net_profit'], x['revenue'])
    em = div(x['ebitda'], x['revenue'])
    roa = div(x['net_profit'], x['total_assets'])
    roe = div(x['net_profit'], x['net_worth'])
    wc = x['current_assets'] - x['current_liabilities']
    ato = div(x['revenue'], x['total_assets'])
    dscr = div(x['ebitda'], x['annual_interest_expense'] + x['monthly_emi'] * 12)
    ctd = div(x['cash_balance'], x['existing_debt'])
    items = {"Current Ratio":(cur, cur>=1.2, "liquidity"), "Quick Ratio":(quick, quick>=0.8, "liquidity"), "Debt to Equity":(de, de<=1.5, "leverage"), "Debt to Assets":(da, da<=0.65, "leverage"), "Interest Coverage":(icr, icr>=2, "coverage"), "Net Profit Margin":(npm, npm>=0.05, "profitability"), "EBITDA Margin":(em, em>=0.1, "profitability"), "ROA":(roa, roa>=0.03, "profitability"), "ROE":(roe, roe>=0.08, "profitability"), "Working Capital":(wc, wc>=0, "liquidity"), "Asset Turnover":(ato, ato>=0.6, "efficiency"), "DSCR":(dscr, dscr>=1.2, "coverage"), "Cash to Debt":(ctd, ctd>=0.15, "liquidity")}
    return {k:{"value":v, "healthy":ok, "interpretation":("Healthy" if ok else "Concerning")+f" {kind}; industry benchmarks vary."} for k,(v,ok,kind) in items.items()}

