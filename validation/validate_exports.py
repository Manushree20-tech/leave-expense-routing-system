import csv,json,sys
from pathlib import Path
from decimal import Decimal
from datetime import date,timedelta

def read(path):
    with open(path,encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))

def validate(folder):
    p=Path(folder); errors=[]
    names=['employees','leave_policies','leave_balances','leave_requests','expense_policies','cost_centers','budget_periods','employee_policies','approval_rules','holidays','expense_claims','expense_lines','reimbursements','approval_steps']
    data={n:read(p/f'{n}.csv') for n in names}
    truth=json.loads((p/'ground_truth.json').read_text(encoding='utf-8'))
    labels={(x['entity_type'],x['entity_id']):x['issue_type'] for x in truth}
    def unique(rows,key,label):
        vals=[r[key] for r in rows]
        if len(vals)!=len(set(vals)): errors.append(f'{label}: duplicate primary keys')
    for key,label in [('employee_id','Employee'),('policy_id','LeavePolicy'),('leave_request_id','LeaveRequest'),('expense_policy_id','ExpensePolicy'),('cost_center_id','CostCenter'),('expense_claim_id','ExpenseClaim'),('expense_line_id','ExpenseLine'),('reimbursement_id','Reimbursement'),('approval_rule_id','ApprovalRule'),('approval_step_id','ApprovalStep')]:
        group={'employee_id':'employees','policy_id':'leave_policies','leave_request_id':'leave_requests','expense_policy_id':'expense_policies','cost_center_id':'cost_centers','expense_claim_id':'expense_claims','expense_line_id':'expense_lines','reimbursement_id':'reimbursements','approval_rule_id':'approval_rules','approval_step_id':'approval_steps'}[key]
        unique(data[group],key,label)
    emp={x['employee_id']:x for x in data['employees']}; policies={x['policy_id']:x for x in data['leave_policies']}
    centers={x['cost_center_id']:x for x in data['cost_centers']}; claims={x['expense_claim_id']:x for x in data['expense_claims']}
    approved_leave=[]
    for r in data['employees']:
        if r['manager_id'] and r['manager_id'] not in emp: errors.append(f"Employee manager FK invalid: {r['employee_id']}")
        if r['termination_date'] and date.fromisoformat(r['termination_date'])<date.fromisoformat(r['hire_date']): errors.append(f"Employment dates invalid: {r['employee_id']}")
    for r in data['leave_balances']:
        if r['employee_id'] not in emp or r['policy_id'] not in policies: errors.append(f"LeaveBalance FK invalid: {r['balance_id']}")
        calc=Decimal(r['opening_balance'])+Decimal(r['accrued'])-Decimal(r['used'])
        if Decimal(r['available'])!=calc and (('LeaveBalance',r['balance_id']) not in labels): errors.append(f"Leave balance reconciliation failed: {r['balance_id']}")
    for r in data['leave_requests']:
        if r['employee_id'] not in emp or r['policy_id'] not in policies: errors.append(f"LeaveRequest FK invalid: {r['leave_request_id']}")
        if date.fromisoformat(r['end_date'])<date.fromisoformat(r['start_date']): errors.append(f"Leave date order invalid: {r['leave_request_id']}")
        if r['status'] not in {'PENDING','APPROVED','REJECTED'}: errors.append(f"Leave status invalid: {r['leave_request_id']}")
        if r['status']=='APPROVED': approved_leave.append(r)
    for r in data['expense_claims']:
        if r['employee_id'] not in emp: errors.append(f"Expense employee FK invalid: {r['expense_claim_id']}")
        if r['cost_center_id'] and r['cost_center_id'] not in centers: errors.append(f"Expense cost center FK invalid: {r['expense_claim_id']}")
        if r['status'] not in {'PENDING','APPROVED','REJECTED'}: errors.append(f"Expense status invalid: {r['expense_claim_id']}")
        if r['expense_date']<emp[r['employee_id']]['hire_date'] and ('ExpenseClaim',r['expense_claim_id']) not in labels: errors.append(f"Expense predates employment without label: {r['expense_claim_id']}")
    grouped={}
    for r in data['expense_lines']:
        if r['claim_id'] not in claims: errors.append(f"ExpenseLine FK invalid: {r['expense_line_id']}")
        grouped.setdefault(r['claim_id'],Decimal('0'))
        grouped[r['claim_id']]+=Decimal(r['line_total'])
        if Decimal(r['quantity'])<=0 or Decimal(r['unit_amount'])<0 or Decimal(r['line_total'])!=Decimal(r['quantity'])*Decimal(r['unit_amount']):
            if ('ExpenseLine',r['expense_line_id']) not in labels: errors.append(f"ExpenseLine arithmetic invalid: {r['expense_line_id']}")
    for cid,c in claims.items():
        count=sum(1 for x in data['expense_lines'] if x['claim_id']==cid)
        if not 1<=count<=10: errors.append(f"Expense line count outside 1..10: {cid}")
        if grouped.get(cid,Decimal('0'))!=Decimal(c['total_amount']) and ('ExpenseClaim',cid) not in labels: errors.append(f"Expense total does not reconcile: {cid}")
    # Every reimbursement must reference an approved claim. The one deliberate duplicate is labelled.
    reimb_by_claim={}
    for r in data['reimbursements']:
        if r['claim_id'] not in claims: errors.append(f"Reimbursement FK invalid: {r['reimbursement_id']}"); continue
        reimb_by_claim.setdefault(r['claim_id'],[]).append(r)
        if claims[r['claim_id']]['status']!='APPROVED' and ('Reimbursement',r['reimbursement_id']) not in labels:
            errors.append(f"Reimbursement exists for non-approved claim: {r['reimbursement_id']}")
    for cid,rows in reimb_by_claim.items():
        if len(rows)>1 and not any(labels.get(('Reimbursement',x['reimbursement_id']))=='DUPLICATE_REIMBURSEMENT' for x in rows):
            errors.append(f"Duplicate reimbursement without ground-truth label: {cid}")
    # Receipt hash duplicates are allowed only when the duplicate row is labelled.
    hashes={}
    for r in data['expense_lines']:
        h=r['receipt_hash']
        if h:
            hashes.setdefault(h,[]).append(r)
    for h,rows in hashes.items():
        if len(rows)>1 and not any(labels.get(('ExpenseLine',x['expense_line_id']))=='DUPLICATE_RECEIPT_HASH' for x in rows):
            errors.append(f"Duplicate receipt hash without ground-truth label: {h}")
    for r in data['approval_steps']:
        if r['approver_id'] not in emp: errors.append(f"Approval approver FK invalid: {r['approval_step_id']}")
        if r['request_type']=='EXPENSE' and r['request_id'] not in claims: errors.append(f"Approval expense reference invalid: {r['approval_step_id']}")
        if r['request_type']=='LEAVE' and r['request_id'] not in {x['leave_request_id'] for x in data['leave_requests']}: errors.append(f"Approval leave reference invalid: {r['approval_step_id']}")
        if r['request_type']=='EXPENSE' and r['request_id'] in claims and claims[r['request_id']]['employee_id']==r['approver_id'] and ('ApprovalStep',r['approval_step_id']) not in labels:
            errors.append(f"Self-approval without ground-truth label: {r['approval_step_id']}")
    # Approved leave overlaps are expected only for the explicitly labelled scenario.
    by_employee={}
    for r in approved_leave: by_employee.setdefault(r['employee_id'],[]).append(r)
    for employee,rows in by_employee.items():
        rows=sorted(rows,key=lambda x:x['start_date'])
        for i in range(1,len(rows)):
            if rows[i]['start_date']<=rows[i-1]['end_date'] and ('LeaveRequest',rows[i]['leave_request_id']) not in labels:
                errors.append(f"Overlapping approved leave without label: {employee}")
    return errors

if __name__=='__main__':
    folder=sys.argv[1] if len(sys.argv)>1 else 'exports/generated'
    errors=validate(folder)
    result={'valid':not errors,'error_count':len(errors),'errors':errors}
    report_path=Path(folder,'validation_report.json')
    report_path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    manifest_path=Path(folder,'source_manifest.json')
    if manifest_path.exists():
        manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        manifest['files']=[x for x in manifest.get('files',[]) if x.get('file')!='validation_report.json']
        manifest['files'].append({'file':'validation_report.json','sha256':__import__('hashlib').sha256(report_path.read_bytes()).hexdigest(),'bytes':report_path.stat().st_size})
        manifest['files']=sorted(manifest['files'],key=lambda x:x['file'])
        manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('VALID' if not errors else '\n'.join(errors))
    sys.exit(1 if errors else 0)
