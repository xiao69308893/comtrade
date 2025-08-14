#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析配置对话框
配置故障检测和特征分析参数
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QGroupBox, QLabel, QSpinBox, QDoubleSpinBox, QCheckBox,
    QComboBox, QLineEdit, QPushButton, QSlider, QTextEdit,
    QDialogButtonBox, QMessageBox, QFormLayout, QGridLayout,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QButtonGroup, QRadioButton, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QDoubleValidator, QIntValidator

from typing import Dict, Any, List
from analysis.fault_detector import FaultDetectionConfig
from config.constants import DEFAULT_FAULT_THRESHOLDS, POWER_SYSTEM_DEFAULTS
from utils.logger import get_logger

logger = get_logger(__name__)


class ThresholdSettingsWidget(QWidget):
    """阈值设置组件"""

    def __init__(self, config: FaultDetectionConfig):
        super().__init__()
        self.config = config
        self.threshold_widgets = {}
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 电压故障阈值
        voltage_group = QGroupBox("电压故障阈值")
        voltage_layout = QFormLayout(voltage_group)

        # 欠电压
        self.undervoltage_spin = QDoubleSpinBox()
        self.undervoltage_spin.setRange(0.1, 1.0)
        self.undervoltage_spin.setSingleStep(0.01)
        self.undervoltage_spin.setSuffix(" p.u.")
        self.undervoltage_spin.setDecimals(2)
        voltage_layout.addRow("欠电压阈值:", self.undervoltage_spin)
        self.threshold_widgets['undervoltage'] = self.undervoltage_spin

        # 过电压
        self.overvoltage_spin = QDoubleSpinBox()
        self.overvoltage_spin.setRange(1.0, 2.0)
        self.overvoltage_spin.setSingleStep(0.01)
        self.overvoltage_spin.setSuffix(" p.u.")
        self.overvoltage_spin.setDecimals(2)
        voltage_layout.addRow("过电压阈值:", self.overvoltage_spin)
        self.threshold_widgets['overvoltage'] = self.overvoltage_spin

        # 电压暂降
        self.voltage_sag_spin = QDoubleSpinBox()
        self.voltage_sag_spin.setRange(0.1, 1.0)
        self.voltage_sag_spin.setSingleStep(0.01)
        self.voltage_sag_spin.setSuffix(" p.u.")
        self.voltage_sag_spin.setDecimals(2)
        voltage_layout.addRow("电压暂降阈值:", self.voltage_sag_spin)
        self.threshold_widgets['voltage_sag'] = self.voltage_sag_spin

        # 电压暂升
        self.voltage_swell_spin = QDoubleSpinBox()
        self.voltage_swell_spin.setRange(1.0, 2.0)
        self.voltage_swell_spin.setSingleStep(0.01)
        self.voltage_swell_spin.setSuffix(" p.u.")
        self.voltage_swell_spin.setDecimals(2)
        voltage_layout.addRow("电压暂升阈值:", self.voltage_swell_spin)
        self.threshold_widgets['voltage_swell'] = self.voltage_swell_spin

        layout.addWidget(voltage_group)

        # 电流故障阈值
        current_group = QGroupBox("电流故障阈值")
        current_layout = QFormLayout(current_group)

        # 过电流
        self.overcurrent_spin = QDoubleSpinBox()
        self.overcurrent_spin.setRange(1.0, 10.0)
        self.overcurrent_spin.setSingleStep(0.1)
        self.overcurrent_spin.setSuffix(" p.u.")
        self.overcurrent_spin.setDecimals(1)
        current_layout.addRow("过电流阈值:", self.overcurrent_spin)
        self.threshold_widgets['overcurrent'] = self.overcurrent_spin

        layout.addWidget(current_group)

        # 频率故障阈值
        freq_group = QGroupBox("频率故障阈值")
        freq_layout = QFormLayout(freq_group)

        # 频率偏差
        self.freq_deviation_spin = QDoubleSpinBox()
        self.freq_deviation_spin.setRange(0.1, 5.0)
        self.freq_deviation_spin.setSingleStep(0.1)
        self.freq_deviation_spin.setSuffix(" Hz")
        self.freq_deviation_spin.setDecimals(1)
        freq_layout.addRow("频率偏差阈值:", self.freq_deviation_spin)
        self.threshold_widgets['frequency_deviation'] = self.freq_deviation_spin

        layout.addWidget(freq_group)

        # 电能质量阈值
        quality_group = QGroupBox("电能质量阈值")
        quality_layout = QFormLayout(quality_group)

        # THD阈值
        self.thd_spin = QDoubleSpinBox()
        self.thd_spin.setRange(1.0, 50.0)
        self.thd_spin.setSingleStep(0.5)
        self.thd_spin.setSuffix(" %")
        self.thd_spin.setDecimals(1)
        quality_layout.addRow("THD阈值:", self.thd_spin)
        self.threshold_widgets['thd'] = self.thd_spin

        # 不平衡度阈值
        self.unbalance_spin = QDoubleSpinBox()
        self.unbalance_spin.setRange(0.5, 10.0)
        self.unbalance_spin.setSingleStep(0.1)
        self.unbalance_spin.setSuffix(" %")
        self.unbalance_spin.setDecimals(1)
        quality_layout.addRow("不平衡度阈值:", self.unbalance_spin)
        self.threshold_widgets['unbalance'] = self.unbalance_spin

        layout.addWidget(quality_group)

        # 时间参数
        time_group = QGroupBox("时间参数")
        time_layout = QFormLayout(time_group)

        # 最小故障持续时间
        self.min_duration_spin = QDoubleSpinBox()
        self.min_duration_spin.setRange(0.001, 1.0)
        self.min_duration_spin.setSingleStep(0.001)
        self.min_duration_spin.setSuffix(" s")
        self.min_duration_spin.setDecimals(3)
        time_layout.addRow("最小故障持续时间:", self.min_duration_spin)
        self.threshold_widgets['min_fault_duration'] = self.min_duration_spin

        # 暂态窗口
        self.transient_window_spin = QDoubleSpinBox()
        self.transient_window_spin.setRange(0.01, 1.0)
        self.transient_window_spin.setSingleStep(0.01)
        self.transient_window_spin.setSuffix(" s")
        self.transient_window_spin.setDecimals(2)
        time_layout.addRow("暂态检测窗口:", self.transient_window_spin)
        self.threshold_widgets['transient_window'] = self.transient_window_spin

        layout.addWidget(time_group)

    def load_settings(self):
        """加载设置到界面"""
        self.undervoltage_spin.setValue(self.config.undervoltage_threshold)
        self.overvoltage_spin.setValue(self.config.overvoltage_threshold)
        self.voltage_sag_spin.setValue(self.config.voltage_sag_threshold)
        self.voltage_swell_spin.setValue(self.config.voltage_swell_threshold)
        self.overcurrent_spin.setValue(self.config.overcurrent_threshold)
        self.freq_deviation_spin.setValue(self.config.frequency_deviation_threshold)
        self.thd_spin.setValue(self.config.thd_threshold)
        self.unbalance_spin.setValue(self.config.unbalance_threshold)
        self.min_duration_spin.setValue(self.config.min_fault_duration)
        self.transient_window_spin.setValue(self.config.transient_window)

    def save_settings(self):
        """保存界面设置到配置"""
        self.config.undervoltage_threshold = self.undervoltage_spin.value()
        self.config.overvoltage_threshold = self.overvoltage_spin.value()
        self.config.voltage_sag_threshold = self.voltage_sag_spin.value()
        self.config.voltage_swell_threshold = self.voltage_swell_spin.value()
        self.config.overcurrent_threshold = self.overcurrent_spin.value()
        self.config.frequency_deviation_threshold = self.freq_deviation_spin.value()
        self.config.thd_threshold = self.thd_spin.value()
        self.config.unbalance_threshold = self.unbalance_spin.value()
        self.config.min_fault_duration = self.min_duration_spin.value()
        self.config.transient_window = self.transient_window_spin.value()


