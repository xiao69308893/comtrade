#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用程序常量定义
"""

# 应用程序信息
APP_NAME = "COMTRADE波形分析器"
APP_VERSION = "2.0.0"
APP_AUTHOR = "电力系统分析工具开发组"
APP_DESCRIPTION = "专业的电力系统暂态数据分析工具"
APP_COPYRIGHT = "Copyright © 2024"

# 文件相关
SUPPORTED_EXTENSIONS = ['.cfg', '.dat', '.cff']
MAX_RECENT_FILES = 10
DEFAULT_EXPORT_FORMAT = 'CSV'

# 界面相关
DEFAULT_WINDOW_WIDTH = 1400
DEFAULT_WINDOW_HEIGHT = 900
DEFAULT_SPLITTER_SIZES = [350, 1050]
MIN_WINDOW_WIDTH = 1000
MIN_WINDOW_HEIGHT = 700

# 绘图相关
DEFAULT_LINE_WIDTH = 1.0
DEFAULT_DPI = 100
MAX_PLOT_POINTS = 100000
DEFAULT_COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
]

# 故障检测阈值
DEFAULT_FAULT_THRESHOLDS = {
    'undervoltage': 0.9,      # 90% 额定电压
    'overvoltage': 1.1,       # 110% 额定电压
    'overcurrent': 2.0,       # 2倍额定电流
    'frequency_deviation': 1.0, # ±1Hz
    'thd': 5.0,              # 5% THD
    'unbalance': 2.0,        # 2% 不平衡度
    'min_fault_duration': 0.01 # 10ms最小故障持续时间
}

# 电力系统标准参数
POWER_SYSTEM_DEFAULTS = {
    'nominal_frequency': 50.0,    # 标称频率 Hz
    'nominal_voltage_levels': [   # 常见电压等级
        0.4, 0.69, 3.15, 6.3, 10.5, 13.8, 20.0, 35.0,
        66.0, 110.0, 220.0, 330.0, 500.0, 750.0, 1000.0
    ],
    'phases': ['A', 'B', 'C'],   # 三相标识
    'sequence_types': ['positive', 'negative', 'zero']  # 对称分量
}

# 谐波分析
HARMONIC_ORDERS = [2, 3, 5, 7, 11, 13, 17, 19, 23, 25]  # 常分析的谐波次数
MAX_HARMONIC_ORDER = 50

# 数据类型标识关键词
VOLTAGE_KEYWORDS = ['V', 'VOLT', 'U', '电压', 'VOLTAGE']
CURRENT_KEYWORDS = ['I', 'CURR', 'A', '电流', 'CURRENT', 'AMP']
POWER_KEYWORDS = ['P', 'Q', 'S', 'POW', '功率', 'POWER', 'WATT', 'VAR']
FREQUENCY_KEYWORDS = ['F', 'FREQ', 'HZ', '频率', 'FREQUENCY']

# 相别识别关键词
PHASE_KEYWORDS = {
    'A': ['A', 'U', 'R', '1'],
    'B': ['B', 'V', 'S', '2'],
    'C': ['C', 'W', 'T', '3'],
    'N': ['N', '0', 'NEUTRAL', '中性'],
    'AB': ['AB', 'UV', 'RS', '12'],
    'BC': ['BC', 'VW', 'ST', '23'],
    'CA': ['CA', 'WU', 'TR', '31']
}

# 故障类型颜色映射
FAULT_COLORS = {
    'SINGLE_PHASE_GROUND': '#FF4444',    # 红色
    'PHASE_TO_PHASE': '#FF8800',         # 橙色
    'TWO_PHASE_GROUND': '#CC0000',       # 深红色
    'THREE_PHASE': '#880000',            # 暗红色
    'OVERVOLTAGE': '#8800FF',            # 紫色
    'UNDERVOLTAGE': '#0088FF',           # 蓝色
    'OVERCURRENT': '#FF0000',            # 亮红色
    'FREQUENCY_DEVIATION': '#00AA00',    # 绿色
    'HARMONIC_DISTORTION': '#FFAA00',    # 黄色
    'VOLTAGE_SAG': '#00AAFF',           # 青色
    'VOLTAGE_SWELL': '#FF00AA',         # 洋红色
    'TRANSIENT': '#888888',             # 灰色
    'UNKNOWN': '#666666'                # 深灰色
}

# 数据导出格式
EXPORT_FORMATS = {
    'CSV': {
        'extension': '.csv',
        'description': 'CSV文件 (*.csv)',
        'separator': ','
    },
    'TXT': {
        'extension': '.txt',
        'description': '文本文件 (*.txt)',
        'separator': '\t'
    },
    'EXCEL': {
        'extension': '.xlsx',
        'description': 'Excel文件 (*.xlsx)',
        'separator': None
    }
}

# 图形导出格式
PLOT_EXPORT_FORMATS = {
    'PNG': {
        'extension': '.png',
        'description': 'PNG图片 (*.png)',
        'dpi': 300
    },
    'PDF': {
        'extension': '.pdf',
        'description': 'PDF文件 (*.pdf)',
        'dpi': 300
    },
    'SVG': {
        'extension': '.svg',
        'description': 'SVG矢量图 (*.svg)',
        'dpi': None
    },
    'EPS': {
        'extension': '.eps',
        'description': 'EPS文件 (*.eps)',
        'dpi': 300
    }
}

# 日志相关
LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
DEFAULT_LOG_LEVEL = 'INFO'
MAX_LOG_FILE_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# 性能相关
MAX_CHANNELS_DISPLAY = 20      # 最大同时显示通道数
MAX_DATA_POINTS_MEMORY = 1000000  # 内存中最大数据点数
ANALYSIS_CHUNK_SIZE = 10000    # 分析时的数据块大小

# 界面字符串
UI_STRINGS = {
    'loading': '正在加载...',
    'analyzing': '正在分析...',
    'completed': '完成',
    'failed': '失败',
    'ready': '就绪',
    'no_data': '无数据',
    'select_channels': '请选择通道',
    'load_file_first': '请先加载文件',
    'analysis_in_progress': '分析正在进行中',
    'export_success': '导出成功',
    'export_failed': '导出失败'
}

# 错误消息
ERROR_MESSAGES = {
    'file_not_found': '文件不存在',
    'invalid_file_format': '无效的文件格式',
    'load_failed': '文件加载失败',
    'analysis_failed': '分析失败',
    'export_failed': '导出失败',
    'insufficient_data': '数据不足',
    'memory_error': '内存不足',
    'unknown_error': '未知错误'
}

# 帮助信息
HELP_TEXTS = {
    'channel_selection': '选择要分析的通道。支持多选，按Ctrl键多选。',
    'fault_detection': '自动检测电力系统故障，包括短路、过电压、频率偏差等。',
    'harmonic_analysis': '分析信号的谐波成分，计算THD等指标。',
    'export_data': '将分析结果导出为CSV、Excel或图片格式。',
    'plot_controls': '使用鼠标缩放和平移图形，或使用工具栏按钮。'
}

# 单位定义
UNITS = {
    'voltage': ['V', 'kV', 'MV'],
    'current': ['A', 'kA', 'mA'],
    'power': ['W', 'kW', 'MW', 'var', 'kvar', 'Mvar', 'VA', 'kVA', 'MVA'],
    'frequency': ['Hz', 'kHz'],
    'time': ['s', 'ms', 'μs', 'ns'],
    'angle': ['deg', 'rad'],
    'percent': ['%'],
    'ratio': ['pu', 'p.u.']
}

# 默认文件过滤器
FILE_FILTERS = {
    'comtrade': 'COMTRADE文件 (*.cfg *.dat *.cff);;所有文件 (*)',
    'csv': 'CSV文件 (*.csv);;所有文件 (*)',
    'image': 'PNG图片 (*.png);;PDF文件 (*.pdf);;SVG图片 (*.svg);;所有文件 (*)',
    'all': '所有文件 (*)'
}

# 快捷键定义
SHORTCUTS = {
    'open': 'Ctrl+O',
    'save': 'Ctrl+S',
    'export': 'Ctrl+E',
    'quit': 'Ctrl+Q',
    'start_analysis': 'F5',
    'stop_analysis': 'Esc',
    'fullscreen': 'F11',
    'preferences': 'Ctrl+,',
    'about': 'F1'
}

# 工具提示
TOOLTIPS = {
    'open_file': '打开COMTRADE文件 (Ctrl+O)',
    'start_analysis': '开始故障检测和特征分析 (F5)',
    'stop_analysis': '停止当前分析 (Esc)',
    'export': '导出数据或图形 (Ctrl+E)',
    'zoom_in': '放大图形',
    'zoom_out': '缩小图形',
    'pan': '平移图形',
    'reset_view': '重置视图',
    'grid': '显示/隐藏网格',
    'legend': '显示/隐藏图例'
}