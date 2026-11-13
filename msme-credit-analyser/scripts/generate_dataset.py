"""Generate documented, statistically correlated synthetic MSME credit data."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'data/raw/synthetic_msme_credit.csv'
rng=np.random.default_rng(42); N=600
industries=np.array(['Manufacturing','Retail','Wholesale','Logistics','Food Processing','Textiles','IT Services','Construction','Healthcare','Other Services'])
rows=[]
for i in range(N):
    industry=str(rng.choice(industries)); revenue=float(np.exp(rng.normal(np.log(1.8e7),.9)))
    age=float(np.clip(rng.gamma(3,2),.5,30)); margin=float(np.clip(rng.normal(.11,.09),-.2,.35)); ebitda=revenue*max(margin+.04,-.08)
    profit=revenue*margin; leverage=float(np.clip(rng.lognormal(-.05,.65),.08,6)); assets=revenue*rng.uniform(.5,1.8); worth=max(assets/(1+leverage),revenue*.03); debt=worth*leverage
    ca=assets*rng.uniform(.3,.7); cl=ca/rng.uniform(.55,2.6); interest=debt*rng.uniform(.07,.16); defaults=int(rng.choice([0,1,2],[1],p=[.86,.11,.03])[0]); payment=float(np.clip(rng.normal(.95-defaults*.16,.07),.15,1)); bounced=int(max(0,rng.poisson(.3+defaults*2)))
    util=float(np.clip(rng.normal(.45+leverage*.08+defaults*.12,.18),0,1)); emi=debt*rng.uniform(.005,.018)
    risk_logit=-2.6+1.0*leverage-2.8*margin-1.1*(ca/cl)+2.2*defaults+2.3*(1-payment)+.45*bounced+.8*util-.08*age
    default=int(rng.random() < 1/(1+np.exp(-risk_logit)))
    rows.append(dict(company_name=f'{industry} Enterprise {i+1:03d}',industry=industry,business_age=age,revenue=revenue,ebitda=ebitda,net_profit=profit,total_assets=assets,current_assets=ca,current_liabilities=cl,total_liabilities=assets-worth,net_worth=worth,existing_debt=debt,annual_interest_expense=interest,cash_balance=ca*rng.uniform(.08,.4),inventory=ca*rng.uniform(.02,.28),monthly_emi=emi,previous_defaults=defaults,credit_history_years=max(.2,age-rng.uniform(0,2)),active_loans=int(rng.integers(0,5)),credit_utilization=util,payment_history=payment,avg_monthly_balance=ca*rng.uniform(.03,.16),monthly_inflows=revenue/12*rng.uniform(.7,1.2),monthly_outflows=revenue/12*rng.uniform(.6,1.1),bounced_payments=bounced,banking_relationship_years=min(age,rng.uniform(.3,age)),default=default))
OUT.parent.mkdir(parents=True,exist_ok=True); pd.DataFrame(rows).to_csv(OUT,index=False); print(f'Created {OUT} ({N} synthetic records)')
if __name__=='__main__': pass

