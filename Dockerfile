# Dockerfile for AWS EB deployment

FROM python:3.11-slim
LABEL maintainer="Rafid Mahbub" \
      version="1.1.0" \
      description="Regen Organics analytics app v1.1.0"

# Set working directory
WORKDIR /app

ENV PYTHONPATH=/app:/app/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port 8080 for nginx
EXPOSE 8080 

CMD ["gunicorn", "-c", "gunicorn.conf.py", "flask_app:app"]
