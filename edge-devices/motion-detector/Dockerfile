FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy sensor code
COPY sensor.py .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash sensor && \
    chown -R sensor:sensor /app

USER sensor

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import kafka; print('Healthy')" || exit 1

# Run the sensor
CMD ["python", "sensor.py"]

