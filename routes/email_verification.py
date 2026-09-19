from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from services.email_verification import verify_email


router = APIRouter(
    prefix="/api/email",
    tags=["Email Verification"]
)


class EmailVerificationRequest(BaseModel):
    sender_name: str = ""
    sender_email: str
    company_name: str = ""
    official_domain: str = ""
    subject: str = ""
    email_body: str = ""
    reply_to: str = ""
    return_path: str = ""
    spf: str = "UNKNOWN"
    dkim: str = "UNKNOWN"
    dmarc: str = "UNKNOWN"
    urls: List[str] = []
    offer_letter_text: str = ""
    signature: str = ""


@router.post("/verify")
async def verify_job_email(data: EmailVerificationRequest):
    try:
        result = verify_email(
            sender_name=data.sender_name,
            sender_email=data.sender_email,
            company_name=data.company_name,
            official_domain=data.official_domain,
            subject=data.subject,
            email_body=data.email_body,
            reply_to=data.reply_to,
            return_path=data.return_path,
            spf=data.spf,
            dkim=data.dkim,
            dmarc=data.dmarc,
            urls=data.urls,
            offer_letter_text=data.offer_letter_text,
            signature=data.signature
        )

        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Email verification failed: {str(e)}"
        )
