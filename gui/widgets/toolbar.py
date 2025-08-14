#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具栏组件
提供常用操作的快速访问
"""

from PyQt6.QtWidgets import (
    QToolBar, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QButtonGroup, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor

from typing import Optional, Dict, Any
from pathlib import Path
from config.constants import SHORTCUTS, TOOLTIPS
from utils.logger import get_logger

logger = get_logger(__name__)


def load_icon(icon_name: str, size: QSize = QSize(16, 16)) -> QIcon:
    """加载图标文件"""
    try:
        # 获取项目根目录
        current_dir = Path(__file__).parent.parent.parent
        icons_dir = current_dir / 'assets' / 'icons'
        
        # 支持的图标文件扩展名
        icon_extensions = ['.png', '.svg', '.ico', '.jpg', '.jpeg']
        
        for ext in icon_extensions:
            icon_path = icons_dir / f"{icon_name}{ext}"
            if icon_path.exists():
                icon = QIcon(str(icon_path))
                if not icon.isNull():
                    logger.debug(f"成功加载图标: {icon_path}")
                    return icon
        
        # 如果没找到图标文件，创建一个默认图标
        logger.warning(f"未找到图标文件: {icon_name}")
        return create_default_icon(size)
        
    except Exception as e:
        logger.error(f"加载图标失败: {e}")
        return create_default_icon(size)


def create_default_icon(size: QSize = QSize(16, 16)) -> QIcon:
    """创建默认图标"""
    pixmap = QPixmap(size)
    pixmap.fill(QColor('#CCCCCC'))
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QColor('#666666'))
    painter.setBrush(QColor('#EEEEEE'))
    painter.drawRect(2, 2, size.width()-4, size.height()-4)
    painter.end()
    
    return QIcon(pixmap)


class ToolbarSeparator(QFrame):
    """工具栏分隔符"""

    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.VLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setFixedWidth(2)
        self.setStyleSheet("QFrame { color: #CCCCCC; }")


class ToolButton(QPushButton):
    """工具按钮"""

    def __init__(self, text: str, icon_name: str = "", tooltip: str = ""):
        super().__init__(text)
        self.setToolTip(tooltip)
        self.setMinimumSize(80, 32)
        self.setMaximumSize(120, 32)
        
        # 设置图标
        if icon_name:
            icon = load_icon(icon_name, QSize(16, 16))
            self.setIcon(icon)
            self.setIconSize(QSize(16, 16))

        # 设置样式
        self.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #a0a0a0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
                border-color: #808080;
            }
            QPushButton:disabled {
                background-color: #f8f8f8;
                border-color: #e0e0e0;
                color: #a0a0a0;
            }
        """)


class StatusIndicator(QWidget):
    """状态指示器"""

    def __init__(self, text: str = "就绪"):
        super().__init__()
        self.status_text = text
        self.status_color = QColor('#4CAF50')  # 绿色表示就绪
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        # 状态指示灯
        self.indicator = QLabel()
        self.indicator.setFixedSize(12, 12)
        layout.addWidget(self.indicator)

        # 状态文本
        self.label = QLabel(self.status_text)
        self.label.setStyleSheet("QLabel { color: #333333; font-size: 11px; }")
        layout.addWidget(self.label)

        self.update_indicator()

    def update_indicator(self):
        """更新指示器"""
        pixmap = QPixmap(12, 12)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self.status_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(1, 1, 10, 10)
        painter.end()

        self.indicator.setPixmap(pixmap)

    def set_status(self, text: str, color: str = '#4CAF50'):
        """
        设置状态

        Args:
            text: 状态文本
            color: 状态颜色（HTML颜色代码）
        """
        self.status_text = text
        self.status_color = QColor(color)
        self.label.setText(text)
        self.update_indicator()


