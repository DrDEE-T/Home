"""
auth.py — Run once to complete Gmail OAuth2 authorization.
Generates token.json which briefing.py uses for all future sends.

Usage:
    python auth.py
"""

import sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CREDENTIALS_FILE = Path("credentials.json")
TOKEN_FILE = Path("token.json")


def authorize() -> None:
    if not CREDENTIALS_FILE.exists():
        print(
            "ERROR: credentials.json not found.\n"
            "Download your OAuth2 credentials from Google Cloud Console and\n"
            "place credentials.json in the project root directory."
        )
        sys.exit(1)

    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            print("Token refreshed successfully.")
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
            print("Authorization successful.")

        TOKEN_FILE.write_text(creds.to_json())
        TOKEN_FILE.chmod(0o600)
        print(f"Token saved to {TOKEN_FILE}")
    else:
        print("Existing token is valid. No action needed.")


if __name__ == "__main__":
    authorize()
