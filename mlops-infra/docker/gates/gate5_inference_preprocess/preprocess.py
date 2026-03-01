#!/usr/bin/env python3
import argparse
import json
import pickle
import numpy as np
from pydantic import BaseModel, ValidationError, validator
from typing import List

class InputData(BaseModel):
    image: List[List[List[float]]]

    @validator('image')
    def check_shape(cls, v):
        if len(v) != 32:
            raise ValueError('Image must have 32 rows')
        for row in v:
            if len(row) != 32:
                raise ValueError('Each row must have 32 columns')
            for pixel in row:
                if len(pixel) != 3:
                    raise ValueError('Each pixel must have 3 channels')
        return v

def load_anomaly_detector(model_path):
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def detect_anomaly(detector, image_np, threshold=0.1):
    reconstructed = detector.predict(image_np[np.newaxis, ...], verbose=0)
    mse = np.mean((image_np - reconstructed[0]) ** 2)
    return mse < threshold, mse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-json', type=str, required=True)
    parser.add_argument('--anomaly-detector', type=str, required=True)
    parser.add_argument('--anomaly-threshold', type=float, default=0.1)
    parser.add_argument('--output-json', type=str, default='preprocessed.json')
    parser.add_argument('--output-report', type=str, default='preprocess_report.json')
    args = parser.parse_args()

    with open(args.input_json, 'r') as f:
        raw_data = json.load(f)

    # 1. Валидация Pydantic
    try:
        validated = InputData(**raw_data)
    except ValidationError as e:
        report = {"passed": False, "error": str(e)}
        with open(args.output_report, 'w') as f:
            json.dump(report, f, indent=2)
        exit(1)

    # 2. Детекция аномалий
    detector = load_anomaly_detector(args.anomaly_detector)
    image_np = np.array(validated.image, dtype=np.float32)
    is_clean, mse = detect_anomaly(detector, image_np, args.anomaly_threshold)

    if not is_clean:
        report = {"passed": False, "error": "Adversarial example detected", "mse": mse}
        with open(args.output_report, 'w') as f:
            json.dump(report, f, indent=2)
        exit(1)

    # Сохраняем предобработанные данные
    with open(args.output_json, 'w') as f:
        json.dump(validated.dict(), f)

    report = {"passed": True, "mse": mse}
    with open(args.output_report, 'w') as f:
        json.dump(report, f, indent=2)
    exit(0)

if __name__ == "__main__":
    main()
