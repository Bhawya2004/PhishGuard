import re
import math
from collections import Counter
from urllib.parse import urlparse

import pandas as pd
import tldextract

# offline mode: uses the suffix list bundled with the package, no network needed
_extract = tldextract.TLDExtract(suffix_list_urls=())

SUSPICIOUS_WORDS = [
    "login", "signin", "verify", "update", "secure", "account", "bank",
    "confirm", "password", "suspend", "wallet", "paypal", "billing", "unlock",
]
SHORTENERS = {"bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd", "buff.ly", "cutt.ly"}
SUSPICIOUS_TLDS = {"xyz", "top", "tk", "ml", "ga", "cf", "gq", "click", "link", "work", "support", "zip"}
IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


def _entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def extract_features(url: str) -> dict:
    url = str(url).strip()
    parsed = urlparse(url if "://" in url else "http://" + url)
    host = (parsed.hostname or "").lower()
    path = parsed.path or ""
    query = parsed.query or ""
    ext = _extract(url)
    registered = f"{ext.domain}.{ext.suffix}" if ext.suffix else ext.domain
    lowered = url.lower()

    return {
        # length features
        "url_length": len(url),
        "host_length": len(host),
        "path_length": len(path),
        "query_length": len(query),
        # character counts
        "num_dots": url.count("."),
        "num_hyphens": url.count("-"),
        "num_underscores": url.count("_"),
        "num_slashes": url.count("/"),
        "num_digits": sum(c.isdigit() for c in url),
        "digit_ratio": sum(c.isdigit() for c in url) / max(len(url), 1),
        "num_params": query.count("&") + (1 if query else 0),
        "num_percent": url.count("%"),
        # structure flags
        "has_at": int("@" in url),
        "has_ip_host": int(bool(IP_RE.match(host))),
        "uses_https": int(parsed.scheme == "https"),
        "has_port": int(parsed.port is not None) if _safe_port(parsed) else 0,
        "double_slash_in_path": int("//" in path),
        # domain features
        "num_subdomains": len([p for p in ext.subdomain.split(".") if p]),
        "subdomain_length": len(ext.subdomain),
        "domain_has_digit": int(any(c.isdigit() for c in ext.domain)),
        "domain_hyphens": ext.domain.count("-"),
        "suspicious_tld": int(ext.suffix.split(".")[-1] in SUSPICIOUS_TLDS),
        "is_shortener": int(registered in SHORTENERS),
        "host_entropy": _entropy(host),
        # keyword features
        "suspicious_word_count": sum(w in lowered for w in SUSPICIOUS_WORDS),
        "brand_in_subdomain": int(any(w in ext.subdomain.lower() for w in ["paypal", "apple", "google", "microsoft", "amazon", "bank"])),
        # path features
        "path_depth": len([p for p in path.split("/") if p]),
    }


def _safe_port(parsed) -> bool:
    try:
        parsed.port
        return True
    except ValueError:
        return False


def build_matrix(df: pd.DataFrame):
    X = pd.DataFrame([extract_features(u) for u in df["url"]])
    y = df["label"].values
    return X, y


if __name__ == "__main__":
    for name in ["train", "val", "test"]:
        df = pd.read_csv(f"data/{name}.csv")
        X, y = build_matrix(df)
        X["label"] = y
        X.to_csv(f"data/{name}_features.csv", index=False)
        print(name, X.shape)