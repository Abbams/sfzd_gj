#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import sys
from random import *
from sfzd_data_maker import *

data_scale=[10,10,100,500,1000,5000,10000,200000]
fixed_data=[0,[1,10],#1
            [2,10],#2
            [3,10],#3
            [10,10],#4
            [10,11],#5
            [10,13],#6
            [100,1000],#7
            [1,10000],#8
            [1,123],#9
            [123,1220]]#10
def make_datamaker(data_id):
    print(fixed_data[data_id][0],fixed_data[data_id][1])
    return

    if data_id<len(data_scale):
        lenn=randint(data_scale[data_id-1],data_scale[data_id])
    else:
        lenn=data_scale[-1]
    n=lenn
    print(n)
    pr(make_list(n,1,2e5))





def main():
    # 读取两个参数：数据编号 和 数据规模
    data_id, scale = map(int, sys.stdin.read().strip().split())
    make_datamaker(data_id)


if __name__ == "__main__":
    main()