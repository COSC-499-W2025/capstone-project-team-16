# Use official lightweight Python image
FROM python:3.12-slim

# Install git (required by GitPython)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the src folder (excluding files in .dockerignore)
COPY src/ ./src/

# Set working directory to src so main.py can run directly
WORKDIR /app/src

# Default command to run the app
CMD ["python", "main.py"]
