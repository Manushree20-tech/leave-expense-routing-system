from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from datetime import date, timedelta, datetime
from decimal import Decimal, InvalidOperation
from werkzeug.utils import secure_filename
import hashlib, os
from . import db
from .models import *
from .services import business_days, accrue_leave, route_request, decide_step, event

bp = Blueprint("main", __name__)

def current_employee():
    return Employee.query.get(session.get("employee_id")) if session.get("employee_id") else None

@bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        e = Employee.query.filter_by(email=request.form.get("email", "").strip().lower()).first()
        if e:
            session["employee_id"] = e.id
            return redirect(url_for("main.dashboard"))
        flash("Use a seeded demo email from README.")
    return render_template("login.html")

@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))

@bp.route("/dashboard")
def dashboard():
    e = current_employee()
    if not e:
        return redirect(url_for("main.login"))
    for policy in LeavePolicy.query.filter_by(country=e.country).all():
        accrue_leave(e, policy)
    db.session.commit()
    balances = LeaveBalance.query.filter_by(employee_id=e.id).order_by(LeaveBalance.policy_id).all()
    return render_template(
        "dashboard.html",
        e=e,
        balances=balances,
        leaves=LeaveRequest.query.filter_by(employee_id=e.id).all(),
        claims=ExpenseClaim.query.filter_by(employee_id=e.id).all(),
        pending=ApprovalStep.query.filter_by(approver_id=e.id, status="PENDING").all(),
        events=StateEvent.query.order_by(StateEvent.occurred_at.desc()).limit(20).all()
    )

@bp.route("/leave", methods=["GET", "POST"])
def leave():
    e = current_employee()
    if not e:
        return redirect(url_for("main.login"))
    policies = LeavePolicy.query.filter_by(country=e.country).all()
    if request.method == "POST":
        try:
            p = LeavePolicy.query.get(request.form["policy_id"])
            s = date.fromisoformat(request.form["start_date"])
            end = date.fromisoformat(request.form["end_date"])
            if not p or p.country != e.country or end < s or p.effective_from > s or (p.effective_to and p.effective_to < end):
                raise ValueError("Invalid or ineffective leave policy/date range.")
            days = business_days(s, end, e.country)
            overlap = LeaveRequest.query.filter_by(employee_id=e.id).filter(
                LeaveRequest.status.in_(["PENDING", "APPROVED"]),
                LeaveRequest.start_date <= end,
                LeaveRequest.end_date >= s
            ).first()
            if overlap:
                raise ValueError(f"Leave dates overlap existing request {overlap.id}.")
            bal = accrue_leave(e, p)
            if days <= 0:
                raise ValueError("The selected period contains no business days.")
            pending_days = sum(
                (Decimal(x.business_days) for x in LeaveRequest.query.filter_by(
                    employee_id=e.id, policy_id=p.id, status="PENDING"
                ).all()), Decimal("0")
            )
            if Decimal(days) + pending_days > Decimal(bal.available):
                raise ValueError("Insufficient leave balance after reserving pending leave requests.")
            if p.max_consecutive_days and days > p.max_consecutive_days:
                raise ValueError("Policy maximum consecutive days exceeded.")
            rid = f"LVE-{s.year}-{LeaveRequest.query.count()+1:06d}"
            obj = LeaveRequest(
                id=rid, employee_id=e.id, policy_id=p.id,
                start_date=s, end_date=end, business_days=days,
                reason=request.form.get("reason", "")
            )
            db.session.add(obj)
            route_request("LEAVE", rid, e, e.country, None, Decimal(days), s)
            event("LeaveRequest", rid, None, "PENDING", e.id, "Submitted by requester.")
            db.session.commit()
            flash(f"Submitted {rid}; {days} business day(s).")
        except Exception as ex:
            db.session.rollback()
            event("Exception", f"EXC-{StateEvent.query.count()+1:06d}", None, "RAISED", e.id, str(ex))
            db.session.commit()
            flash(str(ex))
        return redirect(url_for("main.leave"))
    return render_template("leave.html", e=e, policies=policies)

