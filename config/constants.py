#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置常量定义
定义应用程序中使用的各种常量
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
# 界面字符串
UI_STRINGS = {
    'app_name': 'COMTRADE波形分析器',
    'app_version': 'v2.0.0',
    'app_description': '专业的电力系统暂态数据分析工具',

    # 菜单项
    'menu_file': '文件(&F)',
    'menu_analysis': '分析(&A)',
    'menu_view': '视图(&V)',
    'menu_tools': '工具(&T)',
    'menu_help': '帮助(&H)',

    # 工具栏
    'toolbar_open': '打开',
    'toolbar_save': '保存',
    'toolbar_export': '导出',
    'toolbar_analyze': '分析',
    'toolbar_stop': '停止',

    # 状态栏
    'status_ready': '就绪',
    'status_loading': '正在加载...',
    'status_analyzing': '正在分析...',
    'status_complete': '完成',

    # 对话框
    'dialog_about': '关于',
    'dialog_preferences': '首选项',
    'dialog_export': '导出数据',

    # 按钮
    'btn_ok': '确定',
    'btn_cancel': '取消',
    'btn_apply': '应用',
    'btn_close': '关闭',
    'btn_browse': '浏览...',
    'btn_reset': '重置',

    # 通用
    'loading': '加载中...',
    'saving': '保存中...',
    'error': '错误',
    'warning': '警告',
    'info': '信息',
    'success': '成功',
}

# 电压关键词（用于自动识别电压通道）
VOLTAGE_KEYWORDS = [
    'V', 'VOLT', 'VOLTAGE', 'U', '电压', 'KV', 'MV',
    'VA', 'VB', 'VC', 'VN', 'UAB', 'UBC', 'UCA',
    'UA', 'UB', 'UC', 'UN', 'VAN', 'VBN', 'VCN'
]

# 电流关键词（用于自动识别电流通道）
CURRENT_KEYWORDS = [
    'I', 'CURR', 'CURRENT', 'A', '电流', 'IA', 'IB', 'IC', 'IN',
    'AMP', 'AMPERE', 'MA', 'KA'
]

# 相位关键词（用于相位识别）
PHASE_KEYWORDS = {
    'A': ['A', 'UA', 'IA', 'VA', 'AN', 'PHASE_A', '甲相'],
    'B': ['B', 'UB', 'IB', 'VB', 'BN', 'PHASE_B', '乙相'],
    'C': ['C', 'UC', 'IC', 'VC', 'CN', 'PHASE_C', '丙相'],
    'N': ['N', 'UN', 'IN', 'VN', 'NEUTRAL', '零线', '中性线'],
    'AB': ['AB', 'UAB', 'VAB', 'IAB'],
    'BC': ['BC', 'UBC', 'VBC', 'IBC'],
    'CA': ['CA', 'UCA', 'VCA', 'ICA', 'AC']
}

# 故障类型颜色映射
FAULT_COLORS = {
    'SINGLE_PHASE_GROUND': '#FF4444',  # 红色 - 单相接地
    'PHASE_TO_PHASE': '#FF8800',  # 橙色 - 相间短路
    'TWO_PHASE_GROUND': '#FF0000',  # 深红色 - 两相接地
    'THREE_PHASE': '#CC0000',  # 暗红色 - 三相短路
    'OVERVOLTAGE': '#8800FF',  # 紫色 - 过电压
    'UNDERVOLTAGE': '#0088FF',  # 蓝色 - 欠电压
    'OVERCURRENT': '#FF0044',  # 红粉色 - 过电流
    'FREQUENCY_DEVIATION': '#44FF00',  # 绿色 - 频率偏差
    'HARMONIC_DISTORTION': '#FFFF00',  # 黄色 - 谐波畸变
    'VOLTAGE_SAG': '#00FFFF',  # 青色 - 电压暂降
    'VOLTAGE_SWELL': '#FF00FF',  # 品红色 - 电压暂升
    'TRANSIENT': '#888888',  # 灰色 - 暂态扰动
    'UNKNOWN': '#666666'  # 深灰色 - 未知故障
}

# 快捷键定义
SHORTCUTS = {
    'open_file': 'Ctrl+O',
    'save_file': 'Ctrl+S',
    'save_as': 'Ctrl+Shift+S',
    'export': 'Ctrl+E',
    'exit': 'Ctrl+Q',

    'start_analysis': 'F5',
    'stop_analysis': 'Escape',
    'refresh': 'F5',

    'zoom_in': 'Ctrl++',
    'zoom_out': 'Ctrl+-',
    'zoom_fit': 'Ctrl+0',
    'reset_view': 'Ctrl+R',
    'pan': 'Space',
    'grid': 'Ctrl+G',
    'legend': 'Ctrl+L',

    'preferences': 'Ctrl+,',
    'about': 'F1',
    'help': 'F1',

    'fullscreen': 'F11',
    'toggle_toolbar': 'Ctrl+T',
    'toggle_statusbar': 'Ctrl+/',

    'select_all': 'Ctrl+A',
    'copy': 'Ctrl+C',
    'paste': 'Ctrl+V',
    'delete': 'Delete',
    'undo': 'Ctrl+Z',
    'redo': 'Ctrl+Y'
}

