#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析面板组件
显示故障检测和特征分析结果
"""

import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget,
    QTableWidgetItem, QGroupBox, QLabel, QTextEdit, QTreeWidget,
    QTreeWidgetItem, QPushButton, QComboBox, QCheckBox, QSpinBox,
    QDoubleSpinBox, QProgressBar, QSplitter, QHeaderView, QFrame,
    QScrollArea, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QBrush, QIcon, QAction

from typing import Optional, List, Dict, Any
from models.data_models import AnalysisResult, FaultEvent, FaultType, SignalFeatures
from config.constants import FAULT_COLORS, UI_STRINGS
from utils.logger import get_logger

logger = get_logger(__name__)


class FaultEventWidget(QWidget):
    """故障事件显示组件"""

    # 信号定义
    fault_selected = pyqtSignal(object)  # 选中故障事件
    fault_double_clicked = pyqtSignal(object)  # 双击故障事件

    def __init__(self):
        super().__init__()
        self.fault_events: List[FaultEvent] = []
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 创建组框
        group_box = QGroupBox("🚨 故障事件")
        group_layout = QVBoxLayout(group_box)

        # 控制栏
        control_layout = QHBoxLayout()

        # 过滤控件
        control_layout.addWidget(QLabel("类型过滤:"))
        self.type_filter = QComboBox()
        self.type_filter.addItem("全部类型")
        for fault_type in FaultType:
            self.type_filter.addItem(fault_type.value)
        self.type_filter.currentTextChanged.connect(self.apply_filter)
        control_layout.addWidget(self.type_filter)

        # 严重程度过滤
        control_layout.addWidget(QLabel("严重程度:"))
        self.severity_filter = QComboBox()
        self.severity_filter.addItems(["全部", "高(>0.7)", "中(0.3-0.7)", "低(<0.3)"])
        self.severity_filter.currentTextChanged.connect(self.apply_filter)
        control_layout.addWidget(self.severity_filter)

        control_layout.addStretch()

        # 导出按钮
        self.export_btn = QPushButton("导出故障列表")
        self.export_btn.clicked.connect(self.export_fault_list)
        control_layout.addWidget(self.export_btn)

        group_layout.addLayout(control_layout)

        # 创建故障事件表格
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSortingEnabled(True)

        # 设置表头
        headers = ['开始时间', '结束时间', '持续时间', '故障类型', '严重程度', '置信度', '受影响通道', '描述']
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 开始时间
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 结束时间
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 持续时间
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 故障类型
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 严重程度
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # 置信度
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)  # 受影响通道
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)  # 描述

        # 连接信号
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.itemDoubleClicked.connect(self.on_item_double_clicked)

        # 设置右键菜单
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        group_layout.addWidget(self.table)

        # 统计信息
        self.stats_label = QLabel("统计信息: 暂无数据")
        self.stats_label.setStyleSheet("QLabel { color: #666666; font-size: 11px; }")
        group_layout.addWidget(self.stats_label)

        layout.addWidget(group_box)

    def display_fault_events(self, fault_events: List[FaultEvent]):
        """
        显示故障事件

        Args:
            fault_events: 故障事件列表
        """
        self.fault_events = fault_events
        self.update_table()
        self.update_statistics()

    def update_table(self):
        """更新表格显示"""
        # 应用过滤
        filtered_events = self.apply_current_filter()

        self.table.setRowCount(len(filtered_events))

        for row, event in enumerate(filtered_events):
            # 开始时间
            start_item = QTableWidgetItem(f"{event.start_time:.4f}s")
            start_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            start_item.setData(Qt.ItemDataRole.UserRole, event)  # 存储事件对象
            self.table.setItem(row, 0, start_item)

            # 结束时间
            end_item = QTableWidgetItem(f"{event.end_time:.4f}s")
            end_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, end_item)

            # 持续时间
            duration = event.duration * 1000  # 转换为毫秒
            if duration < 1000:
                duration_str = f"{duration:.1f}ms"
            else:
                duration_str = f"{duration / 1000:.3f}s"
            duration_item = QTableWidgetItem(duration_str)
            duration_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, duration_item)

            # 故障类型
            type_item = QTableWidgetItem(event.fault_type.value)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # 设置类型对应的颜色
            if event.fault_type.name in FAULT_COLORS:
                color = QColor(FAULT_COLORS[event.fault_type.name])
                type_item.setForeground(QBrush(color))
                type_item.setFont(QFont("", -1, QFont.Weight.Bold))
            self.table.setItem(row, 3, type_item)

            # 严重程度
            severity_item = QTableWidgetItem(f"{event.severity:.2f}")
            severity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # 根据严重程度设置背景色
            if event.severity > 0.7:
                severity_item.setBackground(QBrush(QColor('#FFEBEE')))  # 浅红色
            elif event.severity > 0.3:
                severity_item.setBackground(QBrush(QColor('#FFF3E0')))  # 浅橙色
            else:
                severity_item.setBackground(QBrush(QColor('#E8F5E8')))  # 浅绿色
            self.table.setItem(row, 4, severity_item)

            # 置信度
            confidence_item = QTableWidgetItem(f"{event.confidence:.2f}")
            confidence_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, confidence_item)

            # 受影响通道
            channels_str = ", ".join(event.affected_channels[:3])  # 最多显示3个
            if len(event.affected_channels) > 3:
                channels_str += f" 等{len(event.affected_channels)}个"
            channels_item = QTableWidgetItem(channels_str)
            channels_item.setToolTip(", ".join(event.affected_channels))
            self.table.setItem(row, 6, channels_item)

            # 描述
            desc_item = QTableWidgetItem(event.description)
            desc_item.setToolTip(event.description)
            self.table.setItem(row, 7, desc_item)

    def apply_current_filter(self) -> List[FaultEvent]:
        """应用当前过滤条件"""
        filtered = list(self.fault_events)

        # 类型过滤
        type_filter = self.type_filter.currentText()
        if type_filter != "全部类型":
            filtered = [e for e in filtered if e.fault_type.value == type_filter]

        # 严重程度过滤
        severity_filter = self.severity_filter.currentText()
        if severity_filter == "高(>0.7)":
            filtered = [e for e in filtered if e.severity > 0.7]
        elif severity_filter == "中(0.3-0.7)":
            filtered = [e for e in filtered if 0.3 <= e.severity <= 0.7]
        elif severity_filter == "低(<0.3)":
            filtered = [e for e in filtered if e.severity < 0.3]

        return filtered

    def apply_filter(self):
        """应用过滤条件"""
        self.update_table()
        self.update_statistics()

    def update_statistics(self):
        """更新统计信息"""
        filtered_events = self.apply_current_filter()
        total_count = len(filtered_events)

        if total_count == 0:
            self.stats_label.setText("统计信息: 暂无故障事件")
            return

        # 按类型统计
        type_counts = {}
        severity_sum = 0

        for event in filtered_events:
            fault_type = event.fault_type.value
            type_counts[fault_type] = type_counts.get(fault_type, 0) + 1
            severity_sum += event.severity

        # 生成统计文本
        avg_severity = severity_sum / total_count
        most_common_type = max(type_counts.items(), key=lambda x: x[1])

        stats_text = f"统计信息: 共{total_count}个故障，"
        stats_text += f"平均严重程度{avg_severity:.2f}，"
        stats_text += f"最常见类型: {most_common_type[0]}({most_common_type[1]}次)"

        self.stats_label.setText(stats_text)

    def on_selection_changed(self):
        """选择变化处理"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            item = self.table.item(current_row, 0)
            if item:
                event = item.data(Qt.ItemDataRole.UserRole)
                if event:
                    self.fault_selected.emit(event)

    def on_item_double_clicked(self, item: QTableWidgetItem):
        """双击处理"""
        event = item.data(Qt.ItemDataRole.UserRole)
        if event:
            self.fault_double_clicked.emit(event)

    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.table.itemAt(position)
        if not item:
            return

        event = item.data(Qt.ItemDataRole.UserRole)
        if not event:
            return

        menu = QMenu(self)

        # 查看详情
        detail_action = QAction("查看详情", self)
        detail_action.triggered.connect(lambda: self.show_fault_detail(event))
        menu.addAction(detail_action)

        # 定位到故障
        locate_action = QAction("定位到故障", self)
        locate_action.triggered.connect(lambda: self.fault_double_clicked.emit(event))
        menu.addAction(locate_action)

        menu.addSeparator()

        # 导出单个故障
        export_action = QAction("导出此故障", self)
        export_action.triggered.connect(lambda: self.export_single_fault(event))
        menu.addAction(export_action)

        menu.exec(self.table.mapToGlobal(position))

    def show_fault_detail(self, event: FaultEvent):
        """显示故障详情"""
        # TODO: 实现故障详情对话框
        from PyQt6.QtWidgets import QMessageBox

        detail_text = f"故障类型: {event.fault_type.value}\n"
        detail_text += f"开始时间: {event.start_time:.6f}s\n"
        detail_text += f"结束时间: {event.end_time:.6f}s\n"
        detail_text += f"持续时间: {event.duration * 1000:.2f}ms\n"
        detail_text += f"严重程度: {event.severity:.3f}\n"
        detail_text += f"置信度: {event.confidence:.3f}\n"
        detail_text += f"受影响通道: {', '.join(event.affected_channels)}\n"
        detail_text += f"描述: {event.description}\n"

        if event.features:
            detail_text += f"\n附加特征:\n"
            for key, value in event.features.items():
                detail_text += f"  {key}: {value}\n"

        QMessageBox.information(self, f"故障详情 - {event.fault_type.value}", detail_text)

    def export_single_fault(self, event: FaultEvent):
        """导出单个故障"""
        # TODO: 实现单个故障导出
        logger.info(f"导出故障: {event.fault_type.value} at {event.start_time:.4f}s")

    def export_fault_list(self):
        """导出故障列表"""
        # TODO: 实现故障列表导出
        filtered_events = self.apply_current_filter()
        logger.info(f"导出{len(filtered_events)}个故障事件")

    def clear_events(self):
        """清除所有故障事件"""
        self.fault_events.clear()
        self.table.setRowCount(0)
        self.stats_label.setText("统计信息: 暂无数据")


