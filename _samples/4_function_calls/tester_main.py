def mult(a, b):
    mult_r = 0
    while b > 0:
        mult_r = mult_r + a
        b = b - 1
    return mult_r

a = int(input())
b = int(input())
c = mult(a,b)
print(c)
