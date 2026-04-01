from random import randint


def pr_deep(n):
    for i in range(len(n)):
        if isinstance(n[i], list):
            pr(n[i])
        else:
            print(n[i], end=' ')
def pr(n):
    pr_deep(n)
    print()
def make_list(n,l,r):
    res=[]
    for i in range(n):
        res.append(randint(l,r))
    return res
