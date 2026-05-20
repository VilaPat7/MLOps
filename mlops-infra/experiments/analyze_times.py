import re
import numpy as np
from scipy import stats

def extract_times(logfile):
    times = []
    with open(logfile, 'r') as f:
        for line in f:
            # Ищем строку вида "real    0m45.2s"
            m = re.search(r'real\s+(\d+)m([\d\.]+)s', line)
            if m:
                minutes = int(m.group(1))
                seconds = float(m.group(2))
                total_sec = minutes * 60 + seconds
                times.append(total_sec)
    return times

baseline = extract_times('baseline_time.log')
protected = extract_times('protected_time.log')

print(f"Baseline (без гейтов): среднее = {np.mean(baseline):.2f} с, std = {np.std(baseline):.2f}")
print(f"Protected (с гейтами): среднее = {np.mean(protected):.2f} с, std = {np.std(protected):.2f}")

t_stat, p_value = stats.ttest_ind(baseline, protected)
print(f"t-статистика: {t_stat:.3f}, p-value: {p_value:.5f}")
if p_value < 0.05:
    print("Различие статистически значимо (p < 0.05)")
else:
    print("Различие не значимо (p >= 0.05)")
