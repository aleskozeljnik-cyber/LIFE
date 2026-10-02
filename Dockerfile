FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN python -m pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend

CMD ["sh", "-c", "cd backend && echo SYNC_BEGIN && python -c 'import asyncio; from app.jobs import run_user_sync; r=asyncio.run(run_user_sync(\"fd871b21-071f-4c00-b10f-d46988e1a4b1\",\"gmail\")); print(\"SYNC_GMAIL\",r.get(\"gmail\")); r=asyncio.run(run_user_sync(\"fd871b21-071f-4c00-b10f-d46988e1a4b1\",\"calendar\")); print(\"SYNC_CALENDAR\",r.get(\"calendar\"))' && echo SYNC_END && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
