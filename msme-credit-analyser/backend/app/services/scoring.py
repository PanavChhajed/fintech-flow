from typing import Any
from .financial import ratios

def score_result(x: dict[str, Any], probability: float, contributions: list[dict[str, Any]]) -> dict[str, Any]:
    rs = ratios(x)
    healthy = sum(1 for item in rs.values() if item['healthy'])
    # Project-specific transparent overlay on ML probability; no official lending standard.
    score = max(0, min(100, round(100*(1-probability)*0.78 + healthy/13*12 + x['payment_history']*7 - x['previous_defaults']*3 - x['bounced_payments']*1.5)))
    category = "Low" if score >= 61 else "Medium" if score >= 31 else "High"
    decision = "APPROVE" if category == "Low" else "MANUAL REVIEW" if category == "Medium" else "REJECT / HIGH-RISK REVIEW"
    dscr = rs['DSCR']['value']; icr=rs['Interest Coverage']['value']
    capacity = max(0, (x['ebitda'] - x['annual_interest_expense'] - x['monthly_emi']*12) * 2)
    max_exposure = max(0, min(x['revenue']*.25, capacity*max(0.3, min(1.5, dscr))))
    recommended = max(0, round((max_exposure-x['existing_debt']) * (score/100), -3))
    positives = [c for c in contributions if c['impact'] < 0][:4]
    risks = [c for c in contributions if c['impact'] > 0][:4]
    return {"credit_score":score,"default_probability":round(probability,4),"risk_category":category,"decision":decision,"recommended_credit_limit":recommended,"maximum_suggested_exposure":round(max_exposure,-3),"estimated_repayment_capacity":round(capacity,-3),"ratios":rs,"positive_factors":positives,"risk_factors":risks,"methodology":"Project-specific analytical framework combining trained ML default probability, financial resilience, and repayment signals; not an official banking formula.","limit_reason":f"Based on surplus EBITDA, DSCR {dscr:.2f}, interest coverage {icr:.2f}, existing debt, revenue and project risk score."}

