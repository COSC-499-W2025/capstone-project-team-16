# Use an official Python runtime as a parent image. The 'slim' variant is smaller.
FROM python:3.11-slim as base

# Set environment variables to prevent Python from writing .pyc files
# and to ensure output is sent straight to the terminal without buffering.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# --- Dependency Installation ---
# First, copy only the requirements file to leverage Docker's layer caching.
# If requirements.txt doesn't change, this layer won't be rebuilt on subsequent builds.
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# --- Application Code ---
# Copy the application source code into the container at /app
COPY src/ ./src/

# --- Runtime Configuration ---
# Specify the command to run on container startup.
# Using '-m' ensures that Python's module resolution works correctly
# for your project structure (e.g., 'from .contracts import ...').
ENTRYPOINT ["python", "-m", "src.main"]