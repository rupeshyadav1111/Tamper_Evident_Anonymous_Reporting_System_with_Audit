from flask import Flask, request, render_template, redirect
from db import get_db
from security import generate_report_id, generate_hash
from audit import log_action

app = Flask(__name__)

# --------------------------------
# Landing Page (Public)
# --------------------------------
@app.route("/", methods=["GET", "POST"])
def landing():
    error = None

    if request.method == "POST":
        token = request.form.get("token")

        if not token:
            error = "Please enter a valid token."
            return render_template("landing.html", error=error)

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT report_id FROM reports WHERE report_id = %s",
            (token,)
        )

        if cursor.fetchone():
            return redirect(f"/messages-ui/{token}")

        error = "Invalid token. Please check and try again."
        return render_template("landing.html", error=error)

    return render_template("landing.html")


# --------------------------------
# UI: Submit Anonymous Report
# --------------------------------
@app.route("/submit-ui", methods=["GET", "POST"])
def submit_ui():
    if request.method == "POST":
        content = request.form.get("content")

        if not content:
            return "Report content is required", 400

        report_id = generate_report_id()
        content_hash = generate_hash(content)

        db = get_db()
        cursor = db.cursor()

        # 🔹 Working copy (editable layer)
        cursor.execute(
            "INSERT INTO reports (report_id, content, content_hash, status) "
            "VALUES (%s, %s, %s, %s)",
            (report_id, content, content_hash, "SUBMITTED")
        )

        # 🔹 Master copy (immutable layer)
        cursor.execute(
            "INSERT INTO master_reports (report_id, original_content, original_hash) "
            "VALUES (%s, %s, %s)",
            (report_id, content, content_hash)
        )

        db.commit()

        log_action(report_id, "REPORT_SUBMITTED", "anonymous_user")

        return render_template("token.html", token=report_id)

    return render_template("submit.html")


# --------------------------------
# UI: User Messages + Status (PRG SAFE)
# --------------------------------
@app.route("/messages-ui/<report_id>", methods=["GET", "POST"])
def messages_ui(report_id):
    db = get_db()
    cursor = db.cursor()

    # Fetch ticket status
    cursor.execute(
        "SELECT status FROM reports WHERE report_id = %s",
        (report_id,)
    )
    row = cursor.fetchone()

    if not row:
        return "Invalid or unknown ticket ID", 404

    status = row[0]

    # POST → insert → redirect
    if request.method == "POST":

        if status == "CLOSED":
            return "This ticket is closed. Messaging is disabled."

        if status == "TAMPERED":
            return "This report was tampered. Please submit a new report."

        msg = request.form.get("message")

        if msg:
            cursor.execute(
                "INSERT INTO messages (report_id, sender, message) VALUES (%s, %s, %s)",
                (report_id, "user", msg)
            )
            db.commit()
            log_action(report_id, "MESSAGE_SENT_BY_USER", "anonymous_user")

        return redirect(f"/messages-ui/{report_id}")

    # GET → fetch messages
    cursor.execute(
        "SELECT sender, message, timestamp FROM messages WHERE report_id = %s",
        (report_id,)
    )
    messages = cursor.fetchall()

    return render_template(
        "messages.html",
        messages=messages,
        status=status
    )


# --------------------------------
# API: Message Endpoint (Optional)
# --------------------------------
@app.route("/message/<report_id>", methods=["POST"])
def send_message_api(report_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT status FROM reports WHERE report_id = %s",
        (report_id,)
    )
    row = cursor.fetchone()

    if not row:
        return "Invalid ticket ID", 404

    status = row[0]

    if status == "CLOSED":
        return "This ticket is closed. Messaging is disabled."

    if status == "TAMPERED":
        return "This report was tampered. Please submit a new report.", 403

    msg = request.form.get("message")
    if not msg:
        return "Message required", 400

    cursor.execute(
        "INSERT INTO messages (report_id, sender, message) VALUES (%s, %s, %s)",
        (report_id, "user", msg)
    )
    db.commit()

    log_action(report_id, "MESSAGE_SENT_BY_USER", "anonymous_user")

    return "Message sent anonymously"


# --------------------------------
# Run Public App
# --------------------------------
if __name__ == "__main__":
    app.run(debug=False)