def test_function():
    from collections import deque
    n = int(input())
    dl = deque()
    for _ in range(n):
        cmd = input()
        if ' ' in cmd:
            op,v = cmd.split()
        else:
            op = cmd
        if   op == 'insert'     : dl.appendleft(v) 
        elif op == 'delete'     : dl.remove(v) 
        elif op == 'deleteFirst': dl.popleft() 
        elif op == 'deleteLast' : dl.pop() 
    print(*dl)