@bp.route("/expense", methods=["GET", "POST"])
def expense():
    e = current_employee()
    if not e:
        return redirect(url_for("main.login"))
    centers = CostCenter.query.filter_by(country=e.country).all()
    if request.method == "POST":
        saved_files = []
        try:
            d = date.fromisoformat(request.form["expense_date"])
            cat = request.form["category"]
            cc = CostCenter.query.get(request.form.get("cost_center_id"))
            if d < e.hire_date or (e.termination_date and d > e.termination_date):
                raise ValueError("Expense date is outside employment dates.")
            if not cc:
                raise ValueError("A valid cost center is required.")
            if cc.country != e.country:
                raise ValueError("Cost center country does not match employee.")
            descriptions = request.form.getlist("description[]")
            amounts = request.form.getlist("amount[]")
            uploads = request.files.getlist("receipt_file[]")
            if not (1 <= len(descriptions) <= 10) or len(descriptions) != len(amounts):
                raise ValueError("Enter between 1 and 10 complete expense lines.")
            policy = ExpensePolicy.query.filter(
                ExpensePolicy.country == e.country,
                ExpensePolicy.category == cat,
                ExpensePolicy.effective_from <= d
            ).filter(
                (ExpensePolicy.effective_to == None) | (ExpensePolicy.effective_to >= d)
            ).first()
            if not policy:
                raise ValueError("No effective expense policy for this category/country/date.")
            total = Decimal("0")
            lines = []
            receipt_hashes = []
            upload_dir = os.path.join(current_app.instance_path, "receipts")
            os.makedirs(upload_dir, exist_ok=True)
            for i, (desc, amt) in enumerate(zip(descriptions, amounts), 1):
                val = Decimal(amt)
                if val <= 0:
                    raise ValueError("Line amounts must be positive.")
                if val > Decimal(policy.per_item_limit):
                    raise ValueError(f"Line {i} exceeds the per-item policy limit.")
                total += val
                upload = uploads[i-1] if i-1 < len(uploads) else None
                filename = None
                digest = None
                if upload and upload.filename:
                    original = secure_filename(upload.filename)
                    if not original or original.rsplit(".", 1)[-1].lower() not in {"pdf", "png", "jpg", "jpeg"}:
                        raise ValueError("Receipt must be a PDF, PNG or JPG/JPEG file.")
                    raw = upload.read()
                    if not raw:
                        raise ValueError("Receipt file is empty.")
                    digest = hashlib.sha256(raw).hexdigest()
                    if ExpenseLine.query.filter_by(receipt_hash=digest).first() or digest in receipt_hashes:
                        raise ValueError("Duplicate receipt detected; this file has already been submitted.")
                    filename = f"{e.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{i}_{original}"
                    path = os.path.join(upload_dir, filename)
                    with open(path, "wb") as f:
                        f.write(raw)
                    saved_files.append(path)
                    receipt_hashes.append(digest)
                elif val > Decimal(policy.receipt_required_above):
                    raise ValueError(f"Receipt required for line {i} above {policy.receipt_required_above}.")
                lines.append((desc, val, filename, digest))
            if total > policy.claim_limit:
                raise ValueError("Expense claim exceeds policy claim limit.")
            pending_reserved = sum(
                (Decimal(x.total_amount) for x in ExpenseClaim.query.filter_by(
                    cost_center_id=cc.id
                ).filter(ExpenseClaim.status == "PENDING").all()), Decimal("0")
            )
            budget_period = BudgetPeriod.query.filter(
                BudgetPeriod.cost_center_id == cc.id,
                BudgetPeriod.period_start <= d,
                BudgetPeriod.period_end >= d
            ).first()
            effective_budget = Decimal(budget_period.budget_amount) if budget_period else Decimal(cc.budget)
            if total + pending_reserved > effective_budget - Decimal(cc.spent):
                raise ValueError("Cost center budget would be exceeded after pending claims are reserved.")
            related = ExpenseClaim.query.filter_by(
                employee_id=e.id, category=cat, country=e.country
            ).filter(
                ExpenseClaim.expense_date >= d-timedelta(days=7),
                ExpenseClaim.expense_date <= d+timedelta(days=7)
            ).all()
            split_threshold = Decimal("5000") if e.country == "IN" else Decimal("500")
            if sum((Decimal(x.total_amount) for x in related), total) >= split_threshold:
                raise ValueError(f"Potential split-claim threshold evasion: related claims within 7 days exceed {split_threshold}.")
            cid = f"EXP-{d.year}-{ExpenseClaim.query.count()+1:06d}"
            claim = ExpenseClaim(
                id=cid, employee_id=e.id, cost_center_id=cc.id,
                expense_date=d, country=e.country, category=cat,
                total_amount=total, currency="INR" if e.country == "IN" else "USD"
            )
            db.session.add(claim)
            for i, (desc, val, filename, digest) in enumerate(lines, 1):
                db.session.add(ExpenseLine(
                    id=f"EXPL-{cid}-{i:02d}", claim_id=cid,
                    description=desc, category=cat, quantity=1,
                    unit_amount=val, line_total=val,
                    receipt_filename=filename, receipt_hash=digest,
                    receipt_present=bool(filename)
                ))
            route_request("EXPENSE", cid, e, e.country, cat, total, d)
            event("ExpenseClaim", cid, None, "PENDING", e.id, "Submitted by requester.")
            db.session.commit()
            flash(f"Submitted {cid}; total {total}.")
        except (ValueError, InvalidOperation, KeyError) as ex:
            db.session.rollback()
            for path in saved_files:
                try:
                    os.remove(path)
                except OSError:
                    pass
            event("Exception", f"EXC-{StateEvent.query.count()+1:06d}", None, "RAISED", e.id, str(ex))
            db.session.commit()
            flash(str(ex))
        return redirect(url_for("main.expense"))
    return render_template("expense.html", e=e, centers=centers)

