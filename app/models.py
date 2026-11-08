from datetime import datetime, date
from . import db

class Employee(db.Model):
    id=db.Column(db.String(20), primary_key=True); name=db.Column(db.String(120), nullable=False)
    email=db.Column(db.String(160), unique=True, nullable=False); country=db.Column(db.String(2), nullable=False)
    department=db.Column(db.String(80), nullable=False); role=db.Column(db.String(30), nullable=False)
    manager_id=db.Column(db.String(20), db.ForeignKey("employee.id")); hire_date=db.Column(db.Date, nullable=False)
    termination_date=db.Column(db.Date); active=db.Column(db.Boolean, default=True, nullable=False)
    manager=db.relationship("Employee", remote_side=[id], backref="direct_reports")

class LeavePolicy(db.Model):
    id=db.Column(db.String(20), primary_key=True); name=db.Column(db.String(80), nullable=False)
    annual_entitlement=db.Column(db.Numeric(8,2), nullable=False); accrual_method=db.Column(db.String(20), nullable=False)
    max_consecutive_days=db.Column(db.Integer); country=db.Column(db.String(2), nullable=False)
    effective_from=db.Column(db.Date, nullable=False); effective_to=db.Column(db.Date)

class LeaveBalance(db.Model):
    id=db.Column(db.Integer, primary_key=True); employee_id=db.Column(db.String(20), db.ForeignKey("employee.id"), nullable=False)
    policy_id=db.Column(db.String(20), db.ForeignKey("leave_policy.id"), nullable=False)
    opening_balance=db.Column(db.Numeric(8,2), default=0, nullable=False); accrued=db.Column(db.Numeric(8,2), default=0, nullable=False)
    used=db.Column(db.Numeric(8,2), default=0, nullable=False); available=db.Column(db.Numeric(8,2), default=0, nullable=False)
    as_of=db.Column(db.Date, nullable=False); __table_args__=(db.UniqueConstraint("employee_id","policy_id","as_of"),)

class LeaveRequest(db.Model):
    id=db.Column(db.String(30), primary_key=True); employee_id=db.Column(db.String(20), db.ForeignKey("employee.id"), nullable=False)
    policy_id=db.Column(db.String(20), db.ForeignKey("leave_policy.id"), nullable=False)
    start_date=db.Column(db.Date, nullable=False); end_date=db.Column(db.Date, nullable=False)
    business_days=db.Column(db.Integer, nullable=False); reason=db.Column(db.String(500))
    status=db.Column(db.String(20), nullable=False, default="PENDING"); created_at=db.Column(db.DateTime, default=datetime.utcnow)
    issue_type=db.Column(db.String(60))

class ExpensePolicy(db.Model):
    id=db.Column(db.String(20), primary_key=True); country=db.Column(db.String(2), nullable=False)
    category=db.Column(db.String(40), nullable=False); per_item_limit=db.Column(db.Numeric(12,2), nullable=False)
    claim_limit=db.Column(db.Numeric(12,2), nullable=False); receipt_required_above=db.Column(db.Numeric(12,2), nullable=False)
    effective_from=db.Column(db.Date, nullable=False); effective_to=db.Column(db.Date)

class CostCenter(db.Model):
    id=db.Column(db.String(20), primary_key=True); name=db.Column(db.String(100), nullable=False)
    country=db.Column(db.String(2), nullable=False); budget=db.Column(db.Numeric(14,2), nullable=False)
    spent=db.Column(db.Numeric(14,2), default=0, nullable=False); owner_employee_id=db.Column(db.String(20), db.ForeignKey("employee.id"))

class ExpenseClaim(db.Model):
    id=db.Column(db.String(30), primary_key=True); employee_id=db.Column(db.String(20), db.ForeignKey("employee.id"), nullable=False)
    cost_center_id=db.Column(db.String(20), db.ForeignKey("cost_center.id")); expense_date=db.Column(db.Date, nullable=False)
    country=db.Column(db.String(2), nullable=False); category=db.Column(db.String(40), nullable=False)
    total_amount=db.Column(db.Numeric(14,2), nullable=False); currency=db.Column(db.String(3), nullable=False)
    status=db.Column(db.String(20), nullable=False, default="PENDING"); created_at=db.Column(db.DateTime, default=datetime.utcnow)
    issue_type=db.Column(db.String(60))

