# Dockerfile for AWS EB deployment

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy credentials.json first (for caching)
COPY credentials.json .

# Copy the rest of the application
COPY . .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Ensure Flask binds to 0.0.0.0
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8080
EXPOSE 8080

# Use Gunicorn to run the Flask app
CMD ["gunicorn", "-c", "gunicorn.conf.py", "flask_app:app"]