# Acceptance matrix against the supplied problem statement

| Requirement | Implementation | Evidence / test |
|---|---|---|
| Five named actors | `Employee.role` demo actors: requester, process owner, approver, operations analyst, administrator | Seed data and employee table |
| Eleven core entities | `app/models.py` | SQLAlchemy models and MySQL DDL |
| PK/FK, cardinality, optional relationships, effective dates | Core and supporting models | `ERD_AND_SCHEMA.md`, `schema.sql` |
| Employee hierarchy | `Employee.manager_id` self-reference | Seeded hierarchy |
| Leave accrual and balance | `accrue_leave()` | Dashboard balance and approval deduction |
| Weekend/holiday-aware leave days | `business_days()` + `Holiday` | `tests/test_core.py` |
| Leave date/balance/overlap checks | Leave submission route | Request validation and exception event |
| 1–10 expense lines | Expense form and backend | Dynamic 10-row form; backend count validation |
| Receipt metadata and content hash | Private upload storage + `ExpenseLine` | SHA-256; duplicate content check |
| Expense policy limits and budgets | `ExpensePolicy`, `CostCenter`, `BudgetPeriod` | Per-line, per-claim, receipt and budget checks |
| Routing by amount/category/country/manager | Effective-dated `ApprovalRule` | Country/category manager rules and amount-based finance rules |
| Sequential approvals and self-approval prevention | `ApprovalStep`, `decide_step()` | Assigned approver and prior-step checks |
| Reimbursement after final approval | `Reimbursement` | Created only after all steps approve; duplicate guard in application |
| Explicit event history | `StateEvent` | Request, approval, reimbursement and exception events |
| Seven mandatory edge cases | Synthetic anomaly injection | `ground_truth.csv/json` includes seven named cases; extra duplicate-receipt and policy-limit cases included |
| Parent-first deterministic dataset | `generator/generate_data.py` | Fixed seed and deterministic IDs |
| Required dataset volume | Generator defaults | 400 employees, 6 leave policies, 800 requests, 1,000 claims, 1–10 lines |
| CSV/JSON/SQL exports | Generator | CSV and JSON per dataset plus `seed_data.sql` |
| Data dictionary and README | `docs/` and root | Data dictionary, ERD, source manifest, validation summary |
| Validation | `validation/validate_exports.py` | PK/FK, arithmetic, lifecycle and labelled-anomaly checks |
| Reproducibility | `tools/verify_reproducibility.py` | Two-run SHA-256 comparison |

## Verification boundary
The synthetic generator, export validator, source syntax compilation and repeated-generation checksum comparison were run while building this package. The Flask application test suite and live MySQL Workbench connection could not be executed in this build environment because Flask/Flask-SQLAlchemy/PyMySQL were not installed and network package installation was unavailable. Run the documented local test command after installing `requirements.txt`; do not treat a successful ZIP creation as proof of a live MySQL deployment.
