FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
EXPOSE 8000
CMD ["sh", "-c", "python -c 'import asyncio; from app.jobs import run_user_sync; print(asyncio.run(run_user_sync(\"fd871b21-071f-4c00-b10f-d46988e1a4b1\", None)))' && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
