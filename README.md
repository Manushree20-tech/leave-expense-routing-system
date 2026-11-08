# Leave and Expense Routing System
A Flask + SQLAlchemy solution for the supplied leave/expense routing problem statement.

## Requirements
- Python 3.10+
- MySQL 8+ (optional; SQLite is the default for a quick first run)
- MySQL Workbench (optional GUI for database inspection)

## Quick start (Windows PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# MySQL configuration
Open the .env file and update DATABASE_URL
with your own MySQL username and password.
Create the leave_expense_routing database
and execute database/schema.sql in MySQL Workbench.
python run.py
```
Open http://127.0.0.1:5000. Demo users (no password authentication in this training build; email selects the seeded actor):
- mira@example.test — business requester
- ravi@example.test — approver
- asha@example.test — process owner
- nina@example.test — India finance approver\n- liam@example.test — US finance approver
- omar@example.test — operations analyst
- admin@example.test — system administrator

## MySQL Workbench setup
1. In MySQL Workbench, open and execute `database/schema.sql` (it creates `leave_expense_routing` and all relational tables).
2. Copy `.env.example` to `.env`.
3. Set `DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/leave_expense_routing?charset=utf8mb4`.
4. For the small demo, start the app and it seeds reference actors/policies automatically.
5. To load the full synthetic dataset instead, execute `exports/generated/seed_data.sql` after `database/schema.sql` and before starting the app. The app detects existing employees and skips demo seeding.
Never commit `.env`; do not share database passwords.

## Generate and validate synthetic data
```powershell
python generator/generate_data.py --seed 20261022 --employees 400 --leave-requests 800 --expense-claims 1000 --out exports/generated
python validation/validate_exports.py exports/generated
python tools/verify_reproducibility.py --seed 20261022 --employees 400 --leave-requests 800 --expense-claims 1000
python -m pytest
```
The supplied ZIP already contains the full-size generated exports and validation/reproducibility evidence. `ground_truth.csv/json` contain the labelled anomaly cases separately from the feature tables.
The generator writes CSV and JSON tables, separate ground-truth labels, a validation summary and SHA-256 source manifest. Adjust volume arguments for starter-scale runs.

## Core workflows
- Leave: policy selection, current-year monthly accrual, holiday-aware business-day calculation, balance and overlap checks, manager routing and balance deduction after approval.
- Expense: 1–10 line items, derived claim total, private receipt upload and SHA-256 metadata, duplicate receipt check, per-item/claim/receipt policy checks, cost-center budget reservations, split-claim screening, and amount/category/country/manager routing.
- Approvals: sequential assigned-approver decisions; requester self-approval is blocked; reimbursement is created only after final approval.
- Traceability: append-only state events record request, approval, reimbursement and exception transitions.
- Operations metrics: counts and approval/reimbursement/event measures.

## Scope and limitations to verify
This is a working starter implementation of the supplied specification, not a claim of production deployment readiness. Expense receipt files are uploaded to the local static/uploads directory and SHA-256 hashes are stored; never use real sensitive receipts in the demo. Payment execution is not automated: reimbursement records are created in PENDING_PAYMENT after final approval. Synthetic anomaly records are separately labelled in ground truth and should not be loaded as ordinary operational data. Review `docs/ACCEPTANCE_MATRIX.md` before treating it as final.