class ExpenseLine(db.Model):
    id=db.Column(db.String(50), primary_key=True); claim_id=db.Column(db.String(30), db.ForeignKey("expense_claim.id"), nullable=False)
    description=db.Column(db.String(200), nullable=False); category=db.Column(db.String(40), nullable=False)
    quantity=db.Column(db.Numeric(10,2), nullable=False); unit_amount=db.Column(db.Numeric(14,2), nullable=False)
    line_total=db.Column(db.Numeric(14,2), nullable=False); receipt_filename=db.Column(db.String(255))
    receipt_hash=db.Column(db.String(64)); receipt_present=db.Column(db.Boolean, nullable=False, default=False)
    issue_type=db.Column(db.String(60))
    issue_type=db.Column(db.String(60))

class ApprovalRule(db.Model):
    id=db.Column(db.String(30), primary_key=True); request_type=db.Column(db.String(20), nullable=False)
    country=db.Column(db.String(2)); category=db.Column(db.String(40)); min_amount=db.Column(db.Numeric(14,2), default=0)
    max_amount=db.Column(db.Numeric(14,2)); approver_role=db.Column(db.String(30), nullable=False)
    sequence=db.Column(db.Integer, nullable=False); effective_from=db.Column(db.Date, nullable=False)
    effective_to=db.Column(db.Date); active=db.Column(db.Boolean, default=True, nullable=False)

class ApprovalStep(db.Model):
    id=db.Column(db.String(60), primary_key=True); request_type=db.Column(db.String(20), nullable=False)
    request_id=db.Column(db.String(30), nullable=False); sequence=db.Column(db.Integer, nullable=False)
    approver_id=db.Column(db.String(20), db.ForeignKey("employee.id"), nullable=False)
    status=db.Column(db.String(20), nullable=False, default="PENDING"); decision_reason=db.Column(db.String(500))
    decided_at=db.Column(db.DateTime); rule_id=db.Column(db.String(30), db.ForeignKey("approval_rule.id"))
    __table_args__=(db.UniqueConstraint("request_type","request_id","sequence"),)

class Reimbursement(db.Model):
    id=db.Column(db.String(30), primary_key=True); claim_id=db.Column(db.String(30), db.ForeignKey("expense_claim.id"), nullable=False)
    amount=db.Column(db.Numeric(14,2), nullable=False); currency=db.Column(db.String(3), nullable=False)
    status=db.Column(db.String(20), nullable=False, default="PENDING_PAYMENT"); created_at=db.Column(db.DateTime, default=datetime.utcnow)
    paid_at=db.Column(db.DateTime)

class StateEvent(db.Model):
    id=db.Column(db.Integer, primary_key=True); entity_type=db.Column(db.String(30), nullable=False)
    entity_id=db.Column(db.String(50), nullable=False); from_state=db.Column(db.String(30)); to_state=db.Column(db.String(30), nullable=False)
    actor_id=db.Column(db.String(20), db.ForeignKey("employee.id")); reason=db.Column(db.String(500))
    occurred_at=db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Holiday(db.Model):
    id=db.Column(db.Integer, primary_key=True); country=db.Column(db.String(2), nullable=False)
    holiday_date=db.Column(db.Date, nullable=False); name=db.Column(db.String(100), nullable=False)
    __table_args__=(db.UniqueConstraint("country","holiday_date"),)

class BudgetPeriod(db.Model):
    id=db.Column(db.Integer, primary_key=True); cost_center_id=db.Column(db.String(20), db.ForeignKey("cost_center.id"), nullable=False)
    period_start=db.Column(db.Date, nullable=False); period_end=db.Column(db.Date, nullable=False)
    budget_amount=db.Column(db.Numeric(14,2), nullable=False); __table_args__=(db.UniqueConstraint("cost_center_id","period_start","period_end"),)

class EmployeePolicy(db.Model):
    id=db.Column(db.Integer, primary_key=True); employee_id=db.Column(db.String(20), db.ForeignKey("employee.id"), nullable=False)
    policy_id=db.Column(db.String(20), db.ForeignKey("leave_policy.id"), nullable=False)
    effective_from=db.Column(db.Date, nullable=False); effective_to=db.Column(db.Date)
    __table_args__=(db.UniqueConstraint("employee_id","policy_id","effective_from"),)
