import time
import os

# 输入输出数据的topic
REQUEST_TOPICS = ["ntd_soc_model_request_test1"]
RESPONSE_TOPICS = "ntd_soc_model_result_test1"

# 消费者生产者的设置
CONSUMER_SETTINGS = {
    'bootstrap.servers': '172.22.52.81:9092,172.22.52.88:9092,172.22.52.93:9092',
    'group.id': 'ntd_soc_model_2019_7_10',
    'client.id': 'ntd-chengyifan',
    'enable.auto.commit': True,
    'session.timeout.ms': 6000,
    'default.topic.config': {'auto.offset.reset': 'smallest'}
}

PRODUCER_SETTINGS = {
    'bootstrap.servers': '172.22.52.81:9092,172.22.52.88:9092,172.22.52.93:9092'
}

# log地址
LOGS_DIR = './logs'

# log名称
LOGS_NAME = 'battery_predict_20190717.log'

# 模型加载地址
MODEL_PARAMS = "./model_parameter/Battery_Regression_try.hdf5"
TRAIN_SCALER = "./model_parameter/scaler_train"
TEST_SCALER = "./model_parameter/scaler_test"
MEDIAN_DATA = "./model_parameter/median.csv"

# 模型输入特征
INPUT_PARAMS = ['Q_Charge', 'BattChrgLmpSts', 'Blind_charge_Quickmode',
                'EngSpd', 'DrivDoorSts', 'SOH_COR', 'SOCWU', 'SOH_SUL_G',
                'VehicleSpd', 'DisChargeCurrWU', 'U_BATT_Stored',
                'VehTotDistance', 'IBATT_Quiescent', 'ChargeCurrWU',
                'SOH_LAM', 'RLDoorSts', 'T_BATT_Stored', 'SOC1', 'U_BATT',
                'AntitheftSts', 'SOX_Mode', 'SOH_COR_Sts', 'PosnLmpSts',
                'SOC_Stored', 'SOC_Sts', 'SOFV_StopEnable', 'TempSts',
                'SystemPowerMod', 'TrunkSts', 'LowBeamSts', 'SOFV_Restart_Sts',
                'SOH_LAM_Sts', 'PassDoorSts', 'CurrSts', 'SOFV_Restart',
                'TGSLever', 'QuickMod_Sts', 'EngSts', 'I_RANGE', 'SOH_SUL_Sts',
                'HoodSts', 'JumpStart_Quickmode', 'I_RANGE_Stored', 'VoltSts',
                'ACFrntBlwSpd', 'RRDoorSts', 'Q_Discharge', 'T_BATT',
                'HighBeamSts', 'SOFV_StopEnable_Sts', 'I_BATT_Stored']

# 模型特征顺序
COLUMNS_INDEX = ['PosnLmpSts', 'I_BATT_Stored', 'SOFV_StopEnable', 'I_RANGE',
                 'TempSts', 'ACFrntBlwSpd', 'LowBeamSts',  'HoodSts', 'U_BATT',
                 'SOH_LAM_Sts', 'T_BATT_Stored', 'DisChargeCurrWU',
                 'Blind_charge_Quickmode', 'EngSts', 'I_RANGE_Stored',
                 'Q_Discharge', 'TrunkSts', 'RRDoorSts', 'SOC_Stored',
                 'SOH_SUL_G', 'U_BATT_Stored', 'SOH_COR', 'CurrSts',
                 'SOFV_StopEnable_Sts', 'T_BATT', 'SOFV_Restart', 'SystemPowerMod',
                 'EngSpd', 'BattChrgLmpSts', 'SOX_Mode', 'AntitheftSts', 'VehicleSpd',
                 'TGSLever', 'PassDoorSts', 'QuickMod_Sts', 'SOH_COR_Sts', 'SOCWU',
                 'VoltSts', 'SOH_LAM', 'ChargeCurrWU', 'RLDoorSts', 'JumpStart_Quickmode',
                 'DrivDoorSts', 'VehTotDistance', 'IBATT_Quiescent', 'HighBeamSts',
                 'SOC1', 'SOC_Sts', 'Q_Charge', 'SOFV_Restart_Sts', 'SOH_SUL_Sts']

# 模型特征对应排序
COLUMNS_DICT = {'PosnLmpSts': 0, 'I_BATT_Stored': 1, 'SOFV_StopEnable': 2,
                'I_RANGE': 3, 'TempSts': 4, 'ACFrntBlwSpd': 5, 'LowBeamSts': 6,
                'HoodSts': 7, 'U_BATT': 8, 'SOH_LAM_Sts': 9, 'T_BATT_Stored': 10,
                'DisChargeCurrWU': 11, 'Blind_charge_Quickmode': 12, 'EngSts': 13,
                'I_RANGE_Stored': 14, 'Q_Discharge': 15, 'TrunkSts': 16,
                'RRDoorSts': 17, 'SOC_Stored': 18, 'SOH_SUL_G': 19, 'U_BATT_Stored': 20,
                'SOH_COR': 21, 'CurrSts': 22, 'SOFV_StopEnable_Sts': 23, 'T_BATT': 24,
                'SOFV_Restart': 25, 'SystemPowerMod': 26, 'EngSpd': 27,
                'BattChrgLmpSts': 28, 'SOX_Mode': 29, 'AntitheftSts': 30,
                'VehicleSpd': 31, 'TGSLever': 32, 'PassDoorSts': 33, 'QuickMod_Sts': 34,
                'SOH_COR_Sts': 35, 'SOCWU': 36, 'VoltSts': 37, 'SOH_LAM': 38,
                'ChargeCurrWU': 39, 'RLDoorSts': 40, 'JumpStart_Quickmode': 41,
                'DrivDoorSts': 42, 'VehTotDistance': 43, 'IBATT_Quiescent': 44,
                'HighBeamSts': 45, 'SOC1': 46, 'SOC_Sts': 47, 'Q_Charge': 48,
                'SOFV_Restart_Sts': 49, 'SOH_SUL_Sts': 50, 'time_gap': 51}

# 特征重合数量底线
COLUMNS_LIMIT = 10

# 二分法最小时间间隔（小时）
MINHOUR = 1

# 二分法最小SOC差值
MINERROR = 1

# 二分法查找次数限制
CIRCLELIMIT = 20

# # 二分法最大时间yellow（天）
# MAXDAYS_YELLOW = 40
#
# # 二分法最大时间red（天）
# MAXDAYS_RED = 45
#
# # SOC黄色警戒
# LOWESTSOC_YELLOW = 80
#
# # SOC红色警戒
# LOWESTSOC_RED = 70
