FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
ENV DATABASE_URL="postgresql+psycopg://medical_rag_user:change_this_strong_password@postgres:5432/medical_rag"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
