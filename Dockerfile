FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN python -m pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend

CMD ["sh", "-c", "cd backend && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
