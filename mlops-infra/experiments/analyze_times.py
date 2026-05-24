import re
import numpy as np
from scipy import stats

def extract_times(logfile):
    times = []
    with open(logfile, 'r') as f:
        for line in f:
            m = re.search(r'real\s+(\d+)m([\d\.]+)s', line)
            if m:
                minutes = int(m.group(1))
                seconds = float(m.group(2))
                total_sec = minutes * 60 + seconds
                times.append(total_sec)
    return times

baseline = extract_times('baseline_time.log')
protected = extract_times('protected_time.log')

print(f"Baseline (without gates): average= {np.mean(baseline):.2f} с, std = {np.std(baseline):.2f}")
print(f"Protected (with gates): average = {np.mean(protected):.2f} с, std = {np.std(protected):.2f}")

t_stat, p_value = stats.ttest_ind(baseline, protected)
print(f"t-statistics: {t_stat:.3f}, p-value: {p_value:.5f}")
if p_value < 0.05:
    print("The difference is statistically significant (p < 0.05)")
else:
    print("The difference is not significant (p >= 0.05)")
