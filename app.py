import random
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))
import llm_agent
from pipeline import process_email, THRESHOLD
from store import get_by_status, review, stats, all_emails, reset

st.set_page_config(page_title="PhishGuard", layout="wide")
st.title("PhishGuard: real-time phishing detection")

REAL_EMAILS = Path("data/emails_test.csv")
TEMPLATES = [
    ("Account notice", "Hello, please review the activity on your account here: {url}"),
    ("Action required", "We noticed something unusual. Please confirm your details: {url}"),
    ("Your order", "Thanks for your purchase. Track your package here: {url}"),
    ("Security alert", "Sign-in attempt detected. Check it here: {url}"),
]
SENDERS = ["support@mail-service.com", "no-reply@notify.net", "info@updates.org", "team@alerts.io"]


@st.cache_data
def load_test():
    return pd.read_csv("data/test.csv")


@st.cache_data
def load_real():
    return pd.read_csv(REAL_EMAILS).fillna("")


def send_random(n, use_llm, source):
    if source == "Real emails" and REAL_EMAILS.exists():
        df = load_real()
        for _, r in df.sample(min(n, len(df))).iterrows():
            process_email(r["sender"] or "unknown", r["subject"] or "(no subject)", r["body"],
                          true_label=int(r["label"]), use_llm=use_llm)
    else:
        test = load_test()
        for _, row in test.sample(n).iterrows():
            subject, tmpl = random.choice(TEMPLATES)
            process_email(random.choice(SENDERS), subject, tmpl.format(url=row["url"]),
                          url=row["url"], true_label=int(row["label"]), use_llm=use_llm)
    st.session_state["llm_error"] = llm_agent.last_error if use_llm else None


# ---------- sidebar ----------
s = stats()
st.sidebar.header("Live stats")
st.sidebar.metric("Delivered", s.get("delivered", 0))
st.sidebar.metric("Quarantined (waiting)", s.get("quarantined", 0))
st.sidebar.metric("Blocked (confirmed)", s.get("blocked", 0))
st.sidebar.metric("Released (overridden)", s.get("released", 0))
st.sidebar.caption(f"Quarantine threshold: {THRESHOLD}")

st.sidebar.divider()
st.sidebar.header("LLM layer")
if llm_agent.llm_available():
    st.sidebar.success(f"Groq ready: {llm_agent.MODEL}")
else:
    st.sidebar.warning("GROQ_API_KEY not found. Running URL-only.")
use_llm = st.sidebar.checkbox("Use LLM layer", value=llm_agent.llm_available(),
                              disabled=not llm_agent.llm_available())
sources = ["URL test set"] + (["Real emails"] if REAL_EMAILS.exists() else [])
source = st.sidebar.radio("Simulator email source", sources)
if len(sources) == 1:
    st.sidebar.caption("Add data/emails_test.csv (see prepare_emails.py) to simulate real email text.")

st.sidebar.divider()
auto = st.sidebar.checkbox("Auto-stream incoming emails (demo)")
if st.sidebar.button("Clear all data"):
    reset()
    st.rerun()

if st.session_state.get("llm_error"):
    st.warning(f"LLM call failed, so the last email was scored by the URL model only: "
               f"{st.session_state['llm_error']}")
if st.session_state.get("last_result"):
    st.success(st.session_state.pop("last_result"))

# ---------- simulator ----------
st.subheader("Incoming mail simulator")
c1, c2, c3 = st.columns([1, 1, 3])
if c1.button("Send 1 random email"):
    send_random(1, use_llm, source)
    st.rerun()
if c2.button("Send 10 emails"):
    send_random(10, use_llm, source)
    st.rerun()

with st.expander("Or send your own email"):
    with st.form("custom"):
        sender = st.text_input("Sender", "security@paypa1-support.com")
        subject = st.text_input("Subject", "Your account is suspended")
        body = st.text_area("Body (include a link)",
                            "We detected unusual activity. Verify your password within 24 hours: "
                            "http://paypal.account-verify.xyz/signin")
        if st.form_submit_button("Process email"):
            out = process_email(sender, subject, body, use_llm=use_llm)
            txt = f"{out['text_risk']:.2f}" if out["text_risk"] is not None else "not used"
            st.session_state["last_result"] = (
                f"Result: {out['status']} | final score {out['score']:.2f} "
                f"(URL {out['url_score']:.2f}, email text {txt}) | {out['ms']:.0f} ms")
            st.session_state["llm_error"] = llm_agent.last_error if use_llm else None
            st.rerun()

st.divider()

# ---------- tabs ----------
tab1, tab2 = st.tabs(["Quarantine queue", "Full log"])

with tab1:
    queue = get_by_status("quarantined")
    if not queue:
        st.info("No emails waiting for review.")
    for e in queue:
        subj = e["subject"] or "(no subject)"
        with st.expander(f"Score {e['score']:.2f}  |  {subj[:50]}  |  {(e['url'] or 'no link')[:60]}"):
            m1, m2, m3 = st.columns(3)
            m1.metric("Final score", f"{e['score']:.2f}")
            m2.metric("URL model", f"{e['url_score']:.2f}" if e["url_score"] is not None else "n/a")
            m3.metric("Email text (LLM)", f"{e['text_risk']:.2f}" if e["text_risk"] is not None else "not used")

            if e["llm_summary"]:
                st.markdown("**AI explanation**")
                st.text(e["llm_summary"])
            st.markdown("**Flags**")
            st.text(e["reasons"])
            # st.text (not st.write) so links inside a phishing email are never clickable
            st.markdown("**Email**")
            st.text(f"From: {e['sender']}\nSubject: {subj}\n\n{(e['body'] or '')[:1500]}")

            b1, b2, _ = st.columns([1, 1, 4])
            if b1.button("Confirm phishing", key=f"c{e['id']}"):
                review(e["id"], "confirm")
                st.rerun()
            if b2.button("Override: release", key=f"o{e['id']}"):
                review(e["id"], "override")
                st.rerun()

with tab2:
    log = pd.DataFrame(all_emails())
    if log.empty:
        st.info("Nothing processed yet.")
    else:
        cols = ["id", "created_at", "subject", "url", "score", "url_score", "text_risk", "status",
                "reviewer_action", "true_label", "processing_ms"]
        st.dataframe(log[cols].iloc[::-1], use_container_width=True, hide_index=True)

# ---------- auto stream ----------
if auto:
    time.sleep(3 if use_llm else 2)
    send_random(1, use_llm, source)
    st.rerun()