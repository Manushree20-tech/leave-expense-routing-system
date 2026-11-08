from datetime import date, timedelta, datetime
from decimal import Decimal
from . import db
from .models import *

def business_days(start, end, country):
    holidays={h.holiday_date for h in Holiday.query.filter_by(country=country).all()}
    n=0; d=start
    while d<=end:
        if d.weekday()<5 and d not in holidays: n+=1
        d+=timedelta(days=1)
    return n

def accrue_leave(employee, policy, as_of=None):
    as_of=as_of or date.today()
    start=max(employee.hire_date, policy.effective_from, date(as_of.year,1,1))
    months=min(12,max(0,(as_of.year-start.year)*12+as_of.month-start.month+1))
    monthly=Decimal(policy.annual_entitlement)/Decimal(12)
    accrued=(monthly*months).quantize(Decimal("0.01"))
    bal=LeaveBalance.query.filter_by(employee_id=employee.id,policy_id=policy.id).order_by(LeaveBalance.as_of.desc()).first()
    if not bal:
        bal=LeaveBalance(employee_id=employee.id,policy_id=policy.id,opening_balance=0,accrued=accrued,used=0,available=accrued,as_of=as_of)
        db.session.add(bal)
    else:
        # Keep one current balance row per employee/policy; usage survives a later login/date.
        bal.as_of=as_of
        bal.accrued=accrued
        bal.available=Decimal(bal.opening_balance)+Decimal(bal.accrued)-Decimal(bal.used)
    return bal

def event(entity_type, entity_id, old, new, actor_id=None, reason=None):
    db.session.add(StateEvent(entity_type=entity_type,entity_id=entity_id,from_state=old,to_state=new,actor_id=actor_id,reason=reason))

def applicable_rules(request_type, country, category, amount, on_date=None):
    on_date=on_date or date.today()
    rules=ApprovalRule.query.filter_by(request_type=request_type,active=True).all()
    out=[]
    for r in rules:
        if r.effective_from>on_date or (r.effective_to and r.effective_to<on_date): continue
        if r.country and r.country!=country: continue
        if r.category and r.category!=category: continue
        if amount < (r.min_amount or 0): continue
        if r.max_amount is not None and amount>r.max_amount: continue
        out.append(r)
    return sorted(out,key=lambda x:x.sequence)

def route_request(request_type, request_id, employee, country, category, amount, on_date=None):
    rules=applicable_rules(request_type,country,category,amount,on_date)
    if not rules:
        raise ValueError("No effective approval rule matches this request.")
    for rule in rules:
        approver=None
        if rule.approver_role=="MANAGER":
            approver=Employee.query.get(employee.manager_id) if employee.manager_id else None
        elif rule.approver_role=="FINANCE":
            approver=Employee.query.filter_by(role="APPROVER",department="Finance",country=country).first()
        else:
            approver=Employee.query.filter_by(role=rule.approver_role,country=country).first()
        if not approver:
            raise ValueError(f"Missing approver for rule {rule.id}; route flagged for process-owner configuration.")
        step_id=f"APR-{request_id}-{rule.sequence:02d}"
        db.session.add(ApprovalStep(id=step_id,request_type=request_type,request_id=request_id,sequence=rule.sequence,approver_id=approver.id,rule_id=rule.id))
    return True

def decide_step(step, actor, decision, reason):
    if step.approver_id!=actor.id: raise ValueError("Only the assigned approver can decide this step.")
    req=(LeaveRequest.query.get(step.request_id) if step.request_type=="LEAVE" else ExpenseClaim.query.get(step.request_id))
    if not req: raise ValueError("Request not found.")
    if req.employee_id==actor.id: raise ValueError("Requester cannot approve their own request.")
    if step.status!="PENDING": raise ValueError("This approval step has already been decided.")
    earlier=ApprovalStep.query.filter(ApprovalStep.request_type==step.request_type,ApprovalStep.request_id==step.request_id,ApprovalStep.sequence<step.sequence).all()
    if any(x.status!="APPROVED" for x in earlier): raise ValueError("Earlier approval steps must be approved first.")
    if decision not in ["APPROVED","REJECTED"]: raise ValueError("Invalid decision.")
    if decision=="APPROVED" and step.request_type=="LEAVE":
        bal=LeaveBalance.query.filter_by(employee_id=req.employee_id,policy_id=req.policy_id).order_by(LeaveBalance.as_of.desc()).first()
        if bal and Decimal(bal.available)<Decimal(req.business_days):
            raise ValueError("Leave balance is no longer sufficient at approval time.")
    step.status=decision; step.decision_reason=reason; step.decided_at=datetime.utcnow()
    event("ApprovalStep",step.id,"PENDING",decision,actor.id,reason)
    if decision=="REJECTED":
        old=req.status; req.status="REJECTED"; event("LeaveRequest" if step.request_type=="LEAVE" else "ExpenseClaim",req.id,old,"REJECTED",actor.id,reason)
        later=ApprovalStep.query.filter(ApprovalStep.request_type==step.request_type,ApprovalStep.request_id==step.request_id,ApprovalStep.sequence>step.sequence,ApprovalStep.status=="PENDING").all()
        for later_step in later:
            later_step.status="REJECTED"; later_step.decision_reason="Cancelled because an earlier approval step was rejected."; later_step.decided_at=datetime.utcnow()
            event("ApprovalStep",later_step.id,"PENDING","REJECTED",actor.id,later_step.decision_reason)
    else:
        pending=ApprovalStep.query.filter_by(request_type=step.request_type,request_id=step.request_id,status="PENDING").count()
        if pending==0:
            old=req.status; req.status="APPROVED"; event("LeaveRequest" if step.request_type=="LEAVE" else "ExpenseClaim",req.id,old,"APPROVED",actor.id,"All approval steps approved.")
            if step.request_type=="LEAVE":
                bal=LeaveBalance.query.filter_by(employee_id=req.employee_id,policy_id=req.policy_id).order_by(LeaveBalance.as_of.desc()).first()
                if bal:
                    old_available=str(bal.available)
                    bal.used=Decimal(bal.used)+Decimal(req.business_days)
                    bal.available=Decimal(bal.opening_balance)+Decimal(bal.accrued)-Decimal(bal.used)
                    event("LeaveBalance",str(bal.id),old_available,str(bal.available),actor.id,f"Deducted {req.business_days} approved leave day(s).")
            if step.request_type=="EXPENSE" and not Reimbursement.query.filter_by(claim_id=req.id).first():
                reimbursement_id=f"RMB-{date.today().year}-{Reimbursement.query.count()+1:06d}"
                db.session.add(Reimbursement(id=reimbursement_id,claim_id=req.id,amount=req.total_amount,currency=req.currency))
                event("Reimbursement",reimbursement_id,None,"PENDING_PAYMENT",actor.id,"Created after final approval.")
                if req.cost_center_id:
                    center=CostCenter.query.get(req.cost_center_id)
                    if center: center.spent=Decimal(center.spent)+Decimal(req.total_amount)
    db.session.commit()
