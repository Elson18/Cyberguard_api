# CyberGuard API Backend Server

Standalone FastAPI API server for CyberGuard Agentic RAG, Threat Classification, and Incident Response.

## Running Backend API

```bash
python mcp_server.py
```

Server starts on: `http://127.0.0.1:8765`

## Features & Endpoints

- `/query` (POST): Agentic RAG query classification and response generation
- `/register` & `/login` (POST): User management
- `/report` (POST): Incident report processing with file uploads
- `/api/extension/*`: Chrome extension URL scanning & status
- `/docs`: FastAPI Interactive Swagger Documentation
