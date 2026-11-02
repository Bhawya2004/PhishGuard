# PhishGuard — Real-Time Phishing Detection
## Implementation Plan (SIH25159)

**Tech Stack Chosen (recommended defaults):**
- Detection Brain: **Hybrid** — ML model (URL/technical features) + LLM (content/context reasoning)
- Dashboard: **Streamlit**
- Storage: **SQLite**
- Language: **Python**

---

## 1. Project Overview

PhishGuard is an agentic pipeline that:
1. Ingests emails/messages
2. Automatically analyzes them for phishing signals
3. Scores and classifies them (Safe / Suspicious / Phishing)
4. Auto-flags or quarantines likely phishing
5. Routes uncertain/flagged cases to a **human reviewer**
6. Lets the human **override** the AI's decision
7. Logs everything and produces a **confusion matrix** on test data

---

## 2. System Architecture

```
                 ┌─────────────────┐
                 │   Email Input    │  (PhishTank + Ham dataset)
                 └────────┬─────────┘
                          │
                 ┌────────▼─────────┐
                 │  Preprocessing    │  (parse headers, body, URLs)
                 │  & Feature        │
                 │  Extraction       │
                 └────────┬─────────┘
                          │
          ┌───────────────┴───────────────┐
          │                                │
 ┌────────▼────────┐            ┌──────────▼─────────┐
 │  ML Classifier    │            │   LLM Content        │
 │  (URL/technical    │            │   Reasoning Agent    │
 │   features)         │            │   (tone, urgency,    │
 └────────┬────────┘            │   link-text mismatch)│
          │                     └──────────┬─────────┘
          └───────────────┬───────────────┘
                          │
                 ┌────────▼─────────┐
                 │  Decision Engine  │  (combine scores → risk level)
                 └────────┬─────────┘
                          │
            ┌─────────────┼─────────────┐
            │              │              │
     ┌──────▼─────┐ ┌──────▼──────┐ ┌────▼─────┐
     │   Safe      │ │  Suspicious  │ │ Phishing  │
     │  (Allow)    │ │ (→ Human     │ │(Quarantine│
     │             │ │  Review)     │ │ + Human   │
     │             │ │              │ │  Review)  │
     └─────────────┘ └──────┬──────┘ └────┬─────┘
                             │              │
                     ┌───────▼──────────────▼───────┐
                     │   Human Reviewer Dashboard     │
                     │   (Streamlit)                   │
                     │   - View flagged email + score  │
                     │   - Confirm / Override           │
                     └───────────────┬────────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │   SQLite Database     │
                          │   (logs all decisions │
                          │   + overrides)          │
                          └──────────┬──────────┘
                                     │
                          ┌──────────▼──────────┐
                          │  Evaluation Module     │
                          │  (Confusion Matrix,    │
                          │  Precision/Recall/F1)  │
                          └────────────────────────┘
```

---

## 3. Phased Implementation Plan

### **Phase 1 — Setup & Data (Day 1)**
- [ ] Set up Python environment (venv/conda)
- [ ] Download PhishTank dataset (phishing URLs, CSV format)
- [ ] Download a legitimate/"ham" email dataset (e.g., Enron or SpamAssassin) for contrast
- [ ] Clean & merge into a single labeled dataset: `label = phishing/legit`
- [ ] Do a train/test split (e.g., 80/20), keep test set aside for final confusion matrix

**Deliverable:** `dataset.csv` with columns like `sender, subject, body, url, label`

---

### **Phase 2 — Feature Extraction (Day 1–2)**
- [ ] Extract URL-based features:
  - URL length, number of subdomains, use of IP address instead of domain
  - Presence of HTTPS, use of URL shorteners
  - Domain age / WHOIS lookup (if time permits)
  - Special characters, "@" symbol tricks
- [ ] Extract text-based features:
  - Urgency keywords ("verify now", "account suspended", "click immediately")
  - Spelling/grammar anomalies
  - Mismatched display text vs actual link (`<a>` text vs href)
  - Sender domain vs claimed organization mismatch

**Deliverable:** `feature_extractor.py`

---

### **Phase 3 — ML Classifier (Day 2)**
- [ ] Train a classic ML model (Logistic Regression or Random Forest or XGBoost) on extracted features
- [ ] Evaluate with cross-validation
- [ ] Save trained model (`model.pkl`)

**Deliverable:** `train_model.py`, `model.pkl`

---

### **Phase 4 — LLM Reasoning Agent (Day 2–3)**
- [ ] Write a prompt template that gives the LLM the email content and asks it to reason about:
  - Social engineering tactics used
  - Whether tone/urgency looks suspicious
  - A risk score (0–100) with justification
