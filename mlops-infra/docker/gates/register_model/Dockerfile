FROM python:3.10-slim
RUN pip install mlflow boto3
COPY register.py /register.py
ENTRYPOINT ["python", "/register.py"]
