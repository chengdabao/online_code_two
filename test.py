import pandas as pd
import numpy as np

from params import *

convert_data = pd.read_csv(MEDIAN_DATA, index_col=0).T
print(convert_data.columns)
print(convert_data.values)
convert_data = pd.DataFrame(convert_data.values, columns=convert_data.columns)
print(convert_data)
convert_data.to_csv("ok.csv")