- [ ] Call LLM API (e.g., Claude API) per email, parse structured JSON response
- [ ] Combine with ML model score → final weighted risk score

**Deliverable:** `llm_agent.py`

---

### **Phase 5 — Decision Engine (Day 3)**
- [ ] Define thresholds:
  - Score < 30 → Safe (auto-allow)
  - Score 30–70 → Suspicious (send to human review)
  - Score > 70 → Phishing (auto-quarantine + send to human review)
- [ ] Implement quarantine logic (move email status to `quarantined` in DB, don't delete)

**Deliverable:** `decision_engine.py`

---

### **Phase 6 — Database & Logging (Day 3)**
- [ ] Design SQLite schema:

```sql
CREATE TABLE emails (
    id INTEGER PRIMARY KEY,
    sender TEXT,
    subject TEXT,
    body TEXT,
    url TEXT,
    ml_score REAL,
    llm_score REAL,
    final_score REAL,
    ai_decision TEXT,       -- Safe / Suspicious / Phishing
    human_decision TEXT,    -- Pending / Confirmed / Overridden-Safe
    reviewed_by TEXT,
    timestamp DATETIME
);
```
- [ ] Every pipeline run inserts a row
- [ ] Every human action updates `human_decision` + `reviewed_by`

**Deliverable:** `database.py`

---

### **Phase 7 — Human Review Dashboard (Day 3–4)**
- [ ] Build Streamlit app:
  - Table/list of flagged & suspicious emails
  - Click an email → see full content, AI score, reasoning
  - Buttons: "Confirm Phishing" / "Mark as Safe (Override)"
  - Show stats: total flagged, total overridden, accuracy so far
- [ ] Connect to SQLite DB for live updates

**Deliverable:** `dashboard.py`

---

### **Phase 8 — Evaluation & Confusion Matrix (Day 4)**
- [ ] Run the full pipeline on the held-out test dataset
- [ ] Compare `ai_decision` vs actual `label` from dataset
- [ ] Generate confusion matrix using scikit-learn:

```python
from sklearn.metrics import confusion_matrix, classification_report
cm = confusion_matrix(y_true, y_pred)
```
- [ ] Plot confusion matrix (matplotlib/seaborn heatmap)
- [ ] Report Accuracy, Precision, Recall, F1-score

**Deliverable:** `evaluate.py`, `confusion_matrix.png`

---

### **Phase 9 — Demo Preparation (Day 4–5)**
- [ ] Prepare a demo script: show 3–5 sample emails going through the full pipeline live
- [ ] Show at least 1 example of a human override (AI wrong, human corrects it)
- [ ] Prepare slides: problem statement, architecture diagram, confusion matrix results, tech stack
- [ ] Record a short video/backup demo in case of live-demo failure

**Deliverable:** Final working demo + presentation deck

---

## 4. Folder Structure

```
PhishGuard/
├── data/
│   ├── phishtank_raw.csv
│   ├── legit_emails.csv
│   └── dataset.csv
├── src/
│   ├── feature_extractor.py
│   ├── train_model.py
│   ├── llm_agent.py
│   ├── decision_engine.py
│   ├── database.py
│   └── pipeline.py         # orchestrates the full agentic flow
├── dashboard/
│   └── dashboard.py         # Streamlit app
├── evaluation/
│   ├── evaluate.py
│   └── confusion_matrix.png
├── models/
│   └── model.pkl
├── phishguard.db             # SQLite database
├── requirements.txt
└── README.md
```

---

## 5. Required Libraries (`requirements.txt`)

```
scikit-learn
pandas
numpy
streamlit
requests
beautifulsoup4
tldextract
matplotlib
seaborn
anthropic          # or openai, for LLM API calls
python-whois        # optional, for domain age
```

---

## 6. Risk Areas / Things to Watch

- **Class imbalance:** PhishTank-only data will be 100% phishing — you MUST add legitimate emails or the model learns nothing useful
- **LLM API cost/rate limits:** Cache results, don't call LLM for every single test email during evaluation if quota is limited — batch or sample
- **Live demo risk:** Have a pre-recorded backup video in case internet/API fails during presentation
- **Explainability:** Judges will like it if you can show *why* an email was flagged (keywords, suspicious URL) — not just a score

---

## 7. Stretch Goals (if time permits)

- Browser extension or email client plugin as front-end
- Real-time email fetching via IMAP instead of static dataset
- Model retraining loop using human override data (active learning)
- Slack/Teams notification when phishing is quarantined
