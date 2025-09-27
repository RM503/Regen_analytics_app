# Dockerfile for AWS EB deployment

FROM python:3.11-slim
LABEL maintainer="Rafid Mahbub" \
      version="1.1.0" \
      description="Regen Organics analytics app v1.1.0"

# Set working directory
WORKDIR /app

COPY credentials.json .

COPY . .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080 for nginx
EXPOSE 8080 

CMD ["gunicorn", "-c", "gunicorn.conf.py", "flask_app:app"]