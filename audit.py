from db import get_db

def log_action(report_id, action, actor):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO audit_logs (report_id, action, actor) VALUES (%s, %s, %s)",
        (report_id, action, actor)
    )
    db.commit()
