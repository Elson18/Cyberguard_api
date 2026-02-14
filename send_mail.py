from datetime import datetime
from email.message import EmailMessage
import smtplib
import ssl
from database.mongodb import MongoDb
from datetime import datetime

# Email configuration
SENDER_EMAIL = "elsonaron54@gmail.com"
APP_PASSWORD = "ojjfpvsrehvvdxhs"  # move to .env later
CYBERCRIME_EMAIL = "gurubalan1707@gmail.com"

mongo = MongoDb()

def send_cybercrime_report(
    fullname: str,
    email: str,
    phone: str,
    incident_type: str,
    description: str,
    screenshots: list
):
    """Send cybercrime report email and add the user/case to DB"""
    # First, save the case in DB
    mongo.add_case(fullname, phone, email, department="Cybercrime")

    # Prepare email
    subject = f"🚨 Cybercrime Incident Report | {incident_type}"
    body = f"""
🚨 CYBERCRIME INCIDENT REPORT 🚨

👤 Reporter Information
-----------------------
Full Name : {fullname}
Email     : {email}
Phone     : {phone}

🛡 Incident Details
-------------------
Type        : {incident_type}
Description :
{description}

📎 Evidence:
{len(screenshots)} screenshot(s) attached.

Generated via EchoVision AI
"""
    msg = EmailMessage()
    msg["From"] = SENDER_EMAIL
    msg["To"] = CYBERCRIME_EMAIL
    msg["Subject"] = subject
    msg.set_content(body)

    # Attach screenshots if any
    for file in screenshots:
        file_bytes = file.file.read()
        msg.add_attachment(
            file_bytes,
            maintype="image",
            subtype=file.content_type.split("/")[-1],
            filename=file.filename
        )

    # Send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)

    print("✅ Cybercrime report email sent successfully")
