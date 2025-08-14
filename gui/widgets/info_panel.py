#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信息面板组件
显示COMTRADE文件的基本信息、统计数据和数据预览
"""

import numpy as np
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit,
    QScrollArea, QFrame, QProgressBar, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette

from typing import Optional, Dict, Any
from models.data_models import ComtradeRecord
from config.constants import UI_STRINGS
from utils.logger import get_logger

logger = get_logger(__name__)


class InfoDisplayWidget(QWidget):
    """信息显示组件"""

    def __init__(self, title: str, icon: str = "ℹ️"):
        super().__init__()
        self.title = title
        self.icon = icon
        self.info_items = {}
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 创建组框
        self.group_box = QGroupBox(f"{self.icon} {self.title}")
        group_layout = QVBoxLayout(self.group_box)
        group_layout.setSpacing(3)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setMaximumHeight(200)

        # 信息容器
        self.info_container = QWidget()
        self.info_layout = QVBoxLayout(self.info_container)
        self.info_layout.setContentsMargins(5, 5, 5, 5)
        self.info_layout.setSpacing(2)

        scroll_area.setWidget(self.info_container)
        group_layout.addWidget(scroll_area)
        layout.addWidget(self.group_box)

    def add_info_item(self, key: str, label: str, value: str = "",
                      value_color: Optional[QColor] = None):
        """
        添加信息项

        Args:
            key: 键值，用于后续更新
            label: 显示标签
            value: 显示值
            value_color: 值的颜色
        """
        # 创建水平布局
        item_layout = QHBoxLayout()
        item_layout.setContentsMargins(0, 0, 0, 0)

        # 标签
        label_widget = QLabel(f"{label}:")
        label_widget.setMinimumWidth(80)
        label_widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        label_font = QFont()
        label_font.setPointSize(9)
        label_widget.setFont(label_font)
        label_widget.setStyleSheet("QLabel { color: #666666; }")

        # 值
        value_widget = QLabel(value)
        value_widget.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        value_font = QFont()
        value_font.setPointSize(9)
        value_font.setBold(True)
        value_widget.setFont(value_font)

        if value_color:
            value_widget.setStyleSheet(f"QLabel {{ color: {value_color.name()}; }}")
        else:
            value_widget.setStyleSheet("QLabel { color: #333333; }")

        item_layout.addWidget(label_widget)
        item_layout.addWidget(value_widget, 1)

        # 添加到容器
        self.info_layout.addLayout(item_layout)

        # 保存引用
        self.info_items[key] = value_widget

    def update_info_item(self, key: str, value: str,
                         value_color: Optional[QColor] = None):
        """
        更新信息项

        Args:
            key: 键值
            value: 新值
            value_color: 值的颜色
        """
        if key in self.info_items:
            widget = self.info_items[key]
            widget.setText(value)

            if value_color:
                widget.setStyleSheet(f"QLabel {{ color: {value_color.name()}; font-weight: bold; }}")
            else:
                widget.setStyleSheet("QLabel { color: #333333; font-weight: bold; }")

    def clear_info(self):
        """清除所有信息"""
        for widget in self.info_items.values():
            widget.setText("")

        # 也可以完全清除布局
        # for i in reversed(range(self.info_layout.count())):
        #     self.info_layout.itemAt(i).widget().setParent(None)
        # self.info_items.clear()


class DataPreviewWidget(QWidget):
    """数据预览组件"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 创建组框
        group_box = QGroupBox("📊 数据预览")
        group_layout = QVBoxLayout(group_box)

        # 创建表格
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setMaximumHeight(200)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        group_layout.addWidget(self.table)

        # 状态标签
        self.status_label = QLabel("暂无数据")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("QLabel { color: #888888; font-style: italic; }")
        group_layout.addWidget(self.status_label)

        layout.addWidget(group_box)

    def update_preview(self, record: ComtradeRecord):
        """
        更新数据预览

        Args:
            record: COMTRADE记录
        """
        try:
            if not record or len(record.time_axis) == 0:
                self.clear_preview()
                return

            # 准备数据
            preview_data = {'时间(s)': record.time_axis}

            # 添加前几个模拟通道
            max_channels = 6  # 最多显示6个通道
            channel_count = 0

            for channel in record.analog_channels:
                if channel_count >= max_channels:
                    break
                if len(channel.data) > 0:
                    unit_str = f"({channel.unit})" if channel.unit else ""
                    column_name = f"{channel.name}{unit_str}"
                    preview_data[column_name] = channel.scaled_data
                    channel_count += 1

            # 创建DataFrame
            df = pd.DataFrame(preview_data)

            # 只显示前100行
            if len(df) > 100:
                df = df.head(100)
                show_rows = 100
            else:
                show_rows = len(df)

            # 更新表格
            self.table.setRowCount(show_rows)
            self.table.setColumnCount(len(df.columns))
            self.table.setHorizontalHeaderLabels(df.columns.tolist())

            # 填充数据
            for row in range(show_rows):
                for col, column_name in enumerate(df.columns):
                    value = df.iloc[row, col]
                    if isinstance(value, float):
                        if column_name.startswith('时间'):
                            text = f"{value:.6f}"
                        else:
                            text = f"{value:.3f}"
                    else:
                        text = str(value)

                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    # 时间列使用不同颜色
                    if col == 0:
                        item.setForeground(QColor('#0066CC'))

                    self.table.setItem(row, col, item)

            # 调整列宽
            self.table.resizeColumnsToContents()

            # 更新状态
            total_rows = len(record.time_axis)
            if show_rows < total_rows:
                self.status_label.setText(f"显示前 {show_rows} 行，共 {total_rows} 行数据")
            else:
                self.status_label.setText(f"共 {total_rows} 行数据")

            self.status_label.setStyleSheet("QLabel { color: #666666; }")

        except Exception as e:
            logger.error(f"更新数据预览失败: {e}")
            self.clear_preview()

    def clear_preview(self):
        """清除预览"""
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.status_label.setText("暂无数据")
        self.status_label.setStyleSheet("QLabel { color: #888888; font-style: italic; }")


