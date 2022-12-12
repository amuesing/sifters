import numpy as np

def compute_transition_matrix2(data, n, step = 1):
    
    t = np.array(data)
    step = step
    total_inds = t.size - (step + 1) + 1
    t_strided = np.lib.stride_tricks.as_strided(
                                    t,
                                    shape = (total_inds, 2),
                                    strides = (t.strides[0], step * t.strides[0]))
    
    inds, counts = np.unique(t_strided, axis = 0, return_counts = True)

    P = np.zeros((n, n))
    P[inds[:, 0], inds[:, 1]] = counts
    
    sums = P.sum(axis = 1)
    # Avoid divide by zero error by normalizing only non-zero rows
    P[sums != 0] = P[sums != 0] / sums[sums != 0][:, None]
    
    # P = P / P.sum(axis = 1)[:, None]
    return P

print(compute_transition_matrix2([60, 64, 67, 72, 76], 78, 1))