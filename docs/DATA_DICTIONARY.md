# Data dictionary — all 11 required core entities

Conventions: IDs are immutable strings; dates are ISO `YYYY-MM-DD`; timestamps are UTC; monetary values use `DECIMAL` and ISO-4217 currency; countries use ISO-3166 alpha-2. `Required` describes normal operational records. Optional anomaly records are labelled in the separate `ground_truth.csv/json` files, not in model input features.

## Employee
| Field | Type | Required | Allowed values / units | Unique | Validation |
|---|---|---:|---|---:|---|
| id | VARCHAR(20) | Yes | `EMP-######` | PK | Immutable, exact format |
| name | VARCHAR(120) | Yes | Non-empty text | No | Trimmed, non-empty |
| email | VARCHAR(160) | Yes | Email address | Yes | Unique, valid email syntax |
| country | CHAR(2) | Yes | ISO country code | No | Must be supported by policies |
| department | VARCHAR(80) | Yes | Organization department | No | Non-empty |
| role | VARCHAR(30) | Yes | REQUESTER, PROCESS_OWNER, APPROVER, OPS_ANALYST, ADMIN | No | Enum |
| manager_id | VARCHAR(20) | No | Employee ID | No | FK to Employee; cannot self-reference |
| hire_date | DATE | Yes | Calendar date | No | Must be a valid date |
| termination_date | DATE | No | Calendar date | No | Must be on/after hire date |
| active | BOOLEAN | Yes | TRUE/FALSE | No | Boolean |

## LeavePolicy
| Field | Type | Required | Allowed values / units | Unique | Validation |
|---|---|---:|---|---:|---|
| id | VARCHAR(20) | Yes | `LP-*` | PK | Immutable |
| name | VARCHAR(80) | Yes | Policy name | No | Non-empty |
| annual_entitlement | DECIMAL(8,2) | Yes | Days/year | No | Must be >= 0 |
| accrual_method | VARCHAR(20) | Yes | MONTHLY, ANNUAL, FRONT_LOADED | No | Enum |
| max_consecutive_days | INT | No | Calendar/business-day limit | No | Positive when supplied |
| country | CHAR(2) | Yes | ISO country code | No | Supported country |
| effective_from | DATE | Yes | Calendar date | No | Required |
| effective_to | DATE | No | Calendar date | No | Must be >= effective_from |

## LeaveBalance
| Field | Type | Required | Allowed values / units | Unique | Validation |
|---|---|---:|---|---:|---|
| id | INT | Yes | Auto-increment | PK | Database-generated |
| employee_id | VARCHAR(20) | Yes | Employee ID | No | FK Employee |
| policy_id | VARCHAR(20) | Yes | Policy ID | No | FK LeavePolicy |
| opening_balance | DECIMAL(8,2) | Yes | Days | No | >= 0 normally; negative cases labelled separately |
| accrued | DECIMAL(8,2) | Yes | Days | No | Derived from accrual rule |
| used | DECIMAL(8,2) | Yes | Days | No | Derived from approved leave |
| available | DECIMAL(8,2) | Yes | Days | No | opening + accrued - used |
| as_of | DATE | Yes | Balance snapshot date | No | Composite unique with employee_id + policy_id |

## LeaveRequest
| Field | Type | Required | Allowed values / units | Unique | Validation |
|---|---|---:|---|---:|---|
| id | VARCHAR(30) | Yes | `LVE-YYYY-######` | PK | Immutable |
| employee_id | VARCHAR(20) | Yes | Employee ID | No | FK Employee |
| policy_id | VARCHAR(20) | Yes | Policy ID | No | FK LeavePolicy and country match |
| start_date | DATE | Yes | Calendar date | No | Must be <= end_date |
| end_date | DATE | Yes | Calendar date | No | Must be >= start_date |
| business_days | INT | Yes | Business days | No | Derived excluding weekends/holidays |
| reason | VARCHAR(500) | No | Text | No | Optional |
| status | VARCHAR(20) | Yes | PENDING, APPROVED, REJECTED | No | Valid lifecycle transition |
| created_at | DATETIME | Yes | UTC timestamp | No | Generated at submission |
| issue_type | LABEL | No | Ground-truth label only | No | Stored in separate ground_truth, never as a model feature |

