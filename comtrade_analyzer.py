# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMTRADE波形数据分析器
使用PyQt6和matplotlib显示电力系统波形数据
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any

# PyQt6 imports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QStatusBar, QSplitter, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit,
    QPushButton, QFileDialog, QMessageBox, QLabel, QComboBox,
    QCheckBox, QSpinBox, QDoubleSpinBox, QGroupBox, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QFont, QIcon

# Matplotlib imports
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates

# COMTRADE库 - 需要安装: pip install comtrade
try:
    import comtrade

    COMTRADE_AVAILABLE = True
except ImportError:
    COMTRADE_AVAILABLE = False
    print("警告: comtrade库未安装，请运行: pip install comtrade")


class ComtradeData:
    """COMTRADE数据处理类"""

    def __init__(self):
        self.cfg_file = None
        self.data = None
        self.analog_channels = []
        self.digital_channels = []
        self.sample_rate = 0
        self.timestamp = None
        self.trigger_time = None

    def load_file(self, file_path: str) -> bool:
        """加载COMTRADE文件"""
        try:
            if not COMTRADE_AVAILABLE:
                raise ImportError("comtrade库未安装")

            # 自动检测文件类型
            if file_path.endswith('.cfg'):
                cfg_path = file_path
            elif file_path.endswith('.dat'):
                cfg_path = file_path.replace('.dat', '.cfg')
            else:
                cfg_path = file_path + '.cfg'

            if not os.path.exists(cfg_path):
                return False

            # 读取COMTRADE数据
            self.data = comtrade.load(cfg_path)
            self.cfg_file = cfg_path

            # 提取通道信息
            self._extract_channel_info()

            return True

        except Exception as e:
            print(f"加载文件失败: {e}")
            return False

    def _extract_channel_info(self):
        """提取通道信息"""
        if self.data is None:
            return

        # 模拟通道
        self.analog_channels = []
        for i, ch in enumerate(self.data.analog_channel_ids):
            channel_info = {
                'index': i,
                'id': ch,
                'name': self.data.analog_channel_ids[i] if i < len(self.data.analog_channel_ids) else f'Analog_{i}',
                'unit': self.data.analog_units[i] if i < len(self.data.analog_units) else '',
                'multiplier': self.data.analog_multiplier[i] if i < len(self.data.analog_multiplier) else 1.0,
                'offset': self.data.analog_offset[i] if i < len(self.data.analog_offset) else 0.0,
                'data': self.data.analog[i] if i < len(self.data.analog) else []
            }
            self.analog_channels.append(channel_info)

        # 数字通道
        self.digital_channels = []
        if hasattr(self.data, 'digital') and self.data.digital is not None:
            for i, ch in enumerate(self.data.digital_channel_ids):
                channel_info = {
                    'index': i,
                    'id': ch,
                    'name': self.data.digital_channel_ids[i] if i < len(
                        self.data.digital_channel_ids) else f'Digital_{i}',
                    'data': self.data.digital[i] if i < len(self.data.digital) else []
                }
                self.digital_channels.append(channel_info)

        # 采样率和时间信息
        self.sample_rate = self.data.frequency if hasattr(self.data, 'frequency') else 0
        self.trigger_time = self.data.trigger_time if hasattr(self.data, 'trigger_time') else None

    def get_time_axis(self) -> np.ndarray:
        """获取时间轴"""
        if self.data is None or len(self.analog_channels) == 0:
            return np.array([])

        return self.data.time


