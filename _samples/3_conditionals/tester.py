a = int(input())
b = int(input())


if a > b:
    a = a - b
elif a == b:
    a = 0
else:
    b = b - a

print(a) 