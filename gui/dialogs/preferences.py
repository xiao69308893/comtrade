#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
首选项对话框
应用程序设置配置界面
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QGroupBox, QLabel, QSpinBox, QDoubleSpinBox, QCheckBox,
    QComboBox, QLineEdit, QPushButton, QColorDialog, QFontDialog,
    QFileDialog, QSlider, QButtonGroup, QRadioButton, QTextEdit,
    QDialogButtonBox, QMessageBox, QFormLayout, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette

from config.settings import AppSettings, PlotSettings, AnalysisSettings, UISettings
from config.constants import LOG_LEVELS, SHORTCUTS, DEFAULT_COLORS
from utils.logger import get_logger

logger = get_logger(__name__)


class PlotSettingsWidget(QWidget):
    """绘图设置组件"""

    def __init__(self, settings: PlotSettings):
        super().__init__()
        self.settings = settings
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 基本绘图设置
        basic_group = QGroupBox("基本设置")
        basic_layout = QFormLayout(basic_group)

        # 线宽
        self.line_width_spin = QDoubleSpinBox()
        self.line_width_spin.setRange(0.1, 10.0)
        self.line_width_spin.setSingleStep(0.1)
        self.line_width_spin.setSuffix(" px")
        basic_layout.addRow("线宽:", self.line_width_spin)

        # DPI
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(50, 300)
        self.dpi_spin.setSingleStep(10)
        basic_layout.addRow("图形DPI:", self.dpi_spin)

        # 背景色
        self.bg_color_btn = QPushButton()
        self.bg_color_btn.setMinimumHeight(30)
        self.bg_color_btn.clicked.connect(self.choose_background_color)
        basic_layout.addRow("背景颜色:", self.bg_color_btn)

        layout.addWidget(basic_group)

        # 网格设置
        grid_group = QGroupBox("网格设置")
        grid_layout = QFormLayout(grid_group)

        self.grid_enabled_cb = QCheckBox("显示网格")
        grid_layout.addRow(self.grid_enabled_cb)

        self.grid_alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self.grid_alpha_slider.setRange(0, 100)
        self.grid_alpha_slider.valueChanged.connect(self.update_grid_alpha_label)

        self.grid_alpha_label = QLabel("30%")
        grid_alpha_layout = QHBoxLayout()
        grid_alpha_layout.addWidget(self.grid_alpha_slider)
        grid_alpha_layout.addWidget(self.grid_alpha_label)

        grid_layout.addRow("网格透明度:", grid_alpha_layout)

        layout.addWidget(grid_group)

        # 性能设置
        performance_group = QGroupBox("性能设置")
        performance_layout = QFormLayout(performance_group)

        self.auto_scale_cb = QCheckBox("自动缩放")
        performance_layout.addRow(self.auto_scale_cb)

        self.max_points_spin = QSpinBox()
        self.max_points_spin.setRange(1000, 1000000)
        self.max_points_spin.setSingleStep(10000)
        self.max_points_spin.setSuffix(" 点")
        performance_layout.addRow("最大绘图点数:", self.max_points_spin)

        layout.addWidget(performance_group)

        layout.addStretch()

    def load_settings(self):
        """加载设置到界面"""
        self.line_width_spin.setValue(self.settings.line_width)
        self.dpi_spin.setValue(self.settings.figure_dpi)
        self.grid_enabled_cb.setChecked(self.settings.grid_enabled)
        self.grid_alpha_slider.setValue(int(self.settings.grid_alpha * 100))
        self.auto_scale_cb.setChecked(self.settings.auto_scale)
        self.max_points_spin.setValue(self.settings.max_points_per_plot)

        # 设置背景色按钮
        self.update_background_color_button()
        self.update_grid_alpha_label()

    def save_settings(self):
        """保存界面设置到配置"""
        self.settings.line_width = self.line_width_spin.value()
        self.settings.figure_dpi = self.dpi_spin.value()
        self.settings.grid_enabled = self.grid_enabled_cb.isChecked()
        self.settings.grid_alpha = self.grid_alpha_slider.value() / 100.0
        self.settings.auto_scale = self.auto_scale_cb.isChecked()
        self.settings.max_points_per_plot = self.max_points_spin.value()

    def choose_background_color(self):
        """选择背景颜色"""
        current_color = QColor(self.settings.background_color)
        color = QColorDialog.getColor(current_color, self, "选择背景颜色")

        if color.isValid():
            self.settings.background_color = color.name()
            self.update_background_color_button()

    def update_background_color_button(self):
        """更新背景色按钮显示"""
        color = self.settings.background_color
        self.bg_color_btn.setStyleSheet(f"QPushButton {{ background-color: {color}; }}")
        self.bg_color_btn.setText(color)

    def update_grid_alpha_label(self):
        """更新网格透明度标签"""
        value = self.grid_alpha_slider.value()
        self.grid_alpha_label.setText(f"{value}%")


