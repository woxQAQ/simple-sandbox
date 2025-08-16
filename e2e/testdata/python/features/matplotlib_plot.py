import matplotlib.pyplot as plt
import numpy as np

# 创建一个简单的图表
x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(8, 6))
plt.plot(x, y, label='sin(x)')
plt.xlabel('x')
plt.ylabel('sin(x)')
plt.title('Simple Sine Wave')
plt.legend()
plt.grid(True)

# 保存图表到文件
plt.savefig('/tmp/sine_wave.png')
plt.close()

print("Matplotlib plot created successfully")
print(f"Plot saved to: /tmp/sine_wave.png")