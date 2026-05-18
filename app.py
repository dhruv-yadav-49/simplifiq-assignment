"""
app.py — SimplifIQ Assessment
Main Flask server. Handles form submission and orchestrates the full workflow:
  Lead Form → Enrichment → PDF → Email → (Bonus) Sheets/Drive
"""

import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, render_template
from enricher import enrich_company
from pdf_generator import generate_pdf
from mailer import send_email
from bonus_logger import log_to_sheets, upload_to_drive

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("form.html")



@app.route("/submit", methods=["POST"])
def submit():
    # ── Step 1: Capture & validate form data ──────────────────────────
    data = request.form
    name    = data.get("name", "").strip()
    email   = data.get("email", "").strip()
    company = data.get("company", "").strip()
    website = data.get("website", "").strip()
    role    = data.get("role", "").strip()

    if not all([name, email, company]):
        return jsonify({"error": "Name, email, and company are required."}), 400

    print(f"\n[LEAD] {name} | {email} | {company} | {website}")

    # ── Step 2: Enrich company data ────────────────────────────────────
    print("[ENRICH] Scraping and enriching company data...")
    enriched = enrich_company(company, website)

    # ── Step 3: Generate PDF report ────────────────────────────────────
    print("[PDF] Generating personalized audit report...")
    pdf_path = generate_pdf(name=name, email=email, company=company,
                             role=role, enriched=enriched)

    # ── Step 4: Send email with PDF ────────────────────────────────────
    print("[EMAIL] Sending report to prospect...")
    email_sent = send_email(to_name=name, to_email=email,
                             company=company, pdf_path=pdf_path)

    # ── Step 5 (BONUS): Google Sheets logging + Drive upload ──────────
    report_status = "Sent" if email_sent else "Failed"
    drive_link = ""
    try:
        drive_link = upload_to_drive(pdf_path=pdf_path, company=company)
    except Exception as e:
        print(f"[BONUS] Google Drive upload skipped: {e}")

    try:
        log_to_sheets(name=name, email=email, company=company,
                      status=report_status, drive_link=drive_link)
    except Exception as e:
        print(f"[BONUS] Google Sheets logging skipped: {e}")

    return jsonify({
        "message": f"Report sent successfully to {email}!",
        "status": report_status
    })


if __name__ == "__main__":
    os.makedirs("output_pdfs", exist_ok=True)
    app.run(debug=True, port=5000)