class FileToolbar(QToolBar):
    """文件操作工具栏"""

    # 信号定义
    open_file_requested = pyqtSignal()
    save_file_requested = pyqtSignal()
    export_requested = pyqtSignal()
    recent_file_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__("文件工具栏", parent)
        self.setObjectName("file_toolbar")
        self.init_toolbar()

    def init_toolbar(self):
        """初始化工具栏"""
        # 打开文件
        self.open_btn = ToolButton("打开", "open", TOOLTIPS.get('open_file', '打开COMTRADE文件'))
        self.open_btn.clicked.connect(self.open_file_requested.emit)
        self.addWidget(self.open_btn)

        # 最近文件下拉
        self.recent_combo = QComboBox()
        self.recent_combo.setMinimumWidth(150)
        self.recent_combo.setMaximumWidth(200)
        self.recent_combo.setToolTip("最近打开的文件")
        self.recent_combo.activated.connect(self.on_recent_file_selected)
        self.addWidget(self.recent_combo)

        self.addWidget(ToolbarSeparator())

        # 保存/导出
        self.save_btn = ToolButton("保存", "save", "保存当前项目")
        self.save_btn.clicked.connect(self.save_file_requested.emit)
        self.save_btn.setEnabled(False)  # 初始禁用
        self.addWidget(self.save_btn)

        self.export_btn = ToolButton("导出", "export", TOOLTIPS.get('export', '导出数据'))
        self.export_btn.clicked.connect(self.export_requested.emit)
        self.export_btn.setEnabled(False)  # 初始禁用
        self.addWidget(self.export_btn)

    def update_recent_files(self, recent_files: list):
        """更新最近文件列表"""
        self.recent_combo.clear()
        self.recent_combo.addItem("选择最近文件...")

        for file_path in recent_files:
            from pathlib import Path
            file_name = Path(file_path).name
            self.recent_combo.addItem(file_name, file_path)

    def on_recent_file_selected(self, index: int):
        """最近文件选择处理"""
        if index > 0:  # 跳过第一个提示项
            file_path = self.recent_combo.itemData(index)
            if file_path:
                self.recent_file_requested.emit(file_path)
            # 重置选择
            self.recent_combo.setCurrentIndex(0)

    def set_file_loaded(self, loaded: bool):
        """设置文件加载状态"""
        self.save_btn.setEnabled(loaded)
        self.export_btn.setEnabled(loaded)


class AnalysisToolbar(QToolBar):
    """分析工具栏"""

    # 信号定义
    start_analysis_requested = pyqtSignal()
    stop_analysis_requested = pyqtSignal()
    config_analysis_requested = pyqtSignal()
    clear_results_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("分析工具栏", parent)
        self.setObjectName("analysis_toolbar")
        self.is_analyzing = False
        self.init_toolbar()

    def init_toolbar(self):
        """初始化工具栏"""
        # 开始分析
        self.start_btn = ToolButton("开始分析", "analyze", TOOLTIPS.get('start_analysis', '开始分析'))
        self.start_btn.clicked.connect(self.start_analysis_requested.emit)
        self.start_btn.setEnabled(False)
        self.addWidget(self.start_btn)

        # 停止分析
        self.stop_btn = ToolButton("停止", "back", TOOLTIPS.get('stop_analysis', '停止分析'))
        self.stop_btn.clicked.connect(self.stop_analysis_requested.emit)
        self.stop_btn.setEnabled(False)
        self.addWidget(self.stop_btn)

        self.addWidget(ToolbarSeparator())

        # 分析配置
        self.config_btn = ToolButton("配置", "settings", "分析配置")
        self.config_btn.clicked.connect(self.config_analysis_requested.emit)
        self.addWidget(self.config_btn)

        # 清除结果
        self.clear_btn = ToolButton("清除结果", "clear", "清除分析结果")
        self.clear_btn.clicked.connect(self.clear_results_requested.emit)
        self.addWidget(self.clear_btn)

        self.addWidget(ToolbarSeparator())

        # 状态指示器
        self.status_indicator = StatusIndicator("等待数据")
        self.addWidget(self.status_indicator)

    def set_data_loaded(self, loaded: bool):
        """设置数据加载状态"""
        self.start_btn.setEnabled(loaded and not self.is_analyzing)
        if loaded:
            self.status_indicator.set_status("数据已加载", '#4CAF50')
        else:
            self.status_indicator.set_status("等待数据", '#FFC107')

    def set_analysis_state(self, analyzing: bool):
        """设置分析状态"""
        self.is_analyzing = analyzing
        self.start_btn.setEnabled(not analyzing)
        self.stop_btn.setEnabled(analyzing)

        if analyzing:
            self.status_indicator.set_status("正在分析...", '#2196F3')
        else:
            self.status_indicator.set_status("分析完成", '#4CAF50')

    def set_analysis_progress(self, progress: int, message: str = ""):
        """设置分析进度"""
        if message:
            self.status_indicator.set_status(f"分析中... {message}", '#2196F3')


