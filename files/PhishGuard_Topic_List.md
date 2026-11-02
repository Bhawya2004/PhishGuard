# PhishGuard — Topic List
### Everything you need to understand/learn while building this project (SIH25159)

Use this as a checklist — study or revise these topics as you build each part of the pipeline.

---

## 1. Domain Knowledge — Phishing & Security
- What is phishing (email phishing, spear phishing, smishing, vishing)
- How phishing URLs are structured (typosquatting, homograph attacks, subdomains tricks)
- Common social engineering tactics (urgency, authority, fear, curiosity)
- What PhishTank is and how its dataset is structured (URL, verification status, submission date, target brand)
- Real-world impact of phishing (business email compromise, credential theft)

## 2. Data Handling
- Reading/cleaning CSV datasets with pandas
- Combining multiple datasets (phishing + legitimate) into one labeled dataset
- Handling class imbalance (oversampling, undersampling, SMOTE, class weights)
- Train/test split and why you shouldn't test on training data
- Data leakage (a common mistake — make sure test data is never seen during training)

## 3. Feature Engineering
- URL-based features (length, subdomain count, IP-based URLs, HTTPS presence, special characters like `@`, `-`)
- Text-based features (keyword frequency, TF-IDF, urgency phrases)
- Header-based features (sender domain vs display name mismatch, reply-to mismatch)
- Domain reputation / WHOIS lookups (domain age — phishing domains are often very new)

## 4. Machine Learning
- Supervised classification basics
- Logistic Regression (simple baseline)
- Random Forest / Decision Trees
- XGBoost / Gradient Boosting (higher accuracy option)
- Model training, validation, and hyperparameter basics
- Overfitting vs underfitting

## 5. Natural Language Processing (NLP) / LLM Concepts
- Text vectorization (TF-IDF, embeddings)
- What large language models (LLMs) are and how they can "reason" about text
- Prompt engineering (writing a good prompt to get structured, reliable output from an LLM)
- Structured outputs (getting JSON responses from an LLM reliably)
- Combining LLM judgment with ML model scores (ensemble/hybrid scoring)

## 6. Agentic Systems / Pipeline Design
- What "agentic AI" means (multi-step, tool-using, decision-making systems vs single-shot predictions)
- Designing a pipeline: input → processing → decision → action
- Chaining multiple models/tools together (LangChain concepts, or writing your own orchestration logic)
- Decision thresholds and risk scoring
- Idempotency and error handling in a pipeline (what happens if a step fails?)

## 7. Human-in-the-Loop (HITL) Systems
- Why human oversight matters in AI security systems (avoiding false positives/negatives with real consequences)
- Designing review queues (pending / approved / rejected states)
- State machines (how an email moves from "flagged" → "under review" → "resolved")
- Audit logging (tracking who overrode what and when — important for accountability)

## 8. Model Evaluation
- Confusion matrix (True Positive, True Negative, False Positive, False Negative)
- Precision, Recall, F1-score — and why each matters differently for security
  (e.g., missing real phishing = False Negative = dangerous;
  flagging safe emails = False Positive = annoying but less risky)
- ROC curve / AUC (optional, more advanced evaluation)
- Interpreting results for a non-technical audience (judges, users)

## 9. Backend Development
- REST API basics (if you build API endpoints)
- Database design (schema, primary keys, relationships)
- SQLite basics (creating tables, inserting/querying data)
- CRUD operations (Create, Read, Update, Delete)

## 10. Frontend / Dashboard
- Streamlit basics (widgets, tables, buttons, state management)
- Displaying data dynamically from a database
- Basic UX principles for a review dashboard (clarity, minimal clicks to act)

## 11. Software Engineering Practices
- Project structure / modular code organization
- Version control basics (Git/GitHub — useful for team collaboration)
- Writing a clean README
- Environment management (venv, requirements.txt)

## 12. Presentation & Demo Skills
- Explaining technical architecture simply (use diagrams)
- Live demo strategy (have a backup recording)
- Explaining the confusion matrix results to judges in simple terms
- Highlighting the "human override" feature clearly — it's a key differentiator in this problem statement

---

### Priority tip
If you're short on time, prioritize in this order:
1. Data + Feature Engineering + ML model (core detection)
2. Decision Engine + Database (quarantine + logging logic)
3. Streamlit Dashboard (human override — this is explicitly required)
4. Confusion Matrix evaluation (explicitly required deliverable)
5. LLM reasoning layer (adds "agentic" sophistication — do this if time allows)
