FROM tensorflow/tensorflow:2.13.0-gpu

# Устанавливаем дополнительные зависимости
RUN pip install mlflow==2.9.0 minio pandas numpy opacus==1.4.0

COPY train.py /train.py

ENTRYPOINT ["python", "/train.py"]
