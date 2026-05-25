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

import os
import chromadb

chroma_client = chromadb.PersistentClient(
    path=config.PERSIST_DIRECTORY
)

chroma_db = Chroma(
    collection_name=config.COLLECTION_NAME,
    client=chroma_client,
    embedding_function=embedding_fn,
)
# -------------------------------------------------------
# GROQ CLIENT
# -------------------------------------------------------
client = Groq(api_key=config.GROQ_API_KEY)

MODEL = "openai/gpt-oss-120b"

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
def groq_chat(prompt: str, system_prompt: str = None):

    messages = []

    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })

    messages.append({
        "role": "user",
        "content": prompt
    })

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.3
    )

    return response.choices[0].message.content


# -------------------------------------------------------
# CYBER INTENT CLASSIFIER
# -------------------------------------------------------
def classify_intent(query: str) -> bool:

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

    response = groq_chat(prompt)

    return response.strip().lower() == "cyber"


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
    Create a structured cybercrime help response.

    User Query:
    {state['user_query']}

    Issue:
    {state['issue_type']}

    Threat:
    {json.dumps(state['threat_json'], indent=2)}

    Escalation:
    {json.dumps(state.get('escalation_data', {}), indent=2)}

    SOP:
    {rag_text}

    Provide:
    - Issue Identified
    - Threat Assessment
    - Emergency Actions
    - Step-by-step user instructions
    - Evidence Required
    - Reporting Link
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