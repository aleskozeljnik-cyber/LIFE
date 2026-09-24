# LIFE API

FastAPI service for the T1a LIFE implementation.

## Run locally

1. Copy `.env.example` to `.env` and provide the database, session and encryption secrets.
2. Install dependencies: `pip install -r requirements.txt`.
3. Start: `uvicorn app.main:app --reload --port 8000`.

The service intentionally returns authentication/configuration errors until the required Google OAuth and database secrets are configured. This keeps the public API from pretending that demo data is real user data.
