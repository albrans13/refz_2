FROM python:3.9-slim

WORKDIR /app

# تثبيت gcc + أدوات البناء اللازمة لـ tgcrypto
RUN apt-get update && apt-get install -y gcc build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY repo /app

RUN if [ -f "/app/requirements.txt" ]; then \
        pip install --no-cache-dir -r /app/requirements.txt; \
    fi

CMD ["python", "main.py"]
