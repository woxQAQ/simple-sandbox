import numpy as np
import sys

print("Starting memory intensive test...")
print(f"Initial memory usage: {sys.getsizeof([])} bytes")

# 尝试分配大量内存
large_list = []
for i in range(1000000):
    large_list.append(i * 2)
    if i % 100000 == 0:
        print(f"Processed {i} elements, current list size: {sys.getsizeof(large_list)} bytes")

# 使用numpy创建大型数组
print("Creating large numpy array...")
large_array = np.random.random((1000, 1000))
print(f"Large array shape: {large_array.shape}, size: {large_array.nbytes} bytes")

# 计算一些统计信息
print(f"Array mean: {large_array.mean()}")
print(f"Array std: {large_array.std()}")

print("Memory intensive test completed successfully")