class SensitivitySettingsWidget(QWidget):
    """灵敏度设置组件"""

    def __init__(self, config: FaultDetectionConfig):
        super().__init__()
        self.config = config
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 检测灵敏度
        sensitivity_group = QGroupBox("检测灵敏度")
        sensitivity_layout = QFormLayout(sensitivity_group)

        # 灵敏度滑块
        sensitivity_widget = QWidget()
        sensitivity_widget_layout = QVBoxLayout(sensitivity_widget)

        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setRange(10, 100)  # 1.0 到 10.0，放大10倍
        self.sensitivity_slider.setValue(30)  # 默认3.0
        self.sensitivity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.sensitivity_slider.setTickInterval(10)
        self.sensitivity_slider.valueChanged.connect(self.update_sensitivity_label)

        # 刻度标签
        tick_layout = QHBoxLayout()
        for i in range(1, 11):
            label = QLabel(str(i))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tick_layout.addWidget(label)

        self.sensitivity_label = QLabel("3.0")
        self.sensitivity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sensitivity_label.setFont(QFont("", 12, QFont.Weight.Bold))

        sensitivity_widget_layout.addWidget(QLabel("检测灵敏度 (标准差倍数):"))
        sensitivity_widget_layout.addWidget(self.sensitivity_slider)
        sensitivity_widget_layout.addLayout(tick_layout)
        sensitivity_widget_layout.addWidget(self.sensitivity_label)

        sensitivity_layout.addRow(sensitivity_widget)

        # 灵敏度说明
        desc_label = QLabel(
            "• 数值越小，检测越灵敏，但可能产生误报\n"
            "• 数值越大，检测越稳定，但可能漏检\n"
            "• 推荐值：电力系统3.0，实验室2.0，工业现场4.0"
        )
        desc_label.setStyleSheet("QLabel { color: #666666; font-size: 11px; }")
        sensitivity_layout.addRow(desc_label)

        layout.addWidget(sensitivity_group)

        # 预设配置
        preset_group = QGroupBox("预设配置")
        preset_layout = QGridLayout(preset_group)

        # 预设按钮
        self.high_sensitive_btn = QPushButton("高灵敏度\n(实验室)")
        self.high_sensitive_btn.clicked.connect(self.load_high_sensitive_preset)
        preset_layout.addWidget(self.high_sensitive_btn, 0, 0)

        self.standard_btn = QPushButton("标准配置\n(电力系统)")
        self.standard_btn.clicked.connect(self.load_standard_preset)
        preset_layout.addWidget(self.standard_btn, 0, 1)

        self.robust_btn = QPushButton("低误报\n(工业环境)")
        self.robust_btn.clicked.connect(self.load_robust_preset)
        preset_layout.addWidget(self.robust_btn, 0, 2)

        self.custom_btn = QPushButton("自定义")
        self.custom_btn.setEnabled(False)
        preset_layout.addWidget(self.custom_btn, 1, 1)

        layout.addWidget(preset_group)

        # 高级选项
        advanced_group = QGroupBox("高级选项")
        advanced_layout = QFormLayout(advanced_group)

        # 自适应阈值
        self.adaptive_cb = QCheckBox("启用自适应阈值")
        self.adaptive_cb.setToolTip("根据信号统计特性自动调整检测阈值")
        advanced_layout.addRow(self.adaptive_cb)

        # 多尺度分析
        self.multiscale_cb = QCheckBox("启用多尺度分析")
        self.multiscale_cb.setToolTip("在不同时间尺度上进行故障检测")
        advanced_layout.addRow(self.multiscale_cb)

        # 噪声抑制
        self.noise_suppression_cb = QCheckBox("启用噪声抑制")
        self.noise_suppression_cb.setChecked(True)
        self.noise_suppression_cb.setToolTip("减少由噪声引起的误检")
        advanced_layout.addRow(self.noise_suppression_cb)

        layout.addWidget(advanced_group)

    def load_settings(self):
        """加载设置到界面"""
        # 设置灵敏度滑块
        sensitivity_value = int(self.config.detection_sensitivity * 10)
        self.sensitivity_slider.setValue(sensitivity_value)
        self.update_sensitivity_label()

        # TODO: 加载高级选项设置（待实现）

    def save_settings(self):
        """保存界面设置到配置"""
        self.config.detection_sensitivity = self.sensitivity_slider.value() / 10.0

        # TODO: 保存高级选项设置（待实现）

    def update_sensitivity_label(self):
        """更新灵敏度标签"""
        value = self.sensitivity_slider.value() / 10.0
        self.sensitivity_label.setText(f"{value:.1f}")

        # 更新颜色
        if value < 2.0:
            color = "#FF6B6B"  # 红色 - 高灵敏度
        elif value < 4.0:
            color = "#4ECDC4"  # 绿色 - 标准
        else:
            color = "#45B7D1"  # 蓝色 - 低灵敏度

        self.sensitivity_label.setStyleSheet(f"QLabel {{ color: {color}; }}")

    def load_high_sensitive_preset(self):
        """加载高灵敏度预设"""
        self.sensitivity_slider.setValue(20)  # 2.0
        self.adaptive_cb.setChecked(True)
        self.multiscale_cb.setChecked(True)
        self.noise_suppression_cb.setChecked(True)

    def load_standard_preset(self):
        """加载标准预设"""
        self.sensitivity_slider.setValue(30)  # 3.0
        self.adaptive_cb.setChecked(False)
        self.multiscale_cb.setChecked(False)
        self.noise_suppression_cb.setChecked(True)

    def load_robust_preset(self):
        """加载稳定预设"""
        self.sensitivity_slider.setValue(50)  # 5.0
        self.adaptive_cb.setChecked(False)
        self.multiscale_cb.setChecked(False)
        self.noise_suppression_cb.setChecked(True)


