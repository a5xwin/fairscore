FROM python:3.11-slim

# Install system dependencies needed for ML libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy entire project
COPY . .

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -r backend/requirements.txt

# Install Node dependencies
WORKDIR /app/frontend
RUN npm install

# Set working directory back to root for running services
WORKDIR /app

# Expose ports
EXPOSE 8000 5173

# Command to run both services
CMD ["python", "scripts/bootstrap_and_run.py", "--backend-host", "0.0.0.0", "--frontend-host", "0.0.0.0"]
