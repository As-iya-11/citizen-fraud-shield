"""
rag_engine.py
Core RAG pipeline for the Citizen Fraud Shield.

Pipeline:
1. Load scam-pattern knowledge base documents from knowledge_base/
2. Chunk + embed them with HuggingFace sentence-transformers (all-MiniLM-L6-v2)
3. Store in a local FAISS index
4. On a user query, retrieve the most relevant chunks
5. Pass query + retrieved context to Groq's LLaMA 3 model to produce a grounded,
   structured risk verdict
"""

import os
import glob
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from groq import Groq

KB_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")
INDEX_DIR = os.path.join(os.path.dirname(__file__), "faiss_index")

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
GROQ_MODEL_NAME = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """You are Citizen Fraud Shield, an AI safety assistant that helps Indian \
citizens assess whether a call, message, or situation they describe is a likely scam \
(especially digital arrest scams, KYC/bank phishing, fake job offers, lottery scams, \
loan app harassment, or investment fraud).

You are given:
- The user's description of what happened to them.
- Retrieved reference material describing known scam patterns and official reporting
  guidance.

Using ONLY the retrieved reference material and sound reasoning (never invent facts not
grounded in the reference material or the user's own description), respond with:

1. RISK VERDICT: one of [LOW RISK, MEDIUM RISK, HIGH RISK]
2. WHY: 2-4 concise bullet points explaining which specific patterns from the reference
   material match what the user described.
3. WHAT TO DO NOW: concrete next steps, prioritizing official reporting channels
   (1930 / cybercrime.gov.in) if risk is medium or high.

Keep the tone calm, clear, and non-alarming. Do not use jargon. If the description doesn't
match any known scam pattern strongly, say so honestly rather than forcing a high-risk
verdict.
"""


def load_and_split_documents():
    docs = []
    for filepath in glob.glob(os.path.join(KB_DIR, "*.txt")):
        loader = TextLoader(filepath, encoding="utf-8")
        docs.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=80,
        separators=["\n\n", "\n", ". ", " "],
    )
    return splitter.split_documents(docs)


def build_or_load_vectorstore():
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

    if os.path.exists(INDEX_DIR):
        return FAISS.load_local(
            INDEX_DIR, embeddings, allow_dangerous_deserialization=True
        )

    chunks = load_and_split_documents()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(INDEX_DIR)
    return vectorstore


class FraudShieldEngine:
    def __init__(self, groq_api_key: str):
        self.vectorstore = build_or_load_vectorstore()
        self.client = Groq(api_key=groq_api_key)

    def retrieve_context(self, query: str, k: int = 4) -> str:
        results = self.vectorstore.similarity_search(query, k=k)
        return "\n\n---\n\n".join(r.page_content for r in results)

    def assess(self, user_message: str) -> str:
        context = self.retrieve_context(user_message)

        user_prompt = f"""RETRIEVED REFERENCE MATERIAL:
{context}

USER'S DESCRIPTION OF THEIR SITUATION:
{user_message}

Provide your assessment now, following the required format exactly."""

        completion = self.client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=700,
        )
        return completion.choices[0].message.content
