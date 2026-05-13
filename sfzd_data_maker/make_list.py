from random import randint,sample


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

def make_unique_list(n, l, r):
    if n > r - l + 1:
        raise ValueError("n 不能大于区间内可用的整数个数")
    return sample(range(l, r+1), n)
