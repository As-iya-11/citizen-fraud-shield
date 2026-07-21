# Citizen Fraud Shield 🛡️
### ET AI Hackathon 2.0 — Phase 2 Prototype
**Problem Statement 6: AI for Digital Public Safety — Defeating Counterfeiting, Fraud & Digital Arrest Scams**

Scoped sub-solution: **Digital Arrest Scam Detection + Citizen Fraud Shield** (conversational risk assessment)

---

## Problem

Digital arrest scams and related fraud defrauded Indian citizens of ₹1,776+ crore in the
first nine months of 2024 alone (MHA data). Victims are isolated on video calls and
pressured into transferring money before they can seek outside advice or verification.
There is no easily accessible, instant tool for a citizen to check "is this actually a
scam?" in the moment it's happening.

## Solution

A conversational AI tool where a citizen describes what's happening on a call/message, and
gets back:
1. An instant heuristic risk signal (transparent, explainable, no AI call needed)
2. A grounded AI risk verdict, reasoned over a curated knowledge base of real scam patterns
   and official government advisories
3. Clear next steps, prioritizing the official 1930 / cybercrime.gov.in reporting channel

## Architecture

```
                     ┌─────────────────────────┐
   User describes  → │   Streamlit Chat UI      │
   situation         └────────────┬────────────┘
                                  │
                 ┌────────────────┼─────────────────┐
                 ▼                                   ▼
   ┌─────────────────────────┐        ┌─────────────────────────────┐
   │ Heuristic Layer          │        │ RAG Retrieval Layer          │
   │ (classifier.py)          │        │ (rag_engine.py)              │
   │ - Weighted keyword/phrase│        │ - HuggingFace embeddings     │
   │   scoring                │        │   (all-MiniLM-L6-v2)         │
   │ - Instant, explainable   │        │ - FAISS vector store         │
   │ - LOW/MEDIUM/HIGH tier   │        │ - Knowledge base:            │
   └────────────┬─────────────┘        │   digital arrest patterns,   │
                │                      │   general fraud patterns,    │
                │                      │   official advisories        │
                │                      └──────────────┬───────────────┘
                │                                     │
                └───────────────┬─────────────────────┘
                                 ▼
                  ┌───────────────────────────────┐
                  │ LLM Reasoning Layer             │
                  │ Groq API — LLaMA 3 (70B)        │
                  │ Combines heuristic + retrieved  │
                  │ context → grounded verdict +    │
                  │ next steps                      │
                  └────────────────┬────────────────┘
                                   ▼
                    ┌───────────────────────────┐
                    │ Structured Risk Verdict    │
                    │ + Reporting Guidance       │
                    │ (1930 / cybercrime.gov.in) │
                    └───────────────────────────┘
```

**Why two detection layers?** The hackathon's evaluation focus explicitly calls out
minimizing false negatives while keeping false positives very low on citizen-facing tools.
The heuristic layer catches obvious high-signal cases instantly and transparently (no LLM
dependency, fully auditable); the RAG+LLM layer catches subtler or reworded scam
descriptions that don't match exact keywords, by reasoning over retrieved reference
patterns instead of relying on memorized training data.

## Tech Stack

- **Frontend:** Streamlit
- **Embeddings:** HuggingFace `sentence-transformers/all-MiniLM-L6-v2`
- **Vector store:** FAISS (local, no external DB dependency)
- **LLM:** Groq API, LLaMA 3 70B
- **Orchestration:** LangChain

## Project Structure

```
fraud-shield/
├── app.py                          # Streamlit UI
├── rag_engine.py                   # RAG pipeline (embeddings, FAISS, Groq call)
├── classifier.py                   # Heuristic keyword-based pre-classifier
├── requirements.txt
├── knowledge_base/
│   ├── digital_arrest_scams.txt    # Digital arrest scam pattern reference
│   ├── general_fraud_patterns.txt  # KYC/job/lottery/loan/investment scam patterns
│   └── reporting_and_advisories.txt# Official reporting channels + advisory principles
└── README.md
```

## Setup (Local)

```bash
git clone <your-repo-url>
cd fraud-shield
pip install -r requirements.txt --break-system-packages   # or use a venv
```

Get a free Groq API key at [console.groq.com](https://console.groq.com).

Run locally:
```bash
export GROQ_API_KEY="your-key-here"
streamlit run app.py
```

Or enter the key directly in the sidebar when the app launches.

## Deployment (Streamlit Community Cloud — same as your existing RAG chatbot)

1. Push this folder to a public GitHub repo.
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → point to `app.py`.
3. In app Settings → Secrets, add:
   ```
   GROQ_API_KEY = "your-key-here"
   ```
4. Deploy. First run will download the embedding model and build the FAISS index
   (cached after first run).

## Judging Criteria Alignment

| Criteria | How this prototype addresses it |
|---|---|
| Innovation (25%) | Hybrid heuristic + RAG + LLM detection, rather than a single-layer classifier |
| Business Impact (25%) | Directly targets the ₹1,776 crore digital arrest scam problem with an instantly usable citizen tool |
| Technical Excellence (20%) | Two independent, complementary detection layers; grounded (non-hallucinated) LLM reasoning via RAG |
| Scalability (15%) | Stateless architecture; knowledge base easily extended with more scam patterns/languages; FAISS scales to large corpora |
| User Experience (15%) | Plain-language verdicts, no jargon, immediate actionable reporting guidance |

## Known Limitations & Honest Scoping

This prototype deliberately does **not** attempt counterfeit currency detection (computer
vision) or fraud network graph intelligence — both called out in the full problem
statement — because they require CV/graph-AI skills and datasets outside a solo,
2.5-week build scope. This is a conscious scoping decision to build the
conversational/NLP detection sub-problem *well*, rather than attempting all five
sub-ideas shallowly. This should be stated explicitly in the Phase 3 pitch.

## Future Work (mention in pitch as roadmap)

- Multi-language support (Hindi, Telugu, Tamil, etc.) via the LLM's multilingual ability
- WhatsApp Business API integration for real deployment
- Integration with cybercrime.gov.in's reporting API for one-click reporting
- Expansion of knowledge base with real (anonymized) scam call transcripts
