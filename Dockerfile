FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY io_manager.py .
COPY entrypoint.sh /app/entrypoint.sh
COPY config/ config/

RUN chmod +x /app/entrypoint.sh

EXPOSE 8010
ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
