FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies and clean up in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories and user
RUN mkdir -p /app/profiles \
    && useradd -m appuser \
    && chown -R appuser:appuser /app

# Copy only necessary files
COPY --chown=appuser:appuser . .

USER appuser

# Run the application
CMD ["gunicorn", "permitter.wsgi:application", "--bind", "0.0.0.0:8000"] 