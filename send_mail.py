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

# def send_cybercrime_report(
#     fullname: str,
#     email: str,
#     phone: str,
#     incident_type: str,
#     description: str,
#     screenshots: list
# ):
#     """Send cybercrime report email and add the user/case to DB"""
#     # First, save the case in DB
#     mongo.add_case(fullname, phone, email, department="Cybercrime")

#     # Prepare email
#     subject = f"🚨 Cybercrime Incident Report | {incident_type}"
#     body = f"""
# 🚨 CYBERCRIME INCIDENT REPORT 🚨

# 👤 Reporter Information
# -----------------------
# Full Name : {fullname}
# Email     : {email}
# Phone     : {phone}

# 🛡 Incident Details
# -------------------
# Type        : {incident_type}
# Description :
# {description}

# 📎 Evidence:
# {len(screenshots)} screenshot(s) attached.

# Generated via EchoVision AI
# """
#     msg = EmailMessage()
#     msg["From"] = SENDER_EMAIL
#     msg["To"] = CYBERCRIME_EMAIL
#     msg["Subject"] = subject
#     msg.set_content(body)

#     # Attach screenshots if any
#     for file in screenshots:
#         file_bytes = file.file.read()
#         msg.add_attachment(
#             file_bytes,
#             maintype="image",
#             subtype=file.content_type.split("/")[-1],
#             filename=file.filename
#         )

#     # Send email
#     context = ssl.create_default_context()
#     with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
#         server.login(SENDER_EMAIL, APP_PASSWORD)
#         server.send_message(msg)

#     print("✅ Cybercrime report email sent successfully")
from email.message import EmailMessage
import smtplib
import ssl
from datetime import datetime

def send_cybercrime_report(
    fullname: str,
    email: str,
    phone: str,
    incident_type: str,
    description: str,
    screenshots: list
):

    # Save to DB
    mongo.add_case(
        fullname,
        phone,
        email,
        department="Cybercrime"
    )

    subject = f"🚨 Cybercrime Incident Report | {incident_type}"

    current_time = datetime.now().strftime("%d-%m-%Y %I:%M %p")

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f7fb;
                padding: 20px;
                color: #1e293b;
            }}

            .container {{
                max-width: 700px;
                margin: auto;
                background: white;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 10px 35px rgba(0,0,0,0.08);
                border: 1px solid #e2e8f0;
            }}

            .header {{
                background: linear-gradient(135deg, #2563eb, #06b6d4);
                padding: 30px;
                text-align: center;
                color: white;
            }}

            .header h1 {{
                margin: 0;
                font-size: 28px;
            }}

            .header p {{
                margin-top: 8px;
                opacity: 0.9;
                font-size: 14px;
            }}

            .content {{
                padding: 30px;
            }}

            .section {{
                margin-bottom: 28px;
            }}

            .section-title {{
                font-size: 18px;
                font-weight: bold;
                color: #2563eb;
                margin-bottom: 14px;
                border-left: 4px solid #06b6d4;
                padding-left: 10px;
            }}

            .info-box {{
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 18px;
            }}

            .row {{
                margin-bottom: 12px;
            }}

            .label {{
                font-weight: bold;
                color: #0f172a;
            }}

            .value {{
                color: #475569;
            }}

            .description {{
                background: #f8fafc;
                border-radius: 12px;
                padding: 18px;
                border: 1px solid #e2e8f0;
                line-height: 1.7;
                color: #334155;
                white-space: pre-wrap;
            }}

            .evidence {{
                background: #ecfeff;
                border: 1px solid #a5f3fc;
                padding: 16px;
                border-radius: 12px;
                color: #155e75;
                font-weight: 500;
            }}

            .footer {{
                background: #0f172a;
                color: #cbd5e1;
                padding: 24px;
                text-align: center;
                font-size: 13px;
            }}

            .badge {{
                display: inline-block;
                background: #dbeafe;
                color: #1d4ed8;
                padding: 6px 12px;
                border-radius: 30px;
                font-size: 12px;
                font-weight: bold;
            }}

        </style>
    </head>

    <body>

        <div class="container">

            <div class="header">
                <h1>🚨 Cybercrime Incident Report</h1>
                <p>Generated via EchoVision AI Security Platform</p>
            </div>

            <div class="content">

                <div class="section">
                    <div class="section-title">
                        👤 Reporter Information
                    </div>

                    <div class="info-box">

                        <div class="row">
                            <span class="label">Full Name:</span>
                            <span class="value">{fullname}</span>
                        </div>

                        <div class="row">
                            <span class="label">Email:</span>
                            <span class="value">{email}</span>
                        </div>

                        <div class="row">
                            <span class="label">Phone:</span>
                            <span class="value">{phone}</span>
                        </div>

                        <div class="row">
                            <span class="label">Reported Time:</span>
                            <span class="value">{current_time}</span>
                        </div>

                    </div>
                </div>

                <div class="section">

                    <div class="section-title">
                        🛡 Incident Information
                    </div>

                    <div class="info-box">

                        <div class="row">
                            <span class="label">Incident Type:</span>
                            <span class="badge">{incident_type}</span>
                        </div>

                    </div>

                </div>

                <div class="section">

                    <div class="section-title">
                        📝 Incident Description
                    </div>

                    <div class="description">
                        {description}
                    </div>

                </div>

                <div class="section">

                    <div class="section-title">
                        📎 Evidence Attachments
                    </div>

                    <div class="evidence">
                        {len(screenshots)} screenshot(s) attached with this report.
                    </div>

                </div>

            </div>

            <div class="footer">
                EchoVision AI Cyber Security Platform <br>
                Automated Incident Monitoring & Reporting System
            </div>

        </div>

    </body>
    </html>
    """

    msg = EmailMessage()

    msg["From"] = SENDER_EMAIL
    msg["To"] = CYBERCRIME_EMAIL
    msg["Subject"] = subject

    # Plain text fallback
    msg.set_content("Cybercrime Incident Report")

    # HTML content
    msg.add_alternative(html_body, subtype="html")

    # Attach screenshots
    for file in screenshots:

        file.file.seek(0)

        file_bytes = file.file.read()

        msg.add_attachment(
            file_bytes,
            maintype="image",
            subtype=file.content_type.split("/")[-1],
            filename=file.filename
        )

    # Send email
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465,
        context=context
    ) as server:

        server.login(
            SENDER_EMAIL,
            APP_PASSWORD
        )

        server.send_message(msg)

    print("✅ Cybercrime report email sent successfully")