class FilterSettingsWidget(QWidget):
    """滤波设置组件"""

    def __init__(self, config: FaultDetectionConfig):
        super().__init__()
        self.config = config
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 预处理滤波
        preprocess_group = QGroupBox("预处理滤波")
        preprocess_layout = QFormLayout(preprocess_group)

        # 启用预处理
        self.enable_preprocess_cb = QCheckBox("启用预处理滤波")
        self.enable_preprocess_cb.setChecked(True)
        self.enable_preprocess_cb.toggled.connect(self.toggle_preprocess_options)
        preprocess_layout.addRow(self.enable_preprocess_cb)

        # 滤波器类型
        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItems(["Butterworth", "Chebyshev", "Elliptic", "Bessel"])
        preprocess_layout.addRow("滤波器类型:", self.filter_type_combo)

        # 滤波器阶数
        self.filter_order_spin = QSpinBox()
        self.filter_order_spin.setRange(2, 10)
        self.filter_order_spin.setValue(4)
        preprocess_layout.addRow("滤波器阶数:", self.filter_order_spin)

        # 截止频率
        self.cutoff_freq_spin = QDoubleSpinBox()
        self.cutoff_freq_spin.setRange(1.0, 1000.0)
        self.cutoff_freq_spin.setValue(1000.0)
        self.cutoff_freq_spin.setSuffix(" Hz")
        preprocess_layout.addRow("截止频率:", self.cutoff_freq_spin)

        layout.addWidget(preprocess_group)

        # 去噪设置
        denoise_group = QGroupBox("噪声处理")
        denoise_layout = QFormLayout(denoise_group)

        # 启用去噪
        self.enable_denoise_cb = QCheckBox("启用去噪处理")
        self.enable_denoise_cb.toggled.connect(self.toggle_denoise_options)
        denoise_layout.addRow(self.enable_denoise_cb)

        # 去噪方法
        self.denoise_method_combo = QComboBox()
        self.denoise_method_combo.addItems(["小波去噪", "中值滤波", "移动平均", "卡尔曼滤波"])
        self.denoise_method_combo.setEnabled(False)
        denoise_layout.addRow("去噪方法:", self.denoise_method_combo)

        # 去噪强度
        self.denoise_strength_slider = QSlider(Qt.Orientation.Horizontal)
        self.denoise_strength_slider.setRange(1, 10)
        self.denoise_strength_slider.setValue(5)
        self.denoise_strength_slider.setEnabled(False)
        self.denoise_strength_slider.valueChanged.connect(self.update_denoise_label)

        self.denoise_label = QLabel("中等")
        denoise_strength_layout = QHBoxLayout()
        denoise_strength_layout.addWidget(self.denoise_strength_slider)
        denoise_strength_layout.addWidget(self.denoise_label)

        denoise_layout.addRow("去噪强度:", denoise_strength_layout)

        layout.addWidget(denoise_group)

        # 信号质量评估
        quality_group = QGroupBox("信号质量评估")
        quality_layout = QFormLayout(quality_group)

        # 启用质量评估
        self.enable_quality_cb = QCheckBox("启用信号质量评估")
        self.enable_quality_cb.setToolTip("自动评估信号质量，低质量信号可能影响分析结果")
        quality_layout.addRow(self.enable_quality_cb)

        # 最小信噪比
        self.min_snr_spin = QDoubleSpinBox()
        self.min_snr_spin.setRange(1.0, 50.0)
        self.min_snr_spin.setValue(20.0)
        self.min_snr_spin.setSuffix(" dB")
        quality_layout.addRow("最小信噪比:", self.min_snr_spin)

        layout.addWidget(quality_group)

        layout.addStretch()

    def toggle_preprocess_options(self, enabled: bool):
        """切换预处理选项"""
        self.filter_type_combo.setEnabled(enabled)
        self.filter_order_spin.setEnabled(enabled)
        self.cutoff_freq_spin.setEnabled(enabled)

    def toggle_denoise_options(self, enabled: bool):
        """切换去噪选项"""
        self.denoise_method_combo.setEnabled(enabled)
        self.denoise_strength_slider.setEnabled(enabled)
        self.denoise_label.setEnabled(enabled)

    def update_denoise_label(self):
        """更新去噪强度标签"""
        value = self.denoise_strength_slider.value()
        if value <= 3:
            text = "轻微"
        elif value <= 7:
            text = "中等"
        else:
            text = "强烈"
        self.denoise_label.setText(text)


