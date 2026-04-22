from flask import (
    Flask, render_template, request,
    redirect, session, abort
)
from db import get_db
from security import generate_hash
from audit import log_action
ADMIN_PIN = "4321"
ADMIN_PORT = 7001
app = Flask(__name__)
app.secret_key = "VERY_SECRET_ADMIN_KEY_123"
@app.before_request
def enforce_admin_security():
    if request.endpoint in ("admin_login", "static"):
        return

    if request.remote_addr not in ("127.0.0.1", "::1"):
        abort(403)

    if not session.get("admin"):
        return redirect("/login")

@app.route("/")
def root():
    return "Admin service is running. Use /login"

@app.route("/login", methods=["GET", "POST"])
def admin_login():
    error = None

    if request.method == "POST":
        pin = request.form.get("pin")

        if pin == ADMIN_PIN:
            session.clear()
            session["admin"] = True
            return redirect("/admin")

        error = "Invalid PIN. Access denied."

    return render_template("admin_login.html", error=error)

@app.route("/admin")
def admin_dashboard():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT report_id, status FROM reports")
    reports = cursor.fetchall()

    log_action("ALL", "ADMIN_DASHBOARD_VIEWED", "admin")

    return render_template("admin_dashboard.html", reports=reports)

@app.route("/view/<report_id>")
def view_report(report_id):
    db = get_db()
    cursor = db.cursor()


    cursor.execute(
        "SELECT content, content_hash, status FROM reports WHERE report_id = %s",
        (report_id,)
    )
    row = cursor.fetchone()

    if not row:
        return "Report not found", 404

    content, stored_hash, status = row
    current_hash = generate_hash(content)

    
    if stored_hash != current_hash:

        if status != "TAMPERED":
            cursor.execute(
                "UPDATE reports SET status = 'TAMPERED' WHERE report_id = %s",
                (report_id,)
            )
            db.commit()

            log_action(report_id, "TAMPERING_DETECTED", "system")

        
        cursor.execute(
            "SELECT original_content FROM master_reports WHERE report_id = %s",
            (report_id,)
        )
        master_row = cursor.fetchone()

        original_content = (
            master_row[0] if master_row else "Original data not available"
        )

        return render_template(
            "admin_report_view.html",
            content=original_content,
            report_id=report_id,
            status="TAMPERED"
        )

    if status == "SUBMITTED":
        cursor.execute(
            "UPDATE reports SET status = 'UNDER_REVIEW' WHERE report_id = %s",
            (report_id,)
        )
        db.commit()
        status = "UNDER_REVIEW"

    log_action(report_id, "REPORT_VIEWED", "admin")

    return render_template(
        "admin_report_view.html",
        content=content,
        report_id=report_id,
        status=status
    )

@app.route("/close/<report_id>", methods=["POST"])
def close_ticket(report_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT status FROM reports WHERE report_id = %s",
        (report_id,)
    )
    row = cursor.fetchone()

    if not row:
        return "Invalid report ID", 404

    status = row[0]

    if status in ("CLOSED", "TAMPERED"):
        return redirect(f"/view/{report_id}")

    cursor.execute(
        "UPDATE reports SET status = 'CLOSED' WHERE report_id = %s",
        (report_id,)
    )
    db.commit()

    cursor.execute(
        "INSERT INTO messages (report_id, sender, message) VALUES (%s, %s, %s)",
        (
            report_id,
            "system",
            "Your report has been reviewed and closed by the administrator."
        )
    )
    db.commit()

    log_action(report_id, "REPORT_CLOSED", "admin")

    return redirect(f"/view/{report_id}")

@app.route("/messages/<report_id>", methods=["GET", "POST"])
def view_messages(report_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT status FROM reports WHERE report_id = %s",
        (report_id,)
    )
    row = cursor.fetchone()

    if not row:
        return "Invalid report ID", 404

    status = row[0]

    if status == "TAMPERED":
        return redirect(f"/view/{report_id}")

    if request.method == "POST":
        msg = request.form.get("message")

        if msg and status != "CLOSED":
            cursor.execute(
                "INSERT INTO messages (report_id, sender, message) VALUES (%s, %s, %s)",
                (report_id, "admin", msg)
            )
            db.commit()
            log_action(report_id, "MESSAGE_SENT_BY_ADMIN", "admin")

        return redirect(f"/messages/{report_id}")

    cursor.execute(
        "SELECT sender, message, timestamp FROM messages WHERE report_id = %s",
        (report_id,)
    )
    rows = cursor.fetchall()

    log_action(report_id, "MESSAGES_VIEWED", "admin")

    return render_template(
        "admin_messages.html",
        messages=rows,
        report_id=report_id
    )
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=ADMIN_PORT,
        debug=False,
        use_reloader=False
    )