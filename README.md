# Fintech Flow

**Track. Analyze. Improve.** Fintech Flow is a practical, student-level personal finance web application. It helps a user record income and expenses, organize them by category, plan monthly budgets, and review patterns from their own data.

## Problem and objectives

Personal spending is easy to lose track of when records are scattered. Fintech Flow provides one simple place to record activity and answer questions such as “How much did I spend this month?” and “Which category uses the most?” It is an educational project, not a bank or financial advice product.

## Features

- Account registration, login and logout using hashed passwords and Flask sessions.
- Personal dashboard with current-month income, expenses, balance, savings rate, charts and recent activity.
- Add, edit, delete, search and filter transactions.
- Monthly category budgets, progress indicators, and over-limit warnings.
- Analytics based on stored transactions and a clearly labeled educational health indicator.
- Optional 20-transaction sample dataset and five budgets for an empty account.
- Responsive layout for desktop and mobile.

## Technology and architecture

- Python 3.10+, Flask, SQLite, Werkzeug password hashing.
- HTML templates, Bootstrap 5, custom CSS, vanilla JavaScript and Chart.js.
- Browser → Flask routes and session → parameterized SQLite queries → Jinja templates and Chart.js.

SQLite is stored at `instance/fintech_flow.db` by default. Override it with `FINTECH_DATABASE` when necessary. On startup, `init_db()` creates the database and tables if missing. Every transaction and budget lookup is scoped to the signed-in user's ID.

## Database schema

- `users`: id, name, unique email, password hash, creation timestamp.
- `transactions`: id, user ID, type, positive amount, category, description, transaction date, creation timestamp.
- `budgets`: id, user ID, category, monthly limit, month, year, creation timestamp; one row per user/category/month/year.

Foreign keys cascade on account deletion. Transaction types are `income` or `expense`; category choices are validated by the application.

## Run locally

1. Install Python 3.10 or newer.
2. In this folder, create and activate a virtual environment: `python -m venv .venv` followed by `.venv\Scripts\activate` on Windows or `source .venv/bin/activate` on macOS/Linux.
3. Install dependencies: `pip install -r requirements.txt`.
4. Set a private random `SECRET_KEY` environment variable before deployment. For a local demo, the development fallback is used.
5. Start with `python app.py` and visit `http://127.0.0.1:5000`.
6. Register an account. On an empty account, use **Load demo data** if desired.

## Tests

Run `python -m unittest discover -s tests -v`. The suite covers registration and password hashing, duplicate registration, login/logout, transaction CRUD, budgets, analytics, demo data, access control and user isolation. Tests use temporary databases.

## Deploy

`wsgi.py` exposes `app` and `Procfile` is provided for Gunicorn-based hosts. For PythonAnywhere, create a Manual Configuration Flask web app, upload/extract this project under `/home/<username>/fintech-flow`, create a virtual environment, and install the dependencies from `requirements.txt`. In the PythonAnywhere WSGI configuration file, use:

```python
import os
import sys

project_path = "/home/<username>/fintech-flow"
if project_path not in sys.path:
    sys.path.insert(0, project_path)

os.environ["SECRET_KEY"] = "replace-with-a-long-random-secret"
os.environ["FINTECH_DATABASE"] = project_path + "/instance/fintech_flow.db"

from app import app as application
```

Replace `<username>` and use a long random secret that you keep private. Set the PythonAnywhere web app's virtualenv path to the environment where you installed the dependencies, then reload it. PythonAnywhere's WSGI configuration is what serves the public site; `python app.py` is only for local development. Their official [Flask setup guide](https://help.pythonanywhere.com/pages/Flask/) has the current dashboard steps.

No hosting account or deployment credentials were available in this workspace, so a public deployment could not be created from here. Do not use the development secret in a public deployment. A hosted app should use HTTPS and a private secret.

## Authentication and calculations

Passwords are hashed with Werkzeug `generate_password_hash`; login verifies with `check_password_hash`. The user ID is held in a signed Flask session. Route queries include that ID, and edit/delete operations verify ownership.

- Balance = current-month income − current-month expenses.
- Savings = income − expenses; savings rate = savings ÷ income × 100 (0 when income is zero).
- Category totals = sum of expense amounts for that category.
- Monthly spending average = mean of calendar months containing recorded expenses.
- Budget usage = expenses in the budget category this month ÷ that category's monthly limit × 100.
- Health indicator (0–100) combines a capped savings-rate contribution and budget-usage contribution. The score is educational, transparent and not professional financial advice.

## Project layout

```text
app.py                 Flask routes, validation, schema and calculations
wsgi.py                WSGI entry point
requirements.txt       Python dependency list
Procfile               Gunicorn process declaration
templates/             Jinja pages
static/css/style.css   Responsive visual system
static/js/dashboard.js Chart.js setup and category picker
tests/test_app.py      Automated application tests
instance/              Persistent SQLite database (created at startup)
README.md              Setup and feature guide
PROJECT_DOCUMENTATION.md College PBL report
```

## Limitations and future scope

This project does not connect to banks, move money, or provide financial advice. It is a single-currency manual tracker; no CSRF extension, password reset, email verification, or multi-currency support is included. Future work could add CSV export, date-range filters, CSRF protection, password reset, and deployment-specific backup procedures.

## Screenshots

Add screenshots of the landing page, dashboard, budgets and analytics here after launching the app.
