#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
绘图组件
基于matplotlib的波形显示组件
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QCheckBox, QComboBox, QLabel, QSpinBox, QDoubleSpinBox,
    QGroupBox, QSlider, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal

from models.data_models import ComtradeRecord, ChannelInfo, FaultEvent
from config.settings import PlotSettings
from utils.logger import get_logger

logger = get_logger(__name__)

# 导入字体配置
try:
    from utils.font_config import create_safe_text, init_font_config
    FONT_CONFIG_AVAILABLE = True
except ImportError:
    FONT_CONFIG_AVAILABLE = False
    def create_safe_text(text): return text
    def init_font_config(): pass


class PlotCanvas(FigureCanvas):
    """绘图画布"""

    def __init__(self, settings: PlotSettings):
        self.settings = settings

        # 初始化字体配置
        if FONT_CONFIG_AVAILABLE:
            try:
                init_font_config()
            except Exception as e:
                logger.warning(f"字体配置失败: {e}")


        self.figure = Figure(figsize=(12, 8), dpi=settings.figure_dpi)
        super().__init__(self.figure)

        # 设置图形样式
        self.figure.patch.set_facecolor(settings.background_color)
        plt.style.use('default')  # 使用默认样式

        # 存储绘图相关数据
        self.axes = []
        self.current_record = None
        self.selected_channels = {}
        self.fault_events = []

        # 设置鼠标事件
        self.mpl_connect('button_press_event', self.on_mouse_press)
        self.mpl_connect('motion_notify_event', self.on_mouse_move)

    def _setup_matplotlib_font(self):
        """强制设置matplotlib中文字体"""
        try:
            import matplotlib.font_manager as fm
            from pathlib import Path
            
            # 获取自定义字体路径
            current_dir = Path(__file__).parent.parent.parent
            assets_fonts_dir = current_dir / 'assets' / 'fonts'
            
            # 优先使用的字体文件和对应的字体名称
            priority_fonts = [
                ('MicrosoftYaHeiBold.ttc', 'Microsoft YaHei'),
                ('MicrosoftYaHeiNormal.ttc', 'Microsoft YaHei'),
                ('STHeitiMedium.ttc', 'STHeiti')
            ]
            
            font_set = False
            for font_file, font_name in priority_fonts:
                font_path = assets_fonts_dir / font_file
                if font_path.exists():
                    try:
                        # 添加字体到matplotlib字体管理器
                        fm.fontManager.addfont(str(font_path))
                        
                        # 获取字体属性
                        font_prop = fm.FontProperties(fname=str(font_path))
                        actual_font_name = font_prop.get_name()
                        
                        # 设置matplotlib字体
                        plt.rcParams['font.sans-serif'] = [actual_font_name, font_name, 'Microsoft YaHei', 'SimHei']
                        plt.rcParams['axes.unicode_minus'] = False
                        
                        # 强制刷新字体缓存
                        plt.rcParams.update(plt.rcParams)
                        
                        logger.info(f"强制设置matplotlib字体: {actual_font_name} (文件: {font_file})")
                        font_set = True
                        break
                    except Exception as e:
                        logger.warning(f"设置字体 {font_file} 失败: {e}")
                        continue
            
            if not font_set:
                # 回退到系统字体
                plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
                plt.rcParams['axes.unicode_minus'] = False
                logger.warning("使用系统默认中文字体")
                
        except Exception as e:
            logger.error(f"设置matplotlib字体失败: {e}")

    def clear_plots(self):
        """清除所有图形"""
        self.figure.clear()
        self.axes = []
        self.draw()

    def plot_channels(self, record: ComtradeRecord, selected_channels: Dict[str, List[int]]):
        """
        绘制选中的通道

        Args:
            record: COMTRADE记录
            selected_channels: 选中的通道 {'analog': [0, 1, 2], 'digital': [0, 1]}
        """
        # 强制重新设置matplotlib中文字体
        self._setup_matplotlib_font()
        
        self.current_record = record
        self.selected_channels = selected_channels

        self.clear_plots()

        analog_indices = selected_channels.get('analog', [])
        digital_indices = selected_channels.get('digital', [])

        if not analog_indices and not digital_indices:
            return

        # 计算子图布局
        n_analog = len(analog_indices)
        n_digital = 1 if digital_indices else 0  # 数字通道合并显示
        total_subplots = n_analog + n_digital

        if total_subplots == 0:
            return

        # 绘制模拟通道
        self._plot_analog_channels(record, analog_indices, total_subplots, 0)

        # 绘制数字通道
        if digital_indices:
            self._plot_digital_channels(record, digital_indices, total_subplots, n_analog)

        # 设置整体标题
        title = f'COMTRADE{create_safe_text("波形数据")} - {record.station_name}'
        self.figure.suptitle(title, fontsize=14, fontweight='bold')



        # 调整布局
        self.figure.tight_layout()
        self.draw()

    def _plot_analog_channels(self, record: ComtradeRecord, channel_indices: List[int],
                              total_subplots: int, start_subplot: int):
        """绘制模拟通道"""
        time_axis = record.time_axis

        for i, ch_idx in enumerate(channel_indices):
            if ch_idx >= len(record.analog_channels):
                continue

            channel = record.analog_channels[ch_idx]
            subplot_idx = start_subplot + i + 1

            ax = self.figure.add_subplot(total_subplots, 1, subplot_idx)
            self.axes.append(ax)

            # 数据处理
            data = channel.scaled_data

            # 数据抽样（如果数据点太多）
            if len(data) > self.settings.max_points_per_plot:
                step = len(data) // self.settings.max_points_per_plot
                time_plot = time_axis[::step]
                data_plot = data[::step]
            else:
                time_plot = time_axis
                data_plot = data

            # 绘制波形
            line = ax.plot(time_plot, data_plot,
                           linewidth=self.settings.line_width,
                           label=channel.name,
                           color=self._get_channel_color(i))

            # 设置轴标签
            ax.set_ylabel(f"{channel.name}\n({channel.unit})", fontsize=10)


            # 网格
            if self.settings.grid_enabled:
                ax.grid(True, alpha=self.settings.grid_alpha)

            # 图例
            ax.legend(loc='upper right', fontsize=9)

            # 自动缩放
            if self.settings.auto_scale:
                ax.autoscale(enable=True, axis='both', tight=True)

            # 只在最后一个子图显示x轴标签
            if subplot_idx == total_subplots:
                ax.set_xlabel(create_safe_text('时间') + ' (s)', fontsize=10)
            else:
                ax.set_xticklabels([])

            # 设置y轴格式
            ax.ticklabel_format(axis='y', style='scientific', scilimits=(-3, 3))

    def _plot_digital_channels(self, record: ComtradeRecord, channel_indices: List[int],
                               total_subplots: int, subplot_idx: int):
        """绘制数字通道（合并显示）"""
        time_axis = record.time_axis

        ax = self.figure.add_subplot(total_subplots, 1, subplot_idx + 1)
        self.axes.append(ax)

        y_offset = 0
        colors = plt.cm.Set1(np.linspace(0, 1, len(channel_indices)))

        for i, ch_idx in enumerate(channel_indices):
            if ch_idx >= len(record.digital_channels):
                continue

            channel = record.digital_channels[ch_idx]
            data = channel.data.astype(float) + y_offset

            # 创建阶梯图
            ax.step(time_axis, data, where='post',
                    linewidth=self.settings.line_width + 0.5,
                    label=channel.name,
                    color=colors[i])

            y_offset += 1.2

        ax.set_ylabel(create_safe_text('数字状态'), fontsize=10)
        ax.set_xlabel(create_safe_text('时间') + ' (s)', fontsize=10)
        ax.set_title(create_safe_text('数字通道状态'), fontsize=11, fontweight='bold')

        if self.settings.grid_enabled:
            ax.grid(True, alpha=self.settings.grid_alpha)

        ax.legend(loc='upper right', fontsize=9)

        # 设置y轴范围
        ax.set_ylim(-0.5, y_offset)

    def _get_channel_color(self, index: int) -> str:
        """获取通道颜色"""
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        return colors[index % len(colors)]

    def highlight_fault_events(self, fault_events: List[FaultEvent]):
        """高亮显示故障事件"""
        self.fault_events = fault_events

        if not self.axes or not fault_events:
            return

        for ax in self.axes:
            # 清除之前的高亮
            for patch in ax.patches:
                if hasattr(patch, '_fault_highlight'):
                    patch.remove()

            # 添加故障事件高亮
            for event in fault_events:
                # 根据故障类型选择颜色
                color = self._get_fault_color(event.fault_type)
                alpha = 0.3 * event.severity  # 透明度反映严重程度

                # 创建矩形高亮区域
                ylim = ax.get_ylim()
                rect = Rectangle((event.start_time, ylim[0]),
                                 event.end_time - event.start_time,
                                 ylim[1] - ylim[0],
                                 facecolor=color, alpha=alpha,
                                 edgecolor=color, linewidth=1)
                rect._fault_highlight = True  # 标记为故障高亮
                ax.add_patch(rect)

        self.draw()

    def _get_fault_color(self, fault_type) -> str:
        """获取故障类型对应的颜色"""
        from models.data_models import FaultType

        color_map = {
            FaultType.SINGLE_PHASE_GROUND: 'red',
            FaultType.PHASE_TO_PHASE: 'orange',
            FaultType.TWO_PHASE_GROUND: 'red',
            FaultType.THREE_PHASE: 'darkred',
            FaultType.OVERVOLTAGE: 'purple',
            FaultType.UNDERVOLTAGE: 'blue',
            FaultType.OVERCURRENT: 'red',
            FaultType.FREQUENCY_DEVIATION: 'green',
            FaultType.HARMONIC_DISTORTION: 'yellow',
            FaultType.VOLTAGE_SAG: 'cyan',
            FaultType.VOLTAGE_SWELL: 'magenta',
            FaultType.TRANSIENT: 'gray'
        }

        return color_map.get(fault_type, 'gray')

    def zoom_to_time_range(self, start_time: float, end_time: float):
        """缩放到指定时间范围"""
        for ax in self.axes:
            ax.set_xlim(start_time, end_time)
        self.draw()

    def zoom_to_fault_event(self, event: FaultEvent, margin: float = 0.05):
        """缩放到故障事件"""
        duration = event.end_time - event.start_time
        margin_time = duration * margin

        start_time = max(0, event.start_time - margin_time)
        end_time = min(self.current_record.duration if self.current_record else event.end_time + margin_time,
                       event.end_time + margin_time)

        self.zoom_to_time_range(start_time, end_time)

    def reset_zoom(self):
        """重置缩放"""
        if self.current_record:
            for ax in self.axes:
                ax.autoscale(enable=True, axis='both', tight=True)
            self.draw()

    def on_mouse_press(self, event):
        """鼠标点击事件"""
        if event.inaxes and event.button == 1:  # 左键点击
            # 显示点击位置的信息
            x, y = event.xdata, event.ydata
            if x is not None and y is not None:
                logger.debug(f"鼠标点击位置: t={x:.4f}s, y={y:.4f}")

    def on_mouse_move(self, event):
        """鼠标移动事件"""
        if event.inaxes:
            x, y = event.xdata, event.ydata
            if x is not None and y is not None:
                # 可以在这里显示十字线或数值提示
                pass

    def save_plot(self, file_path: str, dpi: int = 300):
        """保存图形"""
        try:
            self.figure.savefig(file_path, dpi=dpi, bbox_inches='tight')
            logger.info(f"图形已保存到: {file_path}")
        except Exception as e:
            logger.error(f"保存图形失败: {e}")
            raise

    def update_settings(self, settings: PlotSettings):
        """更新绘图设置"""
        self.settings = settings

        # 重新绘制当前图形
        if self.current_record and self.selected_channels:
            self.plot_channels(self.current_record, self.selected_channels)


