FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default — overridden by cron docker run commands
CMD ["python", "-m", "ingestion.main", "today"]
