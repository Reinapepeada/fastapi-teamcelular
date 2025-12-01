FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Use a Python entrypoint that waits for DB, runs migrations, then starts the app.
ENTRYPOINT ["python", "docker-entrypoint.py"]
# Default command: start uvicorn (can be overridden in runtime)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
