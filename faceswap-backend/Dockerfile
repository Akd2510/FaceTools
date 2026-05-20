# Use the full Python image (Debian Bookworm based)
FROM python:3.11-bookworm

# Set the working directory
WORKDIR /app

# Update and install modern OpenCV runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Environment variables
ENV MODELS_DIR=/app/models
ENV TEMPLATES_DIR=/app/templates
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Command is usually overridden by docker-compose, but providing a default:
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
