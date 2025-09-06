# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY credentials.json .
COPY . .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "flask_app:app"]