# Data model and relationships
The 11 required core entities are implemented in `app/models.py`. Additional supporting entities are `StateEvent` (append-only state history), `Holiday` (country business-day calendar), `BudgetPeriod` (dated budget allocation), and `EmployeePolicy` (effective-dated employee-to-policy bridge).

## Primary keys and foreign keys
- Employee(employee_id) self-references Employee.manager_id (1:N reporting hierarchy).
- LeavePolicy(policy_id) 1:N LeaveBalance and 1:N LeaveRequest.
- Employee 1:N LeaveBalance and 1:N LeaveRequest.
- Employee N:M LeavePolicy through EmployeePolicy (effective-dated bridge).
- Employee 1:N ExpenseClaim; CostCenter 1:N ExpenseClaim (cost center optional at database level to support labelled anomaly cases; required by normal submission).
- ExpenseClaim 1:N ExpenseLine.
- ExpensePolicy is selected by country/category/effective date.
- ApprovalRule 1:N ApprovalStep (rule matching creates approval steps; request reference is polymorphic by request_type/request_id).
- ExpenseClaim 1:0..1 Reimbursement (unique claim_id; created only on final approval).
- StateEvent records entity type/id, old/new state, actor, reason and timestamp.
- CostCenter 1:N BudgetPeriod.

## Lifecycle
LeaveRequest / ExpenseClaim: PENDING -> APPROVED or REJECTED. ApprovalStep: PENDING -> APPROVED or REJECTED. Reimbursement: PENDING_PAYMENT -> PAID (payment action can be added by finance operations). Events are appended on recorded decisions; do not update old event rows.

## Design notes
ApprovalRule is effective-dated and can filter by request type, country, category, amount range and sequence. `MANAGER` resolves from Employee.manager_id. `FINANCE` resolves to an APPROVER in Finance. Missing configured authority raises an explicit routing error rather than inventing an actor.
