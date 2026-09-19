from langgraph.graph import StateGraph, END
from langchain_chroma import Chroma
from config import Config
from groq import Groq

import json
import re
from datetime import datetime
from typing import TypedDict, List, Dict, Any

from langchain_huggingface import HuggingFaceEmbeddings 
from chromadb.config import Settings

# -------------------------------------------------------
# CONFIG
# -------------------------------------------------------
config = Config()

embedding_fn = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# -------------------------------------------------------
# CHROMADB
# -------------------------------------------------------
# -------------------------------------------------------
# CHROMADB
# -------------------------------------------------------
import os
import shutil
import chromadb

def _init_chroma():
    target_dir = config.PERSIST_DIRECTORY
    try:
        client = chromadb.PersistentClient(path=target_dir)
        db = Chroma(
            collection_name=config.COLLECTION_NAME,
            client=client,
            embedding_function=embedding_fn,
        )
        return client, db
    except Exception as exc:
        print(f"Warning: Stale ChromaDB database schema detected ({exc}). Initializing fresh vector store...")
        target_dir = os.path.join(os.path.dirname(config.PERSIST_DIRECTORY), "chroma_store_v2")
        client = chromadb.PersistentClient(path=target_dir)
        db = Chroma(
            collection_name=config.COLLECTION_NAME,
            client=client,
            embedding_function=embedding_fn,
        )
        return client, db

chroma_client, chroma_db = _init_chroma()
# -------------------------------------------------------
# GROQ CLIENT
# -------------------------------------------------------
groq_key = config.GROQ_API_KEY or os.getenv("GROQ_API_KEY") or "gsk_placeholder"
client = Groq(api_key=groq_key)

MODEL = "openai/gpt-oss-20b"

# -------------------------------------------------------
# STATE
# -------------------------------------------------------
class AgentState(TypedDict, total=False):
    user_query: str
    issue_type: str
    retrieved_docs: List[Any]
    final_answer: str
    threat_json: Dict[str, Any]
    escalation_data: Dict[str, Any]

# -------------------------------------------------------
# HELPER FUNCTION
# -------------------------------------------------------
def groq_chat(prompt: str, system_prompt: str = None) -> str:
    groq_api_key = config.GROQ_API_KEY or os.getenv("GROQ_API_KEY") or ""
    if not groq_api_key.strip():
        return "I am CyberGuard Incident Response Assistant. Please add your `GROQ_API_KEY` to the `.env` file to enable live AI LLM reasoning."

    try:
        groq_client = Groq(api_key=groq_api_key.strip())
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = groq_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.3
        )
        return response.choices[0].message.content or ""
    except Exception as err:
        print(f"Groq API Error: {err}")
        return f"CyberGuard Assistant: Could not connect to AI LLM service ({str(err)[:60]}). Please check your API key."


# -------------------------------------------------------
# CYBER INTENT CLASSIFIER
# -------------------------------------------------------
def classify_intent(query: str) -> bool:
    keywords = [
        "cyber", "hack", "scam", "fraud", "phishing", "virus", "malware",
        "stolen", "harass", "threat", "police", "card", "otp", "bank", "account",
        "breach", "blackmail", "ransom", "fake", "link", "spam", "hi", "hello", "help"
    ]
    query_lower = query.lower().strip()
    if any(k in query_lower for k in keywords):
        return True

    prompt = f"""
    Determine if the following user query is related to:
    cybercrime, cyber safety, cyber fraud, online threats,
    cyberbullying, hacking, digital harassment, account compromise,
    or police reporting.

    Query: "{query}"

    Respond with ONLY one word:
    - cyber
    - general
    """
    try:
        response = groq_chat(prompt)
        return "cyber" in response.strip().lower()
    except Exception:
        return True


# -------------------------------------------------------
# STRICT JSON LLM CALL
# -------------------------------------------------------
def call_llm(prompt: str):

    content = groq_chat(
        prompt,
        system_prompt="You MUST answer only with valid JSON. No explanation. No markdown."
    )

    json_match = re.search(r'{.*}', content, re.DOTALL)

    if json_match:
        content = json_match.group(0)

    return content


# -------------------------------------------------------
# NODE 1 — THREAT DETECTION
# -------------------------------------------------------
def detect_threat(state: AgentState):

    prompt = f"""
    Analyze this user message for threats.

    Message: "{state['user_query']}"

    Respond ONLY in JSON:
    {{
        "threat_type": "...",
        "severity": "Low / Medium / High",
        "requires_escalation": true/false,
        "reason": "..."
    }}
    """

    result = call_llm(prompt)

    try:
        state["threat_json"] = json.loads(result)

    except Exception:
        state["threat_json"] = {
            "threat_type": "Unknown",
            "severity": "Low",
            "requires_escalation": False,
            "reason": "Invalid JSON returned"
        }

    return state


