import os

from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse

router = APIRouter(tags=["frontend"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_ROOT = os.path.normpath(os.path.join(BASE_DIR, "..", "CyberGuard"))


def _serve_page(filename: str, fallback: str = "index.html"):
    path = os.path.join(FRONTEND_ROOT, filename)
    if os.path.isfile(path):
        return FileResponse(path)
    fallback_path = os.path.join(FRONTEND_ROOT, fallback)
    if os.path.isfile(fallback_path):
        return FileResponse(fallback_path)
    return RedirectResponse("/dashboard")


@router.get("/")
async def home():
    return RedirectResponse("/dashboard")


@router.get("/dashboard")
async def dashboard():
    return _serve_page("index.html")


@router.get("/chat")
async def chat():
    return _serve_page("index.html")


@router.get("/extension")
async def extension_page():
    return _serve_page("extension.html")


@router.get("/agents")
async def agents():
    return _serve_page("settings.html", fallback="index.html")


@router.get("/settings")
async def settings_page():
    return _serve_page("settings.html", fallback="index.html")


@router.get("/browse-dashboard")
async def browse_dashboard():
    return _serve_page("index.html")


@router.get("/login")
async def login_page():
    return _serve_page("login.html")


@router.get("/signin")
async def signin_page():
    return _serve_page("Signin.html")


@router.get("/create-agent")
async def create_agent():
    return _serve_page("settings.html", fallback="index.html")
