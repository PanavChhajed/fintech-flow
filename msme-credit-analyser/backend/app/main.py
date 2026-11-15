from pathlib import Path
from io import BytesIO
import csv, json
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from .database import Base, engine, SessionLocal
from .models import MSME, Assessment, User
from .schemas import ApplicationInput, LoginInput
from .services.predictor import predict, metadata
from .services.scoring import score_result
from .services.auth import hash_password, verify_password, create_token, get_user_id, revoke_token
from .services.company_lookup import search_companies, get_company, catalogue_status

ROOT=Path(__file__).resolve().parents[2]
app=FastAPI(title='AI-Based MSME Credit Analyser',version='1.0.0')
app.mount('/static',StaticFiles(directory=ROOT/'backend/app/static'),name='static')
def db():
    s=SessionLocal()
    try: yield s
    finally: s.close()
@app.on_event('startup')
def startup():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        if not session.query(User).filter_by(email='analyst@credlens.in').first():
            session.add(User(full_name='Priya Sharma', email='analyst@credlens.in', password_hash=hash_password('CredLens@2026'), role='Senior Credit Analyst'))
            session.commit()
    finally:
        session.close()
@app.get('/')
def home(): return FileResponse(ROOT/'backend/app/static/index.html')
@app.get('/api/health')
def health(): return {'status':'ok','model_ready':bool(metadata())}
def current_user(authorization: str | None = Header(default=None), session: Session = Depends(db)) -> User:
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Please sign in to access CreditLens.')
    user_id = get_user_id(authorization.removeprefix('Bearer ').strip())
    user = session.get(User, user_id) if user_id else None
    if not user: raise HTTPException(status_code=401, detail='Your session has expired. Please sign in again.')
    return user
@app.post('/api/auth/login')
def login(payload: LoginInput, session: Session = Depends(db)):
    user = session.query(User).filter_by(email=payload.email.lower().strip()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail='Incorrect email or password.')
    return {'access_token': create_token(user.id), 'user': {'name': user.full_name, 'email': user.email, 'role': user.role}}
@app.post('/api/auth/logout')
def logout(authorization: str | None = Header(default=None)):
    if authorization and authorization.startswith('Bearer '): revoke_token(authorization.removeprefix('Bearer ').strip())
    return {'status': 'signed out'}
@app.get('/api/auth/me')
def me(user: User = Depends(current_user)):
    return {'name': user.full_name, 'email': user.email, 'role': user.role}
def run(payload: ApplicationInput, session: Session):
    x=payload.model_dump(); p,contrib=predict(x); result=score_result(x,p,contrib)
    msme=session.query(MSME).filter_by(company_name=x['company_name']).first()
    if not msme:
        msme=MSME(company_name=x['company_name'],industry=x['industry'],business_age=x['business_age'],location=x['location'],employees=x['employees'],ownership_type=x['ownership_type'],business_type=x['business_type']); session.add(msme); session.flush()
    a=Assessment(msme_id=msme.id,payload=x,result=result); session.add(a); session.commit(); session.refresh(a)
    return {'assessment_id':a.id,'company':x['company_name'],'created_at':a.created_at.isoformat(),**result}
@app.post('/api/analyze')
def analyze(payload: ApplicationInput, session: Session=Depends(db), user: User=Depends(current_user)): return run(payload,session)
@app.get('/api/assessment/{assessment_id}')
def assessment(assessment_id:int,session:Session=Depends(db), user: User=Depends(current_user)):
    a=session.get(Assessment,assessment_id)
    if not a: raise HTTPException(404,'Assessment not found')
    return {'assessment_id':a.id,'company':a.msme.company_name,'input':a.payload,**a.result,'created_at':a.created_at.isoformat()}
@app.get('/api/msme')
def list_msme(session:Session=Depends(db), user: User=Depends(current_user)):
    return [{'id':m.id,'company_name':m.company_name,'industry':m.industry,'assessments':len(m.assessments)} for m in session.query(MSME).all()]
@app.get('/api/dashboard')
def dashboard(session:Session=Depends(db), user: User=Depends(current_user)):
    rows=session.query(Assessment).order_by(Assessment.created_at.desc()).all(); results=[a.result for a in rows]
    cats={k:sum(r['risk_category']==k for r in results) for k in ['Low','Medium','High']}
    return {'total_applications':len(rows),'risk_distribution':cats,'average_credit_score':round(sum(r['credit_score'] for r in results)/len(rows),1) if rows else 0,'average_default_probability':round(sum(r['default_probability'] for r in results)/len(rows),3) if rows else 0,'recent':[{'id':a.id,'company':a.msme.company_name,'industry':a.msme.industry,'score':a.result['credit_score'],'risk':a.result['risk_category'],'probability':a.result['default_probability']} for a in rows[:12]]}
