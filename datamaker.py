#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import random


def make_datamaker(data_id):




def main():
    # 读取两个参数：数据编号 和 数据规模
    data_id, scale = map(int, sys.stdin.read().strip().split())
    make_datamaker(data_id)


if __name__ == "__main__":
    main()