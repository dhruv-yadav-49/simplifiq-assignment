"""
bonus_logger.py — Google Sheets Logging + Google Drive PDF Archiving (BONUS)

Setup:
1. Go to Google Cloud Console → Enable Sheets API + Drive API
2. Create a Service Account → Download credentials.json
3. Share your Google Sheet with the service account email
4. Set GOOGLE_SHEET_ID in .env
"""

import os
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CREDENTIALS_FILE = "credentials.json"
if not os.path.exists(CREDENTIALS_FILE) and os.path.exists("credentials.json.json"):
    CREDENTIALS_FILE = "credentials.json.json"

SHEET_ID   = os.getenv("GOOGLE_SHEET_ID", "")
DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")


def _get_service(api: str, version: str):
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    return build(api, version, credentials=creds)


def log_to_sheets(name: str, email: str, company: str, status: str, drive_link: str = "") -> None:
    """
    Appends a new row to the Google Sheet matching the exact columns:
    Timestamp | Company Name | Contact Email | Contact Name | Report Status | PDF Link
    """
    if not SHEET_ID or not os.path.exists(CREDENTIALS_FILE):
        raise ValueError("Google Sheets not configured.")

    service = _get_service("sheets", "v4")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [[timestamp, company, email, name, status, drive_link]]

    service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range="A:F",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": row}
    ).execute()
    print(f"[SHEETS] Logged: {company} | {name} | {status} | {drive_link}")


def upload_to_drive(pdf_path: str, company: str) -> str:
    """
    Uploads the PDF to a Google Drive folder.
    Returns the shareable Drive link.
    """
    if not DRIVE_FOLDER_ID or not os.path.exists(CREDENTIALS_FILE):
        raise ValueError("Google Drive not configured.")

    service = _get_service("drive", "v3")
    file_name = f"{company.replace(' ', '_')}_AI_Audit_Report.pdf"

    file_metadata = {
        "name": file_name,
        "parents": [DRIVE_FOLDER_ID]
    }
    media = MediaFileUpload(pdf_path, mimetype="application/pdf")

    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink"
    ).execute()

    link = uploaded.get("webViewLink", "")
    print(f"[DRIVE] Uploaded: {link}")
    return link
