#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from random import *

data_scale=[10,10,100,500,1000,5000]
def make_datamaker(data_id):
    if data_id<len(data_scale):
        lenn=data_scale[data_id]
    else:
        lenn=data_scale[-1]
    n=randint(1,lenn)
    m=n//2+randint(-1,1)
    print(n,m)





def main():
    # 读取两个参数：数据编号 和 数据规模
    data_id, scale = map(int, sys.stdin.read().strip().split())
    make_datamaker(data_id)


if __name__ == "__main__":
    main()