import numpy as np
from numba import cuda

@cuda.jit
def add_arrays(a, b, c):
    idx = cuda.threadIdx.x
    if idx < a.size:
        c[idx] = a[idx] + b[idx]

# Define arrays
a = np.array([1, 2, 3, 4, 5], dtype=np.float32)
b = np.array([10, 20, 30, 40, 50], dtype=np.float32)
c = np.empty_like(a)

# Transfer arrays to device
d_a = cuda.to_device(a)
d_b = cuda.to_device(b)
d_c = cuda.to_device(c)

# Launch kernel
add_arrays[1, a.size](d_a, d_b, d_c)

# Copy result back to host
d_c.copy_to_host(c)
print(c)
