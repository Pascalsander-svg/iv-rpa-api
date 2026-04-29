FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install flask flask-cors reportlab pypdf requests

WORKDIR /app
COPY iv_rpa_api.py .

EXPOSE 10000

CMD ["python", "iv_rpa_api.py"]
