import numpy as np
arr = np.array([2,3,5,8,13])
s = sum(arr)
prob = []
for i in arr:
    prob.append(i/s)

print(prob)