class AnalysisSettingsWidget(QWidget):
    """分析设置组件"""

    def __init__(self, settings: AnalysisSettings):
        super().__init__()
        self.settings = settings
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 故障检测阈值
        fault_group = QGroupBox("故障检测阈值")
        fault_layout = QFormLayout(fault_group)

        self.fault_threshold_spin = QDoubleSpinBox()
        self.fault_threshold_spin.setRange(1.0, 10.0)
        self.fault_threshold_spin.setSingleStep(0.1)
        self.fault_threshold_spin.setSuffix(" σ")
        fault_layout.addRow("检测灵敏度:", self.fault_threshold_spin)

        self.min_fault_duration_spin = QDoubleSpinBox()
        self.min_fault_duration_spin.setRange(0.001, 1.0)
        self.min_fault_duration_spin.setSingleStep(0.001)
        self.min_fault_duration_spin.setSuffix(" s")
        self.min_fault_duration_spin.setDecimals(3)
        fault_layout.addRow("最小故障持续时间:", self.min_fault_duration_spin)

        layout.addWidget(fault_group)

        # 频率分析
        freq_group = QGroupBox("频率分析")
        freq_layout = QFormLayout(freq_group)

        self.fundamental_freq_spin = QDoubleSpinBox()
        self.fundamental_freq_spin.setRange(45.0, 65.0)
        self.fundamental_freq_spin.setSingleStep(0.1)
        self.fundamental_freq_spin.setSuffix(" Hz")
        freq_layout.addRow("基波频率:", self.fundamental_freq_spin)

        # 谐波次数设置
        self.harmonic_edit = QLineEdit()
        self.harmonic_edit.setPlaceholderText("例如: 2,3,5,7,11,13")
        freq_layout.addRow("分析谐波次数:", self.harmonic_edit)

        layout.addWidget(freq_group)

        # 窗口分析
        window_group = QGroupBox("窗口分析")
        window_layout = QFormLayout(window_group)

        self.window_size_spin = QDoubleSpinBox()
        self.window_size_spin.setRange(0.001, 1.0)
        self.window_size_spin.setSingleStep(0.001)
        self.window_size_spin.setSuffix(" s")
        self.window_size_spin.setDecimals(3)
        window_layout.addRow("分析窗口大小:", self.window_size_spin)

        self.overlap_ratio_spin = QDoubleSpinBox()
        self.overlap_ratio_spin.setRange(0.0, 0.9)
        self.overlap_ratio_spin.setSingleStep(0.1)
        self.overlap_ratio_spin.setSuffix("%")
        window_layout.addRow("窗口重叠比例:", self.overlap_ratio_spin)

        layout.addWidget(window_group)

        # 预设配置
        preset_group = QGroupBox("预设配置")
        preset_layout = QVBoxLayout(preset_group)

        preset_btn_layout = QHBoxLayout()

        self.power_system_btn = QPushButton("电力系统标准")
        self.power_system_btn.clicked.connect(self.load_power_system_preset)
        preset_btn_layout.addWidget(self.power_system_btn)

        self.sensitive_btn = QPushButton("高灵敏度")
        self.sensitive_btn.clicked.connect(self.load_sensitive_preset)
        preset_btn_layout.addWidget(self.sensitive_btn)

        self.robust_btn = QPushButton("低误报")
        self.robust_btn.clicked.connect(self.load_robust_preset)
        preset_btn_layout.addWidget(self.robust_btn)

        preset_layout.addLayout(preset_btn_layout)
        layout.addWidget(preset_group)

        layout.addStretch()

    def load_settings(self):
        """加载设置到界面"""
        self.fault_threshold_spin.setValue(self.settings.fault_threshold_multiplier)
        self.min_fault_duration_spin.setValue(self.settings.min_fault_duration)
        self.fundamental_freq_spin.setValue(self.settings.fundamental_frequency)
        self.window_size_spin.setValue(self.settings.window_size)
        self.overlap_ratio_spin.setValue(self.settings.overlap_ratio * 100)

        # 谐波次数
        if self.settings.harmonic_orders:
            harmonic_str = ",".join(map(str, self.settings.harmonic_orders))
            self.harmonic_edit.setText(harmonic_str)

    def save_settings(self):
        """保存界面设置到配置"""
        self.settings.fault_threshold_multiplier = self.fault_threshold_spin.value()
        self.settings.min_fault_duration = self.min_fault_duration_spin.value()
        self.settings.fundamental_frequency = self.fundamental_freq_spin.value()
        self.settings.window_size = self.window_size_spin.value()
        self.settings.overlap_ratio = self.overlap_ratio_spin.value() / 100.0

        # 解析谐波次数
        try:
            harmonic_text = self.harmonic_edit.text().strip()
            if harmonic_text:
                harmonic_orders = [int(x.strip()) for x in harmonic_text.split(',')]
                self.settings.harmonic_orders = harmonic_orders
        except ValueError:
            logger.warning("谐波次数格式错误，使用默认值")

    def load_power_system_preset(self):
        """加载电力系统标准预设"""
        self.fault_threshold_spin.setValue(3.0)
        self.min_fault_duration_spin.setValue(0.01)
        self.fundamental_freq_spin.setValue(50.0)
        self.window_size_spin.setValue(0.02)
        self.overlap_ratio_spin.setValue(50.0)
        self.harmonic_edit.setText("2,3,5,7,11,13")

    def load_sensitive_preset(self):
        """加载高灵敏度预设"""
        self.fault_threshold_spin.setValue(2.0)
        self.min_fault_duration_spin.setValue(0.005)
        self.fundamental_freq_spin.setValue(50.0)
        self.window_size_spin.setValue(0.01)
        self.overlap_ratio_spin.setValue(75.0)
        self.harmonic_edit.setText("2,3,5,7,11,13,17,19")

    def load_robust_preset(self):
        """加载低误报预设"""
        self.fault_threshold_spin.setValue(5.0)
        self.min_fault_duration_spin.setValue(0.02)
        self.fundamental_freq_spin.setValue(50.0)
        self.window_size_spin.setValue(0.04)
        self.overlap_ratio_spin.setValue(25.0)
        self.harmonic_edit.setText("3,5,7")


