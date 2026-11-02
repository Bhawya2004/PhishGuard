from pathlib import Path

import joblib
import pandas as pd

from features import extract_features

ROOT = Path(__file__).resolve().parent.parent
_bundle = joblib.load(ROOT / "models" / "detector.joblib")
_model, _columns = _bundle["model"], _bundle["columns"]


def _reasons(f: dict) -> list:
    r = []
    if f["has_ip_host"]:
        r.append("Link uses a raw IP address")
    if f["has_at"]:
        r.append("URL contains '@' symbol")
    if f["suspicious_tld"]:
        r.append("Suspicious domain ending")
    if f["brand_in_subdomain"]:
        r.append("Brand name used in subdomain")
    if f["is_shortener"]:
        r.append("URL shortener hides destination")
    if f["suspicious_word_count"] >= 2:
        r.append(f"{f['suspicious_word_count']} phishing keywords (login, verify...)")
    if f["num_subdomains"] >= 3:
        r.append("Many subdomains")
    if f["url_length"] > 75:
        r.append("Unusually long URL")
    if not f["uses_https"]:
        r.append("No HTTPS")
    if f["domain_hyphens"] >= 2:
        r.append("Many hyphens in domain")
    return r or ["Pattern matches known phishing URLs (model score)"]


def score_url(url: str):
    """Returns (phishing_probability, list_of_reasons)."""
    feats = extract_features(url)
    X = pd.DataFrame([feats])[_columns]
    prob = float(_model.predict_proba(X)[0][1])
    return prob, _reasons(feats)