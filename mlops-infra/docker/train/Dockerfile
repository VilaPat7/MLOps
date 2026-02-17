FROM tensorflow/tensorflow:2.13.0-gpu
RUN pip install mlflow==2.9.0 minio pandas numpy
COPY train.py /train.py
ENTRYPOINT ["python", "/train.py"]