class ChannelStatisticsWidget(QWidget):
    """通道统计组件"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 创建组框
        group_box = QGroupBox("📈 通道统计")
        group_layout = QVBoxLayout(group_box)

        # 创建表格
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setMaximumHeight(180)

        # 设置表头
        headers = ['通道名称', 'RMS值', '峰值', '最大值', '最小值']
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        group_layout.addWidget(self.table)
        layout.addWidget(group_box)

    def update_statistics(self, record: ComtradeRecord):
        """
        更新统计信息

        Args:
            record: COMTRADE记录
        """
        try:
            if not record or not record.analog_channels:
                self.clear_statistics()
                return

            # 计算统计信息
            channel_stats = []
            for channel in record.analog_channels:
                if len(channel.data) == 0:
                    continue

                data = channel.scaled_data
                stats = {
                    'name': channel.name,
                    'rms': channel.rms_value,
                    'peak': channel.peak_value,
                    'max': float(np.max(data)),
                    'min': float(np.min(data))
                }
                channel_stats.append(stats)

            # 更新表格
            self.table.setRowCount(len(channel_stats))

            for row, stats in enumerate(channel_stats):
                # 通道名称
                name_item = QTableWidgetItem(stats['name'])
                name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 0, name_item)

                # 数值列
                values = [stats['rms'], stats['peak'], stats['max'], stats['min']]
                for col, value in enumerate(values, 1):
                    item = QTableWidgetItem(f"{value:.3f}")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    # 根据数值大小设置颜色
                    if col == 2:  # 峰值列
                        if value > 1000:
                            item.setForeground(QColor('#CC0000'))  # 红色
                        elif value > 100:
                            item.setForeground(QColor('#FF6600'))  # 橙色

                    self.table.setItem(row, col, item)

            # 调整列宽
            self.table.resizeColumnsToContents()

        except Exception as e:
            logger.error(f"更新通道统计失败: {e}")
            self.clear_statistics()

    def clear_statistics(self):
        """清除统计信息"""
        self.table.clear()
        self.table.setRowCount(0)
        # 重新设置表头
        headers = ['通道名称', 'RMS值', '峰值', '最大值', '最小值']
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)


class InfoPanel(QWidget):
    """信息面板主组件"""

    # 信号定义
    info_updated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_record: Optional[ComtradeRecord] = None
        self.init_ui()

        # 更新定时器
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_all_info)
        self.update_timer.setInterval(500)  # 500ms延迟更新

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 基本信息标签页
        self.basic_info_widget = self.create_basic_info_tab()
        self.tab_widget.addTab(self.basic_info_widget, "基本信息")

        # 数据预览标签页
        self.preview_widget = DataPreviewWidget()
        self.tab_widget.addTab(self.preview_widget, "数据预览")

        # 统计信息标签页
        self.stats_widget = ChannelStatisticsWidget()
        self.tab_widget.addTab(self.stats_widget, "通道统计")

        layout.addWidget(self.tab_widget)

    def create_basic_info_tab(self) -> QWidget:
        """创建基本信息标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # 文件信息
        self.file_info = InfoDisplayWidget("文件信息", "📁")
        self.file_info.add_info_item("file_path", "文件路径", "未加载")
        self.file_info.add_info_item("file_size", "文件大小", "0 KB")
        self.file_info.add_info_item("modified_time", "修改时间", "未知")
        layout.addWidget(self.file_info)

        # 录制信息
        self.record_info = InfoDisplayWidget("录制信息", "📊")
        self.record_info.add_info_item("station_name", "站点名称", "未知")
        self.record_info.add_info_item("device_id", "设备ID", "未知")
        self.record_info.add_info_item("start_time", "开始时间", "未知")
        self.record_info.add_info_item("trigger_time", "触发时间", "未知")
        layout.addWidget(self.record_info)

        # 采样信息
        self.sampling_info = InfoDisplayWidget("采样信息", "⏱️")
        self.sampling_info.add_info_item("frequency", "采样频率", "0 Hz")
        self.sampling_info.add_info_item("duration", "记录时长", "0.000 s")
        self.sampling_info.add_info_item("sample_count", "样本数量", "0")
        self.sampling_info.add_info_item("nominal_freq", "额定频率", "50 Hz")
        layout.addWidget(self.sampling_info)

        # 通道信息
        self.channel_info = InfoDisplayWidget("通道信息", "🔌")
        self.channel_info.add_info_item("analog_count", "模拟通道", "0")
        self.channel_info.add_info_item("digital_count", "数字通道", "0")
        self.channel_info.add_info_item("total_count", "总通道数", "0")
        layout.addWidget(self.channel_info)

        # 添加弹性空间
        layout.addStretch()

        return widget

    def update_info(self, record: ComtradeRecord):
        """
        更新信息显示

        Args:
            record: COMTRADE记录
        """
        self.current_record = record

        # 使用定时器延迟更新，避免频繁刷新
        self.update_timer.start()

    def update_all_info(self):
        """更新所有信息"""
        if not self.current_record:
            self.clear_all_info()
            return

        try:
            record = self.current_record

            # 更新文件信息
            self.update_file_info(record)

            # 更新录制信息
            self.update_record_info(record)

            # 更新采样信息
            self.update_sampling_info(record)

            # 更新通道信息
            self.update_channel_info(record)

            # 更新数据预览
            self.preview_widget.update_preview(record)

            # 更新统计信息
            self.stats_widget.update_statistics(record)

            # 发送更新完成信号
            self.info_updated.emit()

            logger.debug("信息面板更新完成")

        except Exception as e:
            logger.error(f"更新信息面板失败: {e}")
            self.clear_all_info()

    def update_file_info(self, record: ComtradeRecord):
        """更新文件信息"""
        if hasattr(record, 'file_info') and record.file_info:
            file_info = record.file_info

            # 文件路径
            import os
            file_name = os.path.basename(file_info.cfg_file)
            self.file_info.update_info_item("file_path", file_name)

            # 文件大小
            size_mb = file_info.file_size / (1024 * 1024)
            if size_mb > 1:
                size_str = f"{size_mb:.2f} MB"
            else:
                size_kb = file_info.file_size / 1024
                size_str = f"{size_kb:.1f} KB"
            self.file_info.update_info_item("file_size", size_str)

            # 修改时间
            if file_info.modified_time:
                time_str = file_info.modified_time.strftime("%Y-%m-%d %H:%M:%S")
                self.file_info.update_info_item("modified_time", time_str)
        else:
            self.file_info.update_info_item("file_path", "内存数据")
            self.file_info.update_info_item("file_size", "未知")
            self.file_info.update_info_item("modified_time", "未知")

    def update_record_info(self, record: ComtradeRecord):
        """更新录制信息"""
        # 站点名称
        self.record_info.update_info_item("station_name",
                                          record.station_name or "未知")

        # 设备ID
        self.record_info.update_info_item("device_id",
                                          record.rec_dev_id or "未知")

        # 开始时间
        if record.start_timestamp:
            start_str = record.start_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            self.record_info.update_info_item("start_time", start_str)
        else:
            self.record_info.update_info_item("start_time", "未知")

        # 触发时间
        if record.trigger_timestamp:
            trigger_str = record.trigger_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            self.record_info.update_info_item("trigger_time", trigger_str,
                                              QColor('#CC6600'))  # 橙色突出显示
        else:
            self.record_info.update_info_item("trigger_time", "未知")

    def update_sampling_info(self, record: ComtradeRecord):
        """更新采样信息"""
        # 计算实际采样频率
        if len(record.time_axis) > 1:
            dt = record.time_axis[1] - record.time_axis[0]
            actual_freq = 1.0 / dt if dt > 0 else 0
            freq_str = f"{actual_freq:.1f} Hz"
        else:
            freq_str = "未知"

        self.sampling_info.update_info_item("frequency", freq_str)

        # 记录时长
        duration = record.duration
        if duration > 1:
            duration_str = f"{duration:.3f} s"
        else:
            duration_str = f"{duration * 1000:.1f} ms"

        self.sampling_info.update_info_item("duration", duration_str)

        # 样本数量
        sample_count = len(record.time_axis)
        if sample_count > 1000:
            count_str = f"{sample_count:,}"  # 添加千位分隔符
        else:
            count_str = str(sample_count)

        self.sampling_info.update_info_item("sample_count", count_str)

        # 额定频率
        nominal_freq = record.frequency
        self.sampling_info.update_info_item("nominal_freq", f"{nominal_freq} Hz")

    def update_channel_info(self, record: ComtradeRecord):
        """更新通道信息"""
        analog_count = len(record.analog_channels)
        digital_count = len(record.digital_channels)
        total_count = analog_count + digital_count

        # 设置颜色
        analog_color = QColor('#2E86AB') if analog_count > 0 else None
        digital_color = QColor('#A23B72') if digital_count > 0 else None
        total_color = QColor('#2F7D32') if total_count > 0 else None

        self.channel_info.update_info_item("analog_count", str(analog_count), analog_color)
        self.channel_info.update_info_item("digital_count", str(digital_count), digital_color)
        self.channel_info.update_info_item("total_count", str(total_count), total_color)

    def clear_all_info(self):
        """清除所有信息"""
        # 清除基本信息
        self.file_info.clear_info()
        self.record_info.clear_info()
        self.sampling_info.clear_info()
        self.channel_info.clear_info()

        # 清除预览和统计
        self.preview_widget.clear_preview()
        self.stats_widget.clear_statistics()

        logger.debug("信息面板已清除")

    def get_current_info(self) -> Dict[str, Any]:
        """
        获取当前显示的信息

        Returns:
            信息字典
        """
        if not self.current_record:
            return {}

        # TODO: 实现信息提取
        info = {
            'station_name': self.current_record.station_name,
            'duration': self.current_record.duration,
            'channels': self.current_record.total_channels,
            'frequency': self.current_record.frequency,
            'sample_count': len(self.current_record.time_axis)
        }

        return info

    def export_info_to_text(self) -> str:
        """
        导出信息为文本格式

        Returns:
            格式化的文本信息
        """
        if not self.current_record:
            return "无数据"

        # TODO: 实现信息导出
        record = self.current_record

        text = f"COMTRADE文件信息报告\n"
        text += f"=" * 40 + "\n\n"

        text += f"文件信息:\n"
        text += f"  站点名称: {record.station_name}\n"
        text += f"  设备ID: {record.rec_dev_id}\n"
        text += f"  记录时长: {record.duration:.3f} 秒\n"
        text += f"  采样频率: {record.frequency} Hz\n"
        text += f"  样本数量: {len(record.time_axis)}\n\n"

        text += f"通道信息:\n"
        text += f"  模拟通道: {len(record.analog_channels)} 个\n"
        text += f"  数字通道: {len(record.digital_channels)} 个\n"
        text += f"  总通道数: {record.total_channels} 个\n\n"

        if record.start_timestamp:
            text += f"时间信息:\n"
            text += f"  开始时间: {record.start_timestamp}\n"
            if record.trigger_timestamp:
                text += f"  触发时间: {record.trigger_timestamp}\n"

        return text