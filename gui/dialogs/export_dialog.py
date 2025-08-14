#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出对话框
用于导出COMTRADE数据、图形和分析报告
"""

import os
import csv
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QGroupBox, QLabel, QCheckBox, QComboBox, QLineEdit, QPushButton,
    QFileDialog, QSpinBox, QDoubleSpinBox, QProgressBar, QTextEdit,
    QDialogButtonBox, QMessageBox, QFormLayout, QGridLayout,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QSplitter, QButtonGroup, QRadioButton
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon

from typing import Optional, List, Dict, Any
from models.data_models import ComtradeRecord, AnalysisResult
from config.constants import EXPORT_FORMATS, PLOT_EXPORT_FORMATS, FILE_FILTERS
from utils.logger import get_logger

logger = get_logger(__name__)


class ExportWorker(QThread):
    """导出工作线程"""

    # 信号定义
    progress_updated = pyqtSignal(int, str)  # 进度值, 状态消息
    export_completed = pyqtSignal(str)  # 导出完成，文件路径
    error_occurred = pyqtSignal(str)  # 错误消息

    def __init__(self, export_config: Dict[str, Any]):
        super().__init__()
        self.config = export_config
        self.is_cancelled = False

    def run(self):
        """执行导出"""
        try:
            export_type = self.config['type']

            if export_type == 'data':
                self._export_data()
            elif export_type == 'plot':
                self._export_plot()
            elif export_type == 'report':
                self._export_report()
            else:
                self.error_occurred.emit(f"未知的导出类型: {export_type}")

        except Exception as e:
            logger.error(f"导出失败: {e}")
            self.error_occurred.emit(str(e))

    def _export_data(self):
        """导出数据"""
        record = self.config['record']
        file_path = self.config['file_path']
        format_type = self.config['format']
        selected_channels = self.config.get('selected_channels', {})

        self.progress_updated.emit(10, "准备数据...")

        if self.is_cancelled:
            return

        # 准备数据
        data_dict = {'Time(s)': record.time_axis}

        # 添加选中的模拟通道
        analog_channels = selected_channels.get('analog', [])
        for i in analog_channels:
            if i < len(record.analog_channels):
                channel = record.analog_channels[i]
                column_name = f"{channel.name}"
                if channel.unit:
                    column_name += f"({channel.unit})"
                data_dict[column_name] = channel.scaled_data

        # 添加选中的数字通道
        digital_channels = selected_channels.get('digital', [])
        for i in digital_channels:
            if i < len(record.digital_channels):
                channel = record.digital_channels[i]
                data_dict[channel.name] = channel.data.astype(int)

        self.progress_updated.emit(50, "写入文件...")

        if self.is_cancelled:
            return

        # 根据格式导出
        if format_type == 'CSV':
            self._write_csv(data_dict, file_path)
        elif format_type == 'TXT':
            self._write_txt(data_dict, file_path)
        elif format_type == 'EXCEL':
            self._write_excel(data_dict, file_path)

        self.progress_updated.emit(100, "导出完成")
        self.export_completed.emit(file_path)

    def _export_plot(self):
        """导出图形"""
        # TODO: 实现图形导出
        plot_widget = self.config['plot_widget']
        file_path = self.config['file_path']

        self.progress_updated.emit(50, "生成图形...")

        if self.is_cancelled:
            return

        # 保存图形
        plot_widget.save_plot(file_path)

        self.progress_updated.emit(100, "图形导出完成")
        self.export_completed.emit(file_path)

    def _export_report(self):
        """导出分析报告"""
        # TODO: 实现报告导出
        analysis_result = self.config['analysis_result']
        file_path = self.config['file_path']

        self.progress_updated.emit(30, "生成报告...")

        if self.is_cancelled:
            return

        # 生成报告内容
        report_content = self._generate_report_content(analysis_result)

        self.progress_updated.emit(70, "写入文件...")

        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        self.progress_updated.emit(100, "报告导出完成")
        self.export_completed.emit(file_path)

    def _write_csv(self, data_dict: Dict[str, Any], file_path: str):
        """写入CSV文件"""
        import pandas as pd
        df = pd.DataFrame(data_dict)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')

    def _write_txt(self, data_dict: Dict[str, Any], file_path: str):
        """写入文本文件"""
        import pandas as pd
        df = pd.DataFrame(data_dict)
        df.to_csv(file_path, index=False, sep='\t', encoding='utf-8')

    def _write_excel(self, data_dict: Dict[str, Any], file_path: str):
        """写入Excel文件"""
        try:
            import pandas as pd
            df = pd.DataFrame(data_dict)
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='COMTRADE数据', index=False)
        except ImportError:
            # 如果没有openpyxl，使用xlsxwriter
            import pandas as pd
            df = pd.DataFrame(data_dict)
            df.to_excel(file_path, index=False, engine='xlsxwriter')

    def _generate_report_content(self, analysis_result: AnalysisResult) -> str:
        """生成报告内容"""
        report = f"COMTRADE波形分析报告\n"
        report += f"=" * 60 + "\n\n"

        # 基本信息
        report += f"分析时间: {analysis_result.timestamp}\n"
        report += f"分析耗时: {analysis_result.analysis_duration:.2f} 秒\n\n"

        # 故障检测结果
        report += f"故障检测结果:\n"
        report += f"-" * 30 + "\n"

        if analysis_result.fault_events:
            for i, event in enumerate(analysis_result.fault_events, 1):
                report += f"{i}. {event.fault_type.value}\n"
                report += f"   时间: {event.start_time:.4f}s - {event.end_time:.4f}s\n"
                report += f"   持续时间: {event.duration * 1000:.1f}ms\n"
                report += f"   严重程度: {event.severity:.2f}\n"
                report += f"   描述: {event.description}\n\n"
        else:
            report += "未检测到故障事件\n\n"

        # 系统指标
        report += f"系统指标:\n"
        report += f"-" * 30 + "\n"
        report += f"系统频率: {analysis_result.system_frequency:.3f} Hz\n"
        report += f"三相不平衡度: {analysis_result.system_unbalance:.2f}%\n"

        if analysis_result.voltage_rms:
            report += f"\n电压RMS值:\n"
            for channel, rms in analysis_result.voltage_rms.items():
                report += f"  {channel}: {rms:.3f} V\n"

        if analysis_result.current_rms:
            report += f"\n电流RMS值:\n"
            for channel, rms in analysis_result.current_rms.items():
                report += f"  {channel}: {rms:.3f} A\n"

        return report

    def cancel(self):
        """取消导出"""
        self.is_cancelled = True


class DataExportWidget(QWidget):
    """数据导出组件"""

    def __init__(self, record: ComtradeRecord):
        super().__init__()
        self.record = record
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 格式选择
        format_group = QGroupBox("导出格式")
        format_layout = QVBoxLayout(format_group)

        self.format_group = QButtonGroup()

        for format_name, format_info in EXPORT_FORMATS.items():
            radio = QRadioButton(format_info['description'])
            radio.setObjectName(format_name)
            self.format_group.addButton(radio)
            format_layout.addWidget(radio)

            if format_name == 'CSV':
                radio.setChecked(True)  # 默认选择CSV

        layout.addWidget(format_group)

        # 通道选择
        channel_group = QGroupBox("选择导出通道")
        channel_layout = QVBoxLayout(channel_group)

        # 创建通道列表
        self.channel_list = QListWidget()
        self.channel_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

        # 添加模拟通道
        if self.record.analog_channels:
            analog_item = QListWidgetItem("--- 模拟通道 ---")
            analog_item.setFlags(Qt.ItemFlag.NoItemFlags)  # 不可选择
            font = QFont()
            font.setBold(True)
            analog_item.setFont(font)
            self.channel_list.addItem(analog_item)

            for channel in self.record.analog_channels:
                item_text = f"{channel.name}"
                if channel.unit:
                    item_text += f" ({channel.unit})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, ('analog', channel.index))
                self.channel_list.addItem(item)

        # 添加数字通道
        if self.record.digital_channels:
            digital_item = QListWidgetItem("--- 数字通道 ---")
            digital_item.setFlags(Qt.ItemFlag.NoItemFlags)  # 不可选择
            font = QFont()
            font.setBold(True)
            digital_item.setFont(font)
            self.channel_list.addItem(digital_item)

            for channel in self.record.digital_channels:
                item = QListWidgetItem(channel.name)
                item.setData(Qt.ItemDataRole.UserRole, ('digital', channel.index))
                self.channel_list.addItem(item)

        channel_layout.addWidget(self.channel_list)

        # 快速选择按钮
        quick_btn_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self.select_all_channels)
        quick_btn_layout.addWidget(self.select_all_btn)

        self.select_none_btn = QPushButton("清除")
        self.select_none_btn.clicked.connect(self.select_no_channels)
        quick_btn_layout.addWidget(self.select_none_btn)

        self.select_analog_btn = QPushButton("仅模拟")
        self.select_analog_btn.clicked.connect(self.select_analog_channels)
        quick_btn_layout.addWidget(self.select_analog_btn)

        channel_layout.addLayout(quick_btn_layout)
        layout.addWidget(channel_group)

        # 导出选项
        options_group = QGroupBox("导出选项")
        options_layout = QFormLayout(options_group)

        # 时间范围
        self.export_all_cb = QCheckBox("导出全部时间")
        self.export_all_cb.setChecked(True)
        self.export_all_cb.toggled.connect(self.toggle_time_range)
        options_layout.addRow(self.export_all_cb)

        # 自定义时间范围
        time_layout = QHBoxLayout()

        self.start_time_spin = QDoubleSpinBox()
        self.start_time_spin.setRange(0, 999999)
        self.start_time_spin.setSuffix(" s")
        self.start_time_spin.setEnabled(False)
        time_layout.addWidget(QLabel("开始:"))
        time_layout.addWidget(self.start_time_spin)

        self.end_time_spin = QDoubleSpinBox()
        self.end_time_spin.setRange(0, 999999)
        self.end_time_spin.setSuffix(" s")
        self.end_time_spin.setEnabled(False)
        time_layout.addWidget(QLabel("结束:"))
        time_layout.addWidget(self.end_time_spin)

        options_layout.addRow("时间范围:", time_layout)

        # 数据精度
        self.precision_spin = QSpinBox()
        self.precision_spin.setRange(1, 10)
        self.precision_spin.setValue(6)
        options_layout.addRow("小数精度:", self.precision_spin)

        layout.addWidget(options_group)

        # 设置时间范围
        if len(self.record.time_axis) > 0:
            self.start_time_spin.setValue(float(self.record.time_axis[0]))
            self.end_time_spin.setValue(float(self.record.time_axis[-1]))

    def select_all_channels(self):
        """全选通道"""
        for i in range(self.channel_list.count()):
            item = self.channel_list.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsSelectable:
                item.setSelected(True)

    def select_no_channels(self):
        """清除选择"""
        self.channel_list.clearSelection()

    def select_analog_channels(self):
        """选择模拟通道"""
        self.channel_list.clearSelection()
        for i in range(self.channel_list.count()):
            item = self.channel_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if data and data[0] == 'analog':
                item.setSelected(True)

    def toggle_time_range(self, enabled: bool):
        """切换时间范围设置"""
        self.start_time_spin.setEnabled(not enabled)
        self.end_time_spin.setEnabled(not enabled)

    def get_export_config(self) -> Dict[str, Any]:
        """获取导出配置"""
        # 获取选中的格式
        selected_format = None
        for button in self.format_group.buttons():
            if button.isChecked():
                selected_format = button.objectName()
                break

        # 获取选中的通道
        selected_channels = {'analog': [], 'digital': []}
        for item in self.channel_list.selectedItems():
            data = item.data(Qt.ItemDataRole.UserRole)
            if data:
                channel_type, channel_index = data
                selected_channels[channel_type].append(channel_index)

        # 时间范围
        if self.export_all_cb.isChecked():
            time_range = None
        else:
            time_range = (self.start_time_spin.value(), self.end_time_spin.value())

        return {
            'type': 'data',
            'format': selected_format,
            'selected_channels': selected_channels,
            'time_range': time_range,
            'precision': self.precision_spin.value(),
            'record': self.record
        }


class PlotExportWidget(QWidget):
    """图形导出组件"""

    def __init__(self, plot_widget=None):
        super().__init__()
        self.plot_widget = plot_widget
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 格式选择
        format_group = QGroupBox("图形格式")
        format_layout = QVBoxLayout(format_group)

        self.format_group = QButtonGroup()

        for format_name, format_info in PLOT_EXPORT_FORMATS.items():
            radio = QRadioButton(format_info['description'])
            radio.setObjectName(format_name)
            self.format_group.addButton(radio)
            format_layout.addWidget(radio)

            if format_name == 'PNG':
                radio.setChecked(True)  # 默认选择PNG

        layout.addWidget(format_group)

        # 图形选项
        options_group = QGroupBox("图形选项")
        options_layout = QFormLayout(options_group)

        # DPI设置
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 600)
        self.dpi_spin.setValue(300)
        self.dpi_spin.setSuffix(" DPI")
        options_layout.addRow("分辨率:", self.dpi_spin)

        # 尺寸设置
        size_layout = QHBoxLayout()

        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 5000)
        self.width_spin.setValue(1200)
        self.width_spin.setSuffix(" px")
        size_layout.addWidget(self.width_spin)

        size_layout.addWidget(QLabel("×"))

        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 5000)
        self.height_spin.setValue(800)
        self.height_spin.setSuffix(" px")
        size_layout.addWidget(self.height_spin)

        options_layout.addRow("图片尺寸:", size_layout)

        # 透明背景
        self.transparent_cb = QCheckBox("透明背景")
        options_layout.addRow(self.transparent_cb)

        # 包含图例
        self.include_legend_cb = QCheckBox("包含图例")
        self.include_legend_cb.setChecked(True)
        options_layout.addRow(self.include_legend_cb)

        layout.addWidget(options_group)

        layout.addStretch()

    def get_export_config(self) -> Dict[str, Any]:
        """获取导出配置"""
        # 获取选中的格式
        selected_format = None
        for button in self.format_group.buttons():
            if button.isChecked():
                selected_format = button.objectName()
                break

        return {
            'type': 'plot',
            'format': selected_format,
            'dpi': self.dpi_spin.value(),
            'width': self.width_spin.value(),
            'height': self.height_spin.value(),
            'transparent': self.transparent_cb.isChecked(),
            'include_legend': self.include_legend_cb.isChecked(),
            'plot_widget': self.plot_widget
        }


class ReportExportWidget(QWidget):
    """报告导出组件"""

    def __init__(self, analysis_result: Optional[AnalysisResult] = None):
        super().__init__()
        self.analysis_result = analysis_result
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 报告类型
        type_group = QGroupBox("报告类型")
        type_layout = QVBoxLayout(type_group)

        self.summary_cb = QCheckBox("摘要报告")
        self.summary_cb.setChecked(True)
        type_layout.addWidget(self.summary_cb)

        self.detailed_cb = QCheckBox("详细报告")
        self.detailed_cb.setChecked(True)
        type_layout.addWidget(self.detailed_cb)

        self.fault_only_cb = QCheckBox("仅故障分析")
        type_layout.addWidget(self.fault_only_cb)

        layout.addWidget(type_group)

        # 包含内容
        content_group = QGroupBox("包含内容")
        content_layout = QVBoxLayout(content_group)

        self.include_charts_cb = QCheckBox("包含图表")
        self.include_charts_cb.setChecked(True)
        content_layout.addWidget(self.include_charts_cb)

        self.include_statistics_cb = QCheckBox("包含统计数据")
        self.include_statistics_cb.setChecked(True)
        content_layout.addWidget(self.include_statistics_cb)

        self.include_raw_data_cb = QCheckBox("包含原始数据")
        content_layout.addWidget(self.include_raw_data_cb)

        layout.addWidget(content_group)

        # 格式选项
        format_group = QGroupBox("报告格式")
        format_layout = QVBoxLayout(format_group)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["文本报告 (.txt)", "HTML报告 (.html)", "PDF报告 (.pdf)"])
        format_layout.addWidget(self.format_combo)

        layout.addWidget(format_group)

        # 预览区域
        preview_group = QGroupBox("报告预览")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_text = QTextEdit()
        self.preview_text.setMaximumHeight(200)
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)

        # 更新预览按钮
        self.update_preview_btn = QPushButton("更新预览")
        self.update_preview_btn.clicked.connect(self.update_preview)
        preview_layout.addWidget(self.update_preview_btn)

        layout.addWidget(preview_group)

        # 初始化预览
        self.update_preview()

    def update_preview(self):
        """更新报告预览"""
        if not self.analysis_result:
            self.preview_text.setPlainText("暂无分析结果")
            return

        # 生成预览内容
        preview = "COMTRADE分析报告预览\n"
        preview += "=" * 40 + "\n\n"

        if self.summary_cb.isChecked():
            preview += f"检测到 {len(self.analysis_result.fault_events)} 个故障事件\n"
            preview += f"分析了 {len(self.analysis_result.channel_features)} 个通道\n"
            preview += f"系统频率: {self.analysis_result.system_frequency:.3f} Hz\n\n"

        if self.detailed_cb.isChecked() and self.analysis_result.fault_events:
            preview += "故障详情:\n"
            for i, event in enumerate(self.analysis_result.fault_events[:3], 1):
                preview += f"{i}. {event.fault_type.value} "
                preview += f"({event.start_time:.4f}s)\n"

            if len(self.analysis_result.fault_events) > 3:
                preview += f"... 还有 {len(self.analysis_result.fault_events) - 3} 个故障\n"

        self.preview_text.setPlainText(preview)

    def get_export_config(self) -> Dict[str, Any]:
        """获取导出配置"""
        return {
            'type': 'report',
            'format': self.format_combo.currentText().split('(')[1].rstrip(')'),
            'include_summary': self.summary_cb.isChecked(),
            'include_detailed': self.detailed_cb.isChecked(),
            'fault_only': self.fault_only_cb.isChecked(),
            'include_charts': self.include_charts_cb.isChecked(),
            'include_statistics': self.include_statistics_cb.isChecked(),
            'include_raw_data': self.include_raw_data_cb.isChecked(),
            'analysis_result': self.analysis_result
        }


class ExportDialog(QDialog):
    """导出对话框主类"""

    def __init__(self, record: ComtradeRecord, parent=None,
                 plot_widget=None, analysis_result: Optional[AnalysisResult] = None):
        super().__init__(parent)
        self.record = record
        self.plot_widget = plot_widget
        self.analysis_result = analysis_result
        self.export_worker = None

        self.init_ui()
        self.setup_connections()

        # 设置对话框属性
        self.setWindowTitle("导出数据")
        self.setModal(True)
        self.resize(700, 600)

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 数据导出标签页
        self.data_widget = DataExportWidget(self.record)
        self.tab_widget.addTab(self.data_widget, "📊 导出数据")

        # 图形导出标签页
        if self.plot_widget:
            self.plot_export_widget = PlotExportWidget(self.plot_widget)
            self.tab_widget.addTab(self.plot_export_widget, "📈 导出图形")

        # 报告导出标签页
        if self.analysis_result:
            self.report_widget = ReportExportWidget(self.analysis_result)
            self.tab_widget.addTab(self.report_widget, "📄 导出报告")

        layout.addWidget(self.tab_widget)

        # 文件路径选择
        file_group = QGroupBox("导出文件")
        file_layout = QHBoxLayout(file_group)

        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("选择导出文件路径...")
        file_layout.addWidget(self.file_path_edit)

        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.browse_btn)

        layout.addWidget(file_group)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 状态标签
        self.status_label = QLabel("准备导出")
        layout.addWidget(self.status_label)

        # 按钮组
        button_layout = QHBoxLayout()

        self.export_btn = QPushButton("开始导出")
        self.export_btn.clicked.connect(self.start_export)
        button_layout.addWidget(self.export_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.cancel_export)
        button_layout.addWidget(self.cancel_btn)

        button_layout.addStretch()

        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def setup_connections(self):
        """设置信号连接"""
        # 标签页切换时更新文件路径
        self.tab_widget.currentChanged.connect(self.update_default_filename)

    def browse_file(self):
        """浏览文件"""
        current_tab = self.tab_widget.currentWidget()

        if current_tab == self.data_widget:
            # 数据导出
            config = self.data_widget.get_export_config()
            format_name = config['format']
            if format_name in EXPORT_FORMATS:
                ext = EXPORT_FORMATS[format_name]['extension']
                filter_str = EXPORT_FORMATS[format_name]['description']
            else:
                ext = '.csv'
                filter_str = 'CSV文件 (*.csv)'

        elif hasattr(self, 'plot_export_widget') and current_tab == self.plot_export_widget:
            # 图形导出
            config = self.plot_export_widget.get_export_config()
            format_name = config['format']
            if format_name in PLOT_EXPORT_FORMATS:
                ext = PLOT_EXPORT_FORMATS[format_name]['extension']
                filter_str = PLOT_EXPORT_FORMATS[format_name]['description']
            else:
                ext = '.png'
                filter_str = 'PNG图片 (*.png)'

        elif hasattr(self, 'report_widget') and current_tab == self.report_widget:
            # 报告导出
            ext = '.txt'
            filter_str = '文本文件 (*.txt)'

        else:
            ext = '.csv'
            filter_str = 'CSV文件 (*.csv)'

        # 默认文件名
        default_name = f"comtrade_export{ext}"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择导出文件", default_name, filter_str
        )

        if file_path:
            self.file_path_edit.setText(file_path)

    def update_default_filename(self):
        """更新默认文件名"""
        if not self.file_path_edit.text():
            # 根据当前标签页设置默认文件名
            current_tab = self.tab_widget.currentWidget()

            if current_tab == self.data_widget:
                self.file_path_edit.setText("comtrade_data.csv")
            elif hasattr(self, 'plot_export_widget') and current_tab == self.plot_export_widget:
                self.file_path_edit.setText("comtrade_plot.png")
            elif hasattr(self, 'report_widget') and current_tab == self.report_widget:
                self.file_path_edit.setText("comtrade_report.txt")

    def start_export(self):
        """开始导出"""
        file_path = self.file_path_edit.text().strip()
        if not file_path:
            QMessageBox.warning(self, "警告", "请选择导出文件路径")
            return

        # 获取当前标签页的配置
        current_tab = self.tab_widget.currentWidget()

        if current_tab == self.data_widget:
            config = self.data_widget.get_export_config()
        elif hasattr(self, 'plot_export_widget') and current_tab == self.plot_export_widget:
            config = self.plot_export_widget.get_export_config()
        elif hasattr(self, 'report_widget') and current_tab == self.report_widget:
            config = self.report_widget.get_export_config()
        else:
            QMessageBox.warning(self, "警告", "无效的导出类型")
            return

        config['file_path'] = file_path

        # 检查文件是否存在
        if os.path.exists(file_path):
            reply = QMessageBox.question(
                self, "确认", f"文件已存在，是否覆盖？\n{file_path}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                return

        # 创建导出工作线程
        self.export_worker = ExportWorker(config)
        self.export_worker.progress_updated.connect(self.update_progress)
        self.export_worker.export_completed.connect(self.export_completed)
        self.export_worker.error_occurred.connect(self.export_error)
        self.export_worker.finished.connect(self.export_finished)

        # 更新界面状态
        self.export_btn.setEnabled(False)
        self.tab_widget.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # 开始导出
        self.export_worker.start()

    def cancel_export(self):
        """取消导出"""
        if self.export_worker and self.export_worker.isRunning():
            self.export_worker.cancel()
            self.status_label.setText("正在取消导出...")
        else:
            self.reject()

    def update_progress(self, value: int, message: str):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)

    def export_completed(self, file_path: str):
        """导出完成"""
        self.status_label.setText(f"导出完成: {os.path.basename(file_path)}")

        # 询问是否打开文件
        reply = QMessageBox.question(
            self, "导出完成", f"文件已成功导出到:\n{file_path}\n\n是否要打开文件？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 使用系统默认程序打开文件
            try:
                os.startfile(file_path)  # Windows
            except AttributeError:
                import subprocess
                subprocess.call(['open', file_path])  # macOS

    def export_error(self, error_message: str):
        """导出错误"""
        self.status_label.setText(f"导出失败: {error_message}")
        QMessageBox.critical(self, "导出失败", f"导出过程中发生错误：\n{error_message}")

    def export_finished(self):
        """导出完成（线程结束）"""
        # 恢复界面状态
        self.export_btn.setEnabled(True)
        self.tab_widget.setEnabled(True)
        self.progress_bar.setVisible(False)

        # 清理工作线程
        if self.export_worker:
            self.export_worker.deleteLater()
            self.export_worker = None

    def closeEvent(self, event):
        """关闭事件"""
        if self.export_worker and self.export_worker.isRunning():
            reply = QMessageBox.question(
                self, "确认", "导出正在进行中，确定要关闭吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            else:
                self.export_worker.cancel()
                self.export_worker.wait(3000)  # 等待最多3秒

        event.accept()