@app.get('/api/model-info')
def model_info(user: User=Depends(current_user)): return metadata()
@app.get('/api/demo-cases')
def demos(user: User=Depends(current_user)):
    p=ROOT/'data/sample/demo_cases.json'; return json.loads(p.read_text()) if p.exists() else []
@app.get('/api/company-search')
def company_search(q: str = '', refresh: bool = False, user: User = Depends(current_user)):
    """Search the NSE-listed equity universe by company name or symbol."""
    return {"results": search_companies(q, refresh=refresh), **catalogue_status()}
@app.get('/api/company-profile/{company_id}')
def company_profile(company_id: str, user: User = Depends(current_user)):
    company = get_company(company_id)
    if not company: raise HTTPException(404, 'Company profile not found.')
    return company
@app.get('/api/sample-csv')
def sample_csv(user: User=Depends(current_user)):
    return FileResponse(ROOT/'data/sample/msme_upload_template.csv', media_type='text/csv', filename='msme_upload_template.csv')
@app.post('/api/upload-csv')
async def upload_csv(file:UploadFile=File(...),session:Session=Depends(db),user: User=Depends(current_user)):
    if not file.filename.lower().endswith('.csv'): raise HTTPException(400,'Upload a CSV file.')
    content=(await file.read()).decode('utf-8-sig'); rows=list(csv.DictReader(content.splitlines()))
    if not rows: raise HTTPException(400,'CSV has no records.')
    accepted=[]; errors=[]
    for idx,row in enumerate(rows,2):
        try:
            for k,v in list(row.items()):
                if k not in ['company_name','industry','location','ownership_type','business_type'] and v not in ['',None]: row[k]=float(v)
            accepted.append(run(ApplicationInput(**row),session))
        except Exception as e: errors.append({'row':idx,'error':str(e)})
    return {'processed':len(accepted),'results':accepted,'errors':errors}
@app.get('/api/assessment/{assessment_id}/report.pdf')
def report(assessment_id:int,session:Session=Depends(db),user: User=Depends(current_user)):
    a=session.get(Assessment,assessment_id)
    if not a: raise HTTPException(404,'Assessment not found')
    buf=BytesIO(); c=canvas.Canvas(buf,pagesize=A4); w,h=A4; r=a.result; x=a.payload
    c.setFillColor(HexColor('#092b4c')); c.rect(0,h-90,w,90,fill=1,stroke=0); c.setFillColor(HexColor('#ffffff')); c.setFont('Helvetica-Bold',21); c.drawString(42,h-50,'MSME CREDIT ASSESSMENT'); c.setFont('Helvetica',10); c.drawString(42,h-70,'AI-assisted decision-support prototype | Project-specific analysis')
    y=h-125; c.setFillColor(HexColor('#152238')); c.setFont('Helvetica-Bold',16); c.drawString(42,y,x['company_name']); y-=25; c.setFont('Helvetica',11)
    for label,val in [('Industry',x['industry']),('Credit score',f"{r['credit_score']}/100"),('Default probability',f"{r['default_probability']:.1%}"),('Risk category',r['risk_category']),('Recommendation',r['decision']),('Recommended limit',f"INR {r['recommended_credit_limit']:,.0f}")]: c.drawString(42,y,f'{label}: {val}'); y-=18
    y-=8; c.setFont('Helvetica-Bold',13); c.drawString(42,y,'Financial health ratios'); y-=18; c.setFont('Helvetica',9)
    for name,item in r['ratios'].items():
        c.drawString(48,y,f"{name}: {item['value']:.3f} — {item['interpretation']}"); y-=14
        if y<100: c.showPage(); y=h-60
    y-=5;c.setFont('Helvetica-Bold',13);c.drawString(42,y,'Model-derived risk factors');y-=18;c.setFont('Helvetica',9)
    for f in r['risk_factors']: c.drawString(48,y,f"• {f['feature']}: {f['detail']}"); y-=14
    y-=5;c.setFont('Helvetica-Bold',10);c.drawString(42,y,'Disclaimer: This AI-assisted prototype is not a substitute for professional underwriting or regulatory assessment.')
    c.save();buf.seek(0);return StreamingResponse(buf,media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename=assessment_{a.id}.pdf'})

