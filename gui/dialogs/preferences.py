#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
首选项对话框
提供应用程序设置的用户界面
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTabWidget,
    QGroupBox, QCheckBox, QComboBox, QSpinBox,
    QDoubleSpinBox, QSlider, QColorDialog,
    QFontDialog, QMessageBox, QWidget, QTextEdit,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPalette

from typing import Dict, Any
from config.settings import AppSettings
from utils.logger import get_logger

logger = get_logger(__name__)


class PreferencesDialog(QDialog):
    """首选项对话框"""

    settings_changed = pyqtSignal()

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.temp_settings = {}  # 临时设置，用于预览

        self.init_ui()
        self.load_current_settings()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("首选项设置")
        self.setMinimumSize(600, 500)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # 创建标签页
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # 各个设置标签页
        self.create_general_tab()
        self.create_display_tab()
        self.create_analysis_tab()
        self.create_advanced_tab()

        # 按钮区域
        self.create_button_section(layout)

    def create_general_tab(self):
        """创建常规设置标签页"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)

        # 界面设置组
        ui_group = QGroupBox("界面设置")
        ui_layout = QFormLayout(ui_group)

        # 语言设置
        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文", "English"])
        ui_layout.addRow("界面语言:", self.language_combo)

        # 主题设置
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色主题", "深色主题", "跟随系统"])
        ui_layout.addRow("界面主题:", self.theme_combo)

        # 字体设置
        font_layout = QHBoxLayout()
        self.font_label = QLabel("微软雅黑, 9pt")
        font_layout.addWidget(self.font_label)

        self.font_btn = QPushButton("选择字体...")
        self.font_btn.clicked.connect(self.select_font)
        font_layout.addWidget(self.font_btn)

        ui_layout.addRow("界面字体:", font_layout)

        tab_layout.addWidget(ui_group)

        # 文件设置组
        file_group = QGroupBox("文件设置")
        file_layout = QFormLayout(file_group)

        # 最近文件数量
        self.recent_files_count = QSpinBox()
        self.recent_files_count.setRange(0, 20)
        self.recent_files_count.setValue(10)
        file_layout.addRow("最近文件数量:", self.recent_files_count)

        # 自动保存
        self.auto_save_cb = QCheckBox("启用自动保存")
        file_layout.addRow("", self.auto_save_cb)

        self.auto_save_interval = QSpinBox()
        self.auto_save_interval.setRange(1, 60)
        self.auto_save_interval.setValue(5)
        self.auto_save_interval.setSuffix(" 分钟")
        file_layout.addRow("自动保存间隔:", self.auto_save_interval)

        tab_layout.addWidget(file_group)

        tab_layout.addStretch()

        self.tab_widget.addTab(tab_widget, "常规")

    def create_display_tab(self):
        """创建显示设置标签页"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)

        # 绘图设置组
        plot_group = QGroupBox("绘图设置")
        plot_layout = QFormLayout(plot_group)

        # 线宽
        self.line_width_spin = QDoubleSpinBox()
        self.line_width_spin.setRange(0.1, 5.0)
        self.line_width_spin.setSingleStep(0.1)
        self.line_width_spin.setValue(1.0)
        self.line_width_spin.setSuffix(" px")
        plot_layout.addRow("线宽:", self.line_width_spin)

        # 网格设置
        self.grid_enabled_cb = QCheckBox("显示网格")
        plot_layout.addRow("", self.grid_enabled_cb)

        self.grid_alpha_spin = QDoubleSpinBox()
        self.grid_alpha_spin.setRange(0.1, 1.0)
        self.grid_alpha_spin.setSingleStep(0.1)
        self.grid_alpha_spin.setValue(0.3)
        plot_layout.addRow("网格透明度:", self.grid_alpha_spin)

        # 最大绘制点数
        self.max_points_spin = QSpinBox()
        self.max_points_spin.setRange(1000, 100000)
        self.max_points_spin.setValue(10000)
        plot_layout.addRow("最大绘制点数:", self.max_points_spin)

        # 自动缩放
        self.auto_scale_cb = QCheckBox("自动缩放")
        plot_layout.addRow("", self.auto_scale_cb)

        tab_layout.addWidget(plot_group)

        # 颜色设置组
        color_group = QGroupBox("颜色设置")
        color_layout = QFormLayout(color_group)

        # 背景色
        bg_color_layout = QHBoxLayout()
        self.bg_color_label = QLabel()
        self.bg_color_label.setFixedSize(30, 20)
        self.bg_color_label.setStyleSheet("background-color: white; border: 1px solid gray;")
        bg_color_layout.addWidget(self.bg_color_label)

        self.bg_color_btn = QPushButton("选择颜色...")
        self.bg_color_btn.clicked.connect(lambda: self.select_color('background'))
        bg_color_layout.addWidget(self.bg_color_btn)
        bg_color_layout.addStretch()

        color_layout.addRow("背景颜色:", bg_color_layout)

        tab_layout.addWidget(color_group)

        tab_layout.addStretch()

        self.tab_widget.addTab(tab_widget, "显示")

    def create_analysis_tab(self):
        """创建分析设置标签页"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)

        # 故障检测设置组
        fault_group = QGroupBox("故障检测设置")
        fault_layout = QFormLayout(fault_group)

        # 检测灵敏度
        self.sensitivity_spin = QDoubleSpinBox()
        self.sensitivity_spin.setRange(1.0, 10.0)
        self.sensitivity_spin.setSingleStep(0.1)
        self.sensitivity_spin.setValue(3.0)
        fault_layout.addRow("检测灵敏度:", self.sensitivity_spin)

        # 最小故障持续时间
        self.min_fault_duration_spin = QDoubleSpinBox()
        self.min_fault_duration_spin.setRange(0.001, 1.0)
        self.min_fault_duration_spin.setSingleStep(0.001)
        self.min_fault_duration_spin.setValue(0.01)
        self.min_fault_duration_spin.setSuffix(" s")
        fault_layout.addRow("最小故障持续时间:", self.min_fault_duration_spin)

        # 电压阈值
        self.voltage_threshold_spin = QDoubleSpinBox()
        self.voltage_threshold_spin.setRange(0.1, 2.0)
        self.voltage_threshold_spin.setSingleStep(0.05)
        self.voltage_threshold_spin.setValue(0.9)
        fault_layout.addRow("电压故障阈值:", self.voltage_threshold_spin)

        # 电流阈值
        self.current_threshold_spin = QDoubleSpinBox()
        self.current_threshold_spin.setRange(1.0, 10.0)
        self.current_threshold_spin.setSingleStep(0.1)
        self.current_threshold_spin.setValue(2.0)
        fault_layout.addRow("过电流阈值:", self.current_threshold_spin)

        tab_layout.addWidget(fault_group)

        # 特征提取设置组
        feature_group = QGroupBox("特征提取设置")
        feature_layout = QFormLayout(feature_group)

        # 启用谐波分析
        self.harmonic_analysis_cb = QCheckBox("启用谐波分析")
        feature_layout.addRow("", self.harmonic_analysis_cb)

        # 最大谐波次数
        self.max_harmonic_spin = QSpinBox()
        self.max_harmonic_spin.setRange(5, 50)
        self.max_harmonic_spin.setValue(20)
        feature_layout.addRow("最大谐波次数:", self.max_harmonic_spin)

        # THD阈值
        self.thd_threshold_spin = QDoubleSpinBox()
        self.thd_threshold_spin.setRange(1.0, 20.0)
        self.thd_threshold_spin.setSingleStep(0.1)
        self.thd_threshold_spin.setValue(5.0)
        self.thd_threshold_spin.setSuffix(" %")
        feature_layout.addRow("THD阈值:", self.thd_threshold_spin)

        tab_layout.addWidget(feature_group)

        tab_layout.addStretch()

        self.tab_widget.addTab(tab_widget, "分析")

    def create_advanced_tab(self):
        """创建高级设置标签页"""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)

        # 性能设置组
        performance_group = QGroupBox("性能设置")
        performance_layout = QFormLayout(performance_group)

        # 并行处理
        self.parallel_processing_cb = QCheckBox("启用并行处理")
        performance_layout.addRow("", self.parallel_processing_cb)

        # 最大工作线程数
        self.max_workers_spin = QSpinBox()
        self.max_workers_spin.setRange(1, 16)
        self.max_workers_spin.setValue(4)
        performance_layout.addRow("最大工作线程数:", self.max_workers_spin)

        # 内存限制
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setRange(512, 8192)
        self.memory_limit_spin.setValue(2048)
        self.memory_limit_spin.setSuffix(" MB")
        performance_layout.addRow("内存限制:", self.memory_limit_spin)

        tab_layout.addWidget(performance_group)

        # 日志设置组
        log_group = QGroupBox("日志设置")
        log_layout = QFormLayout(log_group)

        # 日志级别
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        log_layout.addRow("日志级别:", self.log_level_combo)

        # 日志文件保留天数
        self.log_retention_spin = QSpinBox()
        self.log_retention_spin.setRange(1, 365)
        self.log_retention_spin.setValue(30)
        self.log_retention_spin.setSuffix(" 天")
        log_layout.addRow("日志保留天数:", self.log_retention_spin)

        tab_layout.addWidget(log_group)

        # 调试设置组
        debug_group = QGroupBox("调试设置")
        debug_layout = QFormLayout(debug_group)

        # 启用调试模式
        self.debug_mode_cb = QCheckBox("启用调试模式")
        debug_layout.addRow("", self.debug_mode_cb)

        # 性能监控
        self.performance_monitor_cb = QCheckBox("启用性能监控")
        debug_layout.addRow("", self.performance_monitor_cb)

        tab_layout.addWidget(debug_group)

        tab_layout.addStretch()

        self.tab_widget.addTab(tab_widget, "高级")

    def create_button_section(self, layout):
        """创建按钮区域"""
        button_layout = QHBoxLayout()

        # 重置为默认值
        self.reset_btn = QPushButton("重置为默认值")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_btn)

        button_layout.addStretch()

        # 确定和取消按钮
        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self.accept_settings)
        button_layout.addWidget(self.ok_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def load_current_settings(self):
        """加载当前设置"""
        try:
            # 常规设置
            if hasattr(self.settings, 'ui_settings'):
                ui_settings = self.settings.ui_settings

                # 最近文件数量
                recent_count = getattr(ui_settings, 'max_recent_files', 10)
                self.recent_files_count.setValue(recent_count)

                # 自动保存
                auto_save = getattr(ui_settings, 'auto_save_enabled', True)
                self.auto_save_cb.setChecked(auto_save)

                interval = getattr(ui_settings, 'auto_save_interval', 5)
                self.auto_save_interval.setValue(interval)

            # 绘图设置
            if hasattr(self.settings, 'plot_settings'):
                plot_settings = self.settings.plot_settings

                # 线宽
                line_width = getattr(plot_settings, 'line_width', 1.0)
                self.line_width_spin.setValue(line_width)

                # 网格
                grid_enabled = getattr(plot_settings, 'grid_enabled', True)
                self.grid_enabled_cb.setChecked(grid_enabled)

                grid_alpha = getattr(plot_settings, 'grid_alpha', 0.3)
                self.grid_alpha_spin.setValue(grid_alpha)

                # 最大点数
                max_points = getattr(plot_settings, 'max_points_per_plot', 10000)
                self.max_points_spin.setValue(max_points)

                # 自动缩放
                auto_scale = getattr(plot_settings, 'auto_scale', True)
                self.auto_scale_cb.setChecked(auto_scale)

            logger.info("已加载当前设置")

        except Exception as e:
            logger.warning(f"加载设置失败: {e}")

    def select_font(self):
        """选择字体"""
        current_font = self.font_label.font()
        font, ok = QFontDialog.getFont(current_font, self)

        if ok:
            self.font_label.setFont(font)
            font_text = f"{font.family()}, {font.pointSize()}pt"
            if font.bold():
                font_text += ", 粗体"
            if font.italic():
                font_text += ", 斜体"
            self.font_label.setText(font_text)

    def select_color(self, color_type: str):
        """选择颜色"""
        if color_type == 'background':
            current_color = QColor('white')
            color = QColorDialog.getColor(current_color, self, "选择背景颜色")

            if color.isValid():
                self.bg_color_label.setStyleSheet(
                    f"background-color: {color.name()}; border: 1px solid gray;"
                )

    def reset_to_defaults(self):
        """重置为默认值"""
        reply = QMessageBox.question(
            self, "确认重置",
            "确定要重置所有设置为默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 重置各个控件为默认值
            self.language_combo.setCurrentIndex(0)
            self.theme_combo.setCurrentIndex(0)
            self.recent_files_count.setValue(10)
            self.auto_save_cb.setChecked(True)
            self.auto_save_interval.setValue(5)

            self.line_width_spin.setValue(1.0)
            self.grid_enabled_cb.setChecked(True)
            self.grid_alpha_spin.setValue(0.3)
            self.max_points_spin.setValue(10000)
            self.auto_scale_cb.setChecked(True)

            self.sensitivity_spin.setValue(3.0)
            self.min_fault_duration_spin.setValue(0.01)
            self.voltage_threshold_spin.setValue(0.9)
            self.current_threshold_spin.setValue(2.0)

            self.harmonic_analysis_cb.setChecked(True)
            self.max_harmonic_spin.setValue(20)
            self.thd_threshold_spin.setValue(5.0)

            self.parallel_processing_cb.setChecked(False)
            self.max_workers_spin.setValue(4)
            self.memory_limit_spin.setValue(2048)

            self.log_level_combo.setCurrentText("INFO")
            self.log_retention_spin.setValue(30)
            self.debug_mode_cb.setChecked(False)
            self.performance_monitor_cb.setChecked(False)

            logger.info("设置已重置为默认值")

    def accept_settings(self):
        """接受设置更改"""
        try:
            # 应用设置更改
            self.apply_settings_changes()

            # 保存设置
            self.settings.save_settings()

            # 发送设置变更信号
            self.settings_changed.emit()

            logger.info("设置更改已保存")
            self.accept()

        except Exception as e:
            logger.error(f"保存设置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存设置失败:\n{str(e)}")

    def apply_settings_changes(self):
        """应用设置更改"""
        # 更新UI设置
        if hasattr(self.settings, 'ui_settings'):
            ui_settings = self.settings.ui_settings
            ui_settings.max_recent_files = self.recent_files_count.value()
            ui_settings.auto_save_enabled = self.auto_save_cb.isChecked()
            ui_settings.auto_save_interval = self.auto_save_interval.value()

        # 更新绘图设置
        if hasattr(self.settings, 'plot_settings'):
            plot_settings = self.settings.plot_settings
            plot_settings.line_width = self.line_width_spin.value()
            plot_settings.grid_enabled = self.grid_enabled_cb.isChecked()
            plot_settings.grid_alpha = self.grid_alpha_spin.value()
            plot_settings.max_points_per_plot = self.max_points_spin.value()
            plot_settings.auto_scale = self.auto_scale_cb.isChecked()

        # TODO: 应用其他设置更改

        logger.info("设置更改已应用")

    def reject(self):
        """取消设置更改"""
        super().reject()
        logger.info("设置更改已取消")