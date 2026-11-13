from pathlib import Path
import json, joblib, pandas as pd
from .financial import ratios

ROOT=Path(__file__).resolve().parents[3]; MODEL_PATH=ROOT/'models/credit_risk_pipeline.joblib'; META_PATH=ROOT/'models/model_metadata.json'
DISPLAY={'debt_to_equity':'Debt-to-equity','interest_coverage':'Interest coverage','dscr':'Debt service coverage','current_ratio':'Current ratio','net_profit_margin':'Net profit margin','payment_history':'Payment history','previous_defaults':'Previous defaults','bounced_payments':'Bounced payments','credit_utilization':'Credit utilization','business_age':'Business age'}
def build_features(x):
    z=dict(x); q=ratios(z); z.update({'current_ratio':q['Current Ratio']['value'],'debt_to_equity':q['Debt to Equity']['value'],'interest_coverage':q['Interest Coverage']['value'],'dscr':q['DSCR']['value'],'net_profit_margin':q['Net Profit Margin']['value']}); return z
def predict(x):
    if not MODEL_PATH.exists(): raise FileNotFoundError('ML model missing. Run: python scripts/train_model.py')
    obj=joblib.load(MODEL_PATH); z=build_features(x); frame=pd.DataFrame([z])[obj['features']]
    frame[obj['numeric_features']] = frame[obj['numeric_features']].astype(float)
    prob=float(obj['pipeline'].predict_proba(frame)[0,1])
    # Actual model-feature based local directional contribution: perturb inputs and observe model probability.
    factors=[]
    for f in DISPLAY:
        if f not in frame.columns: continue
        altered=frame.copy(); val=float(altered.at[0,f])
        if f in ['payment_history','current_ratio','interest_coverage','dscr','net_profit_margin','business_age']: altered.at[0,f]=val*.7
        else: altered.at[0,f]=val*1.3+.01
        impact=prob-float(obj['pipeline'].predict_proba(altered)[0,1]); factors.append({'feature':DISPLAY[f],'impact':round(impact,4),'detail':f'Model sensitivity contribution: {impact:+.1%} default-risk change when stress-tested.'})
    return prob, sorted(factors,key=lambda a:abs(a['impact']),reverse=True)
def metadata(): return json.loads(META_PATH.read_text()) if META_PATH.exists() else {}

