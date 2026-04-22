import hashlib
import uuid

def generate_report_id():
    return str(uuid.uuid4())

def generate_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()
