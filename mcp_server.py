import asyncio
import os
import traceback
from typing import List

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
import random
import time
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from agentic.agent import classify_intent, graph
from chat_response import generate_response_groq
from database.mongodb import MongoDb
from routes.extension import router as extension_router
from routes.email_verification import router as email_router
from send_mail import send_cybercrime_report
from severity import extract_severity
from utils.helpers import check_password, hash_password
from utils.rate_limit import limiter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(title="CyberGuard Unified Platform")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_raw_cors = os.getenv("CORS_ORIGINS", "*")
if _raw_cors.strip() == "*":
    _cors_origins = ["*"]
else:
    _cors_origins = [o.strip() for o in _raw_cors.split(",") if o.strip()]

app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mongo = MongoDb()
cyber_graph = graph
print("Cyber Agent ready!")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(extension_router)
app.include_router(email_router)


class QueryInput(BaseModel):
    query: str
    username: str
    language: str | None = "en"


class RegisterUser(BaseModel):
    name: str
    phone_no: str
    email: EmailStr
    password: str
    re_password: str


class LoginRequest(BaseModel):
    identifier: str
    password: str


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "CyberGuard Unified Platform API",
        "version": "1.0.0",
        "message": "CyberGuard AI Cybersecurity & Email Verification Backend API is running successfully.",
        "documentation": "/docs",
        "endpoints": {
            "health": "/api/health",
            "extension_scan": "/api/extension/scan-url",
            "email_verification": "/api/email/verify",
            "ai_query": "/query",
            "incident_report": "/report"
        }
    }


@app.get("/api/health")
async def health():
    return {
        "message": "CyberGuard Unified API Server",
        "status": "running",
        "mode": "standalone_api",
    }


async def run_cyber_agent(query: str, language: str = "en"):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: cyber_graph.invoke({"user_query": query, "language": language}),
    )


@app.post("/query")
async def run_agent(data: QueryInput):
    try:
        query = data.query
        language = data.language or "en"
        is_cyber = classify_intent(query)

        if is_cyber:
            result = await run_cyber_agent(query, language)
            final_answer = result.get("final_answer", "No response")
            severity = extract_severity(final_answer)

            if severity in ["low"]:
                severity_message = """<div class="threat-card threat-low">
  <div class="threat-header"><span class="badge-pill">🛡️ LOW THREAT LEVEL</span></div>
  <p>I know this may feel uncomfortable, even if the risk is low. Staying aware and calm is enough, and support is always here if you need it.</p>
</div>"""
            elif severity in ["medium"]:
                severity_message = """<div class="threat-card threat-medium">
  <div class="threat-header"><span class="badge-pill">⚠️ MEDIUM THREAT LEVEL</span></div>
  <p>It's understandable to feel worried in this situation. You're not alone, and taking careful steps can help you regain control.</p>
</div>"""
            elif severity in ["high", "urgent"]:
                severity_message = """<div class="threat-card threat-high">
  <div class="threat-header"><span class="badge-pill">🚨 HIGH THREAT LEVEL — URGENT</span></div>
  <p>I'm sorry you're facing something this serious—it's okay to feel overwhelmed. Your safety matters, and trusted help is available to support you.</p>
</div>"""
            else:
                severity_message = ""

            helpline = """<div class="helpline-wrapper">
  <div class="helpline-title"><i class="fa-solid fa-phone-volume"></i> Emergency Cyber Crime Helplines</div>
  <div class="helpline-grid">
    <div class="helpline-item">
      <span class="region">Tamil Nadu</span>
      <a href="tel:04429580300" class="phone">044-29580300</a>
    </div>
    <div class="helpline-item">
      <span class="region">Hyderabad</span>
      <a href="tel:04029320049" class="phone">040-29320049</a>
    </div>
    <div class="helpline-item">
      <span class="region">Kerala</span>
      <a href="tel:04712300042" class="phone">0471-2300042</a>
    </div>
    <div class="helpline-item">
      <span class="region">National Portal</span>
      <a href="tel:1930" class="phone">1930 (Toll-Free)</a>
    </div>
  </div>
</div>"""
            full_answer = f"{severity_message}\n\n{final_answer}\n\n{helpline}"

            if severity in ["high", "urgent"]:
                return {
                    "answer": full_answer,
                    "severity": severity,
                    "mode": "agent",
                    "redirect": True,
                    "redirect_url": "complaint.html",
                }

            return {
                "answer": full_answer,
                "severity": severity,
                "mode": "agent",
                "redirect": False,
            }

        answer = generate_response_groq(query, language=language)
        return {"answer": answer, "mode": "chatbot", "redirect": False}

    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/register")
def register_user(user: RegisterUser):
    if user.password != user.re_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    existing = mongo.find_the_user(user.email)
    if existing:
        raise HTTPException(status_code=409, detail="User already exists")

    result = mongo.add_new_user(
        name=user.name,
        phone_no=user.phone_no,
        email=user.email,
        password=user.password,
        re_password=user.re_password,
    )

    if not result:
        raise HTTPException(status_code=500, detail="User registration failed")

    return {
        "status": "success",
        "message": "User registered successfully",
        "user_id": result["user_id"],
    }


@app.post("/login")
def login_user(data: LoginRequest):
    user = mongo.find_the_user(data.identifier)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stored_pass = user.get("password", "")
    if not check_password(data.password, stored_pass):
        raise HTTPException(status_code=401, detail="Invalid password")

    # Seamless auto-migration: if password in DB was unhashed plaintext, upgrade it to bcrypt hash
    if stored_pass == data.password and not stored_pass.startswith("$2"):
        new_hash = hash_password(data.password)
        if mongo.db is not None:
            try:
                mongo.db.users.update_one({"_id": user["_id"]}, {"$set": {"password": new_hash}})
            except Exception as e:
                print(f"Warning: Failed to upgrade plaintext password to bcrypt hash: {e}")

    return {"status": "success", "user_id": user["user_id"]}





