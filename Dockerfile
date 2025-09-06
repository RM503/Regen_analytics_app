# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY credentials.json .
COPY . .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["gunicorn", "flask_app:app", "--bind", "0.0.0.0:8000", "--timeout", "120"]