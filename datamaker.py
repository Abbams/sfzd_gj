#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import sys
from sfzd_data_maker import *
# a_z =['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
# A_Z= ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']

data_scale=[10,50,100,1000,10000,100000,500000,500000]
fixed_data=[0]#10
def make_datamaker(data_id):
    # print(fixed_data[data_id][0],fixed_data[data_id][1])
    if data_id>=len(data_scale):
        id=len(data_scale)-1
        data_scale[id]-=random.randint(0,5)
    else:
        id=data_id


    # pr(make_list(data_scale[id],1,1000))

    # print_edges(g)






def main():
    # 读取两个参数：数据编号 和 数据规模
    data_id, scale = map(int, sys.stdin.read().strip().split())
    make_datamaker(data_id)


if __name__ == "__main__":
    main()