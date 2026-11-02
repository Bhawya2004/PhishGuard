# PhishGuard — Step-by-Step Coding Flow
### Build order for coding this yourself, one working piece at a time

**Golden rule:** Build and test each piece standalone (in isolation, print outputs, verify it works) BEFORE connecting it to the next piece. Don't try to build the whole pipeline at once — you'll waste time debugging multiple broken things together.

---

## STEP 0 — Environment Setup
**Goal:** Get a working Python environment.

1. Create project folder + virtual environment
2. Install: `pandas`, `scikit-learn`, `streamlit`, `requests`, `tldextract`, `matplotlib`, `seaborn`, `anthropic` (or your LLM SDK)
3. Create the folder structure (`data/`, `src/`, `dashboard/`, `evaluation/`, `models/`)
4. Test: run `python -c "import pandas, sklearn, streamlit"` — no errors = good to go

✅ **Checkpoint:** Environment runs, no import errors.

---

## STEP 1 — Get and Prepare the Dataset
**Goal:** One clean CSV with phishing + legit examples, labeled.

1. Download PhishTank CSV (phishing URLs)
2. Download a legit/ham dataset (Enron or SpamAssassin, or even a small hand-made set of 50–100 real-looking safe emails if time-constrained)
3. Write a script `load_data.py` that:
   - Loads both datasets
   - Standardizes columns: `sender, subject, body, url, label` (label = 1 for phishing, 0 for legit)
   - Merges them into one `dataset.csv`
4. Print `.shape` and `.head()` to confirm it looks right
5. Print `value_counts()` on `label` to check class balance

✅ **Checkpoint:** `dataset.csv` exists, has both classes, no missing critical columns.

---

## STEP 2 — Build Feature Extraction (standalone, testable)
**Goal:** A function that takes ONE email/URL and returns a dictionary of features.

1. Write `feature_extractor.py` with a function like:
   ```python
   def extract_features(email_row) -> dict:
       # returns {'url_length': ..., 'has_ip': ..., 'urgency_words': ..., ...}
   ```
2. Test it manually on 2–3 example rows (one obvious phishing, one obvious legit) — print the dict and sanity-check the values make sense
3. Apply it to the whole `dataset.csv` using `.apply()` → get a features dataframe

✅ **Checkpoint:** You can run this file alone and see correct-looking feature values printed for a sample row.

---

## STEP 3 — Train the ML Classifier (standalone, testable)
**Goal:** A saved model file that can predict phishing/legit from features.

1. Write `train_model.py`:
   - Load features dataframe from Step 2
   - Split train/test (80/20)
   - Train Logistic Regression or Random Forest
   - Print accuracy on the test split
2. Save the trained model: `model.pkl` (using `joblib` or `pickle`)
3. Write a tiny test script that loads `model.pkl` and predicts on 2–3 manual examples

✅ **Checkpoint:** You can run this file alone, see a reasonable accuracy printed (>80% is a good sign), and `model.pkl` exists on disk.

---

## STEP 4 — Build the LLM Reasoning Agent (standalone, testable)
**Goal:** A function that sends email content to an LLM and gets back a structured risk assessment.

1. Write `llm_agent.py` with a function like:
   ```python
   def analyze_with_llm(email_text) -> dict:
       # returns {'llm_score': 0-100, 'reasoning': '...'}
   ```
2. Write a clear prompt instructing the LLM to respond ONLY in JSON with a score + short reasoning
3. Test it manually by calling it on 2–3 sample emails and printing the result — confirm it parses cleanly as JSON
4. Add error handling (try/except around JSON parsing, in case the LLM adds extra text)

✅ **Checkpoint:** You can run this file alone, call it on a sample email, and get back a clean score + reasoning without crashing.

---

## STEP 5 — Build the Decision Engine (standalone, testable)
**Goal:** Combine ML score + LLM score into one final decision.

1. Write `decision_engine.py`:
   ```python
   def decide(ml_score, llm_score) -> str:
       # combine (e.g. weighted average), apply thresholds
       # return 'Safe' / 'Suspicious' / 'Phishing'
   ```
2. Test it with manual score combinations (e.g., `decide(0.9, 85)` should return `'Phishing'`)
3. Tune your thresholds based on what feels right, then adjust later using real evaluation results