# -------------------------------------------------------
# NODE 2 — ESCALATION
# -------------------------------------------------------
def escalation_agent(state: AgentState):

    threat = state["threat_json"]

    severity = threat.get("severity", "Low")
    requires_escalation = threat.get("requires_escalation", False)

    if severity == "High" or requires_escalation:

        state["escalation_data"] = {
            "timestamp": str(datetime.utcnow()),
            "user_message": state["user_query"],
            "issue_type": state.get("issue_type", "Unknown"),
            "threat_type": threat.get("threat_type"),
            "severity": severity,
            "reason": threat.get("reason"),
            "action_required": "URGENT – Notify Cyber Cell Immediately"
        }

    else:

        state["escalation_data"] = {
            "severity": severity,
            "action_required": "No escalation needed"
        }

    return state


# -------------------------------------------------------
# NODE 3 — ISSUE CLASSIFICATION
# -------------------------------------------------------
def detect_issue_type(state: AgentState):

    prompt = f"""
    Classify the cyber issue for this query:

    "{state['user_query']}"

    Respond ONLY with the category text.
    """

    issue = groq_chat(prompt)

    state["issue_type"] = issue.strip()

    return state


# -------------------------------------------------------
# NODE 4 — RETRIEVE SOP
# -------------------------------------------------------
def retrieve_sop(state: AgentState):
    docs = chroma_db.similarity_search(state["user_query"], k=3)
    state["retrieved_docs"] = docs
    return state


# -------------------------------------------------------
# NODE 5 — FINAL ANSWER
# -------------------------------------------------------
def generate_answer(state: AgentState):

    rag_text = "\n\n".join(
        [doc.page_content for doc in state["retrieved_docs"]]
    )

    prompt = f"""
    Create a highly structured, attractive, and empathetic cybercrime response guide in clean Markdown.
    Do NOT use a 2-column table with 'Section | Details'. Instead, use clean Markdown headers, quote boxes, bullet lists, and numbered action steps.

    User Query: "{state['user_query']}"
    Issue Category: {state['issue_type']}
    Threat Data: {json.dumps(state['threat_json'], indent=2)}
    Escalation Status: {json.dumps(state.get('escalation_data', {}), indent=2)}
    SOP Knowledge Base: {rag_text}

    Structure your response using these exact Markdown sections:

    ### 📌 Incident Summary
    > Provide a brief 1-2 sentence empathetic summary of what the user is facing.

    ### 🛡️ Threat & Risk Assessment
    - **Issue Identified**: {state['issue_type']}
    - **Severity Level**: **{state['threat_json'].get('severity', 'Medium')}**
    - **Immediate Escalation Required**: {"Yes" if state.get('threat_json', {}).get('requires_escalation') else "No"}

    ### ⚡ Immediate Emergency Actions
    1. **Do NOT Pay or Comply**: Explain clearly why compliance does not stop extortion.
    2. **Preserve Digital Evidence**: Take screenshots of every message, chat export, and header.
    3. **Block the Harasser**: Block all communication channels immediately.
    4. **Secure Your Accounts**: Change passwords and enable 2-Factor Authentication (2FA).

    ### 📋 Step-by-Step Action Plan
    Numbered step-by-step instructions tailored specifically to this query.

    ### 📁 Evidence Collection Checklist
    Bullet points of exact evidence items to collect before filing a police report.

    ### 🔗 Official Reporting Links
    - **National Cyber Crime Portal**: [cybercrime.gov.in](https://www.cybercrime.gov.in)
    - **National Helpline**: Call **1930** (Toll-Free)
    """

    answer = groq_chat(prompt)

    state["final_answer"] = answer.strip()

    return state


# -------------------------------------------------------
# BUILD GRAPH
# -------------------------------------------------------
builder = StateGraph(AgentState)

builder.add_node("detect_threat", detect_threat)
builder.add_node("escalation_node", escalation_agent)
builder.add_node("detect_issue", detect_issue_type)
builder.add_node("retrieve_sop", retrieve_sop)
builder.add_node("generate", generate_answer)

builder.set_entry_point("detect_threat")

builder.add_edge("detect_threat", "escalation_node")
builder.add_edge("escalation_node", "detect_issue")
builder.add_edge("detect_issue", "retrieve_sop")
builder.add_edge("retrieve_sop", "generate")
builder.add_edge("generate", END)

graph = builder.compile()