class UISettingsWidget(QWidget):
    """界面设置组件"""

    def __init__(self, settings: UISettings):
        super().__init__()
        self.settings = settings
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 窗口设置
        window_group = QGroupBox("窗口设置")
        window_layout = QFormLayout(window_group)

        # 默认窗口大小
        size_layout = QHBoxLayout()

        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 3840)
        self.window_width_spin.setSingleStep(100)
        self.window_width_spin.setSuffix(" px")
        size_layout.addWidget(self.window_width_spin)

        size_layout.addWidget(QLabel("×"))

        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 2160)
        self.window_height_spin.setSingleStep(100)
        self.window_height_spin.setSuffix(" px")
        size_layout.addWidget(self.window_height_spin)

        window_layout.addRow("默认窗口大小:", size_layout)

        layout.addWidget(window_group)

        # 文件设置
        file_group = QGroupBox("文件设置")
        file_layout = QFormLayout(file_group)

        self.max_recent_spin = QSpinBox()
        self.max_recent_spin.setRange(5, 50)
        self.max_recent_spin.setSingleStep(5)
        file_layout.addRow("最大最近文件数:", self.max_recent_spin)

        self.auto_save_cb = QCheckBox("启用自动保存")
        file_layout.addRow(self.auto_save_cb)

        self.auto_save_interval_spin = QSpinBox()
        self.auto_save_interval_spin.setRange(60, 3600)
        self.auto_save_interval_spin.setSingleStep(60)
        self.auto_save_interval_spin.setSuffix(" 秒")
        file_layout.addRow("自动保存间隔:", self.auto_save_interval_spin)

        layout.addWidget(file_group)

        # 外观设置
        appearance_group = QGroupBox("外观设置")
        appearance_layout = QFormLayout(appearance_group)

        # 主题选择
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["系统默认", "浅色主题", "深色主题"])
        appearance_layout.addRow("主题:", self.theme_combo)

        # 字体设置
        self.font_btn = QPushButton("选择字体")
        self.font_btn.clicked.connect(self.choose_font)
        appearance_layout.addRow("界面字体:", self.font_btn)

        layout.addWidget(appearance_group)

        # 语言设置
        language_group = QGroupBox("语言设置")
        language_layout = QFormLayout(language_group)

        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文", "English"])
        language_layout.addRow("界面语言:", self.language_combo)

        layout.addWidget(language_group)

        layout.addStretch()

    def load_settings(self):
        """加载设置到界面"""
        self.window_width_spin.setValue(self.settings.window_width)
        self.window_height_spin.setValue(self.settings.window_height)
        self.max_recent_spin.setValue(self.settings.max_recent_files)
        self.auto_save_cb.setChecked(self.settings.auto_save_enabled)
        self.auto_save_interval_spin.setValue(self.settings.auto_save_interval)

    def save_settings(self):
        """保存界面设置到配置"""
        self.settings.window_width = self.window_width_spin.value()
        self.settings.window_height = self.window_height_spin.value()
        self.settings.max_recent_files = self.max_recent_spin.value()
        self.settings.auto_save_enabled = self.auto_save_cb.isChecked()
        self.settings.auto_save_interval = self.auto_save_interval_spin.value()

    def choose_font(self):
        """选择字体"""
        # TODO: 实现字体选择和保存
        current_font = QFont()
        font, ok = QFontDialog.getFont(current_font, self, "选择界面字体")

        if ok:
            self.font_btn.setText(f"{font.family()} {font.pointSize()}pt")
            # 这里可以保存字体设置


