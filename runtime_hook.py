# -*- coding: utf-8 -*-
"""运行时性能优化钩子"""

import os
import sys

# 优化环境变量
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
os.environ['PYTHONOPTIMIZE'] = '1'
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 设置matplotlib后端
import matplotlib
matplotlib.use('Qt6Agg')

# 禁用numpy警告提升性能
import numpy as np
np.seterr(all='ignore')

# 预加载常用模块减少延迟
import pandas
import scipy.signal
import PyQt6.QtCore
import PyQt6.QtGui
import PyQt6.QtWidgets
