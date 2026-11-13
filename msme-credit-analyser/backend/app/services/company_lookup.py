"""Curated public-company lookup profiles used when live regulated sources are unavailable.

The records mirror the shape of publicly disclosed listed-company information. They are
explicitly labelled snapshots so the credit workflow never represents them as live bureau,
banking, GST, or MCA data.
"""
from typing import Any

COMPANIES: list[dict[str, Any]] = [
    {"id":"apex-precision","company_name":"Apex Precision Manufacturing","industry":"Manufacturing","business_age":12,"location":"Pune, Maharashtra","employees":85,"ownership_type":"Private Limited","business_type":"B2B","revenue":42000000,"ebitda":7200000,"net_profit":3900000,"total_assets":35000000,"current_assets":15000000,"current_liabilities":7200000,"total_liabilities":14000000,"net_worth":21000000,"existing_debt":7500000,"annual_interest_expense":700000,"cash_balance":4200000,"accounts_receivable":3100000,"inventory":3500000,"accounts_payable":1900000,"existing_loans":7500000,"monthly_emi":120000,"previous_defaults":0,"credit_history_years":10,"active_loans":1,"credit_utilization":0.28,"payment_history":0.99,"avg_monthly_balance":2500000,"monthly_inflows":3900000,"monthly_outflows":3200000,"bounced_payments":0,"banking_relationship_years":9,"listed":False},
    {"id":"reliance-industries","company_name":"Reliance Industries Limited","industry":"Diversified Energy & Retail","business_age":52,"location":"Mumbai, Maharashtra","employees":389000,"ownership_type":"Public Limited","business_type":"Diversified","revenue":1000000000000,"ebitda":175000000000,"net_profit":79000000000,"total_assets":1700000000000,"current_assets":370000000000,"current_liabilities":330000000000,"total_liabilities":920000000000,"net_worth":780000000000,"existing_debt":340000000000,"annual_interest_expense":23000000000,"cash_balance":145000000000,"accounts_receivable":78000000000,"inventory":115000000000,"accounts_payable":92000000000,"listed":True,"symbol":"RELIANCE"},
    {"id":"tata-motors","company_name":"Tata Motors Limited","industry":"Automobile Manufacturing","business_age":80,"location":"Mumbai, Maharashtra","employees":95000,"ownership_type":"Public Limited","business_type":"B2C / B2B","revenue":440000000000,"ebitda":62000000000,"net_profit":28000000000,"total_assets":540000000000,"current_assets":135000000000,"current_liabilities":120000000000,"total_liabilities":330000000000,"net_worth":210000000000,"existing_debt":175000000000,"annual_interest_expense":17000000000,"cash_balance":41000000000,"accounts_receivable":46000000000,"inventory":52000000000,"accounts_payable":39000000000,"listed":True,"symbol":"TATAMOTORS"},
    {"id":"infosys","company_name":"Infosys Limited","industry":"IT Services","business_age":44,"location":"Bengaluru, Karnataka","employees":317000,"ownership_type":"Public Limited","business_type":"B2B","revenue":165000000000,"ebitda":39000000000,"net_profit":26500000000,"total_assets":160000000000,"current_assets":92000000000,"current_liabilities":42000000000,"total_liabilities":53000000000,"net_worth":107000000000,"existing_debt":6000000000,"annual_interest_expense":400000000,"cash_balance":39000000000,"accounts_receivable":31000000000,"inventory":1000000000,"accounts_payable":14000000000,"listed":True,"symbol":"INFY"},
    {"id":"itc","company_name":"ITC Limited","industry":"FMCG","business_age":115,"location":"Kolkata, West Bengal","employees":24000,"ownership_type":"Public Limited","business_type":"B2C","revenue":70000000000,"ebitda":25000000000,"net_profit":19000000000,"total_assets":98000000000,"current_assets":29000000000,"current_liabilities":21000000000,"total_liabilities":29000000000,"net_worth":69000000000,"existing_debt":2000000000,"annual_interest_expense":120000000,"cash_balance":15000000000,"accounts_receivable":7000000000,"inventory":10000000000,"accounts_payable":8000000000,"listed":True,"symbol":"ITC"},
]

PUBLIC_NOTE = "Curated public-company demonstration profile based on the kind of information found in listed-company disclosures. Verify live values from MCA/NSE/BSE filings before using in any real decision. Private banking, credit-bureau and GST data are not fetched."

def search_companies(query: str) -> list[dict[str, Any]]:
    query = query.strip().lower()
    if not query: return []
    return [{key: item.get(key) for key in ("id", "company_name", "industry", "location", "listed", "symbol")} for item in COMPANIES if query in item["company_name"].lower() or query in item["industry"].lower()][:8]

def get_company(company_id: str) -> dict[str, Any] | None:
    for company in COMPANIES:
        if company["id"] == company_id:
            result = dict(company)
            result["source"] = "Public-company profile catalogue"
            result["source_note"] = PUBLIC_NOTE
            return result
    return None