class MatplotlibWidget(FigureCanvas):
    """matplotlib绘图组件"""

    def __init__(self, parent=None):
        self.figure = Figure(figsize=(12, 8), dpi=100)
        super().__init__(self.figure)
        self.setParent(parent)

        # 设置图形样式
        self.figure.patch.set_facecolor('white')
        self.axes = []

    def clear_plots(self):
        """清除所有图形"""
        self.figure.clear()
        self.axes = []
        self.draw()

    def plot_analog_channels(self, comtrade_data: ComtradeData, selected_channels: List[int]):
        """绘制模拟通道波形"""
        self.clear_plots()

        if not selected_channels:
            return

        num_channels = len(selected_channels)
        time_axis = comtrade_data.get_time_axis()

        # 创建子图
        for i, ch_idx in enumerate(selected_channels):
            if ch_idx >= len(comtrade_data.analog_channels):
                continue

            channel = comtrade_data.analog_channels[ch_idx]
            ax = self.figure.add_subplot(num_channels, 1, i + 1)
            self.axes.append(ax)

            # 绘制波形
            ax.plot(time_axis, channel['data'], linewidth=1.0, label=channel['name'])
            ax.set_ylabel(f"{channel['name']}\n({channel['unit']})")
            ax.grid(True, alpha=0.3)
            ax.legend()

            # 只在最后一个子图显示x轴标签
            if i == num_channels - 1:
                ax.set_xlabel('时间 (s)')
            else:
                ax.set_xticklabels([])

        self.figure.suptitle('COMTRADE波形数据', fontsize=14, fontweight='bold')
        self.figure.tight_layout()
        self.draw()

    def plot_digital_channels(self, comtrade_data: ComtradeData, selected_channels: List[int]):
        """绘制数字通道波形"""
        if not selected_channels or not comtrade_data.digital_channels:
            return

        time_axis = comtrade_data.get_time_axis()
        ax = self.figure.add_subplot(1, 1, 1)

        offset = 0
        for ch_idx in selected_channels:
            if ch_idx >= len(comtrade_data.digital_channels):
                continue

            channel = comtrade_data.digital_channels[ch_idx]
            data = np.array(channel['data']) + offset
            ax.plot(time_axis, data, linewidth=1.5, label=channel['name'])
            offset += 1.2

        ax.set_xlabel('时间 (s)')
        ax.set_ylabel('数字状态')
        ax.set_title('数字通道状态')
        ax.grid(True, alpha=0.3)
        ax.legend()

        self.figure.tight_layout()
        self.draw()


