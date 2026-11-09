# Full Synthetic Dataset Setup Guide

## Leave and Expense Routing System

This guide explains the difference between the small demonstration
environment and the full synthetic dataset included with this project.
It also explains how a reviewer can prepare a separate MySQL environment
on their own computer.

## 1. What has been implemented and demonstrated

The project includes a Flask-based Leave and Expense Routing System with
leave requests, expense claims, approval routing, reimbursement-status
tracking, and audit/event history.

The main workflows were manually demonstrated using a small MySQL demo
dataset containing **8 employees**. The demonstrated checks included:

-   Submitting and approving a leave request.
-   Verifying the leave-balance update after approval.
-   Submitting and approving an expense claim.
-   Creating a reimbursement-tracking record after approval.
-   Viewing recorded workflow/audit events.

These manual demonstrations confirm the basic workflow in the small demo
environment. They do **not** mean that every workflow has been manually
tested against all 400 synthetic employees or all generated
transactions.

## 2. Full synthetic dataset included in the project

The project also includes a larger, deterministic synthetic dataset for
reviewers who want to inspect or test the system with more records. The
data is fictional and is not actual employee or company information.

The supplied validation summary reports these counts:

  Dataset entity                             Expected records
  ---------------------------------------- ------------------
  Employees                                               400
  Leave policies                                            6
  Leave balances                                        1,440
  Leave requests                                          800
  Expense policies                                         10
  Cost centres                                              2
  Budget periods                                            2
  Employee-policy associations                          1,440
  Approval rules                                           22
  Holidays                                                  7
  Expense claims                                        1,000
  Expense lines                                         5,498
  Reimbursements                                          575
  Approval steps                                        1,790
  Separately labelled ground-truth cases                   10

The generator baseline uses fixed seed `20261022`. The ground-truth
labels are stored separately from the ordinary generated data so they
are not accidentally treated as normal input records.

## 3. Where the dataset files are located

In the project repository, the generated files are under:

``` text
exports/
└── generated/
    ├── seed_data.sql
    ├── validation_summary.json
    ├── validation_report.json
    ├── ground_truth.csv
    ├── ground_truth.json
    └── [generated CSV and JSON table files]
```

The relational table definitions are under:

``` text
database/schema.sql
```

The SQL seed export is the bulk-data script. The schema file defines the
tables and relationships into which the data is intended to be loaded.

## 4. Important database safety note

The full synthetic dataset should be kept separate from the small demo
database.

For a local full-data setup, use a new database name such as:

``` sql
CREATE DATABASE leave_expense_full_dataset
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

Do not drop, overwrite, or reuse an existing database that contains the
working demo or other data.

**Before importing the supplied SQL files, review and correct the schema
for the new database name.** In the packaged `database/schema.sql`, the
database creation/use statements currently name `leave_expense_routing`,
and the `expense_line` table definition contains a duplicate
`issue_type` column declaration. Those items must be corrected in a
working copy of the schema before execution. Do not run the uncorrected
schema against an existing database.

The seed SQL and schema should be checked together for table names,
column names, data types, primary keys, foreign keys, and insert order.
The original files should be preserved; make corrections in a separate
working copy and document any changes.

## 5. Suggested setup process for a reviewer

The following is the intended high-level process for a reviewer using
their own computer:

1.  Download or clone the repository.
2.  Install Python and MySQL 8 or a compatible MySQL version.
3.  Open MySQL Workbench or a MySQL client.
4.  Create a **new, separate** database named
    `leave_expense_full_dataset`.
5.  Make a working copy of `database/schema.sql`.
6.  In that working copy, change the database name to
    `leave_expense_full_dataset` and remove the duplicate `issue_type`
    declaration from the `expense_line` table. Review the complete
    schema for any other errors before executing it.
7.  Execute the corrected schema in the new database.
8.  Review `exports/generated/seed_data.sql` against the corrected
    schema. Import it only after confirming that every insert matches
    the target table and column definitions.
9.  Configure a local `.env` file with the reviewer's own database
    connection details. Do not publish `.env` or passwords to GitHub.
10. Run the validation/count queries in the next section.

The exact application connection and full-dataset application behaviour
must be tested after the import. A successful SQL import by itself does
not prove that every application page, workflow, or approval route works
with the full dataset.

## 6. Verify the imported record counts

After a successful import, run count queries in the new database. For
example:

``` sql
USE leave_expense_full_dataset;

SELECT COUNT(*) AS employees FROM employee;
SELECT COUNT(*) AS leave_policies FROM leave_policy;
SELECT COUNT(*) AS leave_balances FROM leave_balance;
SELECT COUNT(*) AS leave_requests FROM leave_request;
SELECT COUNT(*) AS expense_policies FROM expense_policy;
SELECT COUNT(*) AS cost_centers FROM cost_center;
SELECT COUNT(*) AS budget_periods FROM budget_period;
SELECT COUNT(*) AS employee_policies FROM employee_policy;
SELECT COUNT(*) AS approval_rules FROM approval_rule;
SELECT COUNT(*) AS holidays FROM holiday;
SELECT COUNT(*) AS expense_claims FROM expense_claim;
SELECT COUNT(*) AS expense_lines FROM expense_line;
SELECT COUNT(*) AS reimbursements FROM reimbursement;
SELECT COUNT(*) AS approval_steps FROM approval_step;
```

Compare the results with the expected counts in Section 2 and
`exports/generated/validation_summary.json`.

The 10 ground-truth cases are maintained in separate CSV/JSON files;
they are not necessarily a relational table in the operational schema.
Review those files separately.

If any count differs, stop and investigate before treating the import as
successful. Also check for SQL errors, missing foreign-key references,
duplicate primary keys, and inconsistent claim totals.

## 7. What a reviewer can conclude

-   The project has a small demo environment with 8 employees, and the
    core leave and expense workflows described above were manually
    demonstrated there.
-   The repository also supplies a full synthetic export with 400
    employees and related leave, expense, policy, budget, approval, and
    reimbursement records.
-   A reviewer can prepare a separate MySQL database on their own
    computer and inspect or test the larger dataset after resolving the
    schema issues and validating the import.
-   The full dataset should not be described as already imported into
    the demo database.
-   The full dataset should not be described as fully end-to-end tested
    in the application until the application has been configured for
    that database and the relevant workflows and record counts have been
    tested.

## 8. Privacy and repository safety

All generated employee and transaction records are synthetic. Do not
replace them with real employee, payroll, banking, receipt, or other
confidential information when sharing the project.

Never commit:

-   `.env` files
-   Database passwords
-   API keys or access tokens
-   Private keys
-   Real employee or financial records
-   Sensitive receipt images or documents

Use `.env.example` as a template and enter local credentials only in the
reviewer's own `.env` file.

## 9. Summary

The project demonstrates its main leave and expense workflows with an
8-employee demo dataset and separately provides a larger synthetic
dataset representing 400 employees, 800 leave requests, and 1,000
expense claims, together with related records. Reviewers can use the
supplied exports to set up a separate full-data MySQL environment on
their own computers. The full-data import and application-level testing
must be completed and verified separately; they are not claimed as
already completed by the 8-employee demonstration.
