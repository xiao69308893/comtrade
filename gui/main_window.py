#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口类
COMTRADE分析器的主界面
"""

import os
import sys
from pathlib import Path
from typing import Optional, List

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QStatusBar, QProgressBar, QLabel,
    QFileDialog, QMessageBox, QTabWidget, QTextEdit,
    QToolBar, QDockWidget
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSettings
from PyQt6.QtGui import QAction, QIcon, QKeySequence

# 导入项目模块
from config.settings import AppSettings
from core.comtrade_reader import ComtradeReader
from analysis.feature_extractor import FeatureExtractor
from analysis.fault_detector import FaultDetector, FaultDetectionConfig
from models.data_models import ComtradeRecord, AnalysisResult, FaultEvent
from gui.widgets.plot_widget import PlotWidget
from gui.widgets.channel_tree import ChannelTreeWidget
from gui.widgets.info_panel import InfoPanel
from gui.widgets.analysis_panel import AnalysisPanel
from gui.dialogs.preferences import PreferencesDialog
from gui.dialogs.export_dialog import ExportDialog
from utils.logger import get_logger, PerformanceLogger, get_performance_logger

logger = get_logger(__name__)


class AnalysisWorker(QThread):
    """分析工作线程"""

    # 信号定义
    progress_updated = pyqtSignal(int, str)  # 进度值, 状态消息
    analysis_completed = pyqtSignal(object)  # 分析结果
    error_occurred = pyqtSignal(str)  # 错误消息

    def __init__(self, record: ComtradeRecord, config: FaultDetectionConfig):
        super().__init__()
        self.record = record
        self.config = config
        self.is_cancelled = False

    def run(self):
        """执行分析"""
        try:
            self.progress_updated.emit(10, "初始化分析器...")

            # 检查是否取消
            if self.is_cancelled:
                return

            # 创建分析器
            fault_detector = FaultDetector(self.config)

            # 初始化特征提取器
            if len(self.record.time_axis) > 1:
                sampling_rate = 1.0 / (self.record.time_axis[1] - self.record.time_axis[0])
                feature_extractor = FeatureExtractor(sampling_rate, self.record.frequency)
            else:
                self.error_occurred.emit("无法确定采样频率")
                return

            self.progress_updated.emit(30, "分析通道特征...")

            # 提取各通道特征
            channel_features = {}
            total_channels = len(self.record.analog_channels) + len(self.record.digital_channels)

            for i, channel in enumerate(self.record.analog_channels):
                if self.is_cancelled:
                    return

                features = feature_extractor.extract_features(channel)
                channel_features[channel.name] = features

                progress = 30 + int(30 * (i + 1) / total_channels)
                self.progress_updated.emit(progress, f"分析通道: {channel.name}")

            self.progress_updated.emit(60, "检测故障事件...")

            # 故障检测
            fault_events = fault_detector.detect_faults(self.record)

            if self.is_cancelled:
                return

            self.progress_updated.emit(80, "生成分析报告...")

            # 创建分析结果
            from datetime import datetime
            result = AnalysisResult(
                timestamp=datetime.now(),
                record_info={
                    'station_name': self.record.station_name,
                    'duration': self.record.duration,
                    'channels': self.record.total_channels,
                    'frequency': self.record.frequency
                },
                channel_features=channel_features,
                fault_events=fault_events,
                system_frequency=self.record.frequency
            )

            # 计算系统级指标
            self._calculate_system_metrics(result)

            self.progress_updated.emit(100, "分析完成")
            self.analysis_completed.emit(result)

        except Exception as e:
            logger.error(f"分析过程中发生错误: {e}", exc_info=True)
            self.error_occurred.emit(str(e))

    def _calculate_system_metrics(self, result: AnalysisResult):
        """计算系统级指标"""
        try:
            # 计算各相电压RMS
            voltage_channels = [ch for ch in self.record.analog_channels
                                if any(keyword in ch.name.upper() for keyword in ['V', 'VOLT', 'U'])]

            for channel in voltage_channels:
                if len(channel.data) > 0:
                    features = result.channel_features.get(channel.name)
                    if features:
                        result.voltage_rms[channel.name] = features.rms

            # 计算各相电流RMS
            current_channels = [ch for ch in self.record.analog_channels
                                if any(keyword in ch.name.upper() for keyword in ['I', 'CURR', 'A'])]

            for channel in current_channels:
                if len(channel.data) > 0:
                    features = result.channel_features.get(channel.name)
                    if features:
                        result.current_rms[channel.name] = features.rms

            # 简单的不平衡度计算
            if len(result.voltage_rms) >= 3:
                voltages = list(result.voltage_rms.values())[:3]
                avg_voltage = sum(voltages) / len(voltages)
                if avg_voltage > 0:
                    max_deviation = max(abs(v - avg_voltage) for v in voltages)
                    result.system_unbalance = max_deviation / avg_voltage * 100

        except Exception as e:
            logger.warning(f"计算系统指标时发生错误: {e}")

    def cancel(self):
        """取消分析"""
        self.is_cancelled = True


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self, settings: AppSettings):
        super().__init__()
        self.settings = settings
        self.comtrade_reader = ComtradeReader()
        self.current_record: Optional[ComtradeRecord] = None
        self.current_analysis: Optional[AnalysisResult] = None
        self.analysis_worker: Optional[AnalysisWorker] = None

        # 性能监控
        self.performance_logger = get_performance_logger()

        self.init_ui()
        self.setup_menu_bar()
        self.setup_tool_bar()
        self.setup_status_bar()
        self.setup_dock_widgets()
        self.restore_window_state()

        # 设置定时器用于自动保存
        self.setup_auto_save()

        # 连接信号
        self.setup_signal_connections()

        logger.info("主窗口初始化完成")

    def setup_signal_connections(self):
        """设置信号连接"""
        # 连接分析面板的信号
        self.analysis_panel.fault_event_selected.connect(self.on_fault_event_selected)
        self.analysis_panel.zoom_to_fault_requested.connect(self.on_zoom_to_fault)

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("COMTRADE波形分析器 v2.0")
        self.setGeometry(100, 100,
                         self.settings.ui_settings.window_width,
                         self.settings.ui_settings.window_height)

        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 创建主分割器
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.main_splitter)

        # 左侧面板
        self.create_left_panel()

        # 右侧面板（绘图和分析）
        self.create_right_panel()

        # 设置分割器比例
        self.main_splitter.setSizes(self.settings.ui_settings.splitter_sizes)
        self.main_splitter.splitterMoved.connect(self.on_splitter_moved)

    def create_left_panel(self):
        """创建左侧控制面板"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # 通道选择树
        self.channel_tree = ChannelTreeWidget()
        self.channel_tree.channels_selected.connect(self.on_channels_selected)
        left_layout.addWidget(self.channel_tree)

        # 信息面板
        self.info_panel = InfoPanel()
        left_layout.addWidget(self.info_panel)

        # 设置布局比例
        left_layout.setStretchFactor(self.channel_tree, 3)
        left_layout.setStretchFactor(self.info_panel, 2)

        self.main_splitter.addWidget(left_widget)

    def create_right_panel(self):
        """创建右侧面板"""
        # 创建标签页组件
        self.tab_widget = QTabWidget()

        # 波形显示标签页
        self.plot_widget = PlotWidget(self.settings.plot_settings)
        self.tab_widget.addTab(self.plot_widget, "波形显示")

        # 分析结果标签页
        self.analysis_panel = AnalysisPanel()
        self.tab_widget.addTab(self.analysis_panel, "分析结果")

        # 日志标签页
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.tab_widget.addTab(self.log_widget, "运行日志")

        self.main_splitter.addWidget(self.tab_widget)

    def setup_menu_bar(self):
        """设置菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')

        # 打开文件
        open_action = QAction('打开COMTRADE文件(&O)...', self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setStatusTip('打开COMTRADE文件')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        # 最近文件子菜单
        self.recent_menu = file_menu.addMenu('最近文件(&R)')
        self.update_recent_files_menu()

        file_menu.addSeparator()

        # 导出菜单
        export_menu = file_menu.addMenu('导出(&E)')

        export_csv_action = QAction('导出为CSV...', self)
        export_csv_action.triggered.connect(self.export_csv)
        export_menu.addAction(export_csv_action)

        export_plot_action = QAction('导出图形...', self)
        export_plot_action.triggered.connect(self.export_plot)
        export_menu.addAction(export_plot_action)

        export_report_action = QAction('导出分析报告...', self)
        export_report_action.triggered.connect(self.export_report)
        export_menu.addAction(export_report_action)

        file_menu.addSeparator()

        # 退出
        exit_action = QAction('退出(&X)', self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 分析菜单
        analysis_menu = menubar.addMenu('分析(&A)')

        self.start_analysis_action = QAction('开始分析(&S)', self)
        self.start_analysis_action.setShortcut('F5')
        self.start_analysis_action.triggered.connect(self.start_analysis)
        self.start_analysis_action.setEnabled(False)
        analysis_menu.addAction(self.start_analysis_action)

        self.stop_analysis_action = QAction('停止分析(&T)', self)
        self.stop_analysis_action.triggered.connect(self.stop_analysis)
        self.stop_analysis_action.setEnabled(False)
        analysis_menu.addAction(self.stop_analysis_action)

        analysis_menu.addSeparator()

        config_analysis_action = QAction('分析配置(&C)...', self)
        config_analysis_action.triggered.connect(self.configure_analysis)
        analysis_menu.addAction(config_analysis_action)

        # 视图菜单
        view_menu = menubar.addMenu('视图(&V)')

        # 工具栏显示/隐藏
        toolbar_action = QAction('工具栏(&T)', self)
        toolbar_action.setCheckable(True)
        toolbar_action.setChecked(True)
        toolbar_action.triggered.connect(self.toggle_toolbar)
        view_menu.addAction(toolbar_action)

        # 状态栏显示/隐藏
        statusbar_action = QAction('状态栏(&S)', self)
        statusbar_action.setCheckable(True)
        statusbar_action.setChecked(True)
        statusbar_action.triggered.connect(self.toggle_statusbar)
        view_menu.addAction(statusbar_action)

        view_menu.addSeparator()

        # 全屏
        fullscreen_action = QAction('全屏(&F)', self)
        fullscreen_action.setShortcut('F11')
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        # 工具菜单
        tools_menu = menubar.addMenu('工具(&T)')

        preferences_action = QAction('首选项(&P)...', self)
        preferences_action.triggered.connect(self.show_preferences)
        tools_menu.addAction(preferences_action)

        # 帮助菜单
        help_menu = menubar.addMenu('帮助(&H)')

        about_action = QAction('关于(&A)...', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_tool_bar(self):
        """设置工具栏"""
        self.tool_bar = QToolBar('主工具栏')
        self.tool_bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(self.tool_bar)

        # 打开文件
        open_action = QAction('打开', self)
        open_action.setStatusTip('打开COMTRADE文件')
        open_action.triggered.connect(self.open_file)
        self.tool_bar.addAction(open_action)

        self.tool_bar.addSeparator()

        # 分析控制
        self.start_analysis_tool_action = QAction('开始分析', self)
        self.start_analysis_tool_action.triggered.connect(self.start_analysis)
        self.start_analysis_tool_action.setEnabled(False)
        self.tool_bar.addAction(self.start_analysis_tool_action)

        self.stop_analysis_tool_action = QAction('停止分析', self)
        self.stop_analysis_tool_action.triggered.connect(self.stop_analysis)
        self.stop_analysis_tool_action.setEnabled(False)
        self.tool_bar.addAction(self.stop_analysis_tool_action)

        self.tool_bar.addSeparator()

        # 导出
        export_action = QAction('导出', self)
        export_action.triggered.connect(self.export_csv)
        self.tool_bar.addAction(export_action)

    def setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # 状态标签
        self.status_label = QLabel('就绪')
        self.status_bar.addWidget(self.status_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)

        # 文件信息标签
        self.file_info_label = QLabel('')
        self.status_bar.addPermanentWidget(self.file_info_label)

    def setup_dock_widgets(self):
        """设置停靠窗口（可选功能）"""
        # 这里可以添加停靠窗口，比如属性面板、缩略图等
        pass

    def setup_auto_save(self):
        """设置自动保存"""
        if self.settings.ui_settings.auto_save_enabled:
            self.auto_save_timer = QTimer()
            self.auto_save_timer.timeout.connect(self.auto_save)
            self.auto_save_timer.start(self.settings.ui_settings.auto_save_interval * 1000)

    def restore_window_state(self):
        """恢复窗口状态"""
        settings = QSettings()

        # 恢复窗口几何
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        # 恢复窗口状态
        window_state = settings.value("windowState")
        if window_state:
            self.restoreState(window_state)

    def save_window_state(self):
        """保存窗口状态"""
        settings = QSettings()
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())

        # 保存分割器比例
        self.settings.ui_settings.splitter_sizes = self.main_splitter.sizes()
        self.settings.save_settings()

    def update_recent_files_menu(self):
        """更新最近文件菜单"""
        self.recent_menu.clear()

        recent_files = self.settings.get_recent_files()

        if not recent_files:
            no_recent_action = QAction('(无最近文件)', self)
            no_recent_action.setEnabled(False)
            self.recent_menu.addAction(no_recent_action)
            return

        for file_path in recent_files:
            file_name = Path(file_path).name
            action = QAction(file_name, self)
            action.setStatusTip(file_path)
            action.triggered.connect(lambda checked, path=file_path: self.open_recent_file(path))
            self.recent_menu.addAction(action)

        self.recent_menu.addSeparator()

        clear_action = QAction('清除列表', self)
        clear_action.triggered.connect(self.clear_recent_files)
        self.recent_menu.addAction(clear_action)

    def open_file(self):
        """打开文件对话框"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "打开COMTRADE文件",
            "",
            "COMTRADE文件 (*.cfg *.dat);;所有文件 (*)"
        )

        if file_path:
            self.load_comtrade_file(file_path)

    def open_recent_file(self, file_path: str):
        """打开最近文件"""
        if Path(file_path).exists():
            self.load_comtrade_file(file_path)
        else:
            QMessageBox.warning(self, "文件不存在", f"文件不存在：\n{file_path}")

    def clear_recent_files(self):
        """清除最近文件列表"""
        self.settings.ui_settings.recent_files.clear()
        self.settings.save_settings()
        self.update_recent_files_menu()

    def load_comtrade_file(self, file_path: str):
        """加载COMTRADE文件"""
        self.performance_logger.start_timer("load_file")

        try:
            self.update_status("正在加载文件...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            # 加载文件
            success = self.comtrade_reader.load_file(file_path)

            if success:
                self.current_record = self.comtrade_reader.current_record

                # 更新界面
                self.channel_tree.load_channels(self.current_record)
                self.info_panel.update_info(self.current_record)

                # 更新最近文件
                self.settings.add_recent_file(file_path)
                self.update_recent_files_menu()

                # 更新状态
                file_name = Path(file_path).name
                self.update_status(f"已加载文件: {file_name}")
                self.file_info_label.setText(f"文件: {file_name}")

                # 启用分析功能
                self.start_analysis_action.setEnabled(True)
                self.start_analysis_tool_action.setEnabled(True)

                logger.info(f"成功加载COMTRADE文件: {file_path}")

            else:
                QMessageBox.critical(self, "加载失败", "无法加载COMTRADE文件！\n请检查文件格式是否正确。")

        except Exception as e:
            logger.error(f"加载文件失败: {e}", exc_info=True)
            QMessageBox.critical(self, "错误", f"加载文件时发生错误：\n{str(e)}")

        finally:
            self.progress_bar.setVisible(False)
            elapsed = self.performance_logger.end_timer("load_file")
            logger.info(f"文件加载耗时: {elapsed:.2f}秒")

    def start_analysis(self):
        """开始分析"""
        if not self.current_record:
            QMessageBox.warning(self, "提示", "请先加载COMTRADE文件")
            return

        # 创建分析配置
        config = FaultDetectionConfig()

        # 创建分析工作线程
        self.analysis_worker = AnalysisWorker(self.current_record, config)
        self.analysis_worker.progress_updated.connect(self.on_analysis_progress)
        self.analysis_worker.analysis_completed.connect(self.on_analysis_completed)
        self.analysis_worker.error_occurred.connect(self.on_analysis_error)
        self.analysis_worker.finished.connect(self.on_analysis_finished)

        # 更新界面状态
        self.start_analysis_action.setEnabled(False)
        self.start_analysis_tool_action.setEnabled(False)
        self.stop_analysis_action.setEnabled(True)
        self.stop_analysis_tool_action.setEnabled(True)
        self.progress_bar.setVisible(True)

        # 开始分析
        self.analysis_worker.start()

        logger.info("开始分析COMTRADE数据")

    def stop_analysis(self):
        """停止分析"""
        if self.analysis_worker and self.analysis_worker.isRunning():
            self.analysis_worker.cancel()
            self.update_status("正在停止分析...")

    def on_analysis_progress(self, value: int, message: str):
        """分析进度更新"""
        self.progress_bar.setValue(value)
        self.update_status(message)

    def on_analysis_completed(self, result: AnalysisResult):
        """分析完成"""
        self.current_analysis = result
        self.analysis_panel.display_results(result)

        # 切换到分析结果标签页
        self.tab_widget.setCurrentIndex(1)

        logger.info(f"分析完成，检测到 {len(result.fault_events)} 个故障事件")

    def on_analysis_error(self, error_message: str):
        """分析出错"""
        QMessageBox.critical(self, "分析错误", f"分析过程中发生错误：\n{error_message}")
        logger.error(f"分析错误: {error_message}")

    def on_analysis_finished(self):
        """分析线程结束"""
        # 恢复界面状态
        self.start_analysis_action.setEnabled(True)
        self.start_analysis_tool_action.setEnabled(True)
        self.stop_analysis_action.setEnabled(False)
        self.stop_analysis_tool_action.setEnabled(False)
        self.progress_bar.setVisible(False)

        self.update_status("就绪")

        # 清理工作线程
        if self.analysis_worker:
            self.analysis_worker.deleteLater()
            self.analysis_worker = None

    def on_channels_selected(self, selected_channels: dict):
        """通道选择变化"""
        if self.current_record:
            self.plot_widget.plot_channels(self.current_record, selected_channels)

    def on_fault_event_selected(self, fault_event: FaultEvent):
        """故障事件选中处理"""
        logger.info(f"选中故障事件: {fault_event.fault_type.value} at {fault_event.start_time:.4f}s")

        # 可以在这里添加更多处理逻辑，比如在波形图中高亮显示故障区域
        if hasattr(self.plot_widget, 'highlight_fault_events'):
            self.plot_widget.highlight_fault_events([fault_event])

    def on_zoom_to_fault(self, fault_event: FaultEvent):
        """缩放到故障事件"""
        logger.info(f"缩放到故障事件: {fault_event.fault_type.value}")

        # 切换到波形显示标签页
        self.tab_widget.setCurrentIndex(0)

        # 缩放到故障时间范围
        if hasattr(self.plot_widget.canvas, 'zoom_to_fault_event'):
            self.plot_widget.canvas.zoom_to_fault_event(fault_event)

    def on_splitter_moved(self):
        """分割器移动"""
        # 实时保存分割器比例
        self.settings.ui_settings.splitter_sizes = self.main_splitter.sizes()

    def configure_analysis(self):
        """配置分析参数"""
        # 这里可以打开分析配置对话框
        QMessageBox.information(self, "功能开发中", "分析配置功能正在开发中...")

    def export_csv(self):
        """导出CSV"""
        if not self.current_record:
            QMessageBox.warning(self, "提示", "请先加载COMTRADE文件")
            return

        # 简化的导出功能
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出CSV文件",
            "",
            "CSV文件 (*.csv)"
        )

        if file_path:
            success = self.comtrade_reader.export_to_csv(file_path)
            if success:
                QMessageBox.information(self, "导出成功", f"数据已导出到:\n{file_path}")
            else:
                QMessageBox.warning(self, "导出失败", "导出CSV文件失败")

    def export_plot(self):
        """导出图形"""
        if not self.plot_widget.has_plot():
            QMessageBox.warning(self, "提示", "请先绘制波形")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出图形",
            "",
            "PNG图片 (*.png);;PDF文件 (*.pdf);;SVG图片 (*.svg)"
        )

        if file_path:
            try:
                self.plot_widget.save_plot(file_path)
                QMessageBox.information(self, "导出成功", f"图形已导出到:\n{file_path}")
            except Exception as e:
                QMessageBox.warning(self, "导出失败", f"导出图形失败:\n{str(e)}")

    def export_report(self):
        """导出分析报告"""
        if not self.current_analysis:
            QMessageBox.warning(self, "提示", "请先执行分析")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出分析报告",
            "",
            "文本文件 (*.txt);;HTML文件 (*.html)"
        )

        if file_path:
            try:
                # 生成报告内容
                report_content = self.analysis_panel.export_analysis_report()

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)

                QMessageBox.information(self, "导出成功", f"分析报告已导出到:\n{file_path}")
            except Exception as e:
                QMessageBox.warning(self, "导出失败", f"导出报告失败:\n{str(e)}")

    def show_preferences(self):
        """显示首选项对话框"""
        dialog = PreferencesDialog(self.settings, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            # 应用新设置
            self.apply_settings()

    def apply_settings(self):
        """应用设置更改"""
        # 更新绘图设置
        self.plot_widget.update_settings(self.settings.plot_settings)

        # 保存设置
        self.settings.save_settings()

    def toggle_toolbar(self, checked: bool):
        """切换工具栏显示"""
        self.tool_bar.setVisible(checked)

    def toggle_statusbar(self, checked: bool):
        """切换状态栏显示"""
        self.status_bar.setVisible(checked)

    def toggle_fullscreen(self):
        """切换全屏"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h2>COMTRADE波形分析器 v2.0</h2>
        <p>专业的电力系统暂态数据分析工具</p>

        <h3>主要功能：</h3>
        <ul>
            <li>支持IEEE C37.111标准COMTRADE格式</li>
            <li>智能编码检测和转换</li>
            <li>波形可视化和特征分析</li>
            <li>智能故障检测和分类</li>
            <li>谐波分析和电能质量评估</li>
            <li>分析报告生成和导出</li>
        </ul>

        <h3>技术栈：</h3>
        <p>Python 3.x • PyQt6 • matplotlib • numpy • scipy</p>

        <p><b>开发时间：</b> 2025年</p>
        """

        QMessageBox.about(self, "关于", about_text)

    def update_status(self, message: str):
        """更新状态栏消息"""
        self.status_label.setText(message)

        # 同时输出到日志窗口
        self.log_widget.append(f"[{self.get_current_time()}] {message}")

    def get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

    def auto_save(self):
        """自动保存"""
        self.save_window_state()

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止正在进行的分析
        if self.analysis_worker and self.analysis_worker.isRunning():
            reply = QMessageBox.question(
                self, "确认退出",
                "分析正在进行中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            else:
                self.analysis_worker.cancel()
                self.analysis_worker.wait(3000)  # 等待最多3秒

        # 保存窗口状态
        self.save_window_state()

        # 关闭文件
        if self.comtrade_reader:
            self.comtrade_reader.close()

        logger.info("应用程序退出")
        event.accept()