✅ **Checkpoint:** Function returns correct category for a handful of manually chosen test scores.

---

## STEP 6 — Set Up the Database (standalone, testable)
**Goal:** SQLite database that can store and update email records.

1. Write `database.py`:
   - Function to create the `emails` table (if not exists)
   - Function `insert_email(record)` 
   - Function `update_human_decision(email_id, decision, reviewer)`
   - Function `get_pending_reviews()`
2. Test by inserting 2–3 fake records manually and querying them back — print results to confirm

✅ **Checkpoint:** You can insert, update, and query records without errors. Open the `.db` file with a SQLite viewer to visually confirm data is there.

---

## STEP 7 — Connect Everything: The Pipeline Orchestrator
**Goal:** One function that takes a raw email and runs it through the FULL flow.

1. Write `pipeline.py`:
   ```python
   def process_email(email):
       features = extract_features(email)
       ml_score = model.predict_proba(features)
       llm_result = analyze_with_llm(email['body'])
       final_decision = decide(ml_score, llm_result['llm_score'])
       insert_email({...all data..., 'ai_decision': final_decision})
       return final_decision
   ```
2. Test by running this on 5–10 sample emails from your test set
3. Check the database afterward — confirm rows were inserted with sensible decisions

✅ **Checkpoint:** Running `pipeline.py` on a batch of emails populates the database correctly with AI decisions — this is your core working system.

---

## STEP 8 — Build the Human Review Dashboard
**Goal:** A Streamlit app where a human can see flagged emails and override decisions.

1. Write `dashboard.py`:
   - Query `get_pending_reviews()` from the database
   - Display each email: subject, body snippet, AI decision, ML score, LLM reasoning
   - Add buttons: "Confirm Phishing" and "Mark Safe (Override)"
   - On button click → call `update_human_decision()`
   - Show a small stats panel (total processed, total flagged, total overridden)
2. Run with `streamlit run dashboard.py` and manually test clicking through a few records

✅ **Checkpoint:** You can visually see flagged emails in the browser, click a button, and see the database update (refresh to confirm).

---

## STEP 9 — Run Full Pipeline on Test Dataset
**Goal:** Process your entire held-out test set through the pipeline.

1. Write a small runner script (or extend `pipeline.py`) to loop through all test rows and call `process_email()` on each
2. Let it run (this may take a while if calling an LLM API per email — consider sampling if you have rate limits)
3. Confirm all results are logged in the database

✅ **Checkpoint:** Database now has AI decisions for your entire test set, ready for evaluation.

---

## STEP 10 — Evaluation & Confusion Matrix
**Goal:** Prove your system works with real numbers.

1. Write `evaluate.py`:
   - Pull `ai_decision` and true `label` for all test emails from the database
   - Use `sklearn.metrics.confusion_matrix` and `classification_report`
   - Plot the confusion matrix with `seaborn.heatmap` and save as `confusion_matrix.png`
2. Print accuracy, precision, recall, F1-score to console

✅ **Checkpoint:** You have a confusion matrix image and metrics — this is a required deliverable.

---

## STEP 11 — Polish & Demo Prep
**Goal:** Make it presentable.

1. Pick 3–5 interesting test emails to walk through live (include at least one where the human overrides the AI)
2. Clean up the dashboard UI a little (labels, colors for risk levels)
3. Write a short `README.md` explaining how to run everything
4. Record a backup demo video in case of live failure
5. Prepare a 1-slide architecture diagram (you already have one in the Implementation Plan doc)

✅ **Checkpoint:** You can run the whole thing start-to-finish live, and you have a fallback recording.

---

## Quick Reference: Order to Code Things In

```
1. Environment setup
2. Dataset loading & cleaning
3. Feature extraction        (test standalone)
4. ML model training           (test standalone)
5. LLM reasoning agent         (test standalone)
6. Decision engine             (test standalone)
7. Database layer              (test standalone)
8. Pipeline orchestrator       (connects 3–7)
9. Streamlit dashboard         (human override UI)
10. Run pipeline on full test set
11. Evaluation + confusion matrix
12. Polish + demo prep
```

**Why this order matters:** Every step before Step 7 (Pipeline Orchestrator) is testable in complete isolation — so when something breaks later, you'll already know steps 1–6 work, and the bug is only in how they're wired together. This saves you huge amounts of debugging time.
