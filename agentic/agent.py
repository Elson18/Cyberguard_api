from langgraph.graph import StateGraph, END
from langchain_chroma import Chroma
from config import Config
from mistralai import Mistral
import json
import re
from datetime import datetime

config = Config()

# -------------------------------------------------------
# Load ChromaDB
# -------------------------------------------------------
chroma_db = Chroma(
    collection_name=config.COLLECTION_NAME,
    persist_directory=config.PERSIST_DIRECTORY
)

# -------------------------------------------------------
# LangGraph State
# -------------------------------------------------------
from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict, total=False):
    user_query: str
    issue_type: str
    retrieved_docs: List[Any]
    final_answer: str
    threat_json: Dict[str, Any]
    escalation_data: Dict[str, Any]

# -------------------------------------------------------
# MISTRAL CLIENT
# -------------------------------------------------------
mistral = Mistral(api_key=config.MISTRALAI_API_KEY)
MODEL = "mistral-small-latest"

def classify_intent(query: str) -> bool:
    """
    Returns True if the query is related to cybercrime.
    Returns False if it is a normal/general question.
    """
    
    prompt = f"""
    Determine if the following user query is related to:
    cybercrime, cyber safety, cyber fraud, online threats,
    cyberbullying, hacking, digital harassment, account compromise,
    or police reporting.

    Query: "{query}"

    Respond with ONLY one word:
    - "cyber"   → if it is cybercrime related
    - "general" → if it is NOT cyber related
    """

    response = mistral.chat.complete(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    ).choices[0].message.content.strip().lower()

    return response == "cyber"


# -------------------------------------------------------
# Helper — STRICT JSON LLM CALL
# -------------------------------------------------------
def call_llm(prompt: str):

    response = mistral.chat.complete(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You MUST answer only with valid JSON. No explanation. No markdown."},
            {"role": "user", "content": prompt}
        ]
    )

    content = response.choices[0].message.content

    # -------- Extract JSON if model adds text ----------
    json_match = re.search(r'{.*}', content, re.DOTALL)
    if json_match:
        content = json_match.group(0)

    return content


# -------------------------------------------------------
# Node 1 — Threat Detection
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
    except Exception as e:
        print("❌ Invalid JSON from model:", result)

        state["threat_json"] = {
            "threat_type": "Unknown",
            "severity": "Low",
            "requires_escalation": False,
            "reason": "Invalid JSON returned"
        }

    return state


# -------------------------------------------------------
# Node 2 — Emergency Escalation
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
        state["escalation"] = {
            "severity": severity,
            "action_required": "No escalation needed"
        }

    return state


# -------------------------------------------------------
# Node 3 — Issue Classification
# -------------------------------------------------------
def detect_issue_type(state: AgentState):
    prompt = f"""
    Classify the cyber issue for this query:

    "{state['user_query']}"

    Respond ONLY with the category text.
    """

    issue = mistral.chat.complete(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    ).choices[0].message.content

    state["issue_type"] = issue.strip()
    return state


# -------------------------------------------------------
# Node 4 — Retrieve SOP
# -------------------------------------------------------
def retrieve_sop(state: AgentState):
    state["retrieved_docs"] = chroma_db.similarity_search(state["user_query"], k=3)
    return state


# -------------------------------------------------------
# Node 5 — Final Answer
# -------------------------------------------------------
def generate_answer(state: AgentState):

    rag_text = "\n\n".join([doc.page_content for doc in state["retrieved_docs"]])

    prompt = f"""
    Create a structured cybercrime help response:

    User Query: {state['user_query']}
    Issue: {state['issue_type']}
    Threat: {json.dumps(state['threat_json'], indent=2)}
    Escalation: {json.dumps(state.get('escalation_data', {}), indent=2)}

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

    answer = mistral.chat.complete(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    ).choices[0].message.content

    state["final_answer"] = answer.strip()
    return state


# -------------------------------------------------------
# Build Flow
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
