"""Fintech Flow: small, understandable personal finance tracker."""
import os
import re
import sqlite3
from datetime import date, datetime
from functools import wraps
from pathlib import Path

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("FINTECH_DATABASE", BASE_DIR / "instance" / "fintech_flow.db")).resolve()
INCOME_CATEGORIES = ["Salary", "Scholarship", "Freelance", "Business", "Other Income"]
EXPENSE_CATEGORIES = ["Food", "Transportation", "Shopping", "Entertainment", "Education", "Bills", "Healthcare", "Rent", "Travel", "Other"]

app = Flask(__name__)
app.config.update(SECRET_KEY=os.environ.get("SECRET_KEY", "dev-change-this-before-deployment"),
                  DATABASE=str(DATABASE), SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 transaction_type TEXT NOT NULL CHECK(transaction_type IN ('income','expense')), amount REAL NOT NULL CHECK(amount>0),
 category TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', transaction_date TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, transaction_date);
CREATE TABLE IF NOT EXISTS budgets (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 category TEXT NOT NULL, monthly_limit REAL NOT NULL CHECK(monthly_limit>0), month INTEGER NOT NULL, year INTEGER NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(user_id,category,month,year));
"""

def connect_db():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db

def init_db():
    db = connect_db()
    try:
        db.executescript(SCHEMA)
        db.commit()
    finally:
        db.close()

init_db()

def db():
    if "db" not in g:
        g.db = connect_db()
    return g.db

@app.teardown_appcontext
def close_db(_error=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

@app.context_processor
def globals_for_templates():
    return {"current_user": db().execute("SELECT id,name,email FROM users WHERE id=?", (session["user_id"],)).fetchone() if session.get("user_id") else None,
            "income_categories": INCOME_CATEGORIES, "expense_categories": EXPENSE_CATEGORIES,
            "today": date.today().isoformat()}

def valid_email(value):
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value or ""))

def month_bounds(year, month):
    start = f"{year:04d}-{month:02d}-01"
    end = f"{year+1:04d}-01-01" if month == 12 else f"{year:04d}-{month+1:02d}-01"
    return start, end

def user_transactions(user_id, start=None, end=None):
    sql = "SELECT * FROM transactions WHERE user_id=?"
    args = [user_id]
    if start:
        sql += " AND transaction_date>=?"; args.append(start)
    if end:
        sql += " AND transaction_date<?"; args.append(end)
    return db().execute(sql, args)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name, email = request.form.get("name", "").strip(), request.form.get("email", "").strip().lower()
        password, confirm = request.form.get("password", ""), request.form.get("confirm_password", "")
        if not name or not email or not password:
            flash("Please complete all required fields.", "danger")
        elif not valid_email(email):
            flash("Enter a valid email address.", "danger")
        elif len(password) < 8:
            flash("Use a password with at least 8 characters.", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        else:
            try:
                cur = db().execute("INSERT INTO users(name,email,password_hash) VALUES(?,?,?)", (name,email,generate_password_hash(password)))
                db().commit(); session.clear(); session["user_id"] = cur.lastrowid
                flash("Your account is ready. Welcome to Fintech Flow!", "success")
                return redirect(url_for("dashboard"))
            except sqlite3.IntegrityError:
                flash("Email already registered.", "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], request.form.get("password", "")):
            session.clear(); session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.post("/logout")
def logout():
    session.clear(); flash("You are logged out.", "info"); return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    today = date.today(); start,end = month_bounds(today.year,today.month); uid=session["user_id"]
    month_rows = user_transactions(uid,start,end).fetchall()
    income=sum(r["amount"] for r in month_rows if r["transaction_type"]=="income")
    expenses=sum(r["amount"] for r in month_rows if r["transaction_type"]=="expense")
    total_rows=user_transactions(uid).fetchall()
    cats={}
    for r in month_rows:
        if r["transaction_type"]=="expense": cats[r["category"]]=cats.get(r["category"],0)+r["amount"]
    budgets=db().execute("SELECT b.*,COALESCE((SELECT SUM(t.amount) FROM transactions t WHERE t.user_id=b.user_id AND t.category=b.category AND t.transaction_type='expense' AND t.transaction_date>=? AND t.transaction_date<?),0) spent FROM budgets b WHERE b.user_id=? AND b.month=? AND b.year=? ORDER BY b.category",(start,end,uid,today.month,today.year)).fetchall()
    budget_total=sum(b["monthly_limit"] for b in budgets); budget_spent=sum(b["spent"] for b in budgets)
    chart_months=[]; monthly_income=[]; monthly_expenses=[]; trends=[]
    for offset in range(5,-1,-1):
        y,m=today.year,(today.month-offset)
        while m<=0: m+=12; y-=1
        s,e=month_bounds(y,m); rows=user_transactions(uid,s,e).fetchall(); chart_months.append(date(y,m,1).strftime("%b"))
        monthly_income.append(round(sum(x["amount"] for x in rows if x["transaction_type"]=="income"),2))
        monthly_expenses.append(round(sum(x["amount"] for x in rows if x["transaction_type"]=="expense"),2))
        trends.append(monthly_expenses[-1])
    return render_template("dashboard.html", income=income, expenses=expenses, balance=income-expenses,
        savings_rate=(100*(income-expenses)/income if income else 0), month_label=today.strftime("%B %Y"),
        recent=db().execute("SELECT * FROM transactions WHERE user_id=? ORDER BY transaction_date DESC,id DESC LIMIT 6",(uid,)).fetchall(),
        budgets=budgets, remaining_budget=budget_total-budget_spent, category_labels=list(cats),category_values=list(cats.values()),
        chart_months=chart_months,monthly_income=monthly_income,monthly_expenses=monthly_expenses,trends=trends)

@app.route("/transactions")
@login_required
def transactions():
    filters=[session["user_id"]]; sql="SELECT * FROM transactions WHERE user_id=?"
    kind=request.args.get("type",""); category=request.args.get("category",""); search=request.args.get("q","")
    if kind in ("income","expense"): sql+=" AND transaction_type=?"; filters.append(kind)
    if category: sql+=" AND category=?"; filters.append(category)
    if search: sql+=" AND description LIKE ?"; filters.append("%"+search+"%")
    order="ASC" if request.args.get("sort")=="oldest" else "DESC"
    rows=db().execute(sql+f" ORDER BY transaction_date {order},id {order}",filters).fetchall()
    return render_template("transactions.html", transactions=rows, selected_type=kind, selected_category=category, search=search, sort=order.lower())

def parse_transaction(form):
    kind=form.get("transaction_type",""); category=form.get("category","")
    if kind not in ("income","expense") or category not in (INCOME_CATEGORIES if kind=="income" else EXPENSE_CATEGORIES): raise ValueError("Choose a valid transaction type and category.")
    amount=float(form.get("amount","0"))
    if not (amount>0 and amount<1_000_000_000): raise ValueError("Amount must be greater than zero.")
    dt=datetime.strptime(form.get("transaction_date",""),"%Y-%m-%d").date().isoformat()
    return kind,amount,category,form.get("description","").strip()[:200],dt

@app.route("/transactions/new", methods=["GET","POST"])
@login_required
def add_transaction():
    if request.method=="POST":
        try:
            values=parse_transaction(request.form); db().execute("INSERT INTO transactions(user_id,transaction_type,amount,category,description,transaction_date) VALUES(?,?,?,?,?,?)",(session["user_id"],*values)); db().commit()
            flash("Transaction saved.","success"); return redirect(url_for("transactions"))
        except (ValueError,TypeError): flash("Enter a valid amount, date, type and category.","danger")
    return render_template("transaction_form.html", transaction=None, title="Add transaction")

@app.route("/transactions/<int:transaction_id>/edit", methods=["GET","POST"])
@login_required
def edit_transaction(transaction_id):
    row=db().execute("SELECT * FROM transactions WHERE id=? AND user_id=?",(transaction_id,session["user_id"])).fetchone()
    if not row: abort(404)
    if request.method=="POST":
        try:
            values=parse_transaction(request.form); db().execute("UPDATE transactions SET transaction_type=?,amount=?,category=?,description=?,transaction_date=? WHERE id=? AND user_id=?",(*values,transaction_id,session["user_id"])); db().commit()
            flash("Transaction updated.","success"); return redirect(url_for("transactions"))
        except (ValueError,TypeError): flash("Enter a valid amount, date, type and category.","danger")
    return render_template("transaction_form.html", transaction=row,title="Edit transaction")

@app.post("/transactions/<int:transaction_id>/delete")
@login_required
def delete_transaction(transaction_id):
    db().execute("DELETE FROM transactions WHERE id=? AND user_id=?",(transaction_id,session["user_id"])); db().commit()
    flash("Transaction deleted.","info"); return redirect(url_for("transactions"))

@app.route("/budgets",methods=["GET","POST"])
@login_required
def budgets():
    today=date.today(); uid=session["user_id"]
    if request.method=="POST":
        category=request.form.get("category","")
        try:
            limit=float(request.form.get("monthly_limit","0"))
            if category not in EXPENSE_CATEGORIES or limit<=0: raise ValueError()
            db().execute("INSERT INTO budgets(user_id,category,monthly_limit,month,year) VALUES(?,?,?,?,?) ON CONFLICT(user_id,category,month,year) DO UPDATE SET monthly_limit=excluded.monthly_limit",(uid,category,limit,today.month,today.year)); db().commit()
            flash("Monthly budget saved.","success"); return redirect(url_for("budgets"))
        except (ValueError,TypeError): flash("Choose a category and enter a positive limit.","danger")
    start,end=month_bounds(today.year,today.month)
    rows=db().execute("SELECT b.*,COALESCE((SELECT SUM(t.amount) FROM transactions t WHERE t.user_id=b.user_id AND t.category=b.category AND t.transaction_type='expense' AND t.transaction_date>=? AND t.transaction_date<?),0) spent FROM budgets b WHERE b.user_id=? AND b.month=? AND b.year=? ORDER BY b.category",(start,end,uid,today.month,today.year)).fetchall()
    return render_template("budgets.html",budgets=rows,month_label=today.strftime("%B %Y"))

@app.post("/budgets/<int:budget_id>/delete")
@login_required
def delete_budget(budget_id):
    db().execute("DELETE FROM budgets WHERE id=? AND user_id=?",(budget_id,session["user_id"])); db().commit(); flash("Budget removed.","info"); return redirect(url_for("budgets"))

@app.route("/analytics")
@login_required
def analytics():
    today=date.today(); uid=session["user_id"]; rows=user_transactions(uid).fetchall()
    expenses=[r for r in rows if r["transaction_type"]=="expense"]; incomes=[r for r in rows if r["transaction_type"]=="income"]
    totals={}
    for r in expenses: totals[r["category"]]=totals.get(r["category"],0)+r["amount"]
    monthly={}
    for r in expenses: monthly[r["transaction_date"][:7]]=monthly.get(r["transaction_date"][:7],0)+r["amount"]
    mstart,mend=month_bounds(today.year,today.month); current=[r for r in rows if mstart<=r["transaction_date"]<mend]
    inc=sum(r["amount"] for r in current if r["transaction_type"]=="income"); exp=sum(r["amount"] for r in current if r["transaction_type"]=="expense")
    b_rows=db().execute("SELECT b.*,COALESCE((SELECT SUM(t.amount) FROM transactions t WHERE t.user_id=b.user_id AND t.category=b.category AND t.transaction_type='expense' AND t.transaction_date>=? AND t.transaction_date<?),0) spent FROM budgets b WHERE b.user_id=? AND b.month=? AND b.year=?",(mstart,mend,uid,today.month,today.year)).fetchall()
    budget_usage=(100*sum(b["spent"] for b in b_rows)/sum(b["monthly_limit"] for b in b_rows)) if b_rows and sum(b["monthly_limit"] for b in b_rows)>0 else 0
    savings_rate=100*(inc-exp)/inc if inc else 0
    score=max(0,min(100,round(max(0,min(savings_rate,40))*1.5 + max(0,40-min(budget_usage,140))*.5)))
    months=sorted(monthly)[-12:]; amounts=[round(monthly[x],2) for x in months]
    return render_template("analytics.html",total_spending=sum(r["amount"] for r in expenses),average_monthly=(sum(monthly.values())/max(1,len(monthly))),highest_category=max(totals,key=totals.get) if totals else "—",highest_expense=max(expenses,key=lambda x:x["amount"])["amount"] if expenses else 0,savings_rate=savings_rate,score=score,budget_usage=budget_usage,category_labels=list(totals),category_values=list(totals.values()),trend_labels=months,trend_values=amounts,month_label=today.strftime("%B %Y"),insights=totals,expenses=expenses)

@app.route("/profile",methods=["GET","POST"])
@login_required
def profile():
    uid=session["user_id"]; user=db().execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()
    if request.method=="POST":
        name=request.form.get("name","").strip(); password=request.form.get("password","")
        if not name: flash("Name is required.","danger")
        elif password and len(password)<8: flash("New password must contain at least 8 characters.","danger")
        else:
            if password: db().execute("UPDATE users SET name=?,password_hash=? WHERE id=?",(name,generate_password_hash(password),uid))
            else: db().execute("UPDATE users SET name=? WHERE id=?",(name,uid))
            db().commit(); flash("Profile updated.","success"); return redirect(url_for("profile"))
    return render_template("profile.html",user=user)

@app.post("/demo-data")
@login_required
def load_demo_data():
    uid=session["user_id"]; exists=db().execute("SELECT 1 FROM transactions WHERE user_id=? LIMIT 1",(uid,)).fetchone()
    if exists: flash("Demo data can only be loaded into an empty account.","warning"); return redirect(url_for("dashboard"))
    today=date.today(); samples=[("income",40000,"Salary","Monthly salary"),("income",5000,"Freelance","Design project"),("expense",4500,"Food","Groceries and meals"),("expense",2000,"Transportation","Metro and bus"),("expense",3500,"Shopping","Clothing"),("expense",2500,"Education","Course materials"),("expense",1800,"Entertainment","Movies and outings"),("expense",2200,"Bills","Phone and internet"),("expense",1200,"Healthcare","Pharmacy"),("expense",900,"Food","Cafe"),("expense",750,"Transportation","Auto rides"),("expense",1100,"Shopping","Household items"),("expense",600,"Entertainment","Streaming"),("expense",1400,"Education","Books"),("expense",950,"Food","Dinner"),("expense",800,"Travel","Weekend trip"),("expense",500,"Bills","Utilities"),("expense",1300,"Food","Dining out"),("expense",450,"Transportation","Bus pass"),("expense",700,"Other","Personal care")]
    for i,(kind,amt,cat,desc) in enumerate(samples):
        d=(today.replace(day=1)).toordinal()-i*2; day=date.fromordinal(max(date(today.year,today.month,1).toordinal(),d))
        db().execute("INSERT INTO transactions(user_id,transaction_type,amount,category,description,transaction_date) VALUES(?,?,?,?,?,?)",(uid,kind,amt,cat,desc,day.isoformat()))
    for category,limit in [("Food",5000),("Transportation",2500),("Shopping",3000),("Entertainment",2000),("Education",3500)]:
        db().execute("INSERT INTO budgets(user_id,category,monthly_limit,month,year) VALUES(?,?,?,?,?) ON CONFLICT(user_id,category,month,year) DO NOTHING",(uid,category,limit,today.month,today.year))
    db().commit(); flash("Demo dataset loaded: 20 realistic transactions and 5 budgets.","success"); return redirect(url_for("dashboard"))

@app.errorhandler(404)
def not_found(_error): return render_template("error.html",code=404,message="We couldn't find that page."),404

@app.errorhandler(500)
def server_error(_error):
    db().rollback() if g.get("db") else None
    return render_template("error.html",code=500,message="Something went wrong. Please try again."),500

if __name__=="__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG")=="1",port=int(os.environ.get("PORT",5000)))
