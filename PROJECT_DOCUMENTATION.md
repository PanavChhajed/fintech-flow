# FINTECH FLOW — Personal Finance Management & Analytics Platform

## 1. Title

Fintech Flow: Personal Finance Management & Analytics Platform

## 2. Abstract

Fintech Flow is a web-based application for recording personal income and expenses. It organizes transactions into categories, supports monthly spending limits, and presents summaries and charts from the user's saved records. The system uses Flask and SQLite to remain understandable and deployable as an engineering college project. It does not connect to financial institutions or make financial decisions for the user.

## 3. Introduction

Students and individuals may find it difficult to understand their monthly spending when transactions are not recorded consistently. A lightweight tracker can make spending visible and provide a basis for budgeting. Fintech Flow gives each account a private ledger and derives basic totals and trends from it.

## 4. Problem Statement

Manual notes and scattered records do not provide a convenient way to summarize income, expenses, category totals, or budget usage. The project addresses this problem with a small authenticated web application and a relational database.

## 5. Objectives

- Provide account registration and session-based login.
- Record, categorize, edit, filter and delete income and expenses.
- Summarize monthly income, expenses, balance and savings rate.
- Let users define monthly limits by expense category.
- Visualize actual stored data and keep each user's records private.

## 6. Existing System

The baseline alternatives considered are manual notebooks or generic spreadsheet entries. These can record amounts but require users to calculate summaries and maintain category consistency themselves. This project demonstrates those common calculations in a small web interface; it does not claim that all existing finance products lack these features.

## 7. Proposed System

The proposed application offers a responsive browser interface, Flask route handlers, server-side validation and SQLite persistence. A signed session identifies the logged-in account. Each data query is scoped to that account. Chart.js renders category and monthly summaries generated from database values.

## 8. Functional Requirements

1. A visitor can register using a unique, valid email and confirmed password.
2. A registered user can log in and log out.
3. A user can create, edit, list, filter and delete their transactions.
4. A user can create or update a category budget for the current month and remove it.
5. The dashboard and analytics page summarize saved activity.
6. A user can update their name and password.
7. An empty account can load clearly identified demonstration data.

## 9. Non-Functional Requirements

- Usability: forms and summaries use concise labels and responsive layouts.
- Security: hashed passwords, parameterized SQL, login-required routes and ownership checks.
- Reliability: startup initializes missing database tables and SQLite foreign keys are enabled.
- Maintainability: the code uses a single Flask module and a small relational schema.
- Portability: standard Python dependencies and SQLite support local and basic hosted use.

## 10. Technology Stack

Python, Flask, Werkzeug, SQLite, Jinja2, HTML5, CSS3, Bootstrap 5, JavaScript and Chart.js.

## 11. System Architecture

The client sends HTTP requests to Flask routes. Authentication and validation occur on the server. Routes use parameterized SQL through Python's SQLite driver. Jinja renders page responses, while JSON data attributes initialize Chart.js in the browser. The SQLite file persists the account and transaction records.

## 12. Database Design

`users(id, name, email, password_hash, created_at)` stores account identity. `transactions(id, user_id, transaction_type, amount, category, description, transaction_date, created_at)` stores ledger entries. `budgets(id, user_id, category, monthly_limit, month, year, created_at)` stores category plans. User foreign keys cascade on delete. Budget rows are unique by user, category, month and year.

## 13. ER Diagram Description

One user can own many transactions and many budgets. Each transaction and budget references exactly one user through `user_id`. The relationship is one-to-many from `users` to both dependent tables.

## 14. Module Description

- Authentication: registration validation, password hashing, login verification and logout.
- Dashboard: current-month totals, recent entries, charts and budget progress.
- Transactions: create, update, delete, filter and search operations.
- Budgets: current-month category limits with spending and usage feedback.
- Analytics: recorded expense category totals, monthly values and a transparent educational score.
- Profile: update display name and password.
- Demo data: insert twenty sample transactions and five budgets into an empty account.

## 15. Implementation

The `app.py` module initializes schema with `CREATE TABLE IF NOT EXISTS`, configures an absolute default database path based on the project directory, and defines routes. User input is validated server-side and SQL values are bound as parameters. The template layer uses Bootstrap and custom styles. Chart datasets are derived in Flask and passed to Chart.js through template-generated JSON.

## 16. Analytics Methodology

Monthly income and expenses are sums of matching transaction amounts in the current calendar month. Balance and savings are income minus expense; savings rate divides savings by income when income is nonzero. Category totals sum expense records per category. Average monthly spending averages months in which expenses exist. Budget utilization divides matching current-month category expenses by the monthly limit. The 0–100 educational indicator uses capped savings-rate and budget-usage contributions; it does not estimate emergency savings or predict outcomes.

## 17. Testing

The standard-library `unittest` suite creates a temporary SQLite file per test. It exercises registration, password hashing, duplicate email rejection, login/logout, transaction create/update/delete, budget creation, analytics output, demo records, unauthenticated routes and cross-account isolation. Run with `python -m unittest discover -s tests -v`.

## 18. Results

The implemented application provides a working manual ledger, personalized summaries, monthly budgets and data-derived charts. The demo dataset supports a repeatable classroom walkthrough. Automated tests cover the primary route and isolation behavior. Hosted availability depends on completing a deployment with a hosting account.

## 19. Limitations

The application is not a banking system and does not import statements, initiate payments, or provide financial advice. It records one currency, requires manual entry, and does not include email verification, password recovery, or production CSRF middleware. The free hosting setup and persistent storage must be configured by the deployer.

## 20. Future Scope

Possible improvements include date-range analytics, CSV export, optional CSRF protection, password reset, account deletion, scheduled database backups and deployment-specific monitoring.

## 21. Conclusion

Fintech Flow demonstrates how a small full-stack application can store personal finance entries and turn them into useful summaries. Its scope and calculations are intentionally simple enough to explain and extend in a college project viva.
