FROM python:3.13-slim

WORKDIR /app

# System deps for psycopg2 (sync driver used by Alembic migrations)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make startup script executable
RUN chmod +x start.sh

EXPOSE 8000

# start.sh: runs alembic upgrade head, then uvicorn on $PORT (Railway injects this)
CMD ["./start.sh"]
