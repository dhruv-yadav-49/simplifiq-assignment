"""
mailer.py — Email Delivery via SendGrid
Sends the generated PDF as an attachment to the prospect.
Falls back to SMTP if SendGrid is not configured.
"""

import os
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName,
    FileType, Disposition
)


def send_email(to_name: str, to_email: str,
               company: str, pdf_path: str) -> bool:
    """
    Sends the audit PDF to the prospect.
    First tries SMTP (if configured), then tries SendGrid, and falls back to SMTP if SendGrid fails.
    Returns True on success, False on failure.
    """
    from_email   = os.getenv("FROM_EMAIL", "noreply@simplifiq.ai")
    from_name    = os.getenv("FROM_NAME", "SimplifIQ Team")
    subject      = f"Your Personalized AI Audit Report — {company}"

    # Email body template
    body_html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
      <h2 style="color: #1a1a2e;">Hi {to_name},</h2>
      <p>Thank you for your interest in <strong>SimplifIQ</strong>.</p>
      <p>We've prepared a <strong>personalized AI audit report</strong> for <strong>{company}</strong>,
         highlighting key opportunities where intelligent automation can drive real results for your team.</p>
      <p>Please find the full report attached to this email.</p>
      <br/>
      <p>Looking forward to connecting,<br/>
         <strong>{from_name}</strong><br/>
         SimplifIQ | AI-Powered Business Intelligence
      </p>
      <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;"/>
      <p style="font-size: 12px; color: #888;">
        This report was generated automatically based on publicly available information.
        If you have questions, reply to this email.
      </p>
    </div>
    """

    # ── 1. Try SMTP if configured in .env ─────────────────────────
    smtp_user = os.getenv("EMAIL_SENDER") or os.getenv("SMTP_USER") or os.getenv("FROM_EMAIL")
    smtp_pass = os.getenv("EMAIL_PASSWORD") or os.getenv("SMTP_PASSWORD")
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")

    # Auto-detect Gmail SMTP host/port if a Gmail address is used and host is not set
    if smtp_user and smtp_pass and not smtp_host:
        if "@gmail.com" in smtp_user.lower():
            smtp_host = "smtp.gmail.com"
            smtp_port = "587"

    # Override from_email with EMAIL_SENDER if present
    if smtp_user:
        from_email = smtp_user

    if smtp_host and smtp_user and smtp_pass:
        print(f"[EMAIL] Trying SMTP delivery via {smtp_host}:{smtp_port}...")
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders

        try:
            msg = MIMEMultipart()
            msg['From'] = f"{from_name} <{from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body_html, 'html'))

            # Attach PDF
            with open(pdf_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={company.replace(' ', '_')}_AI_Audit_Report.pdf",
                )
                msg.attach(part)

            server = smtplib.SMTP(smtp_host, int(smtp_port or 587))
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())
            server.quit()
            print("[EMAIL] Sent successfully via SMTP!")
            return True
        except Exception as e:
            print(f"[EMAIL] SMTP Delivery failed: {e}. Falling back to SendGrid...")

    # ── 2. Try SendGrid ───────────────────────────────────────────
    sendgrid_key = os.getenv("SENDGRID_API_KEY")
    if sendgrid_key and not sendgrid_key.startswith("YOUR_"):
        print("[EMAIL] Trying SendGrid delivery...")
        try:
            # Read and encode PDF
            with open(pdf_path, "rb") as f:
                pdf_data = base64.b64encode(f.read()).decode()

            message = Mail(
                from_email=(from_email, from_name),
                to_emails=to_email,
                subject=subject,
                html_content=body_html
            )

            # Attach PDF
            attachment = Attachment(
                file_content=FileContent(pdf_data),
                file_name=FileName(f"{company.replace(' ', '_')}_AI_Audit_Report.pdf"),
                file_type=FileType("application/pdf"),
                disposition=Disposition("attachment")
            )
            message.attachment = attachment

            sg = SendGridAPIClient(sendgrid_key)
            response = sg.send(message)
            print(f"[EMAIL] Sent successfully via SendGrid! Status: {response.status_code}")
            return response.status_code in (200, 202)
        except Exception as e:
            print(f"[EMAIL] SendGrid failed: {e}")
            return False

    print("[EMAIL] No valid mail configurations found (SMTP or SendGrid). Skipping email.")
    return False