class FeatureAnalysisWidget(QWidget):
    """特征分析显示组件"""

    def __init__(self):
        super().__init__()
        self.analysis_result: Optional[AnalysisResult] = None
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 通道特征标签页
        self.channel_features_widget = self.create_channel_features_tab()
        self.tab_widget.addTab(self.channel_features_widget, "通道特征")

        # 系统指标标签页
        self.system_metrics_widget = self.create_system_metrics_tab()
        self.tab_widget.addTab(self.system_metrics_widget, "系统指标")

        # 电能质量标签页
        self.power_quality_widget = self.create_power_quality_tab()
        self.tab_widget.addTab(self.power_quality_widget, "电能质量")

        layout.addWidget(self.tab_widget)

    def create_channel_features_tab(self) -> QWidget:
        """创建通道特征标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 控制栏
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("显示通道:"))

        self.channel_combo = QComboBox()
        self.channel_combo.currentTextChanged.connect(self.update_channel_features)
        control_layout.addWidget(self.channel_combo)

        control_layout.addStretch()
        control_layout.addWidget(QLabel("特征类型:"))

        self.feature_type_combo = QComboBox()
        self.feature_type_combo.addItems(["全部", "时域特征", "频域特征", "谐波特征"])
        self.feature_type_combo.currentTextChanged.connect(self.update_channel_features)
        control_layout.addWidget(self.feature_type_combo)

        layout.addLayout(control_layout)

        # 特征表格
        self.features_table = QTableWidget()
        self.features_table.setColumnCount(3)
        self.features_table.setHorizontalHeaderLabels(["特征名称", "数值", "单位"])
        self.features_table.setAlternatingRowColors(True)

        # 设置列宽
        header = self.features_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.features_table)

        return widget

    def create_system_metrics_tab(self) -> QWidget:
        """创建系统指标标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 系统频率
        freq_group = QGroupBox("系统频率")
        freq_layout = QVBoxLayout(freq_group)

        self.freq_label = QLabel("系统频率: -- Hz")
        self.freq_label.setFont(QFont("", 12, QFont.Weight.Bold))
        freq_layout.addWidget(self.freq_label)

        self.freq_deviation_label = QLabel("频率偏差: -- Hz")
        freq_layout.addWidget(self.freq_deviation_label)

        layout.addWidget(freq_group)

        # 三相不平衡
        unbalance_group = QGroupBox("三相不平衡")
        unbalance_layout = QVBoxLayout(unbalance_group)

        self.unbalance_label = QLabel("不平衡度: --%")
        self.unbalance_label.setFont(QFont("", 12, QFont.Weight.Bold))
        unbalance_layout.addWidget(self.unbalance_label)

        # 各相电压
        self.voltage_labels = {}
        for phase in ['A', 'B', 'C']:
            label = QLabel(f"{phase}相电压: -- V")
            self.voltage_labels[phase] = label
            unbalance_layout.addWidget(label)

        layout.addWidget(unbalance_group)

        # 电流统计
        current_group = QGroupBox("电流统计")
        current_layout = QVBoxLayout(current_group)

        self.current_labels = {}
        for phase in ['A', 'B', 'C']:
            label = QLabel(f"{phase}相电流: -- A")
            self.current_labels[phase] = label
            current_layout.addWidget(label)

        layout.addWidget(current_group)

        layout.addStretch()

        return widget

    def create_power_quality_tab(self) -> QWidget:
        """创建电能质量标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 谐波分析
        harmonic_group = QGroupBox("谐波分析")
        harmonic_layout = QVBoxLayout(harmonic_group)

        # 谐波表格
        self.harmonic_table = QTableWidget()
        self.harmonic_table.setColumnCount(4)
        self.harmonic_table.setHorizontalHeaderLabels(["次数", "频率(Hz)", "幅值", "相位(°)"])
        self.harmonic_table.setMaximumHeight(200)
        harmonic_layout.addWidget(self.harmonic_table)

        # THD显示
        self.thd_label = QLabel("总谐波畸变率(THD): --%")
        self.thd_label.setFont(QFont("", 11, QFont.Weight.Bold))
        harmonic_layout.addWidget(self.thd_label)

        layout.addWidget(harmonic_group)

        # 功率指标
        power_group = QGroupBox("功率指标")
        power_layout = QVBoxLayout(power_group)

        self.power_factor_label = QLabel("功率因数: --")
        power_layout.addWidget(self.power_factor_label)

        self.active_power_label = QLabel("有功功率: -- W")
        power_layout.addWidget(self.active_power_label)

        self.reactive_power_label = QLabel("无功功率: -- var")
        power_layout.addWidget(self.reactive_power_label)

        layout.addWidget(power_group)

        layout.addStretch()

        return widget

    def display_analysis_result(self, result: AnalysisResult):
        """
        显示分析结果

        Args:
            result: 分析结果
        """
        self.analysis_result = result

        # 更新通道列表
        self.channel_combo.clear()
        if result.channel_features:
            self.channel_combo.addItems(list(result.channel_features.keys()))

        # 更新各个标签页
        self.update_channel_features()
        self.update_system_metrics()
        self.update_power_quality()

    def update_channel_features(self):
        """更新通道特征显示"""
        if not self.analysis_result:
            return

        channel_name = self.channel_combo.currentText()
        if not channel_name or channel_name not in self.analysis_result.channel_features:
            self.features_table.setRowCount(0)
            return

        features = self.analysis_result.channel_features[channel_name]
        feature_type = self.feature_type_combo.currentText()

        # 准备特征数据
        feature_data = []

        if feature_type in ["全部", "时域特征"]:
            feature_data.extend([
                ("平均值", f"{features.mean:.6f}", ""),
                ("RMS值", f"{features.rms:.6f}", ""),
                ("峰值", f"{features.peak:.6f}", ""),
                ("峰峰值", f"{features.peak_to_peak:.6f}", ""),
                ("波峰因子", f"{features.crest_factor:.3f}", ""),
                ("波形因子", f"{features.form_factor:.3f}", ""),
                ("过零点数", f"{features.zero_crossings}", "个"),
                ("信号能量", f"{features.energy:.3e}", "")
            ])

        if feature_type in ["全部", "频域特征"]:
            feature_data.extend([
                ("基波幅值", f"{features.fundamental_magnitude:.6f}", ""),
                ("基波相位", f"{features.fundamental_phase:.2f}", "°"),
                ("主导频率", f"{features.dominant_frequency:.2f}", "Hz"),
                ("总谐波畸变", f"{features.thd:.2f}", "%")
            ])

        if feature_type in ["全部", "谐波特征"] and features.harmonics:
            for order, (magnitude, phase) in list(features.harmonics.items())[:10]:  # 显示前10次谐波
                feature_data.append((f"{order}次谐波幅值", f"{magnitude:.6f}", ""))
                feature_data.append((f"{order}次谐波相位", f"{phase:.2f}", "°"))

        # 更新表格
        self.features_table.setRowCount(len(feature_data))

        for row, (name, value, unit) in enumerate(feature_data):
            # 特征名称
            name_item = QTableWidgetItem(name)
            self.features_table.setItem(row, 0, name_item)

            # 数值
            value_item = QTableWidgetItem(value)
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # 根据特征类型设置颜色
            if "谐波" in name and "幅值" in name:
                try:
                    val = float(value)
                    if val > 0.05:  # 5%以上的谐波用红色显示
                        value_item.setForeground(QBrush(QColor('#CC0000')))
                except:
                    pass

            self.features_table.setItem(row, 1, value_item)

            # 单位
            unit_item = QTableWidgetItem(unit)
            unit_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.features_table.setItem(row, 2, unit_item)

    def update_system_metrics(self):
        """更新系统指标"""
        if not self.analysis_result:
            return

        # 系统频率
        freq = self.analysis_result.system_frequency
        self.freq_label.setText(f"系统频率: {freq:.3f} Hz")

        # 频率偏差
        deviation = abs(freq - 50.0)  # 假设额定频率为50Hz
        color = "red" if deviation > 1.0 else "green"
        self.freq_deviation_label.setText(f"频率偏差: {deviation:.3f} Hz")
        self.freq_deviation_label.setStyleSheet(f"QLabel {{ color: {color}; }}")

        # 三相不平衡
        unbalance = self.analysis_result.system_unbalance
        self.unbalance_label.setText(f"不平衡度: {unbalance:.2f}%")

        # 电压显示
        phase_names = ['A', 'B', 'C']
        voltage_values = list(self.analysis_result.voltage_rms.values())

        for i, (phase, label) in enumerate(self.voltage_labels.items()):
            if i < len(voltage_values):
                voltage = voltage_values[i]
                label.setText(f"{phase}相电压: {voltage:.2f} V")
            else:
                label.setText(f"{phase}相电压: -- V")

        # 电流显示
        current_values = list(self.analysis_result.current_rms.values())

        for i, (phase, label) in enumerate(self.current_labels.items()):
            if i < len(current_values):
                current = current_values[i]
                label.setText(f"{phase}相电流: {current:.3f} A")
            else:
                label.setText(f"{phase}相电流: -- A")

    def update_power_quality(self):
        """更新电能质量指标"""
        if not self.analysis_result:
            return

        # 功率因数
        pf = self.analysis_result.power_factor
        self.power_factor_label.setText(f"功率因数: {pf:.3f}")

        # TODO: 实现更多电能质量指标
        # 暂时显示占位符
        self.active_power_label.setText("有功功率: 计算中...")
        self.reactive_power_label.setText("无功功率: 计算中...")
        self.thd_label.setText("总谐波畸变率(THD): 计算中...")

        # 清空谐波表格
        self.harmonic_table.setRowCount(0)

    def clear_analysis(self):
        """清除分析结果"""
        self.analysis_result = None
        self.channel_combo.clear()
        self.features_table.setRowCount(0)

        # 重置标签
        self.freq_label.setText("系统频率: -- Hz")
        self.freq_deviation_label.setText("频率偏差: -- Hz")
        self.unbalance_label.setText("不平衡度: --%")

        for label in self.voltage_labels.values():
            label.setText(label.text().split(':')[0] + ": -- V")

        for label in self.current_labels.values():
            label.setText(label.text().split(':')[0] + ": -- A")


class AnalysisPanel(QWidget):
    """分析面板主组件"""

    # 信号定义
    fault_event_selected = pyqtSignal(object)  # 选中故障事件
    zoom_to_fault_requested = pyqtSignal(object)  # 缩放到故障

    def __init__(self):
        super().__init__()
        self.current_result: Optional[AnalysisResult] = None
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Vertical)

        # 故障事件组件
        self.fault_widget = FaultEventWidget()
        splitter.addWidget(self.fault_widget)

        # 特征分析组件
        self.feature_widget = FeatureAnalysisWidget()
        splitter.addWidget(self.feature_widget)

        # 设置分割器比例
        splitter.setSizes([300, 400])

        layout.addWidget(splitter)

        # 状态标签
        self.status_label = QLabel("等待分析结果...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("QLabel { color: #888888; font-style: italic; padding: 10px; }")
        layout.addWidget(self.status_label)

    def setup_connections(self):
        """设置信号连接"""
        # 故障事件信号
        self.fault_widget.fault_selected.connect(self.fault_event_selected.emit)
        self.fault_widget.fault_double_clicked.connect(self.zoom_to_fault_requested.emit)

    def display_results(self, result: AnalysisResult):
        """
        显示分析结果

        Args:
            result: 分析结果对象
        """
        self.current_result = result

        try:
            # 显示故障事件
            self.fault_widget.display_fault_events(result.fault_events)

            # 显示特征分析
            self.feature_widget.display_analysis_result(result)

            # 更新状态
            fault_count = len(result.fault_events)
            channel_count = len(result.channel_features)

            status_text = f"分析完成: 检测到 {fault_count} 个故障事件，"
            status_text += f"分析了 {channel_count} 个通道"

            if result.analysis_duration > 0:
                status_text += f"，耗时 {result.analysis_duration:.2f} 秒"

            self.status_label.setText(status_text)
            self.status_label.setStyleSheet("QLabel { color: #333333; padding: 10px; }")

            logger.info(f"分析结果显示完成: {fault_count}个故障，{channel_count}个通道")

        except Exception as e:
            logger.error(f"显示分析结果失败: {e}")
            self.clear_results()
            self.status_label.setText(f"显示结果失败: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; padding: 10px; }")

    def clear_results(self):
        """清除分析结果"""
        self.current_result = None
        self.fault_widget.clear_events()
        self.feature_widget.clear_analysis()
        self.status_label.setText("等待分析结果...")
        self.status_label.setStyleSheet("QLabel { color: #888888; font-style: italic; padding: 10px; }")

    def get_selected_fault(self) -> Optional[FaultEvent]:
        """获取当前选中的故障事件"""
        # TODO: 从故障表格获取选中的故障
        return None

    def export_analysis_report(self) -> str:
        """
        导出分析报告

        Returns:
            格式化的分析报告文本
        """
        if not self.current_result:
            return "无分析结果"

        # TODO: 实现详细的报告生成
        result = self.current_result

        report = f"COMTRADE波形分析报告\n"
        report += f"=" * 50 + "\n\n"

        report += f"分析时间: {result.timestamp}\n"
        report += f"分析耗时: {result.analysis_duration:.2f} 秒\n\n"

        # 故障统计
        report += f"故障检测结果:\n"
        report += f"  检测到故障事件: {len(result.fault_events)} 个\n"

        if result.fault_events:
            fault_summary = {}
            for event in result.fault_events:
                fault_type = event.fault_type.value
                fault_summary[fault_type] = fault_summary.get(fault_type, 0) + 1

            for fault_type, count in fault_summary.items():
                report += f"    {fault_type}: {count} 次\n"

        report += f"\n"

        # 系统指标
        report += f"系统指标:\n"
        report += f"  系统频率: {result.system_frequency:.3f} Hz\n"
        report += f"  三相不平衡度: {result.system_unbalance:.2f}%\n"

        if result.voltage_rms:
            report += f"  电压RMS值:\n"
            for channel, rms in result.voltage_rms.items():
                report += f"    {channel}: {rms:.3f} V\n"

        return report