class AdvancedSettingsWidget(QWidget):
    """高级设置组件"""

    def __init__(self, config: FaultDetectionConfig):
        super().__init__()
        self.config = config
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 机器学习增强
        ml_group = QGroupBox("机器学习增强 (实验性)")
        ml_layout = QFormLayout(ml_group)

        # 启用ML
        self.enable_ml_cb = QCheckBox("启用机器学习故障识别")
        self.enable_ml_cb.setToolTip("使用预训练模型提高故障识别准确度")
        ml_layout.addRow(self.enable_ml_cb)

        # 模型选择
        self.ml_model_combo = QComboBox()
        self.ml_model_combo.addItems(["随机森林", "支持向量机", "神经网络", "集成模型"])
        self.ml_model_combo.setEnabled(False)
        self.enable_ml_cb.toggled.connect(self.ml_model_combo.setEnabled)
        ml_layout.addRow("模型类型:", self.ml_model_combo)

        # 置信度阈值
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.1, 1.0)
        self.confidence_spin.setValue(0.8)
        self.confidence_spin.setSingleStep(0.1)
        self.confidence_spin.setEnabled(False)
        self.enable_ml_cb.toggled.connect(self.confidence_spin.setEnabled)
        ml_layout.addRow("置信度阈值:", self.confidence_spin)

        layout.addWidget(ml_group)

        # 并行处理
        parallel_group = QGroupBox("并行处理")
        parallel_layout = QFormLayout(parallel_group)

        # 启用并行处理
        self.enable_parallel_cb = QCheckBox("启用多线程处理")
        self.enable_parallel_cb.setChecked(True)
        self.enable_parallel_cb.toggled.connect(self.toggle_parallel_options)
        parallel_layout.addRow(self.enable_parallel_cb)

        # 线程数
        self.thread_count_spin = QSpinBox()
        self.thread_count_spin.setRange(1, 16)
        self.thread_count_spin.setValue(4)
        parallel_layout.addRow("线程数量:", self.thread_count_spin)

        # 内存限制
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setRange(512, 8192)
        self.memory_limit_spin.setValue(2048)
        self.memory_limit_spin.setSuffix(" MB")
        parallel_layout.addRow("内存限制:", self.memory_limit_spin)

        layout.addWidget(parallel_group)

        # 输出选项
        output_group = QGroupBox("输出选项")
        output_layout = QFormLayout(output_group)

        # 详细日志
        self.verbose_log_cb = QCheckBox("详细日志输出")
        output_layout.addRow(self.verbose_log_cb)

        # 中间结果
        self.save_intermediate_cb = QCheckBox("保存中间结果")
        self.save_intermediate_cb.setToolTip("保存特征提取等中间步骤的结果")
        output_layout.addRow(self.save_intermediate_cb)

        # 生成报告
        self.auto_report_cb = QCheckBox("自动生成分析报告")
        self.auto_report_cb.setChecked(True)
        output_layout.addRow(self.auto_report_cb)

        layout.addWidget(output_group)

        # 专家模式
        expert_group = QGroupBox("专家模式")
        expert_layout = QVBoxLayout(expert_group)

        # 自定义算法
        algorithm_layout = QHBoxLayout()
        algorithm_layout.addWidget(QLabel("自定义算法配置:"))

        self.algorithm_edit_btn = QPushButton("编辑算法")
        self.algorithm_edit_btn.clicked.connect(self.edit_custom_algorithm)
        algorithm_layout.addWidget(self.algorithm_edit_btn)

        expert_layout.addLayout(algorithm_layout)

        # 配置文件
        config_layout = QHBoxLayout()
        config_layout.addWidget(QLabel("配置文件:"))

        self.load_config_btn = QPushButton("加载配置")
        self.load_config_btn.clicked.connect(self.load_config_file)
        config_layout.addWidget(self.load_config_btn)

        self.save_config_btn = QPushButton("保存配置")
        self.save_config_btn.clicked.connect(self.save_config_file)
        config_layout.addWidget(self.save_config_btn)

        expert_layout.addLayout(config_layout)

        layout.addWidget(expert_group)

        layout.addStretch()

    def toggle_parallel_options(self, enabled: bool):
        """切换并行处理选项"""
        self.thread_count_spin.setEnabled(enabled)
        self.memory_limit_spin.setEnabled(enabled)

    def edit_custom_algorithm(self):
        """编辑自定义算法"""
        # TODO: 实现算法编辑器
        QMessageBox.information(self, "功能开发中", "自定义算法编辑器正在开发中...")

    def load_config_file(self):
        """加载配置文件"""
        # TODO: 实现配置文件加载
        QMessageBox.information(self, "功能开发中", "配置文件加载功能正在开发中...")

    def save_config_file(self):
        """保存配置文件"""
        # TODO: 实现配置文件保存
        QMessageBox.information(self, "功能开发中", "配置文件保存功能正在开发中...")