class LoggingSettingsWidget(QWidget):
    """日志设置组件"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 日志级别
        level_group = QGroupBox("日志级别")
        level_layout = QFormLayout(level_group)

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(LOG_LEVELS)
        self.log_level_combo.setCurrentText("INFO")
        level_layout.addRow("日志级别:", self.log_level_combo)

        layout.addWidget(level_group)

        # 日志文件
        file_group = QGroupBox("日志文件")
        file_layout = QFormLayout(file_group)

        self.log_to_file_cb = QCheckBox("记录到文件")
        self.log_to_file_cb.setChecked(True)
        file_layout.addRow(self.log_to_file_cb)

        self.log_to_console_cb = QCheckBox("输出到控制台")
        self.log_to_console_cb.setChecked(True)
        file_layout.addRow(self.log_to_console_cb)

        # 日志目录
        log_dir_layout = QHBoxLayout()
        self.log_dir_edit = QLineEdit()
        self.log_dir_edit.setPlaceholderText("使用默认目录")
        log_dir_layout.addWidget(self.log_dir_edit)

        self.browse_dir_btn = QPushButton("浏览...")
        self.browse_dir_btn.clicked.connect(self.browse_log_dir)
        log_dir_layout.addWidget(self.browse_dir_btn)

        file_layout.addRow("日志目录:", log_dir_layout)

        layout.addWidget(file_group)

        # 日志操作
        actions_group = QGroupBox("日志操作")
        actions_layout = QVBoxLayout(actions_group)

        btn_layout = QHBoxLayout()

        self.view_logs_btn = QPushButton("查看日志文件")
        self.view_logs_btn.clicked.connect(self.view_logs)
        btn_layout.addWidget(self.view_logs_btn)

        self.clear_logs_btn = QPushButton("清除日志文件")
        self.clear_logs_btn.clicked.connect(self.clear_logs)
        btn_layout.addWidget(self.clear_logs_btn)

        self.export_logs_btn = QPushButton("导出日志")
        self.export_logs_btn.clicked.connect(self.export_logs)
        btn_layout.addWidget(self.export_logs_btn)

        actions_layout.addLayout(btn_layout)
        layout.addWidget(actions_group)

        layout.addStretch()

    def browse_log_dir(self):
        """浏览日志目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择日志目录")
        if directory:
            self.log_dir_edit.setText(directory)

    def view_logs(self):
        """查看日志文件"""
        # TODO: 实现日志查看器
        QMessageBox.information(self, "提示", "日志查看器功能开发中...")

    def clear_logs(self):
        """清除日志文件"""
        reply = QMessageBox.question(
            self, "确认", "确定要清除所有日志文件吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # TODO: 实现日志清除
            QMessageBox.information(self, "提示", "日志文件已清除")

    def export_logs(self):
        """导出日志"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出日志", "", "文本文件 (*.txt);;所有文件 (*)"
        )

        if file_path:
            # TODO: 实现日志导出
            QMessageBox.information(self, "提示", f"日志已导出到: {file_path}")


class PreferencesDialog(QDialog):
    """首选项对话框主类"""

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.init_ui()
        self.setup_connections()

        # 设置对话框属性
        self.setWindowTitle("首选项")
        self.setModal(True)
        self.resize(600, 500)

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 绘图设置标签页
        self.plot_widget = PlotSettingsWidget(self.settings.plot_settings)
        self.tab_widget.addTab(self.plot_widget, "🎨 绘图设置")

        # 分析设置标签页
        self.analysis_widget = AnalysisSettingsWidget(self.settings.analysis_settings)
        self.tab_widget.addTab(self.analysis_widget, "🔬 分析设置")

        # 界面设置标签页
        self.ui_widget = UISettingsWidget(self.settings.ui_settings)
        self.tab_widget.addTab(self.ui_widget, "🖥️ 界面设置")

        # 日志设置标签页
        self.logging_widget = LoggingSettingsWidget()
        self.tab_widget.addTab(self.logging_widget, "📝 日志设置")

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
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_changes)
        button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self.restore_defaults)

    def setup_connections(self):
        """设置信号连接"""
        # 可以在这里添加实时预览等功能
        pass

    def accept_changes(self):
        """接受更改"""
        self.apply_changes()
        self.accept()

    def apply_changes(self):
        """应用更改"""
        try:
            # 保存各标签页的设置
            self.plot_widget.save_settings()
            self.analysis_widget.save_settings()
            self.ui_widget.save_settings()

            # 保存到文件
            self.settings.save_settings()

            logger.info("首选项设置已保存")

        except Exception as e:
            logger.error(f"保存首选项失败: {e}")
            QMessageBox.critical(self, "错误", f"保存设置失败：\n{str(e)}")

    def restore_defaults(self):
        """恢复默认设置"""
        reply = QMessageBox.question(
            self, "确认", "确定要恢复所有设置为默认值吗？\n这将丢失当前的自定义设置。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 重置设置
            self.settings.reset_to_defaults()

            # 重新加载界面
            self.plot_widget.load_settings()
            self.analysis_widget.load_settings()
            self.ui_widget.load_settings()

            QMessageBox.information(self, "提示", "设置已恢复为默认值")

    def closeEvent(self, event):
        """关闭事件"""
        # 检查是否有未保存的更改
        # TODO: 实现更改检测
        event.accept()