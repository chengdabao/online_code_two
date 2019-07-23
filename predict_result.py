# -*- coding: utf-8 -*-
"""
author: ChengYifan

input:
    {
    data: receive kafka data(json)
    model: time_calculator
    }

output:
    something wrong :{"vin": "wrong", "signal_type": "none", "soc1": 0, "time_stamp": 0}
    start soc<65 :{"vin": self._vin, "signal_type": self._SignalType, "soc1": self._SOC1, "time_stamp": self._time}
    normal result:{"vin": "LGWEE5A50JH532583", "timestamp": 1564539654128, "soc_predict": 77.83793139457703}

description:
    1. Check input data feature
    2. Use time_calculator  get the result

"""

import pandas as pd
import numpy as np
import logging

from params import *


class Predict(object):
    def __init__(self, data, model_one, model_two):
        self._vin = data["vin"]
        self._SignalType = data["canSignalType"]
        self._time = int(data["reportTime"])
        self._SOC1 = int(data["SOC1"])

        # 参数可配kafka模型，大哥上游需做对应字段的增加
        self.max_day_yellow = int(data["MAXDAYS_YELLOW"])
        self.max_day_red = int(data["MAXDAYS_RED"])
        self.lowest_soc_yellow = int(data["LOWESTSOC_YELLOW"])
        self.lowest_soc_red = int(data["LOWESTSOC_RED"])

        data.pop("vin")
        data.pop("reportTime")
        data.pop("canSignalType")
        self.data = data
        self.model_one = model_one
        self.model_two = model_two

    def check_convert(self):
        # 匹配输入特征、对不存在特征数据进行补0、排除输入特征数不足数据
        ip_data = pd.DataFrame([self.data])
        types = ip_data.convert_objects(convert_numeric=True).dtypes
        ip_data = ip_data.astype(types)
        cross_columns = list(set(INPUT_PARAMS) & set(ip_data.columns))
        if len(cross_columns) < COLUMNS_LIMIT:
            raise ValueError("input feature is not enough")
        else:
            # 补零
            # convert_data = pd.DataFrame(np.zeros((1, len(INPUT_PARAMS))), columns=INPUT_PARAMS)
            # 补中值
            convert_data = pd.read_csv(MEDIAN_DATA, index_col=0)
            types = convert_data.convert_objects(convert_numeric=True).dtypes
            convert_data = convert_data.astype(types)
            convert_data[cross_columns] = ip_data[cross_columns]

        return convert_data

    def model_predict(self):
        try:
            predict_input = self.check_convert()
            # 如果当前soc小于黄色预警大于红色预警阈值，则红色预警用模型输出，黄色预警取当前数值
            if self._SOC1 < self.lowest_soc_yellow & self._SOC1 > self.lowest_soc_red:
                result_red = self.model_help(predict_input, self.model_two)
                result_yellow = {"vin": self._vin, "signal_type": self._SignalType, "soc_predict": self._SOC1,
                                 "time_stamp": self._time}
            # 如果当前soc小于红色预警阈值，则红色预警用当前数值，黄色预警无法输出
            elif self._SOC1 < self.lowest_soc_red:
                result_red = {"vin": self._vin, "signal_type": self._SignalType, "soc_predict": self._SOC1,
                              "time_stamp": self._time}
                result_yellow = {"vin": self._vin, "signal_type": self._SignalType, "soc_predict": -1,
                                 "time_stamp": -1}
            # 如果soc大于黄色预警阈值，则二者都用模型输出
            else:
                result_red = self.model_help(predict_input, self.model_two)
                result_yellow = self.model_help(predict_input, self.model_one)

                if result_red["time_stamp"] < result_yellow["time_stamp"]:
                    result_red = {"vin": self._vin, "signal_type": self._SignalType, "soc_predict": -1,
                                  "time_stamp": self._time+self.max_day_red*24*3600*1000}

            # result = {"red": result_red, "yellow": result_yellow, "vin": self._vin}
            result = {"vin": str(self._vin), "signal_type": str(self._SignalType),
                      "red_soc": int(result_red["soc_predict"]), "yellow_soc": int(result_yellow["soc_predict"]),
                      "red_time": int(result_red["time_stamp"]/1000), "yellow_time": int(result_yellow["time_stamp"]/1000)}

        except:
            logging.error('xxxxxxxxxx Something Wrong In Model xxxxxxxxxxx', exc_info=True)
            result_red = {"vin": self._vin, "signal_type": self._SignalType, "soc_predict": -1,
                          "time_stamp": self._time+self.max_day_red*24*3600*1000}
            result_yellow = {"vin": self._vin, "signal_type": self._SignalType, "soc_predict": -1,
                             "time_stamp": self._time + self.max_day_yellow * 24 * 3600 * 1000}

            # result = {"red": result_red, "yellow": result_yellow, "vin": self._vin}
            result = {"vin": str(self._vin), "signal_type": str(self._SignalType),
                      "red_soc": int(result_red["soc_predict"]), "yellow_soc": int(result_yellow["soc_predict"]),
                      "red_time": int(result_red["time_stamp"]/1000), "yellow_time": int(result_yellow["time_stamp"]/1000)}

        return result

    def model_help(self, predict_input, model):
        ####### model_predict ########
        result = model.time_soc_predict(predict_input)
        ##############################

        result["vin"] = self._vin
        result["signal_type"] = self._SignalType
        result["time_stamp"] = self._time + result["time_gap"]
        result["soc_predict"] = self._SOC1 + result["soc_change"]

        # 保证结果一定>0 且<100
        if result["soc_predict"] < 0 or result["soc_predict"] > 100:
            raise ValueError("input feature is wrong")

        result.pop("time_gap")
        result.pop("soc_change")

        return result


