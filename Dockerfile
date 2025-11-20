FROM python:3.9-slim

WORKDIR /app

# تثبيت gcc وأدوات البناء
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY repo /app

RUN if [ -f "/app/requirements.txt" ]; then \
        pip install --upgrade pip && \
        pip install --no-cache-dir -r /app/requirements.txt; \
    fi

CMD ["python", "main.py"]
