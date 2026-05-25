import asyncio
import os
import traceback
from typing import List

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
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
from routes.frontend import FRONTEND_ROOT, router as frontend_router
from send_mail import send_cybercrime_report
from severity import extract_severity
from utils.rate_limit import limiter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(title="CyberGuard Unified Platform")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:8765,http://127.0.0.1:8765",
).split(",")

app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in _cors_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mongo = MongoDb()
cyber_graph = graph
print("Cyber Agent ready!")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
if os.path.isdir(FRONTEND_ROOT):
    app.mount("/cyberguard", StaticFiles(directory=FRONTEND_ROOT), name="cyberguard")

app.include_router(frontend_router)
app.include_router(extension_router)


class QueryInput(BaseModel):
    query: str
    username: str


class RegisterUser(BaseModel):
    name: str
    phone_no: str
    email: EmailStr
    password: str
    re_password: str


class LoginRequest(BaseModel):
    identifier: str
    password: str


@app.get("/api/health")
async def health():
    return {
        "message": "CyberGuard Unified Platform",
        "status": "running",
        "frontend": os.path.isdir(FRONTEND_ROOT),
    }


async def run_cyber_agent(query: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: cyber_graph.invoke({"user_query": query}),
    )


@app.post("/query")
async def run_agent(data: QueryInput):
    try:
        query = data.query
        is_cyber = classify_intent(query)

        if is_cyber:
            result = await run_cyber_agent(query)
            final_answer = result.get("final_answer", "No response")
            severity = extract_severity(final_answer)

            if severity in ["low"]:
                severity_message = (
                    "Low Threat Level\n\n"
                    "I know this may feel uncomfortable, even if the risk is low. "
                    "Staying aware and calm is enough, and support is always here if you need it"
                )
            elif severity in ["medium"]:
                severity_message = (
                    "Medium Threat Level\n\n"
                    "It's understandable to feel worried in this situation. "
                    "You're not alone, and taking careful steps can help you regain control"
                )
            elif severity in ["high", "urgent"]:
                severity_message = (
                    "High Threat Level\n\n"
                    "I'm sorry you're facing something this serious—it's okay to feel overwhelmed. "
                    "Your safety matters, and trusted help is available to support you"
                )
            else:
                severity_message = ""

            helpline = """#### HELPLINE

            ###Tamil Nadu: 044-29580300
            ###Hyderabad: 040-29320049
            ###Kerala: 0471-2300042"""
            full_answer = f"{severity_message}\n\n{final_answer}\n\n{helpline}"

            if severity in ["high", "urgent"]:
                return {
                    "answer": full_answer,
                    "severity": severity,
                    "mode": "agent",
                    "redirect": True,
                    "redirect_url": "/complaint-form",
                }

            return {
                "answer": full_answer,
                "severity": severity,
                "mode": "agent",
                "redirect": False,
            }

        answer = generate_response_groq(query)
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

    if user.get("password") != data.password:
        raise HTTPException(status_code=401, detail="Invalid password")

    return {"status": "success", "user_id": user["user_id"]}


@app.get("/complaint-form")
def complaint_form():
    cyberguard_complaint = os.path.join(FRONTEND_ROOT, "complaint.html")
    if os.path.isfile(cyberguard_complaint):
        return FileResponse(cyberguard_complaint)
    return FileResponse(os.path.join(STATIC_DIR, "complaint.html"))


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


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8765"))
    uvicorn.run("mcp_server:app", port=port, log_level="info", reload=True)
