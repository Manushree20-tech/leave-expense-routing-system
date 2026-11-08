#!/usr/bin/env python3
import argparse,csv,json,random,hashlib,sqlite3
from pathlib import Path
from datetime import date,timedelta
from decimal import Decimal
from collections import defaultdict

def iso(d): return d.isoformat()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--seed',type=int,default=20261022); ap.add_argument('--employees',type=int,default=400); ap.add_argument('--leave-requests',type=int,default=800); ap.add_argument('--expense-claims',type=int,default=1000); ap.add_argument('--out',default='exports/generated'); a=ap.parse_args()
    rng=random.Random(a.seed); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    employees=[]
    for i in range(1,a.employees+1):
        country='IN' if i%5 else 'US'; role=('PROCESS_OWNER' if i==1 else 'ADMIN' if i==2 else 'OPS_ANALYST' if i==3 else 'APPROVER' if i%23==0 else 'REQUESTER')
        manager=None if i==1 else 'EMP-000001'
        hire=date(2019+(i%6),1+(i%12),1+(i%25))
        employees.append(dict(employee_id=f'EMP-{i:06d}',name=f'Employee {i:03d}',email=f'employee{i:03d}@example.test',country=country,department=['Operations','Finance','Engineering','Sales'][i%4],role=role,manager_id=manager,hire_date=iso(hire),termination_date='',active=True))
    policies=[dict(policy_id=f'LP-{i:02d}',name=n,annual_entitlement=v,country=c,accrual_method='MONTHLY',effective_from='2026-01-01',effective_to='') for i,(n,v,c) in enumerate([('Annual',18,'IN'),('Casual',12,'IN'),('Sick',10,'IN'),('Personal',5,'IN'),('Annual US',15,'US'),('Sick US',10,'US')],1)]
    balances=[]; today=date(2026,10,22)
    for e in employees:
        for p in policies:
            if e['country']==p['country']:
                months=max(0,(today.year-date.fromisoformat(e['hire_date']).year)*12+today.month-date.fromisoformat(e['hire_date']).month+1)
                accr=round(float(p['annual_entitlement'])*min(months,12)/12,2)
                balances.append(dict(balance_id=f"LB-{e['employee_id']}-{p['policy_id']}",employee_id=e['employee_id'],policy_id=p['policy_id'],opening_balance=0,accrued=accr,used=0,available=accr,as_of=iso(today)))
    leave=[]; used=defaultdict(Decimal); approved_spans=defaultdict(list)
    holiday_dates={date(2026,1,1),date(2026,8,15),date(2026,10,2),date(2026,12,25),date(2026,7,4)}
    for i in range(1,a.leave_requests+1):
        e=rng.choice(employees); p=rng.choice([x for x in policies if x['country']==e['country']]); start=date(2026,1,1)+timedelta(days=rng.randrange(0,330)); end=start+timedelta(days=rng.randrange(0,5))
        days=sum(1 for k in range((end-start).days+1) if (start+timedelta(days=k)).weekday()<5 and (start+timedelta(days=k)) not in holiday_dates)
        hire=date.fromisoformat(e['hire_date']); months=max(0,(today.year-hire.year)*12+today.month-hire.month+1)
        accrued=min(Decimal(str(p['annual_entitlement'])),(Decimal(str(p['annual_entitlement']))/Decimal(12)*Decimal(min(months,12))).quantize(Decimal('0.01')))
        key=e['employee_id']
        overlap=any(start<=b and end>=a0 for a0,b in approved_spans[key])
        enough=used[(e['employee_id'],p['policy_id'])]+Decimal(days)<=accrued
        status='APPROVED' if days>0 and enough and not overlap else 'REJECTED'
        if status=='APPROVED':
            used[(e['employee_id'],p['policy_id'])]+=Decimal(days); approved_spans[key].append((start,end))
        leave.append(dict(leave_request_id=f'LVE-2026-{i:06d}',employee_id=e['employee_id'],policy_id=p['policy_id'],start_date=iso(start),end_date=iso(end),business_days=days,reason='Synthetic scenario',status=status,issue_type=''))
    for b in balances:
        b['used']=float(used[(b['employee_id'],b['policy_id'])])
        b['available']=round(float(b['opening_balance'])+float(b['accrued'])-float(b['used']),2)
    centers=[dict(cost_center_id='CC-IN-OPS',name='India Operations',country='IN',budget=500000,spent=0),dict(cost_center_id='CC-US-OPS',name='US Operations',country='US',budget=100000,spent=0)]
    expense_policies=[dict(expense_policy_id=f'EP-{country}-{cat}',country=country,category=cat,per_item_limit=2500 if country=='IN' else 100,claim_limit=10000 if country=='IN' else 1000,receipt_required_above=500 if country=='IN' else 25,effective_from='2026-01-01',effective_to='') for country in ['IN','US'] for cat in ['TRAVEL','MEALS','LODGING','EQUIPMENT','OTHER']]
    approval_rules=[]
    for country in ['IN','US']:
        approval_rules.append(dict(approval_rule_id=f'AR-LEAVE-{country}-MANAGER',request_type='LEAVE',country=country,category='',min_amount=0,max_amount='',approver_role='MANAGER',sequence=1,effective_from='2026-01-01',effective_to='',active=True))
        threshold=5000 if country=='IN' else 500
        for category in ['TRAVEL','MEALS','LODGING','EQUIPMENT','OTHER']:
            approval_rules.append(dict(approval_rule_id=f'AR-EXP-{country}-{category}-MANAGER',request_type='EXPENSE',country=country,category=category,min_amount=0,max_amount='',approver_role='MANAGER',sequence=1,effective_from='2026-01-01',effective_to='',active=True))
            approval_rules.append(dict(approval_rule_id=f'AR-EXP-{country}-{category}-FINANCE',request_type='EXPENSE',country=country,category=category,min_amount=threshold,max_amount='',approver_role='FINANCE',sequence=2,effective_from='2026-01-01',effective_to='',active=True))
    holidays=[dict(country=c,holiday_date=d,name=n) for c,d,n in [('IN','2026-01-01','New Year'),('IN','2026-08-15','Independence Day'),('IN','2026-10-02','Gandhi Jayanti'),('IN','2026-12-25','Christmas'),('US','2026-01-01','New Year'),('US','2026-07-04','Independence Day'),('US','2026-12-25','Christmas')]]
    budget_periods=[dict(cost_center_id='CC-IN-OPS',period_start='2026-01-01',period_end='2026-12-31',budget_amount=500000),dict(cost_center_id='CC-US-OPS',period_start='2026-01-01',period_end='2026-12-31',budget_amount=100000)]
    employee_policies=[dict(employee_id=e['employee_id'],policy_id=p['policy_id'],effective_from='2026-01-01',effective_to='') for e in employees for p in policies if e['country']==p['country']]
    claims=[]; lines=[]; reimburse=[]; approval_steps=[]; used_hash=set(); spent_by_cc=defaultdict(Decimal)
    employee_by_id={e['employee_id']:e for e in employees}
    for lr in leave:
        employee=employee_by_id[lr['employee_id']]
        if employee['manager_id']:
            approval_steps.append(dict(approval_step_id=f"APR-{lr['leave_request_id']}-01",request_type='LEAVE',request_id=lr['leave_request_id'],sequence=1,approver_id=employee['manager_id'],status=lr['status'],issue_type=''))
    for i in range(1,a.expense_claims+1):
        e=rng.choice(employees); d=date(2026,1,1)+timedelta(days=rng.randrange(0,295)); cat=rng.choice(['TRAVEL','MEALS','LODGING','EQUIPMENT','OTHER']); n=rng.randint(1,10); ls=[]; total=Decimal('0')
        for j in range(1,n+1):
            amt=Decimal(rng.randrange(100,50000 if e['country']=='IN' else 1000))/100; total+=amt
            receipt=f"receipt-{i}-{j}.pdf" if rng.random()>.12 else ''
            rh=hashlib.sha256(receipt.encode()).hexdigest() if receipt else ''
            ls.append(dict(expense_line_id=f'EXPL-EXP-2026-{i:06d}-{j:02d}',claim_id=f'EXP-2026-{i:06d}',description=f'{cat.title()} item {j}',category=cat,quantity=1,unit_amount=str(amt),line_total=str(amt),receipt_filename=receipt,receipt_hash=rh,receipt_present=bool(receipt)))
        cc='CC-IN-OPS' if e['country']=='IN' else 'CC-US-OPS'
        per_item_limit=Decimal('2500') if e['country']=='IN' else Decimal('100')
        claim_limit=Decimal('10000') if e['country']=='IN' else Decimal('1000')
        receipt_threshold=Decimal('500') if e['country']=='IN' else Decimal('25')
        policy_ok=total<=claim_limit and all(Decimal(x['line_total'])<=per_item_limit and (Decimal(x['line_total'])<=receipt_threshold or x['receipt_present']) for x in ls)
        budget_ok=spent_by_cc[cc]+total<=Decimal(500000 if e['country']=='IN' else 100000)
        manager=e['manager_id']
        status='APPROVED' if policy_ok and budget_ok and manager else ('PENDING' if policy_ok and budget_ok else 'REJECTED')
        cid=f'EXP-2026-{i:06d}'
        claims.append(dict(expense_claim_id=cid,employee_id=e['employee_id'],cost_center_id=cc,expense_date=iso(d),country=e['country'],category=cat,total_amount=str(total),currency='INR' if e['country']=='IN' else 'USD',status=status,issue_type=''))
        lines.extend(ls)
        if status=='APPROVED':
            approval_steps.append(dict(approval_step_id=f'APR-{cid}-01',request_type='EXPENSE',request_id=cid,sequence=1,approver_id=manager,status='APPROVED',issue_type=''))
            if total>=Decimal('5000'):
                finance=next((x for x in employees if x['country']==e['country'] and x['role']=='APPROVER' and x['department']=='Finance'),None)
                if finance:
                    approval_steps.append(dict(approval_step_id=f'APR-{cid}-02',request_type='EXPENSE',request_id=cid,sequence=2,approver_id=finance['employee_id'],status='APPROVED',issue_type=''))
                else:
                    status='PENDING'; claims[-1]['status']=status
            if status=='APPROVED':
                spent_by_cc[cc]+=total
                reimburse.append(dict(reimbursement_id=f'RMB-2026-{len(reimburse)+1:06d}',claim_id=cid,amount=str(total),currency='INR' if e['country']=='IN' else 'USD',status='PENDING_PAYMENT'))
        elif status=='REJECTED' and manager:
            approval_steps.append(dict(approval_step_id=f'APR-{cid}-01',request_type='EXPENSE',request_id=cid,sequence=1,approver_id=manager,status='REJECTED',issue_type=''))
    for center in centers: center['spent']=float(spent_by_cc[center['cost_center_id']])
    # Inject seven deterministic, labelled exception scenarios after generating the valid baseline.
    truth=[]
    if employees and leave and claims and balances and reimburse:
        # 1. Negative leave balance: deliberately alter a dedicated balance row.
        balances[0]['opening_balance']=0; balances[0]['used']=float(balances[0]['accrued'])+2
        balances[0]['available']=-2; balances[0]['issue_type']='NEGATIVE_LEAVE_BALANCE'
        truth.append(dict(case_id='GT-001',issue_type='NEGATIVE_LEAVE_BALANCE',entity_type='LeaveBalance',entity_id=balances[0]['balance_id'],expected_decision='FLAG_NEGATIVE_BALANCE',description='Available balance is negative after usage.'))
        # 2. Two approved leave spans for the same employee overlap.
        e0=employees[0]['employee_id']; l1,l2=leave[0],leave[1]
        l1.update(employee_id=e0,start_date='2026-05-04',end_date='2026-05-08',status='APPROVED',issue_type='OVERLAPPING_APPROVED_LEAVE')
        l2.update(employee_id=e0,start_date='2026-05-06',end_date='2026-05-11',status='APPROVED',issue_type='OVERLAPPING_APPROVED_LEAVE')
        for other in leave:
            if other['employee_id']==e0 and other['leave_request_id'] not in {l1['leave_request_id'],l2['leave_request_id']}:
                other['status']='REJECTED'
        truth.append(dict(case_id='GT-002',issue_type='OVERLAPPING_APPROVED_LEAVE',entity_type='LeaveRequest',entity_id=l1['leave_request_id'],expected_decision='FLAG_OVERLAP',description='Two approved requests for one employee overlap in date range.'))
        truth.append(dict(case_id='GT-002B',issue_type='OVERLAPPING_APPROVED_LEAVE',entity_type='LeaveRequest',entity_id=l2['leave_request_id'],expected_decision='FLAG_OVERLAP',description='Second member of the deliberately overlapping approved-leave pair.'))
        # 3. Expense date before employee hire date.
        claims[0].update(employee_id=e0,country=employees[0]['country'],cost_center_id='CC-IN-OPS',currency='INR',expense_date='2018-01-01',issue_type='EXPENSE_OUTSIDE_EMPLOYMENT',status='REJECTED')
        truth.append(dict(case_id='GT-003',issue_type='EXPENSE_OUTSIDE_EMPLOYMENT',entity_type='ExpenseClaim',entity_id=claims[0]['expense_claim_id'],expected_decision='REJECT_OR_FLAG',description='Expense date predates employee hire date.'))
        # 4. Two same-employee claims intentionally split below a review threshold.
        split_date='2026-06-15'
        claims[1].update(employee_id=e0,country='IN',cost_center_id='CC-IN-OPS',currency='INR',category='TRAVEL',expense_date=split_date,total_amount='4900.00',issue_type='SPLIT_CLAIMS_THRESHOLD_EVASION',status='REJECTED')
        claims[2].update(employee_id=e0,country='IN',cost_center_id='CC-IN-OPS',currency='INR',category='TRAVEL',expense_date=split_date,total_amount='4900.00',issue_type='SPLIT_CLAIMS_THRESHOLD_EVASION',status='REJECTED')
        for target_claim in [claims[1]['expense_claim_id'], claims[2]['expense_claim_id']]:
            target_lines=[x for x in lines if x['claim_id']==target_claim]
            per_line=Decimal('4900.00')/Decimal(len(target_lines))
            running=Decimal('0.00')
            for ix,line in enumerate(target_lines):
                amount=(Decimal('4900.00')-running) if ix==len(target_lines)-1 else per_line.quantize(Decimal('0.01'))
                running+=amount
                line['unit_amount']=str(amount); line['line_total']=str(amount); line['category']='TRAVEL'
        truth.append(dict(case_id='GT-004',issue_type='SPLIT_CLAIMS_THRESHOLD_EVASION',entity_type='ExpenseClaim',entity_id=claims[1]['expense_claim_id'],expected_decision='FLAG_SPLIT_PATTERN',description='Two related claims total 9800 and are split below a 5000 threshold.'))
        # 5. Missing cost center.
        claims[3].update(cost_center_id='',issue_type='MISSING_COST_CENTER')
        truth.append(dict(case_id='GT-005',issue_type='MISSING_COST_CENTER',entity_type='ExpenseClaim',entity_id=claims[3]['expense_claim_id'],expected_decision='FLAG_MISSING_COST_CENTER',description='Claim has no cost-center assignment.'))
        # 6. Deliberately misconfigured self-approval step, expected to be blocked by application logic.
        approval_steps.append(dict(approval_step_id='APR-SELF-APPROVAL-01',request_type='EXPENSE',request_id=claims[4]['expense_claim_id'],sequence=1,approver_id=claims[4]['employee_id'],status='PENDING',issue_type='REQUESTER_SELF_APPROVAL'))
        truth.append(dict(case_id='GT-006',issue_type='REQUESTER_SELF_APPROVAL',entity_type='ApprovalStep',entity_id='APR-SELF-APPROVAL-01',expected_decision='BLOCK_SELF_APPROVAL',description='Requester is deliberately assigned as approver.'))
        # 7. Duplicate reimbursement for one claim.
        duplicate=reimburse[0].copy(); duplicate['reimbursement_id']=f"RMB-2026-{len(reimburse)+1:06d}"; duplicate['issue_type']='DUPLICATE_REIMBURSEMENT'
        reimburse.append(duplicate)
        truth.append(dict(case_id='GT-007',issue_type='DUPLICATE_REIMBURSEMENT',entity_type='Reimbursement',entity_id=duplicate['reimbursement_id'],expected_decision='FLAG_DUPLICATE_REIMBURSEMENT',description='A second reimbursement references the same claim.'))
        # Ensure exception claims are not treated as clean approved baseline outcomes.
        for bad in claims[:4]:
            bad['status']='REJECTED'
            reimburse[:]=[r for r in reimburse if r['claim_id']!=bad['expense_claim_id']]
            approval_steps[:]=[x for x in approval_steps if x['request_id']!=bad['expense_claim_id']]
        # 8. Duplicate receipt content hash: an intentional labelled anomaly.
        receipt_lines=[x for x in lines if x['receipt_hash']]
        if len(receipt_lines)>=2:
            receipt_lines[1]['receipt_hash']=receipt_lines[0]['receipt_hash']
            receipt_lines[1]['issue_type']='DUPLICATE_RECEIPT_HASH'
            truth.append(dict(case_id='GT-008',issue_type='DUPLICATE_RECEIPT_HASH',entity_type='ExpenseLine',entity_id=receipt_lines[1]['expense_line_id'],expected_decision='FLAG_DUPLICATE_RECEIPT',description='Two line items intentionally share one receipt content hash.'))
        # 9. Policy limit breach: line amount is deliberately above the INR per-item limit.
        breach_claim=claims[5]
        breach_line=next(x for x in lines if x['claim_id']==breach_claim['expense_claim_id'])
        old_amount=Decimal(breach_line['line_total']); new_amount=Decimal('3000.00')
        breach_line['unit_amount']=str(new_amount); breach_line['line_total']=str(new_amount); breach_line['issue_type']='POLICY_LIMIT_BREACH'
        breach_claim['total_amount']=str(Decimal(breach_claim['total_amount'])-old_amount+new_amount); breach_claim['status']='REJECTED'; breach_claim['issue_type']='POLICY_LIMIT_BREACH'
        reimburse[:]=[r for r in reimburse if r['claim_id']!=breach_claim['expense_claim_id']]
        approval_steps[:]=[x for x in approval_steps if x['request_id']!=breach_claim['expense_claim_id']]
        truth.append(dict(case_id='GT-009',issue_type='POLICY_LIMIT_BREACH',entity_type='ExpenseLine',entity_id=breach_line['expense_line_id'],expected_decision='REJECT_POLICY_LIMIT',description='Expense line exceeds the configured country/category per-item policy limit.'))
    datasets={'employees':employees,'leave_policies':policies,'leave_balances':balances,'leave_requests':leave,'expense_policies':expense_policies,'cost_centers':centers,'budget_periods':budget_periods,'employee_policies':employee_policies,'approval_rules':approval_rules,'holidays':holidays,'expense_claims':claims,'expense_lines':lines,'reimbursements':reimburse,'approval_steps':approval_steps}
    # Ground-truth labels are deliberately kept out of feature/input tables.
    for rows in [balances,leave,claims,reimburse,lines,approval_steps]:
        for row in rows: row.pop('issue_type',None)
    for name,rows in datasets.items():
        with open(out/f'{name}.csv','w',newline='',encoding='utf-8') as f:
            if rows:
                w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        (out/f'{name}.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    (out/'ground_truth.json').write_text(json.dumps(truth,indent=2),encoding='utf-8')
    with open(out/'ground_truth.csv','w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(truth[0]));w.writeheader();w.writerows(truth)
    # Portable SQL seed export: one INSERT statement per exported row; identifiers quoted safely.
    sql_lines=['-- Generated deterministic synthetic seed data','-- Review target schema before loading.']
    table_map={'employees':('employee',{'employee_id':'id'}),'leave_policies':('leave_policy',{'policy_id':'id'}),'leave_balances':('leave_balance',{'balance_id':'id'}),'leave_requests':('leave_request',{'leave_request_id':'id'}),'cost_centers':('cost_center',{'cost_center_id':'id'}),'expense_claims':('expense_claim',{'expense_claim_id':'id'}),'expense_lines':('expense_line',{'expense_line_id':'id'}),'reimbursements':('reimbursement',{'reimbursement_id':'id'}),'approval_steps':('approval_step',{'approval_step_id':'id'}),'expense_policies':('expense_policy',{'expense_policy_id':'id'}),'approval_rules':('approval_rule',{'approval_rule_id':'id'}),'holidays':('holiday',{}),'budget_periods':('budget_period',{}),'employee_policies':('employee_policy',{})}
    allowed={'employee':{'id','name','email','country','department','role','manager_id','hire_date','termination_date','active'},
      'leave_policy':{'id','name','annual_entitlement','accrual_method','max_consecutive_days','country','effective_from','effective_to'},
      'leave_balance':{'employee_id','policy_id','opening_balance','accrued','used','available','as_of'},
      'leave_request':{'id','employee_id','policy_id','start_date','end_date','business_days','reason','status'},
      'cost_center':{'id','name','country','budget','spent'},
      'expense_claim':{'id','employee_id','cost_center_id','expense_date','country','category','total_amount','currency','status'},
      'expense_line':{'id','claim_id','description','category','quantity','unit_amount','line_total','receipt_filename','receipt_hash','receipt_present'},
      'reimbursement':{'id','claim_id','amount','currency','status'},
      'approval_step':{'id','request_type','request_id','sequence','approver_id','status'},
      'expense_policy':{'id','country','category','per_item_limit','claim_limit','receipt_required_above','effective_from','effective_to'},
      'approval_rule':{'id','request_type','country','category','min_amount','max_amount','approver_role','sequence','effective_from','effective_to','active'},
      'holiday':{'country','holiday_date','name'},'budget_period':{'cost_center_id','period_start','period_end','budget_amount'},
      'employee_policy':{'employee_id','policy_id','effective_from','effective_to'}}
    for key,rows in datasets.items():
        if not rows or key not in table_map: continue
        table,aliases=table_map[key]
        cols=[(aliases.get(col,col),col) for col in rows[0].keys() if aliases.get(col,col) in allowed[table]]
        for row in rows:
            vals=[]
            for dbcol,col in cols:
                val=row.get(col)
                if val is None or val=='': vals.append('NULL')
                elif isinstance(val,bool): vals.append('1' if val else '0')
                elif isinstance(val,(int,float)): vals.append(str(val))
                else: vals.append("'" + str(val).replace("'","''") + "'")
            sql_lines.append(f"INSERT INTO {table} ({', '.join(dbcol for dbcol,col in cols)}) VALUES ({', '.join(vals)});")
    (out/'seed_data.sql').write_text('\n'.join(sql_lines),encoding='utf-8')
    summary={'seed':a.seed,'counts':{k:len(v) for k,v in datasets.items()},'ground_truth_cases':len(truth)}
    (out/'validation_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    manifest=[]
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name!='source_manifest.json': manifest.append({'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
    (out/'source_manifest.json').write_text(json.dumps({'seed':a.seed,'files':manifest},indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
if __name__=='__main__': main()
