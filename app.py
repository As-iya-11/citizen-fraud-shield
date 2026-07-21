import os
import streamlit as st
from classifier import score_message
from rag_engine import FraudShieldEngine

st.set_page_config(
    page_title="Citizen Fraud Shield",
    page_icon="🛡️",
    layout="centered",
)

st.title("🛡️ Citizen Fraud Shield")
st.caption(
    "AI-powered fraud & digital arrest scam risk assessment — "
    "ET AI Hackathon 2.0 Prototype (Problem Statement 6: Digital Public Safety)"
)

with st.expander("ℹ️ About this tool", expanded=False):
    st.markdown(
        """
This prototype helps citizens quickly assess whether a call, message, or situation they
describe matches known **digital arrest scam** or **fraud** patterns, and gives clear next
steps for reporting.

**How it works (architecture):**
1. **Heuristic layer** — instant keyword/phrase pattern scoring (transparent, explainable)
2. **RAG layer** — retrieves the most relevant known scam patterns from a curated
   knowledge base (MHA/RBI/TRAI advisory patterns) using FAISS + HuggingFace embeddings
3. **LLM reasoning layer** — Groq LLaMA 3 combines both signals to produce a grounded,
   structured risk verdict and actionable guidance

⚠️ This is a hackathon prototype for demonstration. In a real emergency, call the
**National Cyber Crime Helpline: 1930** or report at **cybercrime.gov.in** immediately.
        """
    )

api_key = ""
try:
    api_key = st.secrets.get("GROQ_API_KEY", "")
except Exception:
    api_key = ""
if not api_key:
    api_key = os.environ.get("GROQ_API_KEY", "")
if not api_key:
    api_key = st.sidebar.text_input(
        "Groq API Key", type="password", help="Get a free key at console.groq.com"
    )

if "engine" not in st.session_state:
    st.session_state.engine = None

if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.chat_area = st.text_area(
    "Describe the call, message, or situation you'd like assessed:",
    height=150,
    placeholder=(
        "Example: I got a video call from someone claiming to be a CBI officer. "
        "They said a parcel with drugs was booked in my name and I need to stay on "
        "the call and transfer money to a verification account or I'll be arrested."
    ),
)

col1, col2 = st.columns([1, 4])
with col1:
    assess_clicked = st.button("Assess Risk", type="primary")

if assess_clicked:
    if not user_input.strip():
        st.warning("Please describe the situation first.")
    elif not api_key:
        st.warning("Please enter a Groq API key in the sidebar to run the full assessment.")
    else:
        with st.spinner("Analyzing patterns..."):
            heuristic = score_message(user_input)

            if st.session_state.engine is None:
                st.session_state.engine = FraudShieldEngine(groq_api_key=api_key)

            llm_verdict = st.session_state.engine.assess(user_input)

        st.subheader("⚡ Instant Heuristic Signal")
        tier_color = {"HIGH": "red", "MEDIUM": "orange", "LOW": "green"}[heuristic.tier]
        st.markdown(f"**Tier:** :{tier_color}[{heuristic.tier} RISK]  |  **Score:** {heuristic.score}")
        if heuristic.matched_phrases:
            st.write("Matched signals:")
            st.write(", ".join(p for p, _ in heuristic.matched_phrases))
        else:
            st.write("No strong keyword signals matched.")

        st.subheader("🧠 AI Reasoning + Verdict (RAG + LLaMA 3)")
        st.markdown(llm_verdict)

        st.subheader("📞 Report a Fraud")
        st.info(
            "National Cyber Crime Helpline: **1930**  \n"
            "Report online: **cybercrime.gov.in**  \n"
            "Report as soon as possible — quick reporting improves the chance of "
            "freezing transferred funds."
        )

st.divider()
st.caption(
    "Built for ET AI Hackathon 2.0 — Phase 2 Prototype Submission | "
    "Not affiliated with any government agency. For real emergencies, always contact "
    "official channels directly."
)