class PlotControlPanel(QWidget):
    """绘图控制面板"""

    # 信号定义
    zoom_to_range_requested = pyqtSignal(float, float)  # 缩放到指定范围
    reset_zoom_requested = pyqtSignal()  # 重置缩放
    highlight_faults_requested = pyqtSignal(bool)  # 高亮故障
    settings_changed = pyqtSignal()  # 设置变更

    def __init__(self, settings: PlotSettings):
        super().__init__()
        self.settings = settings
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)

        # 显示控制组
        display_group = QGroupBox("显示控制")
        display_layout = QVBoxLayout(display_group)

        # 网格显示
        self.grid_checkbox = QCheckBox("显示网格")
        self.grid_checkbox.setChecked(self.settings.grid_enabled)
        self.grid_checkbox.toggled.connect(self.on_grid_toggled)
        display_layout.addWidget(self.grid_checkbox)

        # 自动缩放
        self.auto_scale_checkbox = QCheckBox("自动缩放")
        self.auto_scale_checkbox.setChecked(self.settings.auto_scale)
        self.auto_scale_checkbox.toggled.connect(self.on_auto_scale_toggled)
        display_layout.addWidget(self.auto_scale_checkbox)

        # 线宽控制
        line_width_layout = QHBoxLayout()
        line_width_layout.addWidget(QLabel("线宽:"))
        self.line_width_spin = QDoubleSpinBox()
        self.line_width_spin.setRange(0.1, 5.0)
        self.line_width_spin.setSingleStep(0.1)
        self.line_width_spin.setValue(self.settings.line_width)
        self.line_width_spin.valueChanged.connect(self.on_line_width_changed)
        line_width_layout.addWidget(self.line_width_spin)
        display_layout.addLayout(line_width_layout)

        layout.addWidget(display_group)

        # 缩放控制组
        zoom_group = QGroupBox("缩放控制")
        zoom_layout = QVBoxLayout(zoom_group)

        # 时间范围输入
        time_range_layout = QHBoxLayout()
        time_range_layout.addWidget(QLabel("开始时间:"))
        self.start_time_spin = QDoubleSpinBox()
        self.start_time_spin.setRange(0, 999999)
        self.start_time_spin.setSuffix(" s")
        time_range_layout.addWidget(self.start_time_spin)

        time_range_layout.addWidget(QLabel("结束时间:"))
        self.end_time_spin = QDoubleSpinBox()
        self.end_time_spin.setRange(0, 999999)
        self.end_time_spin.setSuffix(" s")
        time_range_layout.addWidget(self.end_time_spin)

        zoom_layout.addLayout(time_range_layout)

        # 缩放按钮
        zoom_button_layout = QHBoxLayout()

        self.zoom_to_range_btn = QPushButton("缩放到范围")
        self.zoom_to_range_btn.clicked.connect(self.on_zoom_to_range)
        zoom_button_layout.addWidget(self.zoom_to_range_btn)

        self.reset_zoom_btn = QPushButton("重置缩放")
        self.reset_zoom_btn.clicked.connect(self.on_reset_zoom)
        zoom_button_layout.addWidget(self.reset_zoom_btn)

        zoom_layout.addLayout(zoom_button_layout)

        layout.addWidget(zoom_group)

        # 故障显示控制
        fault_group = QGroupBox("故障显示")
        fault_layout = QVBoxLayout(fault_group)

        self.highlight_faults_checkbox = QCheckBox("高亮显示故障事件")
        self.highlight_faults_checkbox.toggled.connect(self.on_highlight_faults_toggled)
        fault_layout.addWidget(self.highlight_faults_checkbox)

        layout.addWidget(fault_group)

        # 添加弹性空间
        layout.addStretch()

    def update_time_range(self, min_time: float, max_time: float):
        """更新时间范围控件"""
        self.start_time_spin.setRange(min_time, max_time)
        self.end_time_spin.setRange(min_time, max_time)
        self.start_time_spin.setValue(min_time)
        self.end_time_spin.setValue(max_time)

    def on_grid_toggled(self, checked: bool):
        """网格显示切换"""
        self.settings.grid_enabled = checked
        self.settings_changed.emit()

    def on_auto_scale_toggled(self, checked: bool):
        """自动缩放切换"""
        self.settings.auto_scale = checked
        self.settings_changed.emit()

    def on_line_width_changed(self, value: float):
        """线宽变更"""
        self.settings.line_width = value
        self.settings_changed.emit()

    def on_zoom_to_range(self):
        """缩放到指定范围"""
        start_time = self.start_time_spin.value()
        end_time = self.end_time_spin.value()

        if start_time >= end_time:
            return

        self.zoom_to_range_requested.emit(start_time, end_time)

    def on_reset_zoom(self):
        """重置缩放"""
        self.reset_zoom_requested.emit()

    def on_highlight_faults_toggled(self, checked: bool):
        """故障高亮切换"""
        self.highlight_faults_requested.emit(checked)