class ChannelTreeWidget(QTreeWidget):
    """通道选择树形控件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(['通道', '单位', '类型'])
        self.setSelectionMode(QTreeWidget.SelectionMode.MultiSelection)

    def load_channels(self, comtrade_data: ComtradeData):
        """加载通道信息到树形控件"""
        self.clear()

        # 添加模拟通道
        if comtrade_data.analog_channels:
            analog_root = QTreeWidgetItem(self, ['模拟通道', '', ''])
            analog_root.setExpanded(True)

            for ch in comtrade_data.analog_channels:
                item = QTreeWidgetItem(analog_root, [
                    ch['name'],
                    ch['unit'],
                    '模拟'
                ])
                item.setData(0, Qt.ItemDataRole.UserRole, ('analog', ch['index']))
                item.setCheckState(0, Qt.CheckState.Unchecked)

        # 添加数字通道
        if comtrade_data.digital_channels:
            digital_root = QTreeWidgetItem(self, ['数字通道', '', ''])
            digital_root.setExpanded(True)

            for ch in comtrade_data.digital_channels:
                item = QTreeWidgetItem(digital_root, [
                    ch['name'],
                    '',
                    '数字'
                ])
                item.setData(0, Qt.ItemDataRole.UserRole, ('digital', ch['index']))
                item.setCheckState(0, Qt.CheckState.Unchecked)

    def get_selected_channels(self) -> tuple:
        """获取选中的通道"""
        analog_channels = []
        digital_channels = []

        def traverse_tree(item):
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and item.checkState(0) == Qt.CheckState.Checked:
                ch_type, ch_index = data
                if ch_type == 'analog':
                    analog_channels.append(ch_index)
                elif ch_type == 'digital':
                    digital_channels.append(ch_index)

            for i in range(item.childCount()):
                traverse_tree(item.child(i))

        for i in range(self.topLevelItemCount()):
            traverse_tree(self.topLevelItem(i))

        return analog_channels, digital_channels


class InfoWidget(QWidget):
    """信息显示组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 文件信息
        file_group = QGroupBox("文件信息")
        file_layout = QVBoxLayout(file_group)
        self.file_info = QTextEdit()
        self.file_info.setMaximumHeight(100)
        file_layout.addWidget(self.file_info)

        # 通道统计
        stats_group = QGroupBox("通道统计")
        stats_layout = QVBoxLayout(stats_group)
        self.stats_info = QTextEdit()
        self.stats_info.setMaximumHeight(100)
        stats_layout.addWidget(self.stats_info)

        # 数据表格
        table_group = QGroupBox("数据预览")
        table_layout = QVBoxLayout(table_group)
        self.data_table = QTableWidget()
        table_layout.addWidget(self.data_table)

        layout.addWidget(file_group)
        layout.addWidget(stats_group)
        layout.addWidget(table_group)

    def update_info(self, comtrade_data: ComtradeData):
        """更新信息显示"""
        # 文件信息
        file_info = f"""
文件路径: {comtrade_data.cfg_file or '未加载'}
采样频率: {comtrade_data.sample_rate} Hz
触发时间: {comtrade_data.trigger_time or '未知'}
"""
        self.file_info.setPlainText(file_info.strip())

        # 通道统计
        analog_count = len(comtrade_data.analog_channels)
        digital_count = len(comtrade_data.digital_channels)
        stats_info = f"""
模拟通道数: {analog_count}
数字通道数: {digital_count}
总通道数: {analog_count + digital_count}
数据点数: {len(comtrade_data.get_time_axis())}
"""
        self.stats_info.setPlainText(stats_info.strip())

        # 数据表格 - 显示前100个数据点
        self.update_data_table(comtrade_data)

    def update_data_table(self, comtrade_data: ComtradeData):
        """更新数据表格"""
        time_axis = comtrade_data.get_time_axis()
        if len(time_axis) == 0:
            return

        # 最多显示100行数据
        max_rows = min(100, len(time_axis))

        # 设置表格大小
        columns = ['时间(s)'] + [ch['name'] for ch in comtrade_data.analog_channels[:10]]  # 最多显示10个通道
        self.data_table.setRowCount(max_rows)
        self.data_table.setColumnCount(len(columns))
        self.data_table.setHorizontalHeaderLabels(columns)

        # 填充数据
        for row in range(max_rows):
            # 时间列
            self.data_table.setItem(row, 0, QTableWidgetItem(f"{time_axis[row]:.6f}"))

            # 数据列
            for col, ch in enumerate(comtrade_data.analog_channels[:10], 1):
                if row < len(ch['data']):
                    value = f"{ch['data'][row]:.3f}"
                    self.data_table.setItem(row, col, QTableWidgetItem(value))