class ViewToolbar(QToolBar):
    """视图工具栏"""

    # 信号定义
    zoom_in_requested = pyqtSignal()
    zoom_out_requested = pyqtSignal()
    zoom_fit_requested = pyqtSignal()
    pan_requested = pyqtSignal(bool)
    grid_toggled = pyqtSignal(bool)
    legend_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__("视图工具栏", parent)
        self.setObjectName("view_toolbar")
        self.init_toolbar()

    def init_toolbar(self):
        """初始化工具栏"""
        # 缩放控制
        self.zoom_in_btn = ToolButton("放大", "zoom-in", TOOLTIPS.get('zoom_in', '放大图形'))
        self.zoom_in_btn.clicked.connect(self.zoom_in_requested.emit)
        self.addWidget(self.zoom_in_btn)

        self.zoom_out_btn = ToolButton("缩小", "zoom-out", TOOLTIPS.get('zoom_out', '缩小图形'))
        self.zoom_out_btn.clicked.connect(self.zoom_out_requested.emit)
        self.addWidget(self.zoom_out_btn)

        self.zoom_fit_btn = ToolButton("适应", "zoom-fit", TOOLTIPS.get('reset_view', '重置视图'))
        self.zoom_fit_btn.clicked.connect(self.zoom_fit_requested.emit)
        self.addWidget(self.zoom_fit_btn)

        self.addWidget(ToolbarSeparator())

        # 平移工具
        self.pan_btn = ToolButton("平移", "hand", TOOLTIPS.get('pan', '平移图形'))
        self.pan_btn.setCheckable(True)
        self.pan_btn.toggled.connect(self.pan_requested.emit)
        self.addWidget(self.pan_btn)

        self.addWidget(ToolbarSeparator())

        # 显示选项
        self.grid_cb = QCheckBox("网格")
        self.grid_cb.setToolTip(TOOLTIPS.get('grid', '显示/隐藏网格'))
        self.grid_cb.setChecked(True)
        self.grid_cb.toggled.connect(self.grid_toggled.emit)
        self.addWidget(self.grid_cb)

        self.legend_cb = QCheckBox("图例")
        self.legend_cb.setToolTip(TOOLTIPS.get('legend', '显示/隐藏图例'))
        self.legend_cb.setChecked(True)
        self.legend_cb.toggled.connect(self.legend_toggled.emit)
        self.addWidget(self.legend_cb)


class QuickSettingsToolbar(QToolBar):
    """快速设置工具栏"""

    # 信号定义
    line_width_changed = pyqtSignal(float)
    point_size_changed = pyqtSignal(int)
    alpha_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__("快速设置", parent)
        self.setObjectName("quick_settings_toolbar")
        self.init_toolbar()

    def init_toolbar(self):
        """初始化工具栏"""
        # 线宽设置
        self.addWidget(QLabel("线宽:"))
        self.line_width_spin = QDoubleSpinBox()
        self.line_width_spin.setRange(0.1, 5.0)
        self.line_width_spin.setSingleStep(0.1)
        self.line_width_spin.setValue(1.0)
        self.line_width_spin.setSuffix("px")
        self.line_width_spin.setMaximumWidth(80)
        self.line_width_spin.valueChanged.connect(self.line_width_changed.emit)
        self.addWidget(self.line_width_spin)

        self.addWidget(ToolbarSeparator())

        # 数据点大小
        self.addWidget(QLabel("点大小:"))
        self.point_size_spin = QSpinBox()
        self.point_size_spin.setRange(1, 20)
        self.point_size_spin.setValue(2)
        self.point_size_spin.setMaximumWidth(60)
        self.point_size_spin.valueChanged.connect(self.point_size_changed.emit)
        self.addWidget(self.point_size_spin)

        self.addWidget(ToolbarSeparator())

        # 透明度
        self.addWidget(QLabel("透明度:"))
        self.alpha_spin = QDoubleSpinBox()
        self.alpha_spin.setRange(0.1, 1.0)
        self.alpha_spin.setSingleStep(0.1)
        self.alpha_spin.setValue(1.0)
        self.alpha_spin.setMaximumWidth(70)
        self.alpha_spin.valueChanged.connect(self.alpha_changed.emit)
        self.addWidget(self.alpha_spin)


