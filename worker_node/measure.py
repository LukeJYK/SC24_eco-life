import os
import sys
import re
def get_info(output):
    pattern1 = r"Energy consumed: (\d+\.\d+)"
    pattern2 = r"Runtime: (\d+\.\d+)"
    matches1 = re.findall(pattern1, output)
    matches2 = re.findall(pattern2, output)
    power_consumed_values = [float(match) for match in matches1]
    runtime= [float(match) for match in matches2]
    return power_consumed_values, runtime

app = sys.argv[1]
result = os.popen("sudo likwid-powermeter python3 node.py " + app).read()
a, b = get_info(result)
print(a[0]+a[2],a[1]+a[3], sum(b))