class ComtradeAnalyzer(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.comtrade_data = ComtradeData()
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle('COMTRADE波形数据分析器')
        self.setGeometry(100, 100, 1400, 900)

        # 创建菜单栏
        self.create_menus()

        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('就绪')

        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # 左侧面板
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # 右侧面板 - 绘图和信息
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        # 设置分割器比例
        splitter.setSizes([350, 1050])

    def create_menus(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu('文件')

        open_action = QAction('打开COMTRADE文件', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 视图菜单
        view_menu = menubar.addMenu('视图')

        plot_action = QAction('绘制选中通道', self)
        plot_action.setShortcut('Ctrl+P')
        plot_action.triggered.connect(self.plot_selected_channels)
        view_menu.addAction(plot_action)

        # 帮助菜单
        help_menu = menubar.addMenu('帮助')

        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_left_panel(self) -> QWidget:
        """创建左侧控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 文件操作按钮
        file_group = QGroupBox("文件操作")
        file_layout = QVBoxLayout(file_group)

        self.open_btn = QPushButton('打开COMTRADE文件')
        self.open_btn.clicked.connect(self.open_file)
        file_layout.addWidget(self.open_btn)

        # 通道选择
        channel_group = QGroupBox("通道选择")
        channel_layout = QVBoxLayout(channel_group)

        self.channel_tree = ChannelTreeWidget()
        channel_layout.addWidget(self.channel_tree)

        # 操作按钮
        btn_layout = QHBoxLayout()
        self.select_all_btn = QPushButton('全选')
        self.select_all_btn.clicked.connect(self.select_all_channels)
        self.clear_selection_btn = QPushButton('清除')
        self.clear_selection_btn.clicked.connect(self.clear_selection)
        btn_layout.addWidget(self.select_all_btn)
        btn_layout.addWidget(self.clear_selection_btn)
        channel_layout.addLayout(btn_layout)

        # 绘图按钮
        self.plot_btn = QPushButton('绘制波形')
        self.plot_btn.clicked.connect(self.plot_selected_channels)
        self.plot_btn.setEnabled(False)
        channel_layout.addWidget(self.plot_btn)

        layout.addWidget(file_group)
        layout.addWidget(channel_group)

        return panel

    def create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 创建标签页
        tab_widget = QTabWidget()

        # 波形显示标签页
        self.plot_widget = MatplotlibWidget()
        tab_widget.addTab(self.plot_widget, "波形显示")

        # 信息显示标签页
        self.info_widget = InfoWidget()
        tab_widget.addTab(self.info_widget, "文件信息")

        layout.addWidget(tab_widget)

        return panel

    def open_file(self):
        """打开COMTRADE文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择COMTRADE文件",
            "",
            "COMTRADE文件 (*.cfg *.dat);;所有文件 (*)"
        )

        if file_path:
            if self.comtrade_data.load_file(file_path):
                self.status_bar.showMessage(f'成功加载文件: {os.path.basename(file_path)}')
                self.channel_tree.load_channels(self.comtrade_data)
                self.info_widget.update_info(self.comtrade_data)
                self.plot_btn.setEnabled(True)
            else:
                QMessageBox.critical(self, "错误", "无法加载COMTRADE文件！")

    def select_all_channels(self):
        """全选通道"""

        def set_check_state(item, state):
            if item.data(0, Qt.ItemDataRole.UserRole):
                item.setCheckState(0, state)
            for i in range(item.childCount()):
                set_check_state(item.child(i), state)

        for i in range(self.channel_tree.topLevelItemCount()):
            set_check_state(self.channel_tree.topLevelItem(i), Qt.CheckState.Checked)

    def clear_selection(self):
        """清除选择"""

        def set_check_state(item, state):
            if item.data(0, Qt.ItemDataRole.UserRole):
                item.setCheckState(0, state)
            for i in range(item.childCount()):
                set_check_state(item.child(i), state)

        for i in range(self.channel_tree.topLevelItemCount()):
            set_check_state(self.channel_tree.topLevelItem(i), Qt.CheckState.Unchecked)

    def plot_selected_channels(self):
        """绘制选中的通道"""
        analog_channels, digital_channels = self.channel_tree.get_selected_channels()

        if not analog_channels and not digital_channels:
            QMessageBox.information(self, "提示", "请先选择要显示的通道！")
            return

        # 绘制模拟通道
        if analog_channels:
            self.plot_widget.plot_analog_channels(self.comtrade_data, analog_channels)

        # 如果只有数字通道，单独绘制
        elif digital_channels:
            self.plot_widget.plot_digital_channels(self.comtrade_data, digital_channels)

        self.status_bar.showMessage(f'已绘制 {len(analog_channels)} 个模拟通道和 {len(digital_channels)} 个数字通道')

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于COMTRADE分析器",
            """
COMTRADE波形数据分析器 v1.0

这是一个用于分析电力系统COMTRADE格式数据的工具。

功能特性：
• 支持读取标准COMTRADE格式文件(.cfg/.dat)
• 可视化显示模拟和数字通道波形
• 通道信息和数据统计显示
• 交互式通道选择

开发技术：
• Python 3.x
• PyQt6
• matplotlib
• comtrade库

使用说明：
1. 点击"打开COMTRADE文件"选择数据文件
2. 在左侧通道树中选择要显示的通道
3. 点击"绘制波形"查看波形数据
            """
        )

def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("COMTRADE分析器")

    # 检查必要的库
    if not COMTRADE_AVAILABLE:
        QMessageBox.critical(
            None,
            "缺少依赖库",
            "请先安装comtrade库：\npip install comtrade"
        )
        return

    # 创建主窗口
    window = ComtradeAnalyzer()
    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()