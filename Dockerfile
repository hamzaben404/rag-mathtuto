# 1) Use a lightweight Python base image
FROM python:3.11-slim

# 2) Set working directory inside the container
WORKDIR /app

# 3) Turn off Python bytecode & buffering (optional, good practice)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 4) Install system dependencies if needed (minimal here)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# 5) Copy requirements and install them
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 6) Copy the rest of your project code
COPY . /app

# 7) Default env for services INSIDE Docker
#    Here Meilisearch and Qdrant are on your HOST, so we use host.docker.internal
ENV MEILI_HOST="http://host.docker.internal:7700"
ENV QDRANT_URL="http://host.docker.internal:6333"

# 8) Expose port for FastAPI
EXPOSE 8000

# 9) Command to run the app
#    0.0.0.0 so the container accepts external connections
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
