from datetime import date
from app import create_app
from app.models import Employee, LeavePolicy
from app.services import business_days

def test_business_days_excludes_seeded_holiday():
    app=create_app({'TESTING':True,'SQLALCHEMY_DATABASE_URI':'sqlite://'})
    with app.app_context():
        assert business_days(date(2025,12,29),date(2026,1,2),'IN')==4

def test_seeded_actors_and_policies():
    app=create_app({'TESTING':True,'SQLALCHEMY_DATABASE_URI':'sqlite://'})
    with app.app_context():
        assert Employee.query.count()==8
        assert LeavePolicy.query.count()==6
        assert {e.role for e in Employee.query.all()} >= {'PROCESS_OWNER','APPROVER','OPS_ANALYST','ADMIN'}
