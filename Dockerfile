FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt setup.py ./
COPY mpesa_kit ./mpesa_kit
RUN pip install --no-cache-dir .

ENV MPESA_DB_PATH=/data/mpesa_events.db
EXPOSE 8000
CMD ["kenyapay", "serve", "--host", "0.0.0.0", "--port", "8000"]
