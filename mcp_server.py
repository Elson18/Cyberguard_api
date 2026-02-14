from fastapi import FastAPI,HTTPException, Form, UploadFile,File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,EmailStr
from agentic.agent import graph, classify_intent
from chat_response import generate_response_mistral
from database.mongodb import MongoDb
from severity import extract_severity
import uvicorn
import asyncio
from typing import List
from send_mail import send_cybercrime_report
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


app = FastAPI(title="MultiThread ChatBot API")
# Initialize MongoDB
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mongo = MongoDb()


cyber_graph = graph
print("🚀 Cyber Agent ready!")

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
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def root():
    return {"message": "MultiThread ChatBot API Server", "status": "running"}

# -------------------------------
# Async cyber agent
# -------------------------------
async def run_cyber_agent(query):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: cyber_graph.invoke({"user_query": query})
    )

@app.post("/query")
async def run_agent(data: QueryInput):
    try:
        query = data.query
        user_email = data.username

        is_cyber = classify_intent(query)

        if is_cyber:
            print("Cyber Security Agent")
            result = await run_cyber_agent(query)
            final_answer = result.get("final_answer", "No response")
            severity = extract_severity(final_answer)

            # Prepend severity message
            if severity in ["low"]:
                severity_message = (
                    "Low Threat Level\n\n"
                    "“I know this may feel uncomfortable, even if the risk is low. Staying aware and calm is enough, and support is always here if you need it"
                )
            elif severity in ["medium"]:
                severity_message = (
                    "Medium Threat Level\n\n"
                    "It’s understandable to feel worried in this situation. You’re not alone, and taking careful steps can help you regain control"
                )
            elif severity in ["high", "urgent"]:
                severity_message = (
                    "High Threat Level\n\n"
                    "“I’m sorry you’re facing something this serious—it’s okay to feel overwhelmed. Your safety matters, and trusted help is available to support you")
            else:
                severity_message = ""
            helpline = """#### HELPLINE

            ###Tamil Nadu: 044-29580300\n
            ###Hyderabad: 040-29320049\n
            ###Kerala: 0471-2300042\n"""
            # Combine severity message with final answer
            full_answer = f"{severity_message}\n\n{final_answer}\n\n{helpline}"

            if severity in ["high", "urgent"]:
                return {
                    "answer": full_answer,
                    "severity": severity,
                    "mode": "agent",
                    "redirect": True,
                    "redirect_url": "/complaint-form"
                }

            return {
                "answer": full_answer,
                "severity": severity,
                "mode": "agent",
                "redirect": False
            }

        else:
            print("Multimodel Url")
            answer = generate_response_mistral(query)
            return {
                "answer": answer,
                "mode": "chatbot",
                "redirect": False
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/register")
def register_user(user: RegisterUser):
    if user.password != user.re_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    # Optional: Check existing user
    existing = mongo.find_the_user(user.email)
    if existing:
        raise HTTPException(status_code=409, detail="User already exists")

    result = mongo.add_new_user(
        name=user.name,
        phone_no=user.phone_no,
        email=user.email,
        password=user.password,
        re_password=user.re_password
    )

    if not result:
        raise HTTPException(status_code=500, detail="User registration failed")

    return {
        "status": "success",
        "message": "User registered successfully",
        "user_id": result["user_id"]
    }


@app.post("/login")
def login_user(data: LoginRequest):
    user = mongo.find_the_user(data.identifier)


    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("password") != data.password:
        raise HTTPException(status_code=401, detail="Invalid password")

    return {
        "status": "success",
        "user_id": user["user_id"]
    }

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/complaint-form")
def complaint_form():
    return FileResponse("static/complaint.html")

@app.post("/report")
async def report_incident(
    fullname: str = Form(...),
    email: EmailStr = Form(...),
    phone: str = Form(...),
    incident_type: str = Form(...),
    description: str = Form(...),
    screenshot: List[UploadFile] = File(...)
):
    # 🔥 EMAIL WILL BE SENT HERE
    send_cybercrime_report(
        fullname=fullname,
        email=email,
        phone=phone,
        incident_type=incident_type,
        description=description,
        screenshots=screenshot
    )

    return {"message": "Incident reported successfully"}

if __name__ == "__main__":

    uvicorn.run(app, port=8765, log_level="info")
