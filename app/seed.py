from datetime import date
from decimal import Decimal

from . import db
from .models import (
    Employee,
    LeavePolicy,
    ExpensePolicy,
    CostCenter,
    ApprovalRule,
    Holiday,
    BudgetPeriod,
    EmployeePolicy,
)


def seed_reference_data():
    # Avoid inserting reference data more than once.
    if Employee.query.first():
        return

    try:
        # 1. Create employees.
        people = [
            ("EMP-000001", "Asha Rao", "asha@example.test", "IN", "Operations", "PROCESS_OWNER", None, date(2020, 1, 1)),
            ("EMP-000002", "Ravi Kumar", "ravi@example.test", "IN", "Operations", "APPROVER", "EMP-000001", date(2021, 2, 1)),
            ("EMP-000003", "Mira Shah", "mira@example.test", "IN", "Engineering", "REQUESTER", "EMP-000002", date(2022, 3, 1)),
            ("EMP-000004", "John Lee", "john@example.test", "US", "Sales", "REQUESTER", "EMP-000001", date(2022, 5, 1)),
            ("EMP-000005", "Nina Das", "nina@example.test", "IN", "Finance", "APPROVER", "EMP-000001", date(2019, 7, 1)),
            ("EMP-000006", "Omar Ali", "omar@example.test", "US", "Operations", "OPS_ANALYST", "EMP-000001", date(2020, 8, 1)),
            ("EMP-000007", "System Admin", "admin@example.test", "IN", "IT", "ADMIN", None, date(2018, 1, 1)),
            ("EMP-000008", "Liam Carter", "liam@example.test", "US", "Finance", "APPROVER", "EMP-000001", date(2020, 4, 1)),
        ]

        for p in people:
            db.session.add(
                Employee(
                    id=p[0],
                    name=p[1],
                    email=p[2],
                    country=p[3],
                    department=p[4],
                    role=p[5],
                    manager_id=p[6],
                    hire_date=p[7],
                )
            )

        db.session.flush()

        # 2. Create leave policies.
        for i in range(1, 7):
            country = "IN" if i <= 4 else "US"

            policy = LeavePolicy(
                id=f"LP-{i:02d}",
                name=["Annual", "Casual", "Sick", "Personal", "Parental", "Unpaid"][i - 1],
                annual_entitlement=Decimal(
                    [18, 12, 10, 5, 90, 0][i - 1]
                ),
                accrual_method="MONTHLY",
                max_consecutive_days=30,
                country=country,
                effective_from=date(2026, 1, 1),
            )
            db.session.add(policy)

        db.session.flush()

        # 3. Assign leave policies to employees.
        policies = LeavePolicy.query.all()

        for policy in policies:
            employees = Employee.query.filter_by(
                country=policy.country
            ).all()

            for employee in employees:
                db.session.add(
                    EmployeePolicy(
                        employee_id=employee.id,
                        policy_id=policy.id,
                        effective_from=date(2026, 1, 1),
                    )
                )

        # 4. Create expense policies.
        for country in ["IN", "US"]:
            for category in [
                "TRAVEL",
                "MEALS",
                "LODGING",
                "EQUIPMENT",
                "OTHER",
            ]:
                db.session.add(
                    ExpensePolicy(
                        id=f"EP-{country}-{category}",
                        country=country,
                        category=category,
                        per_item_limit=Decimal(
                            "2500" if country == "IN" else "100"
                        ),
                        claim_limit=Decimal(
                            "10000" if country == "IN" else "1000"
                        ),
                        receipt_required_above=Decimal(
                            "500" if country == "IN" else "25"
                        ),
                        effective_from=date(2026, 1, 1),
                    )
                )

        # 5. Create ALL cost centers first.
        cost_centers = [
            ("CC-IN-OPS", "India Operations", "IN", Decimal("500000")),
            ("CC-IN-ENG", "India Engineering", "IN", Decimal("300000")),
            ("CC-US-SALES", "US Sales", "US", Decimal("100000")),
        ]

        for cc in cost_centers:
            db.session.add(
                CostCenter(
                    id=cc[0],
                    name=cc[1],
                    country=cc[2],
                    budget=cc[3],
                    spent=Decimal("0"),
                )
            )

        # Important: insert cost centers before budget periods.
        db.session.flush()

        # 6. Create budget periods after cost centers exist.
        for cc in cost_centers:
            db.session.add(
                BudgetPeriod(
                    cost_center_id=cc[0],
                    period_start=date(2026, 1, 1),
                    period_end=date(2026, 12, 31),
                    budget_amount=cc[3],
                )
            )

        # 7. Create approval rules.
        for country in ["IN", "US"]:
            db.session.add(
                ApprovalRule(
                    id=f"AR-LEAVE-{country}-MANAGER",
                    request_type="LEAVE",
                    country=country,
                    approver_role="MANAGER",
                    sequence=1,
                    effective_from=date(2026, 1, 1),
                    active=True,
                )
            )

            threshold = (
                Decimal("5000")
                if country == "IN"
                else Decimal("500")
            )

            for category in [
                "TRAVEL",
                "MEALS",
                "LODGING",
                "EQUIPMENT",
                "OTHER",
            ]:
                db.session.add(
                    ApprovalRule(
                        id=f"AR-EXP-{country}-{category}-MANAGER",
                        request_type="EXPENSE",
                        country=country,
                        category=category,
                        approver_role="MANAGER",
                        sequence=1,
                        effective_from=date(2026, 1, 1),
                        active=True,
                    )
                )

                db.session.add(
                    ApprovalRule(
                        id=f"AR-EXP-{country}-{category}-FINANCE",
                        request_type="EXPENSE",
                        country=country,
                        category=category,
                        min_amount=threshold,
                        approver_role="FINANCE",
                        sequence=2,
                        effective_from=date(2026, 1, 1),
                        active=True,
                    )
                )

        # 8. Create Indian holidays.
        indian_holidays = [
            (date(2026, 1, 1), "New Year"),
            (date(2026, 8, 15), "Independence Day"),
            (date(2026, 10, 2), "Gandhi Jayanti"),
            (date(2026, 12, 25), "Christmas"),
        ]

        for holiday_date, name in indian_holidays:
            db.session.add(
                Holiday(
                    country="IN",
                    holiday_date=holiday_date,
                    name=name,
                )
            )

        # 9. Create US holidays.
        us_holidays = [
            (date(2026, 1, 1), "New Year"),
            (date(2026, 7, 4), "Independence Day"),
            (date(2026, 12, 25), "Christmas"),
        ]

        for holiday_date, name in us_holidays:
            db.session.add(
                Holiday(
                    country="US",
                    holiday_date=holiday_date,
                    name=name,
                )
            )

        # 10. Save all reference data together.
        db.session.commit()

        print("Reference data seeded successfully.")

    except Exception:
        db.session.rollback()
        raise