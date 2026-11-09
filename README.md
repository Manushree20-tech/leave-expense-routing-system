Leave and Expense Routing System

A full-scale Flask and MySQL application for managing employee leave requests, expense claims, approval workflows, reimbursements, and operational analytics.

The project implements a synthetic enterprise dataset and demonstrates policy-based routing, approval decisions, validation, and reporting.

1. Project Overview

The Leave and Expense Routing System is designed to streamline employee leave and expense management through a centralized application.

It supports:

- Employee leave requests and leave balance tracking.
- Expense claims with multiple line items.
- Policy-based approval routing.
- Manager and finance approval workflows.
- Reimbursement tracking.
- Operations analytics and reporting.
- Exception and audit-history pages.

2. Dataset Overview

The project includes a full-scale synthetic dataset.

Dataset| Records
Employees| 400
Leave policies| 6
Leave requests| 800
Expense claims| 1,000
Expense line items| 5,498
Reimbursements| 575
Approval steps| 1,789
Cost centres| 2
Budget periods| 2
Holidays| 7
Employee-policy associations| 1,440
Approval rules| 22

The dataset is synthetic and intended for development, demonstration, and evaluation.

The generator uses a fixed seed to support reproducibility. Ground-truth anomaly labels are maintained separately from the ordinary feature datasets.

3. Technology Stack

- Backend: Python, Flask
- Database: MySQL 8+
- ORM: SQLAlchemy
- Frontend: HTML, CSS, Jinja2
- Database tool: MySQL Workbench
- Version control: Git and GitHub

4. Application Roles

The system supports the following roles:

1. Business Requester
2. Approver
3. Process Owner
4. Operations Analyst
5. System Administrator

Access and available actions depend on the employee's assigned role.

5. Application Features

Leave Management

- Submit employee leave requests.
- Select applicable leave policies.
- Calculate business days.
- Check leave balances.
- Check overlapping leave requests.
- Route requests for approval.
- Update leave balances after approval.

Expense Management

- Submit expense claims.
- Add multiple expense line items.
- Calculate claim totals.
- Store receipt metadata and SHA-256 hashes.
- Check duplicate receipts.
- Apply expense policy checks.
- Check cost-centre budgets.
- Route claims according to approval rules.

Approval Management

- Assign approval steps.
- Support sequential approval workflows.
- Prevent requester self-approval.
- Track approved and rejected claims.
- Create reimbursement records after final approval.

Reimbursement Management

- Track reimbursement records.
- Display reimbursement status.
- Monitor reimbursement amounts.

Payment execution is not automated. Approved claims create reimbursement records with a pending-payment status.

Operations Analytics

The analytics dashboard displays:

- Total employees.
- Total leave requests.
- Total expense claims.
- Approved and rejected claims.
- Expense approval rate.
- Reimbursement count and value.
- Recorded exceptions.
- Audit-event count.

6. Project Structure

Leave_Expense_Routing_System/
│
├── app/
│   ├── templates/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── seed.py
│   └── services.py
│
├── database/
│   └── schema.sql
│
├── docs/
│   ├── ACCEPTANCE_MATRIX.md
│   ├── DATA_DICTIONARY.md
│   ├── ERD_AND_SCHEMA.md
│   └── SOURCE_MANIFEST.md
│
├── exports/
│   ├── generated/
│   └── reproducibility_report.json
│
├── generator/
│   └── generate_data.py
│
├── validation/
│   └── validate_exports.py
│
├── tools/
│   └── verify_reproducibility.py
│
├── .env.example
├── .gitignore
├── requirements.txt
├── run.py
└── README.md

Additional project files may be present in the repository.

7. Requirements

- Python 3.10 or later
- MySQL 8 or later
- MySQL Workbench (recommended)
- Git
- A web browser

8. Installation and Setup

Step 1: Clone the repository

git clone https://github.com/Manushree20-tech/leave-expense-routing-system.git
cd leave-expense-routing-system

Step 2: Create a virtual environment

py -m venv .venv

Activate it:

.\.venv\Scripts\Activate.ps1

Step 3: Install dependencies

python -m pip install -r requirements.txt

Step 4: Configure environment variables

Copy the example environment file:

Copy-Item .env.example .env

Open ".env" and configure your own secret key and MySQL connection.

Example:

SECRET_KEY=replace-with-your-own-secret-key
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/leave_expense_full_dataset?charset=utf8mb4

