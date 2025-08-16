print("Before error")
# 故意制造一个错误
raise ValueError("This is a test error")
print("This line should not be reached")