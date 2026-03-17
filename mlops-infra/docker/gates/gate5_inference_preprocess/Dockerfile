FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY preprocess.py anomaly_detector.pkl ./
ENTRYPOINT ["python", "/app/preprocess.py"]