@app.post("/report")
async def report_incident(
    fullname: str = Form(...),
    email: EmailStr = Form(...),
    phone: str = Form(...),
    incident_type: str = Form(...),
    description: str = Form(...),
    screenshot: List[UploadFile] = File(...),
):
    send_cybercrime_report(
        fullname=fullname,
        email=email,
        phone=phone,
        incident_type=incident_type,
        description=description,
        screenshots=screenshot,
    )
    return {"message": "Incident reported successfully"}


VOICE_QUESTIONS = [
    {
        "step": 0,
        "key": "what_happened",
        "question": "Can you tell me what happened?",
        "field_name": "What happened",
    },
    {
        "step": 1,
        "key": "when_happened",
        "question": "When did this happen?",
        "field_name": "Date / time",
    },
    {
        "step": 2,
        "key": "where_happened",
        "question": "Where did this happen?",
        "field_name": "Location / platform",
    },
    {
        "step": 3,
        "key": "who_involved",
        "question": "Do you have any details about the person or organization involved?",
        "field_name": "People / organization involved",
    },
    {
        "step": 4,
        "key": "additional_details",
        "question": "Is there anything else you'd like to add?",
        "field_name": "Additional details",
    },
]


class VoiceComplaintRequest(BaseModel):
    what_happened: str
    when_happened: str | None = "Not specified"
    where_happened: str | None = "Not specified"
    who_involved: str | None = "Not specified"
    additional_details: str | None = "None"


@app.websocket("/ws/voice-complaint")
async def voice_complaint_websocket(websocket: WebSocket):
    await websocket.accept()
    session_data = {
        "what_happened": "",
        "when_happened": "",
        "where_happened": "",
        "who_involved": "",
        "additional_details": "",
    }
    current_step = 0
    total_steps = len(VOICE_QUESTIONS)

    await websocket.send_json({
        "type": "INIT",
        "step": 0,
        "total_steps": total_steps,
        "question": VOICE_QUESTIONS[0]["question"],
        "field_name": VOICE_QUESTIONS[0]["field_name"]
    })

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "START":
                current_step = 0
                await websocket.send_json({
                    "type": "QUESTION",
                    "step": 0,
                    "total_steps": total_steps,
                    "question": VOICE_QUESTIONS[0]["question"],
                    "field_name": VOICE_QUESTIONS[0]["field_name"]
                })

            elif msg_type == "ANSWER":
                user_answer = data.get("answer", "").strip()
                if current_step < total_steps:
                    key = VOICE_QUESTIONS[current_step]["key"]
                    session_data[key] = user_answer or "Not specified"
                    current_step += 1

                if current_step < total_steps:
                    await websocket.send_json({
                        "type": "QUESTION",
                        "step": current_step,
                        "total_steps": total_steps,
                        "question": VOICE_QUESTIONS[current_step]["question"],
                        "field_name": VOICE_QUESTIONS[current_step]["field_name"],
                        "recorded": session_data
                    })
                else:
                    await websocket.send_json({
                        "type": "REVIEW",
                        "summary": session_data,
                        "message": "Does everything look correct?"
                    })

            elif msg_type == "REPEAT_QUESTION":
                if current_step < total_steps:
                    await websocket.send_json({
                        "type": "QUESTION",
                        "step": current_step,
                        "total_steps": total_steps,
                        "question": VOICE_QUESTIONS[current_step]["question"],
                        "field_name": VOICE_QUESTIONS[current_step]["field_name"],
                        "is_repeat": True
                    })

            elif msg_type == "UPDATE_FIELD":
                field_key = data.get("key")
                field_val = data.get("value")
                if field_key in session_data:
                    session_data[field_key] = field_val
                await websocket.send_json({
                    "type": "REVIEW",
                    "summary": session_data,
                    "message": "Does everything look correct?"
                })

            elif msg_type == "CONFIRM_SUBMIT":
                ref_num = f"REF-{time.strftime('%Y')}-{random.randint(10000, 99999)}"
                if mongo.db is not None:
                    try:
                        mongo.db.voice_complaints.insert_one({
                            "reference_number": ref_num,
                            "summary": session_data,
                            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
                        })
                    except Exception as err:
                        print("Failed to store voice complaint in mongo:", err)

                await websocket.send_json({
                    "type": "SUBMITTED",
                    "reference_number": ref_num,
                    "summary": session_data,
                    "message": "Your complaint has been submitted successfully."
                })

    except WebSocketDisconnect:
        print("Voice complaint WebSocket client disconnected")
    except Exception as e:
        print("WebSocket Error:", e)


@app.post("/api/complaint/submit-voice")
async def submit_voice_complaint(data: VoiceComplaintRequest):
    ref_num = f"REF-{time.strftime('%Y')}-{random.randint(10000, 99999)}"
    record = {
        "reference_number": ref_num,
        "summary": data.model_dump(),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    if mongo.db is not None:
        try:
            mongo.db.voice_complaints.insert_one(record)
        except Exception as err:
            print("Failed to store voice complaint in mongo:", err)

    return {
        "status": "success",
        "reference_number": ref_num,
        "summary": record["summary"],
        "created_at": record["created_at"],
        "message": "Your complaint has been submitted successfully."
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8765"))
    uvicorn.run("mcp_server:app", port=port, log_level="info", reload=True)
