import numpy as np

# 基本数组操作
arr1 = np.array([1, 2, 3, 4, 5])
arr2 = np.array([2, 3, 4, 5, 6])
result = arr1 + arr2

print(f"Array 1: {arr1}")
print(f"Array 2: {arr2}")
print(f"Sum: {result}")
print(f"Mean: {np.mean(result)}")
print(f"Std: {np.std(result)}")