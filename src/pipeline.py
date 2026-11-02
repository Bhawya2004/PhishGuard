import re
import time

from detector import score_url
from store import add_email, init_db

THRESHOLD = 0.7
URL_RE = re.compile(r"https?://[^\s<>\"']+")


def process_email(sender, subject, body, url=None, true_label=None, threshold=THRESHOLD):
    """Runs one email through the full pipeline and returns the saved record info."""
    start = time.perf_counter()

    # Agent 1: find the links in the email
    urls = [url] if url else URL_RE.findall(body)
    if not urls:
        urls = [""]

    # Agent 2: score every link, keep the riskiest
    results = [score_url(u) for u in urls if u]
    score, reasons = max(results, key=lambda r: r[0]) if results else (0.0, ["No links found"])

    # Agent 3: decision
    status = "quarantined" if score >= threshold else "delivered"

    ms = (time.perf_counter() - start) * 1000
    email_id = add_email(sender, subject, body, urls[0], score, reasons, status, true_label, ms)
    return {"id": email_id, "score": score, "status": status, "reasons": reasons, "ms": ms}


init_db()