@bp.route("/approvals")
def approvals():
    e = current_employee()
    if not e:
        return redirect(url_for("main.login"))
    steps = ApprovalStep.query.filter_by(approver_id=e.id, status="PENDING").all()
    return render_template("approvals.html", e=e, steps=steps)

@bp.route("/decision/<step_id>", methods=["POST"])
def decision(step_id):
    e = current_employee()
    if not e:
        return redirect(url_for("main.login"))
    step = ApprovalStep.query.get_or_404(step_id)
    try:
        decide_step(step, e, request.form["decision"], request.form.get("reason", ""))
    except Exception as ex:
        db.session.rollback()
        flash(str(ex))
    return redirect(url_for("main.approvals"))

@bp.route("/reimbursements")
def reimbursements():
    e = current_employee()
    if not e:
        return redirect(url_for("main.login"))
    return render_template("reimbursements.html", e=e, rows=Reimbursement.query.all())

@bp.route("/exceptions")
def exceptions():
    e = current_employee()
    if not e:
        return redirect(url_for("main.login"))
    rows = StateEvent.query.filter_by(entity_type="Exception").order_by(StateEvent.occurred_at.desc()).all()
    return render_template("exceptions.html", e=e, rows=rows)

# Audit trail page
@bp.route("/audit")
def audit():
    e = current_employee()
    if not e:
        return redirect(url_for("main.login"))
    rows = StateEvent.query.order_by(StateEvent.occurred_at.desc()).all()
    return render_template("audit.html", e=e, rows=rows, events=rows)

@bp.route("/analyst")
def analyst():
    e = current_employee()
    if not e:
        return redirect(url_for("main.login"))
    total_claims = ExpenseClaim.query.count()
    approved = ExpenseClaim.query.filter_by(status="APPROVED").count()
    rejected = ExpenseClaim.query.filter_by(status="REJECTED").count()
    exceptions = StateEvent.query.filter_by(entity_type="Exception").count()
    reimbursed_amount = sum((Decimal(x.amount) for x in Reimbursement.query.all()), Decimal("0"))
    approval_rate = round((approved / total_claims * 100), 2) if total_claims else 0
    return render_template(
        "analyst.html", e=e, employees=Employee.query.count(),
        leaves=LeaveRequest.query.count(), claims=total_claims,
        approved=approved, rejected=rejected,
        approval_rate=approval_rate, exceptions=exceptions,
        reimb=Reimbursement.query.count(),
        reimbursed_amount=reimbursed_amount,
        events=StateEvent.query.count()
    )