class AnalysisConfigDialog(QDialog):
    """分析配置对话框主类"""

    def __init__(self, config: FaultDetectionConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.backup_config = None  # 用于取消时恢复

        self.init_ui()
        self.setup_connections()
        self.backup_current_config()

        # 设置对话框属性
        self.setWindowTitle("分析配置")
        self.setModal(True)
        self.resize(650, 700)

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 标题
        title_label = QLabel("故障检测与分析配置")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 阈值设置标签页
        self.threshold_widget = ThresholdSettingsWidget(self.config)
        self.tab_widget.addTab(self.threshold_widget, "⚙️ 阈值设置")

        # 灵敏度设置标签页
        self.sensitivity_widget = SensitivitySettingsWidget(self.config)
        self.tab_widget.addTab(self.sensitivity_widget, "🎯 灵敏度")

        # 滤波设置标签页
        self.filter_widget = FilterSettingsWidget(self.config)
        self.tab_widget.addTab(self.filter_widget, "🔧 滤波设置")

        # 高级设置标签页
        self.advanced_widget = AdvancedSettingsWidget(self.config)
        self.tab_widget.addTab(self.advanced_widget, "🔬 高级设置")

        layout.addWidget(self.tab_widget)

        # 按钮组
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.RestoreDefaults
        )

        # 设置按钮文本
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("确定")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        button_box.button(QDialogButtonBox.StandardButton.Apply).setText("应用")
        button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults).setText("恢复默认")

        layout.addWidget(button_box)

        # 连接按钮信号
        button_box.accepted.connect(self.accept_changes)
        button_box.rejected.connect(self.reject_changes)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_changes)
        button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self.restore_defaults)

    def setup_connections(self):
        """设置信号连接"""
        # 可以在这里添加实时预览等功能
        pass

    def backup_current_config(self):
        """备份当前配置"""
        # TODO: 实现配置备份
        # 创建配置的深拷贝
        pass

    def accept_changes(self):
        """接受更改"""
        self.apply_changes()
        self.accept()

    def reject_changes(self):
        """拒绝更改"""
        # TODO: 恢复备份的配置
        self.reject()

    def apply_changes(self):
        """应用更改"""
        try:
            # 保存各标签页的设置
            self.threshold_widget.save_settings()
            self.sensitivity_widget.save_settings()

            # TODO: 保存其他标签页的设置

            logger.info("分析配置已更新")

        except Exception as e:
            logger.error(f"保存分析配置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存配置失败：\n{str(e)}")

    def restore_defaults(self):
        """恢复默认设置"""
        reply = QMessageBox.question(
            self, "确认", "确定要恢复所有设置为默认值吗？\n这将丢失当前的自定义设置。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 重置配置为默认值
            self.config = FaultDetectionConfig()

            # 重新加载界面
            self.threshold_widget.load_settings()
            self.sensitivity_widget.load_settings()

            QMessageBox.information(self, "提示", "配置已恢复为默认值")

    def get_config(self) -> FaultDetectionConfig:
        """获取当前配置"""
        return self.config