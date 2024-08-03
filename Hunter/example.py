def test_function():
    N = int(input())
    c=list(map(int, input().split()))
    c.sort()
    Max = 0
    for i in range(N):
      K = 2*N
      Max = Max + c[K]
    print(Max)
