# -*- coding: utf-8 -*-
"""
author: ChengYifan

function:
    check_transform:
        check the data types

    producer_callback:
        log produce status

    Communicate:
        Encapsulation kafka consumer、producer

"""


import logging
import json

from params import *
from time_calculator import TimeCalculator
from sklearn.externals import joblib
from predict_result import Predict
from confluent_kafka import Consumer, Producer, KafkaError
from logging.handlers import RotatingFileHandler
from keras.models import load_model

# 捕获log
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 定义log.name与路径
filename = os.path.join(LOGS_DIR, LOGS_NAME)
if not os.path.exists(LOGS_DIR):
    os.mkdir(LOGS_DIR)

# 控制log数量，定义输出格式
fh = RotatingFileHandler(filename=filename, maxBytes=1024 * 1024 * 10, backupCount=5, encoding='UTF-8')  # 总体格式与外部名称
fh.setLevel(logging.INFO)
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
fh.setFormatter(formatter)  # 文件内部格式

# 将格式运用于log
logger.addHandler(fh)


def check_transform(data):
    if isinstance(data, bytes):
        data = json.loads(data.decode("utf-8"))
    elif isinstance(data, str):
        data = json.loads(data)
    else:
        raise ValueError("json string must be str or bytes")

    return data


def producer_callback(err, msg):
    """
    由kafka producer自动调用，
    将produce成功/失败的记录保存到日志。
    """
    vin = json.loads(msg.value().decode('utf-8'))["vin"]
    if err:
        # 将produce失败信息保存到日志
        logger.exception("**********Fail to produce.**********"
                         "vin: %s\n%s" % (vin, err.str()), stack_info=True)
    else:
        # 将produce成功信息保存到日志
        logger.info("Produce successfully.\nvin: %s" % vin)


class Communicate(object):
    """
    封装kafka的consumer和producer
    """
    def __init__(self):
        self.c = Consumer(CONSUMER_SETTINGS)
        self.p = Producer(PRODUCER_SETTINGS)
        self.c.subscribe(REQUEST_TOPICS)
        # 加载模型
        self.train_scaler = joblib.load("./model_parameter/scaler_train")
        self.target_scaler = joblib.load("./model_parameter/scaler_test")
        self.origin_model = load_model(MODEL_PARAMS)
        # self.model_one = TimeCalculator(train_scaler, target_scaler, origin_model)
        # self.model_two = TimeCalculator(train_scaler, target_scaler, origin_model)

    def communicate(self):
        try:
            while True:
                request = self.c.poll(0.1)
                if request is None:
                    continue
                elif not request.error():
                    try:
                        # 将consume成功的message的offset和partition保存到日志
                        logger.info("Accept msg from kafka successfully.\n"
                                    "topic: %s | offset: %d | partition: %d" %
                                    (request.topic(), request.offset(), request.partition()))
                        receive_data = check_transform(request.value())
                        
                        model_yellow = TimeCalculator(
                            self.train_scaler, self.target_scaler, self.origin_model,
                            int(receive_data["MAXDAYS_YELLOW"]), int(receive_data["LOWESTSOC_YELLOW"]))
                        model_red = TimeCalculator(
                            self.train_scaler, self.target_scaler, self.origin_model,
                            int(receive_data["MAXDAYS_RED"]), int(receive_data["LOWESTSOC_RED"]))

                        ############# model_predict##############
                        response_data = Predict(receive_data, model_yellow, model_red).model_predict()
                        #########################################

                        self.p.produce(
                            topic=RESPONSE_TOPICS,
                            key=str(response_data["vin"]),
                            value=json.dumps(response_data).encode('utf-8'),
                            callback=producer_callback)

                        self.p.poll(0.5)

                    except Exception as e:
                        # 将模型调用异常信息保存到日志
                        logger.exception(e, stack_info=True)

                elif request.error().code() == KafkaError._PARTITION_EOF:
                    # 表示数据已consume完
                    # 将topic/partition已consume完的情况保存到日志
                    logger.info('##########End of partition reached {0}/{1}.##########'
                                .format(request.topic(), request.partition()))
                else:
                    # 将kafka传输异常信息保存到日志
                    logger.exception(
                        '**********Error occured: {0}.**********'.format(request.error().str()))

        # 手动停止consumer监听
        except KeyboardInterrupt as e:
            logger.info("**********Keyboard Interrupt.**********")
        # 将kafka未知异常保存到日志
        except Exception as e:
            logger.exception(e, stack_info=True)
        finally:
            # 关闭consumer
            self.c.close()
            logger.critical('**********consumer was closed.**********')

if __name__ == "__main__":
    Communicate().communicate()