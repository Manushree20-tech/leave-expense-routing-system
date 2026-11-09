-- Complete MySQL 8+ schema for Leave and Expense Routing System

CREATE DATABASE IF NOT EXISTS leave_expense_full_dataset
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE leave_expense_full_dataset;

CREATE TABLE IF NOT EXISTS employee (
 id VARCHAR(20) PRIMARY KEY,
 name VARCHAR(120) NOT NULL,
 email VARCHAR(160) NOT NULL UNIQUE,
 country CHAR(2) NOT NULL,
 department VARCHAR(80) NOT NULL,
 role VARCHAR(30) NOT NULL,
 manager_id VARCHAR(20) NULL,
 hire_date DATE NOT NULL,
 termination_date DATE NULL,
 active BOOLEAN NOT NULL DEFAULT TRUE,
 CONSTRAINT fk_employee_manager FOREIGN KEY(manager_id) REFERENCES employee(id),
 CONSTRAINT chk_employee_dates CHECK(termination_date IS NULL OR termination_date >= hire_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS leave_policy (
 id VARCHAR(20) PRIMARY KEY,
 name VARCHAR(80) NOT NULL,
 annual_entitlement DECIMAL(8,2) NOT NULL,
 accrual_method VARCHAR(20) NOT NULL,
 max_consecutive_days INT NULL,
 country CHAR(2) NOT NULL,
 effective_from DATE NOT NULL,
 effective_to DATE NULL,
 CHECK(annual_entitlement >= 0),
 CHECK(effective_to IS NULL OR effective_to >= effective_from)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS leave_balance (
 id INT AUTO_INCREMENT PRIMARY KEY,
 employee_id VARCHAR(20) NOT NULL,
 policy_id VARCHAR(20) NOT NULL,
 opening_balance DECIMAL(8,2) NOT NULL DEFAULT 0,
 accrued DECIMAL(8,2) NOT NULL DEFAULT 0,
 used DECIMAL(8,2) NOT NULL DEFAULT 0,
 available DECIMAL(8,2) NOT NULL DEFAULT 0,
 as_of DATE NOT NULL,
 UNIQUE KEY uq_leave_balance(employee_id,policy_id,as_of),
 FOREIGN KEY(employee_id) REFERENCES employee(id),
 FOREIGN KEY(policy_id) REFERENCES leave_policy(id),
 CHECK(available = opening_balance + accrued - used)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS leave_request (
 id VARCHAR(30) PRIMARY KEY,
 employee_id VARCHAR(20) NOT NULL,
 policy_id VARCHAR(20) NOT NULL,
 start_date DATE NOT NULL,
 end_date DATE NOT NULL,
 business_days INT NOT NULL,
 reason VARCHAR(500),
 status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
 created_at DATETIME,
 issue_type VARCHAR(60),
 FOREIGN KEY(employee_id) REFERENCES employee(id),
 FOREIGN KEY(policy_id) REFERENCES leave_policy(id),
 CHECK(end_date >= start_date),
 CHECK(business_days >= 0),
 CHECK(status IN ('PENDING','APPROVED','REJECTED'))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS expense_policy (
 id VARCHAR(20) PRIMARY KEY,
 country CHAR(2) NOT NULL,
 category VARCHAR(40) NOT NULL,
 per_item_limit DECIMAL(12,2) NOT NULL,
 claim_limit DECIMAL(12,2) NOT NULL,
 receipt_required_above DECIMAL(12,2) NOT NULL,
 effective_from DATE NOT NULL,
 effective_to DATE NULL,
 UNIQUE KEY uq_expense_policy(country,category,effective_from),
 CHECK(per_item_limit >= 0 AND claim_limit >= 0 AND receipt_required_above >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS cost_center (
 id VARCHAR(20) PRIMARY KEY,
 name VARCHAR(100) NOT NULL,
 country CHAR(2) NOT NULL,
 budget DECIMAL(14,2) NOT NULL,
 spent DECIMAL(14,2) NOT NULL DEFAULT 0,
 owner_employee_id VARCHAR(20) NULL,
 FOREIGN KEY(owner_employee_id) REFERENCES employee(id),
 CHECK(budget >= 0 AND spent >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS expense_claim (
 id VARCHAR(30) PRIMARY KEY,
 employee_id VARCHAR(20) NOT NULL,
 cost_center_id VARCHAR(20) NULL,
 expense_date DATE NOT NULL,
 country CHAR(2) NOT NULL,
 category VARCHAR(40) NOT NULL,
 total_amount DECIMAL(14,2) NOT NULL,
 currency CHAR(3) NOT NULL,
 status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
 created_at DATETIME,
 issue_type VARCHAR(60),
 FOREIGN KEY(employee_id) REFERENCES employee(id),
 FOREIGN KEY(cost_center_id) REFERENCES cost_center(id),
 CHECK(total_amount >= 0),
 CHECK(status IN ('PENDING','APPROVED','REJECTED'))
) ENGINE=InnoDB;

-- FIXED: issue_type appears only once

CREATE TABLE IF NOT EXISTS expense_line (
 id VARCHAR(50) PRIMARY KEY,
 claim_id VARCHAR(30) NOT NULL,
 description VARCHAR(200) NOT NULL,
 category VARCHAR(40) NOT NULL,
 quantity DECIMAL(10,2) NOT NULL,
 unit_amount DECIMAL(14,2) NOT NULL,
 line_total DECIMAL(14,2) NOT NULL,
 receipt_filename VARCHAR(255) NULL,
 receipt_hash CHAR(64) NULL,
 receipt_present BOOLEAN NOT NULL DEFAULT FALSE,
 issue_type VARCHAR(60) NULL,
 FOREIGN KEY(claim_id) REFERENCES expense_claim(id),
 INDEX ix_receipt_hash(receipt_hash),
 CHECK(quantity > 0 AND unit_amount >= 0 AND line_total = quantity * unit_amount)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS approval_rule (
 id VARCHAR(30) PRIMARY KEY,
 request_type VARCHAR(20) NOT NULL,
 country CHAR(2) NULL,
 category VARCHAR(40) NULL,
 min_amount DECIMAL(14,2) DEFAULT 0,
 max_amount DECIMAL(14,2) NULL,
 approver_role VARCHAR(30) NOT NULL,
 sequence INT NOT NULL,
 effective_from DATE NOT NULL,
 effective_to DATE NULL,
 active BOOLEAN NOT NULL DEFAULT TRUE,
 CHECK(request_type IN ('LEAVE','EXPENSE')),
 CHECK(max_amount IS NULL OR max_amount >= min_amount)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS approval_step (
 id VARCHAR(60) PRIMARY KEY,
 request_type VARCHAR(20) NOT NULL,
 request_id VARCHAR(30) NOT NULL,
 sequence INT NOT NULL,
 approver_id VARCHAR(20) NOT NULL,
 status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
 decision_reason VARCHAR(500),
 decided_at DATETIME,
 rule_id VARCHAR(30) NULL,
 UNIQUE KEY uq_approval_step(request_type,request_id,sequence),
 FOREIGN KEY(approver_id) REFERENCES employee(id),
 FOREIGN KEY(rule_id) REFERENCES approval_rule(id),
 CHECK(status IN ('PENDING','APPROVED','REJECTED'))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reimbursement (
 id VARCHAR(30) PRIMARY KEY,
 claim_id VARCHAR(30) NOT NULL UNIQUE,
 amount DECIMAL(14,2) NOT NULL,
 currency CHAR(3) NOT NULL,
 status VARCHAR(20) NOT NULL DEFAULT 'PENDING_PAYMENT',
 created_at DATETIME,
 paid_at DATETIME,
 FOREIGN KEY(claim_id) REFERENCES expense_claim(id),
 CHECK(amount >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS state_event (
 id INT AUTO_INCREMENT PRIMARY KEY,
 entity_type VARCHAR(30) NOT NULL,
 entity_id VARCHAR(50) NOT NULL,
 from_state VARCHAR(30) NULL,
 to_state VARCHAR(30) NOT NULL,
 actor_id VARCHAR(20) NULL,
 reason VARCHAR(500),
 occurred_at DATETIME NOT NULL,
 FOREIGN KEY(actor_id) REFERENCES employee(id),
 INDEX ix_event_entity(entity_type,entity_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS holiday (
 id INT AUTO_INCREMENT PRIMARY KEY,
 country CHAR(2) NOT NULL,
 holiday_date DATE NOT NULL,
 name VARCHAR(100) NOT NULL,
 UNIQUE KEY uq_holiday(country,holiday_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS budget_period (
 id INT AUTO_INCREMENT PRIMARY KEY,
 cost_center_id VARCHAR(20) NOT NULL,
 period_start DATE NOT NULL,
 period_end DATE NOT NULL,
 budget_amount DECIMAL(14,2) NOT NULL,
 UNIQUE KEY uq_budget_period(cost_center_id,period_start,period_end),
 FOREIGN KEY(cost_center_id) REFERENCES cost_center(id),
 CHECK(period_end >= period_start)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS employee_policy (
 id INT AUTO_INCREMENT PRIMARY KEY,
 employee_id VARCHAR(20) NOT NULL,
 policy_id VARCHAR(20) NOT NULL,
 effective_from DATE NOT NULL,
 effective_to DATE NULL,
 UNIQUE KEY uq_employee_policy(employee_id,policy_id,effective_from),
 FOREIGN KEY(employee_id) REFERENCES employee(id),
 FOREIGN KEY(policy_id) REFERENCES leave_policy(id),
 CHECK(effective_to IS NULL OR effective_to >= effective_from)
) ENGINE=InnoDB;