# 工具提示文本
TOOLTIPS = {
    # 文件操作
    'open_file': '打开COMTRADE文件 (Ctrl+O)',
    'save_file': '保存当前分析结果 (Ctrl+S)',
    'export': '导出数据或图形 (Ctrl+E)',
    'recent_files': '最近打开的文件',

    # 分析操作
    'start_analysis': '开始分析当前数据 (F5)',
    'stop_analysis': '停止当前分析 (Escape)',
    'analysis_config': '配置分析参数',
    'clear_results': '清除分析结果',

    # 视图操作
    'zoom_in': '放大图形 (Ctrl++)',
    'zoom_out': '缩小图形 (Ctrl+-)',
    'reset_view': '重置视图 (Ctrl+R)',
    'pan': '平移图形 (Space)',
    'grid': '显示/隐藏网格 (Ctrl+G)',
    'legend': '显示/隐藏图例 (Ctrl+L)',

    # 工具
    'preferences': '打开首选项设置 (Ctrl+,)',
    'about': '关于本软件 (F1)',
    'help': '帮助文档 (F1)',

    # 界面
    'fullscreen': '切换全屏模式 (F11)',
    'toolbar': '显示/隐藏工具栏',
    'statusbar': '显示/隐藏状态栏',

    # 通道操作
    'select_channels': '选择要显示的通道',
    'channel_info': '查看通道详细信息',
    'select_all_channels': '选择所有通道',
    'clear_selection': '清除选择',
    'voltage_channels': '选择所有电压通道',
    'current_channels': '选择所有电流通道',

    # 分析结果
    'fault_list': '故障事件列表',
    'fault_details': '查看故障详细信息',
    'zoom_to_fault': '缩放到故障时间段',
    'export_report': '导出分析报告',

    # 绘图控制
    'line_width': '设置线宽',
    'point_size': '设置数据点大小',
    'alpha': '设置透明度',
    'time_range': '设置时间显示范围'
}

# 文件类型过滤器
FILE_FILTERS = {
    'comtrade': 'COMTRADE文件 (*.cfg *.dat);;所有文件 (*)',
    'csv': 'CSV文件 (*.csv);;所有文件 (*)',
    'excel': 'Excel文件 (*.xlsx *.xls);;所有文件 (*)',
    'image': 'PNG图片 (*.png);;JPEG图片 (*.jpg);;所有图片 (*.png *.jpg *.gif *.bmp)',
    'plot': 'PNG图片 (*.png);;PDF文件 (*.pdf);;SVG图片 (*.svg);;所有文件 (*)',
    'report': '文本文件 (*.txt);;HTML文件 (*.html);;PDF文件 (*.pdf);;所有文件 (*)',
    'all': '所有文件 (*)'
}

# 数据类型定义
DATA_TYPES = {
    'analog': '模拟',
    'digital': '数字',
    'voltage': '电压',
    'current': '电流',
    'power': '功率',
    'frequency': '频率',
    'phase': '相位',
    'impedance': '阻抗'
}

# 单位定义
UNITS = {
    'voltage': ['V', 'kV', 'MV', 'mV'],
    'current': ['A', 'kA', 'mA', 'μA'],
    'power': ['W', 'kW', 'MW', 'GW', 'VAR', 'kVAR', 'MVAR'],
    'frequency': ['Hz', 'kHz', 'MHz'],
    'time': ['s', 'ms', 'μs', 'ns'],
    'angle': ['°', 'rad', 'mrad'],
    'impedance': ['Ω', 'kΩ', 'MΩ', 'mΩ'],
    'percentage': ['%']
}

# 默认配置值
DEFAULT_VALUES = {
    # 界面设置
    'window_width': 1200,
    'window_height': 800,
    'splitter_sizes': [300, 900],
    'font_family': '微软雅黑',
    'font_size': 9,

    # 绘图设置
    'line_width': 1.0,
    'grid_enabled': True,
    'grid_alpha': 0.3,
    'auto_scale': True,
    'max_points_per_plot': 10000,
    'figure_dpi': 100,
    'background_color': 'white',

    # 分析设置
    'detection_sensitivity': 3.0,
    'min_fault_duration': 0.01,
    'undervoltage_threshold': 0.9,
    'overvoltage_threshold': 1.1,
    'overcurrent_threshold': 2.0,
    'frequency_deviation_threshold': 1.0,
    'thd_threshold': 5.0,
    'unbalance_threshold': 2.0,

    # 性能设置
    'max_workers': 4,
    'memory_limit_mb': 2048,
    'parallel_processing': False,

    # 文件设置
    'max_recent_files': 10,
    'auto_save_enabled': True,
    'auto_save_interval': 5,

    # 日志设置
    'log_level': 'INFO',
    'log_retention_days': 30,
    'debug_mode': False,
    'performance_monitor': False
}

# 错误消息
ERROR_MESSAGES = {
    'file_not_found': '文件未找到',
    'file_format_error': '文件格式错误',
    'encoding_error': '文件编码错误',
    'memory_error': '内存不足',
    'analysis_error': '分析过程出错',
    'export_error': '导出失败',
    'import_error': '导入失败',
    'network_error': '网络连接错误',
    'permission_error': '权限不足',
    'unknown_error': '未知错误'
}

# 成功消息
SUCCESS_MESSAGES = {
    'file_loaded': '文件加载成功',
    'analysis_complete': '分析完成',
    'export_complete': '导出完成',
    'settings_saved': '设置已保存',
    'data_cleared': '数据已清除'
}

# 应用程序元数据
APP_METADATA = {
    'name': 'COMTRADE Analyzer',
    'display_name': 'COMTRADE波形分析器',
    'version': '2.0.0',
    'description': '专业的电力系统暂态数据分析工具',
    'author': '开发团队',
    'copyright': '© 2025 电力系统分析工具',
    'website': 'https://github.com/your-repo/comtrade-analyzer',
    'email': 'support@example.com',
    'license': 'MIT',
    'platform': 'Windows, macOS, Linux',
    'python_version': '3.8+',
    'qt_version': 'PyQt6'
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