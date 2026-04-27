# Tamper Evident Anonymous Reporting System with Audit

## Overview

This project is a secure anonymous reporting system designed to detect tampering using audit logs and hashing mechanisms.
It provides two interfaces within the same application:

1. Public Interface — for submitting anonymous reports
2. Admin Interface — for managing and auditing reports

Both interfaces share the same database and security logic.

---

## Project Structure

public_app.py — Public reporting interface
admin_app.py — Admin dashboard interface
db.py — Database connection logic
audit.py — Audit logging and tamper detection
security.py — Security and hashing functions
templates/ — HTML templates
static/ — CSS / JS files

---

## Installation

1. Clone the repository

git clone (https://github.com/rupeshyadav1111/Tamper_Evident_Anonymous_Reporting_System_with_Audit)

2. Navigate to project folder

cd tamper_evident_reporting

3. Create virtual environment

python -m venv venv

4. Activate virtual environment

Windows:

venv\Scripts\activate

5. Install dependencies

pip install -r requirements.txt

---

## Environment Configuration

Create a `.env` file in the project root:

DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=your_database_name

---

## Running the Application

### Run Public Interface

python public_app.py

Then open:

http://127.0.0.1:5000

---

### Run Admin Interface

python admin_app.py

Then open:

http://127.0.0.1:7001

---

## Security Note

Sensitive credentials are stored in the `.env` file and are not included in the repository.

---

## Author

KAMBALA RUPESHWAR