## ExpensePolicy
| Field | Type | Required | Allowed values / units | Unique | Validation |
|---|---|---:|---|---:|---|
| id | VARCHAR(20) | Yes | `EP-*` | PK | Immutable |
| country | CHAR(2) | Yes | ISO country code | No | Supported country |
| category | VARCHAR(40) | Yes | TRAVEL, MEALS, LODGING, EQUIPMENT, OTHER | No | Enum |
| per_item_limit | DECIMAL(12,2) | Yes | Currency units | No | >= 0 |
| claim_limit | DECIMAL(12,2) | Yes | Currency units | No | >= 0 |
| receipt_required_above | DECIMAL(12,2) | Yes | Currency units | No | >= 0 |
| effective_from | DATE | Yes | Calendar date | No | Required |
| effective_to | DATE | No | Calendar date | No | >= effective_from |
| Combination rule | — | — | country + category + effective_from | Composite unique | One policy version per effective start |

## ExpenseClaim
| Field | Type | Required | Allowed values / units | Unique | Validation |
|---|---|---:|---|---:|---|
| id | VARCHAR(30) | Yes | `EXP-YYYY-######` | PK | Immutable |
| employee_id | VARCHAR(20) | Yes | Employee ID | No | FK Employee |
| cost_center_id | VARCHAR(20) | No in anomaly data; required operationally | CostCenter ID | No | FK CostCenter; country must match |
| expense_date | DATE | Yes | Calendar date | No | Within employment dates |
| country | CHAR(2) | Yes | ISO country code | No | Must match employee |
| category | VARCHAR(40) | Yes | TRAVEL, MEALS, LODGING, EQUIPMENT, OTHER | No | Must match effective policy |
| total_amount | DECIMAL(14,2) | Yes | Currency units | No | Sum of line totals; >= 0 |
| currency | CHAR(3) | Yes | ISO-4217 | No | Must match country/company policy |
| status | VARCHAR(20) | Yes | PENDING, APPROVED, REJECTED | No | Valid lifecycle |
| created_at | DATETIME | Yes | UTC timestamp | No | Generated at submission |
| issue_type | LABEL | No | Ground-truth label only | No | Separate ground_truth file, not a feature |

## ExpenseLine
| Field | Type | Required | Allowed values / units | Unique | Validation |
|---|---|---:|---|---:|---|
| id | VARCHAR(50) | Yes | `EXPL-<claim-id>-NN` | PK | Immutable |
| claim_id | VARCHAR(30) | Yes | ExpenseClaim ID | No | FK ExpenseClaim |
| description | VARCHAR(200) | Yes | Text | No | Non-empty |
| category | VARCHAR(40) | Yes | Expense category | No | Must match claim/policy |
| quantity | DECIMAL(10,2) | Yes | Units | No | > 0 |
| unit_amount | DECIMAL(14,2) | Yes | Currency units | No | >= 0 |
| line_total | DECIMAL(14,2) | Yes | Currency units | No | quantity * unit_amount |
| receipt_filename | VARCHAR(255) | No | Stored safe filename | No | Private upload location |
| receipt_hash | CHAR(64) | No | SHA-256 hex | No | Duplicate content check |
| receipt_present | BOOLEAN | Yes | TRUE/FALSE | No | Consistent with receipt metadata |
| issue_type | LABEL | No | Ground-truth label only | No | Kept in separate ground_truth, not a feature |