Replace "YOUR_PASSWORD" with your own MySQL password.

Do not upload ".env" to GitHub.

9. MySQL Database Setup

1. Open MySQL Workbench.
2. Connect to your local MySQL server.
3. Open "database/schema.sql".
4. Ensure the database name in the SQL file matches the database configured in ".env" ("leave_expense_full_dataset" in this example).
5. Execute the schema script.
6. Load the generated full dataset from "exports/generated/seed_data.sql", if provided.
7. Verify the imported records using the SQL queries below.

Important: Use a separate database for this full dataset. Do not overwrite an existing application database.

Verify database records

USE leave_expense_full_dataset;

SELECT COUNT(*) AS total_employees
FROM employee;

SELECT COUNT(*) AS total_leave_requests
FROM leave_request;

SELECT COUNT(*) AS total_expense_claims
FROM expense_claim;

SELECT COUNT(*) AS total_expense_lines
FROM expense_line;

SELECT COUNT(*) AS total_reimbursements
FROM reimbursement;

SELECT COUNT(*) AS total_approval_steps
FROM approval_step;

Expected primary dataset counts:

- Employees: 400
- Leave requests: 800
- Expense claims: 1,000

The other counts should be compared with the dataset overview above.

10. Generate and Validate Synthetic Data

The project includes a deterministic data generator.

To generate the full dataset:

python generator/generate_data.py --seed 20261022 --employees 400 --leave-requests 800 --expense-claims 1000 --out exports/generated

Validate the generated exports:

python validation/validate_exports.py exports/generated

Verify reproducibility:

python tools/verify_reproducibility.py --seed 20261022 --employees 400 --leave-requests 800 --expense-claims 1000

Run automated tests:

python -m pytest

The generated exports include CSV and JSON data, ground-truth labels, and reproducibility information.

11. Run the Application

After configuring the database and environment:

python run.py

Open the application in your browser:

http://127.0.0.1:5000

The application runs locally on the machine where it is started.

12. Demo Login

This training application uses email-based demo actor selection rather than password authentication.

The following employee accounts were verified in the full synthetic employee dataset:

Employee ID| Demo email| Role
EMP-000001| employee001@example.test| Process Owner
EMP-000002| employee002@example.test| System Administrator
EMP-000003| employee003@example.test| Operations Analyst
EMP-000004| employee004@example.test| Business Requester

Other approver accounts should be selected from the employee records and their assigned roles.

Example query:

SELECT id, name, email, role
FROM employee
ORDER BY id;

Use the email address of an employee with the required role on the sign-in page.

Security note: These are demonstration accounts, not production authentication credentials.

13. Workflow

The main application workflow is:

1. Employee submits a leave request or expense claim.
2. The application checks applicable policies and balances.
3. The system determines the required approval route.
4. Assigned approvers review the request.
5. The request is approved or rejected.
6. Reimbursement records are created after final expense approval.
7. Operations metrics display available workflow information.

14. Testing and Verification

The full dataset was loaded into the separate MySQL database and checked using MySQL Workbench.

The following primary counts were verified:

Check| Verified result
Employees| 400
Leave requests| 800
Expense claims| 1,000

The browser application was also opened successfully.

The following application pages were checked:

- Sign-in
- Requester dashboard
- Operations analytics
- Recorded exceptions
- Audit history

Known verification limitation: At the time of the latest browser check, the Exceptions page displayed zero recorded exceptions and the Audit History page displayed zero events. These records and their integration require further verification before claiming complete exception and audit-event coverage.

15. Scope and Limitations

- The project is a development and demonstration implementation, not a production deployment.
- Demo sign-in does not provide production-grade password authentication.
- Receipt uploads use local application storage.
- Do not use real confidential employee or receipt information in the demonstration.
- Reimbursements are recorded, but payment execution is not automated.
- Ground-truth anomaly labels are separate from ordinary operational data.
- Exception and audit-event coverage should be evaluated against "docs/ACCEPTANCE_MATRIX.md".

16. Security

- Never commit ".env".
- Never publish database passwords or secret keys.
- Use ".env.example" as the configuration template.
- Do not upload confidential employee information.
- Use synthetic data for public demonstrations.

17. GitHub Repository

Repository:

https://github.com/Manushree20-tech/leave-expense-routing-system

The repository contains the application source, database schema, generated dataset exports, and project documentation.

18. Author

Manushree H P

Leave and Expense Routing System