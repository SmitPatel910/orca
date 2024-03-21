def testFun():
    for i in range(n):
        total += i
        if (i + total) % 2 == 0:
            ans = ("Even")
            continue
        else:
            ans = ("Odd")
            total = total + i
        total = total + 1
    total= 1 / (total-13)