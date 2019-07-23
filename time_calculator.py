# -*- coding: utf-8 -*-
"""
author: YangZiming、ChengYifan

input:
    {
    normX:train_data stand_scaler
    normY:target stand_scaler
    model:DNN model
    }

output:
    {
    "time_gap":predict time_gap,
     "soc_change":predict soc_change
     }

description:
    1. Change the order of features to fit the input
    2. Use dichotomy to get the result

"""

import numpy as np

from params import *


class TimeCalculator(object):
    def __init__(self, normX, normY, model, max_days, lowest_SOC):
        self.normX = normX
        self.normY = normY
        self.model = model
        self.max_days = max_days
        self.max_hours = max_days * 24
        # self.lowest_SOC = lowest_SOC
        # self.cur_soc = None

    def get_soc_change(self, input_data):
        # 对输入数据进行归一化，对预测结果恢复原始值
        norm_input_data = self.normX.transform(input_data.reshape(1, -1))
        predict = self.model.predict(norm_input_data)

        return self.normY.inverse_transform(predict)

    def make_input(self, input_df, time_gap):
        # 指定输入特征顺序
        self.cur_soc = np.float(input_df['SOC1'])
        input_df = input_df[COLUMNS_INDEX]
        input_data = np.array(input_df)

        return np.append(input_data, time_gap)

    def time_soc_predict(self, input_df):
        # 二分法输出结果
        input_array = self.make_input(input_df, self.max_hours)
        soc_change = np.float(self.get_soc_change(input_array))
        if self.cur_soc + soc_change > self.lowest_SOC:  # 最大预测时间节点的时候，SOC也没下降到警戒值
            rs = {"time_gap": self.max_hours*3600*1000, "soc_change": soc_change}
            return rs

        # 下降到低于警戒值，二分法查找
        low, high = 0, self.max_hours
        error = 2  # 足够进入while循环的值
        count = 0
        while high - low > MINHOUR or abs(error) > MINERROR:  # 当搜索区间
            count += 1
            if count > CIRCLELIMIT:
                break
            time_gap = (low + high) // 2
            input_array = self.make_input(input_df, time_gap)
            soc_change = np.float(self.get_soc_change(input_array))
            error = self.cur_soc + soc_change - self.lowest_SOC
            if error > 0:  # 预测的soc值大于最低警戒值
                low = time_gap
            else:  # 预测的soc值小于最低警戒值
                high = time_gap
        rs = {"time_gap": time_gap*3600*1000, "soc_change": soc_change}

        return rs
