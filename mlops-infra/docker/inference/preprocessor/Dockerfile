FROM python:3.9-slim

WORKDIR /app

# Устанавливаем системные зависимости (при необходимости)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt -v

COPY main.py model_loader.py prepost_processor.py ./
COPY anomaly_detector.pkl ./

# Создаём папку для ключей (будет монтироваться через secret)
RUN mkdir -p /app/keys

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
