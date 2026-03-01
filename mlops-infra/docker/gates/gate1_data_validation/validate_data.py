#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import json

def load_data(data_path):
    if data_path.endswith('.csv'):
        return pd.read_csv(data_path)
    elif data_path.endswith('.parquet'):
        return pd.read_parquet(data_path)
    else:
        raise ValueError("Unsupported file format")

def check_label_distribution(df, label_col='label', threshold_sigma=3):
    counts = df[label_col].value_counts()
    mean = counts.mean()
    std = counts.std()
    anomalies = {}
    for label, count in counts.items():
        z_score = (count - mean) / std if std != 0 else 0
        if abs(z_score) > threshold_sigma:
            anomalies[str(label)] = float(z_score)
    return anomalies

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-path', type=str, required=True)
    parser.add_argument('--threshold-sigma', type=float, default=3.0)
    parser.add_argument('--label-col', type=str, default='label')
    parser.add_argument('--output-report', type=str, default='report.json')
    args = parser.parse_args()

    df = load_data(args.data_path)
    anomalies = check_label_distribution(df, args.label_col, args.threshold_sigma)

    result = {
        "passed": len(anomalies) == 0,
        "anomalies": anomalies,
        "threshold_sigma": args.threshold_sigma
    }
    with open(args.output_report, 'w') as f:
        json.dump(result, f, indent=2)

    exit(0 if result["passed"] else 1)

if __name__ == "__main__":
    main()
