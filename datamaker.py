#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import random

data_scale=[10,10,100,500,1000,5000]
def make_datamaker(data_id):
    if data_id<len(data_scale):
        n=data_scale[data_id]
    else:
        n=data_scale[-1]





def main():
    # 读取两个参数：数据编号 和 数据规模
    data_id, scale = map(int, sys.stdin.read().strip().split())
    make_datamaker(data_id)


if __name__ == "__main__":
    main()