class MainToolbarWidget(QWidget):
    """主工具栏组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # 主工具栏行
        main_toolbar_layout = QHBoxLayout()
        main_toolbar_layout.setContentsMargins(5, 2, 5, 2)

        # 文件工具栏
        self.file_toolbar = FileToolbar()
        main_toolbar_layout.addWidget(self.file_toolbar)

        main_toolbar_layout.addWidget(ToolbarSeparator())

        # 分析工具栏
        self.analysis_toolbar = AnalysisToolbar()
        main_toolbar_layout.addWidget(self.analysis_toolbar)

        main_toolbar_layout.addWidget(ToolbarSeparator())

        # 视图工具栏
        self.view_toolbar = ViewToolbar()
        main_toolbar_layout.addWidget(self.view_toolbar)

        main_toolbar_layout.addStretch()

        layout.addLayout(main_toolbar_layout)

        # 快速设置工具栏（可选）
        self.quick_settings_toolbar = QuickSettingsToolbar()
        self.quick_settings_toolbar.setVisible(False)  # 默认隐藏
        layout.addWidget(self.quick_settings_toolbar)

        # 设置样式
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f8f8;
                border-bottom: 1px solid #d0d0d0;
            }
        """)

    def setup_connections(self):
        """设置信号连接"""
        # TODO: 连接到主窗口的相应方法
        pass

    def toggle_quick_settings(self, visible: bool):
        """切换快速设置工具栏显示"""
        self.quick_settings_toolbar.setVisible(visible)

    def update_state(self, state_dict: Dict[str, Any]):
        """
        更新工具栏状态

        Args:
            state_dict: 状态字典，包含各种状态信息
        """
        # 更新文件工具栏状态
        if 'file_loaded' in state_dict:
            self.file_toolbar.set_file_loaded(state_dict['file_loaded'])

        if 'recent_files' in state_dict:
            self.file_toolbar.update_recent_files(state_dict['recent_files'])

        # 更新分析工具栏状态
        if 'data_loaded' in state_dict:
            self.analysis_toolbar.set_data_loaded(state_dict['data_loaded'])

        if 'analyzing' in state_dict:
            self.analysis_toolbar.set_analysis_state(state_dict['analyzing'])

        if 'analysis_progress' in state_dict:
            progress_info = state_dict['analysis_progress']
            if isinstance(progress_info, tuple) and len(progress_info) >= 2:
                self.analysis_toolbar.set_analysis_progress(progress_info[0], progress_info[1])

    def get_toolbar_settings(self) -> Dict[str, Any]:
        """获取工具栏设置"""
        return {
            'line_width': self.quick_settings_toolbar.line_width_spin.value(),
            'point_size': self.quick_settings_toolbar.point_size_spin.value(),
            'alpha': self.quick_settings_toolbar.alpha_spin.value(),
            'grid_enabled': self.view_toolbar.grid_cb.isChecked(),
            'legend_enabled': self.view_toolbar.legend_cb.isChecked(),
            'quick_settings_visible': self.quick_settings_toolbar.isVisible()
        }

    def load_toolbar_settings(self, settings: Dict[str, Any]):
        """加载工具栏设置"""
        if 'line_width' in settings:
            self.quick_settings_toolbar.line_width_spin.setValue(settings['line_width'])

        if 'point_size' in settings:
            self.quick_settings_toolbar.point_size_spin.setValue(settings['point_size'])

        if 'alpha' in settings:
            self.quick_settings_toolbar.alpha_spin.setValue(settings['alpha'])

        if 'grid_enabled' in settings:
            self.view_toolbar.grid_cb.setChecked(settings['grid_enabled'])

        if 'legend_enabled' in settings:
            self.view_toolbar.legend_cb.setChecked(settings['legend_enabled'])

        if 'quick_settings_visible' in settings:
            self.quick_settings_toolbar.setVisible(settings['quick_settings_visible'])


# 导出工具栏类
__all__ = [
    'FileToolbar',
    'AnalysisToolbar',
    'ViewToolbar',
    'QuickSettingsToolbar',
    'MainToolbarWidget',
    'StatusIndicator',
    'ToolButton'
]