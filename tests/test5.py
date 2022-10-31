import numpy as np


x = np.random.random((4,4))

rsum = None
csum = None

while (np.any(rsum != 1)) | (np.any(csum != 1)):
    x /= x.sum(0)
    x = x / x.sum(1)[:, np.newaxis]
    rsum = x.sum(1)
    csum = x.sum(0)

print(x)