## CostCenter
| Field | Type | Required | Allowed values / units | Unique | Validation |
|---|---|---:|---|---:|---|
| id | VARCHAR(20) | Yes | `CC-*` | PK | Immutable |
| name | VARCHAR(100) | Yes | Text | No | Non-empty |
| country | CHAR(2) | Yes | ISO country code | No | Must match claim country |
| budget | DECIMAL(14,2) | Yes | Currency units | No | >= 0 |
| spent | DECIMAL(14,2) | Yes | Currency units | No | >= 0; updated after final approval |
| owner_employee_id | VARCHAR(20) | No | Employee ID | No | FK Employee |

## ApprovalRule
| Field | Type | Required | Allowed values / units | Unique | Validation |
|---|---|---:|---|---:|---|
| id | VARCHAR(30) | Yes | `AR-*` | PK | Immutable |
| request_type | VARCHAR(20) | Yes | LEAVE, EXPENSE | No | Enum |
| country | CHAR(2) | No | ISO country code | No | Optional matching filter |
| category | VARCHAR(40) | No | Expense category | No | Optional matching filter |
| min_amount | DECIMAL(14,2) | No | Currency or leave-day amount | No | >= 0 |
| max_amount | DECIMAL(14,2) | No | Currency or leave-day amount | No | >= min_amount |
| approver_role | VARCHAR(30) | Yes | MANAGER, FINANCE or configured actor role | No | Must resolve to an eligible employee |
| sequence | INT | Yes | Approval order | No | Positive; unique per request instance |
| effective_from | DATE | Yes | Calendar date | No | Required |
| effective_to | DATE | No | Calendar date | No | >= effective_from |
| active | BOOLEAN | Yes | TRUE/FALSE | No | Boolean |

## ApprovalStep
| Field | Type | Required | Allowed values / units | Unique | Validation |
|---|---|---:|---|---:|---|
| id | VARCHAR(60) | Yes | `APR-<request-id>-NN` | PK | Immutable |
| request_type | VARCHAR(20) | Yes | LEAVE, EXPENSE | No | Enum |
| request_id | VARCHAR(30) | Yes | LeaveRequest or ExpenseClaim ID | No | Polymorphic reference validated by request_type |
| sequence | INT | Yes | Approval order | Composite unique | Earlier steps must be approved first |
| approver_id | VARCHAR(20) | Yes | Employee ID | No | FK Employee; cannot equal requester |
| status | VARCHAR(20) | Yes | PENDING, APPROVED, REJECTED | No | Valid lifecycle |
| decision_reason | VARCHAR(500) | No | Text | No | Required by UI for a decision |
| decided_at | DATETIME | No | UTC timestamp | No | Set when decided |
| rule_id | VARCHAR(30) | No | ApprovalRule ID | No | FK ApprovalRule |

## Reimbursement
| Field | Type | Required | Allowed values / units | Unique | Validation |
|---|---|---:|---|---:|---|
| id | VARCHAR(30) | Yes | `RMB-YYYY-######` | PK | Immutable |
| claim_id | VARCHAR(30) | Yes | ExpenseClaim ID | No in anomaly dataset | FK ExpenseClaim; application prevents duplicate reimbursement |
| amount | DECIMAL(14,2) | Yes | Currency units | No | Must equal approved claim total |
| currency | CHAR(3) | Yes | ISO-4217 | No | Must match claim |
| status | VARCHAR(20) | Yes | PENDING_PAYMENT, PAID | No | Reimbursement lifecycle |
| created_at | DATETIME | Yes | UTC timestamp | No | Only after final approval |
| paid_at | DATETIME | No | UTC timestamp | No | Set only when paid |

## Supporting tables
`EmployeePolicy` is the effective-dated N:M bridge between Employee and LeavePolicy. `BudgetPeriod` stores dated cost-center budget windows. `Holiday` stores country/date calendars. `StateEvent` stores immutable from/to state, actor, reason and timestamp records. `ground_truth.csv/json` contains anomaly `issue_type`, entity reference, expected decision and description; it is not included in feature tables.