class PlotWidget(QWidget):
    """绘图组件主类"""

    def __init__(self, settings: PlotSettings):
        super().__init__()
        self.settings = settings
        self.init_ui()

        # 连接控制面板信号
        self.control_panel.zoom_to_range_requested.connect(self.canvas.zoom_to_time_range)
        self.control_panel.reset_zoom_requested.connect(self.canvas.reset_zoom)
        self.control_panel.settings_changed.connect(self.on_settings_changed)
        self.control_panel.highlight_faults_requested.connect(self.on_highlight_faults_requested)

    def init_ui(self):
        """初始化界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # 绘图区域
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)

        # 绘图画布
        self.canvas = PlotCanvas(self.settings)
        plot_layout.addWidget(self.canvas)

        # 导航工具栏
        self.toolbar = NavigationToolbar(self.canvas, self)
        plot_layout.addWidget(self.toolbar)

        splitter.addWidget(plot_widget)

        # 控制面板
        self.control_panel = PlotControlPanel(self.settings)
        self.control_panel.setMaximumWidth(250)
        splitter.addWidget(self.control_panel)

        # 设置分割器比例
        splitter.setSizes([800, 250])

    def plot_channels(self, record: ComtradeRecord, selected_channels: Dict[str, List[int]]):
        """绘制通道"""
        self.canvas.plot_channels(record, selected_channels)

        # 更新控制面板的时间范围
        if record and len(record.time_axis) > 0:
            min_time = float(record.time_axis[0])
            max_time = float(record.time_axis[-1])
            self.control_panel.update_time_range(min_time, max_time)

    def highlight_fault_events(self, fault_events: List[FaultEvent]):
        """高亮故障事件"""
        self.canvas.highlight_fault_events(fault_events)

    def has_plot(self) -> bool:
        """检查是否有绘图"""
        return len(self.canvas.axes) > 0

    def save_plot(self, file_path: str):
        """保存图形"""
        self.canvas.save_plot(file_path)

    def update_settings(self, settings: PlotSettings):
        """更新设置"""
        self.settings = settings
        self.canvas.update_settings(settings)

    def on_settings_changed(self):
        """设置变更处理"""
        self.canvas.update_settings(self.settings)

    def on_highlight_faults_requested(self, enabled: bool):
        """故障高亮请求处理"""
        if enabled and self.canvas.fault_events:
            self.canvas.highlight_fault_events(self.canvas.fault_events)
        else:
            # 清除高亮
            self.canvas.highlight_fault_events([])