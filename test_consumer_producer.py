import json
import pandas as pd
import numpy as np
import json
from confluent_kafka import Consumer, Producer, KafkaError
from params import *


def action_consumer():

    c = Consumer(CONSUMER_SETTINGS)
    # c.subscribe([RESPONSE_TOPICS])
    c.subscribe(REQUEST_TOPICS)
    while True:
        msg = c.poll(1.0)
        if msg is None:
            continue
        elif not msg.error():
            print('Received message: {}'.format(msg.value().decode('utf-8')))

        elif msg.error():
            print(msg.error())
            # if msg.error().code() == KafkaError._PARTITION_EOF:
            #     break
            # else:
            #     print(msg.error())
            #     break
    c.close()


def action_producer(produce_data,i):

    _data = json.dumps(produce_data)
    p = Producer(PRODUCER_SETTINGS)

    def delivery_report(err, msg):
        """ Called once for each message produced to indicate delivery result.
            Triggered by poll() or flush(). """
        if err is not None:
            print('Message delivery failed: {}'.format(err))
        else:
            print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))

    # Trigger any available delivery report callbacks from previous produce() calls
    p.poll(0)

    # Asynchronously produce a message, the delivery report callback
    # will be triggered from poll() above, or flush() below, when the message has
    # been successfully delivered or failed permanently.

    p.produce(topic=REQUEST_TOPICS[0], key=str(i), value=_data.encode('utf-8'), callback=delivery_report)

    # Wait for any outstanding messages to be delivered and delivery report
    # callbacks to be triggered.
    p.flush()


if __name__ == "__main__":

    df = pd.read_csv(r"D:\jupyter_analysis\四维项目\长城电池项目\项目code\data\01_choke_0628_soc1.csv")
    ex = pd.read_excel(r"D:\离职交接\已上线\长城_电池预警\需求文档\整车CAN信号标准数据字典V3.5-20190516.xlsx", sheet_name="CHB027新")
    new_ex = ex["标准项字段（英文）"]
    new_ex.index = ex["采集项（CHB027）"]
    dic = new_ex.to_dict()
    df.rename(columns=dic, inplace=True)
    df.rename(columns={"vc:reportTime": "reportTime", "vc:vin": "vin"}, inplace=True)
    for i in range(100):
        ip_data = df.iloc[i].to_dict()
        ip_data["vin"] = "{}".format(i)
        ip_data["canSignalType"] = "CH88"
        print(ip_data)
        action_producer(ip_data,i)

    # action_consumer()


    # action_producer()