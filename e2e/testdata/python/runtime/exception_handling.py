try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"Caught exception: {e}")
    print("Exception handled successfully")