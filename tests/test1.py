import matplotlib.pyplot as plt
from comtrade import Comtrade

cfgFile = "ZH5X_RCD_2517_20240427_054924_244_S.CFG"
datFile = "ZH5X_RCD_2517_20240427_054924_244_S.DAT"
rec = Comtrade()
rec.load(cfgFile, datFile)
# 模拟通道的数量
analog_count = rec.analog_count

# 循环获取模拟通道的名称
for i in range(analog_count):
    print(rec.analog_channel_ids[i])

# 开关量通道的数量
digital_count = rec.digital_count
# 循环获取开关量通道的名称
for i in range(digital_count):
    print(rec.digital_channel_ids[i])

# 循环输出81个模拟量通道的采集数据
for analog in rec.analog:
    print(analog)

# 打印采集时间
print(rec.time)

# 打印采集的时间戳
print(rec.start_timestamp)

# 处理前三个通道的波形数据,因数据量过大,此处只取前250个点的采集数据
plt.rcParams['font.family'] = 'SimHei'
plt.figure()
plt.plot(rec.time[0:250], rec.analog[0][0:250])
plt.plot(rec.time[0:250], rec.analog[1][0:250])
plt.plot(rec.time[0:250], rec.analog[2][0:250])
plt.legend([rec.analog_channel_ids[0], rec.analog_channel_ids[1],rec.analog_channel_ids[2]])
plt.show()