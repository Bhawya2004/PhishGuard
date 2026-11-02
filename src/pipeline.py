import json
import re
import time

from detector import score_url
from llm_agent import analyze_email, flags
from store import add_email, init_db

THRESHOLD = 0.7
URL_RE = re.compile(r"https?://[^\s<>\"']+")


def combine(url_score: float, text_risk) -> float:
    """The LLM can only raise the risk, never lower it (so it cannot release an email)."""
    if text_risk is None:
        return url_score
    return max(url_score, text_risk)


def process_email(sender, subject, body, url=None, true_label=None,
                  threshold=THRESHOLD, use_llm=True):
    """Runs one email through the full pipeline and returns the saved record info."""
    start = time.perf_counter()

    # Agent 1: find the links in the email
    urls = [url] if url else URL_RE.findall(body or "")

    # Agent 2: URL model scores every link, keep the riskiest
    results = [score_url(u) for u in urls if u]
    url_score, reasons = max(results, key=lambda r: r[0]) if results else (0.0, ["No links found"])

    # Agent 3: LLM reads the email text (optional, falls back to URL-only if it fails)
    text_risk, summary, fields = None, None, None
    if use_llm:
        llm = analyze_email(sender, subject, body, urls)
        if llm:
            text_risk, summary, fields = llm["text_risk"], llm["explanation"], llm
            reasons = reasons + flags(llm)

    # Agent 4: decision
    score = combine(url_score, text_risk)
    status = "quarantined" if score >= threshold else "delivered"

    ms = (time.perf_counter() - start) * 1000
    email_id = add_email(sender, subject, body, urls[0] if urls else "", score, reasons, status,
                         true_label, ms, url_score=url_score, text_risk=text_risk,
                         llm_summary=summary, llm_fields=json.dumps(fields) if fields else None)
    return {"id": email_id, "score": score, "url_score": url_score, "text_risk": text_risk,
            "summary": summary, "status": status, "reasons": reasons, "ms": ms}


init_db()