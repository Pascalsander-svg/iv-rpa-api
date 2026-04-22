FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget curl gnupg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install flask playwright flask-cors

RUN playwright install chromium --with-deps

WORKDIR /app
COPY iv_rpa_api.py .

EXPOSE 10000

CMD ["python", "iv_rpa_api.py"]
