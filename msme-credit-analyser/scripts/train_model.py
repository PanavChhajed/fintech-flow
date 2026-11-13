"""Train and select an actual supervised default-risk pipeline from synthetic data."""
from pathlib import Path
import json, sys
import joblib, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'backend'))
from app.services.financial import ratios
DATA=ROOT/'data/raw/synthetic_msme_credit.csv'; MODEL=ROOT/'models/credit_risk_pipeline.joblib'; META=ROOT/'models/model_metadata.json'
def enrich(df):
    rows=[]
    for _,r in df.iterrows():
        z=r.to_dict(); q=ratios(z); z.update({'current_ratio':q['Current Ratio']['value'],'debt_to_equity':q['Debt to Equity']['value'],'interest_coverage':q['Interest Coverage']['value'],'dscr':q['DSCR']['value'],'net_profit_margin':q['Net Profit Margin']['value']}); rows.append(z)
    return pd.DataFrame(rows)
def main():
    if not DATA.exists():
        import subprocess; subprocess.run([sys.executable,str(ROOT/'scripts/generate_dataset.py')],check=True)
    df=enrich(pd.read_csv(DATA)); y=df.pop('default'); X=df.drop(columns=['company_name'],errors='ignore')
    train,test=train_test_split(range(len(X)),test_size=.25,random_state=42,stratify=y)
    cats=['industry']; nums=[c for c in X.columns if c not in cats]
    prep=ColumnTransformer([('num',Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler())]),nums),('cat',OneHotEncoder(handle_unknown='ignore'),cats)])
    candidates={'Logistic Regression':LogisticRegression(max_iter=1500,class_weight='balanced'),'Random Forest':RandomForestClassifier(n_estimators=300,max_depth=10,min_samples_leaf=3,class_weight='balanced',random_state=42,n_jobs=-1)}
    scored={}
    for n,m in candidates.items():
        p=Pipeline([('prep',prep),('model',m)]); p.fit(X.iloc[train],y.iloc[train]); pred=p.predict(X.iloc[test]); prob=p.predict_proba(X.iloc[test])[:,1]
        scored[n]=(p,{'accuracy':accuracy_score(y.iloc[test],pred),'precision':precision_score(y.iloc[test],pred,zero_division=0),'recall':recall_score(y.iloc[test],pred,zero_division=0),'f1':f1_score(y.iloc[test],pred,zero_division=0),'roc_auc':roc_auc_score(y.iloc[test],prob),'pr_auc':average_precision_score(y.iloc[test],prob),'confusion_matrix':confusion_matrix(y.iloc[test],pred).tolist()})
    name=max(scored,key=lambda n:scored[n][1]['roc_auc']); pipe,metrics=scored[name]; pipe.fit(X,y); MODEL.parent.mkdir(exist_ok=True); joblib.dump({'pipeline':pipe,'features':list(X.columns),'numeric_features':nums},MODEL)
    # permutation-like source model importances, where available
    model=pipe.named_steps['model']; importances=getattr(model,'feature_importances_',None)
    META.write_text(json.dumps({'model_name':name,'dataset':'Synthetic statistically correlated MSME dataset (not real-world bureau data)','dataset_size':len(df),'features':len(X.columns),'metrics':metrics,'comparison':{k:v[1] for k,v in scored.items()},'training_date':pd.Timestamp.utcnow().isoformat(),'false_negative_note':'Recall is emphasized because missing a likely default can create material lender losses.'},indent=2))
    print(f'Trained {name}; ROC-AUC={metrics["roc_auc"]:.3f}')
if __name__=='__main__': main()

