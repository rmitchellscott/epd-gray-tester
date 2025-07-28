FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    imagemagick \
    fontconfig \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p /app/output

CMD ["python", "generate_test_image.py"]