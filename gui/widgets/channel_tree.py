#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通道选择树组件
用于显示和选择COMTRADE文件中的通道
"""

from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QCheckBox, QLabel, QLineEdit, QComboBox, QGroupBox,
    QHeaderView, QMenu, QToolButton, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QFont, QBrush, QColor, QIcon

from typing import Dict, List, Optional, Tuple
from models.data_models import ComtradeRecord, ChannelInfo, ChannelType
from config.constants import VOLTAGE_KEYWORDS, CURRENT_KEYWORDS, PHASE_KEYWORDS
from utils.logger import get_logger

logger = get_logger(__name__)


class ChannelItem(QTreeWidgetItem):
    """自定义通道项"""

    def __init__(self, parent, channel: ChannelInfo, channel_type: str):
        super().__init__(parent)
        self.channel = channel
        self.channel_type = channel_type  # 'analog' or 'digital'
        self.setup_item()

    def setup_item(self):
        """设置项目显示"""
        # 设置复选框
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        self.setCheckState(0, Qt.CheckState.Unchecked)

        # 设置显示文本
        self.setText(0, self.channel.name)
        self.setText(1, self.channel.unit if hasattr(self.channel, 'unit') else '')
        self.setText(2, f"通道 {self.channel.index}")

        # 设置相位信息
        if hasattr(self.channel, 'phase') and self.channel.phase:
            self.setText(3, self.channel.phase)

        # 设置工具提示
        tooltip = f"通道: {self.channel.name}\n"
        tooltip += f"索引: {self.channel.index}\n"
        if hasattr(self.channel, 'unit') and self.channel.unit:
            tooltip += f"单位: {self.channel.unit}\n"
        if hasattr(self.channel, 'phase') and self.channel.phase:
            tooltip += f"相位: {self.channel.phase}\n"

        # 添加统计信息
        if len(self.channel.data) > 0:
            tooltip += f"数据点数: {len(self.channel.data)}\n"
            if self.channel_type == 'analog':
                tooltip += f"RMS值: {self.channel.rms_value:.3f}\n"
                tooltip += f"峰值: {self.channel.peak_value:.3f}"

        self.setToolTip(0, tooltip)

        # 根据通道类型设置颜色
        if self.channel_type == 'analog':
            self.setForeground(0, QBrush(QColor('#2E86AB')))  # 蓝色
        else:
            self.setForeground(0, QBrush(QColor('#A23B72')))  # 紫色


class ChannelGroupItem(QTreeWidgetItem):
    """通道组项"""

    def __init__(self, parent, group_name: str, group_type: str):
        super().__init__(parent)
        self.group_name = group_name
        self.group_type = group_type
        self.setup_group()

    def setup_group(self):
        """设置组显示"""
        self.setText(0, self.group_name)
        self.setText(1, '')
        self.setText(2, self.group_type)

        # 设置字体加粗
        font = QFont()
        font.setBold(True)
        self.setFont(0, font)

        # 设置背景色
        if self.group_type == '模拟通道':
            self.setBackground(0, QBrush(QColor('#E8F4FD')))
        else:
            self.setBackground(0, QBrush(QColor('#F5E6F1')))

        # 默认展开
        self.setExpanded(True)


class ChannelFilterWidget(QWidget):
    """通道过滤控件"""

    filter_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # 搜索框
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入通道名称...")
        self.search_edit.textChanged.connect(self.filter_changed.emit)
        search_layout.addWidget(self.search_edit)

        # 清除按钮
        self.clear_button = QToolButton()
        self.clear_button.setText("×")
        self.clear_button.setToolTip("清除搜索")
        self.clear_button.clicked.connect(self.clear_search)
        search_layout.addWidget(self.clear_button)

        layout.addLayout(search_layout)

        # 过滤选项
        filter_layout = QHBoxLayout()

        # 通道类型过滤
        self.type_combo = QComboBox()
        self.type_combo.addItems(['全部', '模拟通道', '数字通道'])
        self.type_combo.currentTextChanged.connect(self.filter_changed.emit)
        filter_layout.addWidget(QLabel("类型:"))
        filter_layout.addWidget(self.type_combo)

        # 相别过滤
        self.phase_combo = QComboBox()
        self.phase_combo.addItems(['全部', 'A相', 'B相', 'C相', '中性线', '线电压'])
        self.phase_combo.currentTextChanged.connect(self.filter_changed.emit)
        filter_layout.addWidget(QLabel("相别:"))
        filter_layout.addWidget(self.phase_combo)

        layout.addLayout(filter_layout)

    def clear_search(self):
        """清除搜索"""
        self.search_edit.clear()

    def get_filter_text(self) -> str:
        """获取搜索文本"""
        return self.search_edit.text().strip().lower()

    def get_type_filter(self) -> str:
        """获取类型过滤"""
        return self.type_combo.currentText()

    def get_phase_filter(self) -> str:
        """获取相别过滤"""
        return self.phase_combo.currentText()


class ChannelSelectionWidget(QWidget):
    """通道选择控制组件"""

    def __init__(self, tree_widget):
        super().__init__()
        self.tree_widget = tree_widget
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # 选择统计
        self.selection_label = QLabel("已选择: 0 个通道")
        self.selection_label.setStyleSheet("QLabel { color: #666666; font-size: 11px; }")
        layout.addWidget(self.selection_label)

        # 按钮组
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setToolTip("选择所有通道")
        self.select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(self.select_all_btn)

        self.select_none_btn = QPushButton("清除")
        self.select_none_btn.setToolTip("清除所有选择")
        self.select_none_btn.clicked.connect(self.select_none)
        button_layout.addWidget(self.select_none_btn)

        self.invert_btn = QPushButton("反选")
        self.invert_btn.setToolTip("反转选择状态")
        self.invert_btn.clicked.connect(self.invert_selection)
        button_layout.addWidget(self.invert_btn)

        layout.addLayout(button_layout)

        # 快速选择按钮
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(5)

        self.voltage_btn = QPushButton("电压")
        self.voltage_btn.setToolTip("选择所有电压通道")
        self.voltage_btn.clicked.connect(self.select_voltage_channels)
        quick_layout.addWidget(self.voltage_btn)

        self.current_btn = QPushButton("电流")
        self.current_btn.setToolTip("选择所有电流通道")
        self.current_btn.clicked.connect(self.select_current_channels)
        quick_layout.addWidget(self.current_btn)

        layout.addLayout(quick_layout)

    def update_selection_count(self):
        """更新选择计数"""
        count = self.tree_widget.get_selected_count()
        self.selection_label.setText(f"已选择: {count} 个通道")

    def select_all(self):
        """全选"""
        self.tree_widget.select_all_channels(True)
        self.update_selection_count()

    def select_none(self):
        """清除选择"""
        self.tree_widget.select_all_channels(False)
        self.update_selection_count()

    def invert_selection(self):
        """反选"""
        self.tree_widget.invert_selection()
        self.update_selection_count()

    def select_voltage_channels(self):
        """选择电压通道"""
        self.tree_widget.select_channels_by_type('voltage')
        self.update_selection_count()

    def select_current_channels(self):
        """选择电流通道"""
        self.tree_widget.select_channels_by_type('current')
        self.update_selection_count()


class ChannelTreeWidget(QWidget):
    """完整的通道选择组件"""

    # 信号定义
    channels_selected = pyqtSignal(dict)  # 发送选中的通道字典
    selection_changed = pyqtSignal()  # 选择变化

    def __init__(self):
        super().__init__()
        self.current_record: Optional[ComtradeRecord] = None
        self.filtered_items = []  # 过滤后的项目
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 创建组框
        group_box = QGroupBox("通道选择")
        group_layout = QVBoxLayout(group_box)
        group_layout.setSpacing(5)

        # 过滤控件
        self.filter_widget = ChannelFilterWidget()
        group_layout.addWidget(self.filter_widget)

        # 树形控件
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['通道名称', '单位', '类型', '相位'])
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setSortingEnabled(False)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)

        # 设置列宽
        header = self.tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        group_layout.addWidget(self.tree)

        # 选择控制组件
        self.selection_widget = ChannelSelectionWidget(self)
        group_layout.addWidget(self.selection_widget)

        layout.addWidget(group_box)

        # 设置右键菜单
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

    def setup_connections(self):
        """设置信号连接"""
        # 过滤变化
        self.filter_widget.filter_changed.connect(self.apply_filters)

        # 选择变化
        self.tree.itemChanged.connect(self.on_item_changed)

        # 延迟发送信号，避免频繁更新
        self.selection_timer = QTimer()
        self.selection_timer.setSingleShot(True)
        self.selection_timer.timeout.connect(self.emit_selection_changed)
        self.selection_timer.setInterval(100)  # 100ms延迟

    def load_channels(self, record: ComtradeRecord):
        """
        加载通道信息

        Args:
            record: COMTRADE记录
        """
        self.current_record = record
        self.tree.clear()

        if not record:
            return

        try:
            # 创建模拟通道组
            if record.analog_channels:
                analog_group = ChannelGroupItem(self.tree,
                                                f"模拟通道 ({len(record.analog_channels)})",
                                                "模拟通道")

                # 按类型分组模拟通道
                voltage_channels = []
                current_channels = []
                other_channels = []

                for i, channel in enumerate(record.analog_channels):
                    channel_type = self._identify_channel_type(channel.name)
                    if channel_type == 'voltage':
                        voltage_channels.append(channel)
                    elif channel_type == 'current':
                        current_channels.append(channel)
                    else:
                        other_channels.append(channel)

                # 创建子分组
                if voltage_channels:
                    voltage_group = ChannelGroupItem(analog_group,
                                                     f"电压 ({len(voltage_channels)})",
                                                     "电压")
                    for channel in voltage_channels:
                        ChannelItem(voltage_group, channel, 'analog')

                if current_channels:
                    current_group = ChannelGroupItem(analog_group,
                                                     f"电流 ({len(current_channels)})",
                                                     "电流")
                    for channel in current_channels:
                        ChannelItem(current_group, channel, 'analog')

                if other_channels:
                    other_group = ChannelGroupItem(analog_group,
                                                   f"其他 ({len(other_channels)})",
                                                   "其他")
                    for channel in other_channels:
                        ChannelItem(other_group, channel, 'analog')

            # 创建数字通道组
            if record.digital_channels:
                digital_group = ChannelGroupItem(self.tree,
                                                 f"数字通道 ({len(record.digital_channels)})",
                                                 "数字通道")

                for channel in record.digital_channels:
                    ChannelItem(digital_group, channel, 'digital')

            # 展开所有项目
            self.tree.expandAll()

            # 更新选择计数
            self.selection_widget.update_selection_count()

            logger.info(f"已加载 {len(record.analog_channels)} 个模拟通道和 {len(record.digital_channels)} 个数字通道")

        except Exception as e:
            logger.error(f"加载通道失败: {e}")

    def _identify_channel_type(self, channel_name: str) -> str:
        """
        识别通道类型

        Args:
            channel_name: 通道名称

        Returns:
            通道类型 ('voltage', 'current', 'other')
        """
        name_upper = channel_name.upper()

        # 检查是否为电压通道
        for keyword in VOLTAGE_KEYWORDS:
            if keyword in name_upper:
                return 'voltage'

        # 检查是否为电流通道
        for keyword in CURRENT_KEYWORDS:
            if keyword in name_upper:
                return 'current'

        return 'other'

    def _identify_phase(self, channel_name: str) -> str:
        """
        识别通道相别

        Args:
            channel_name: 通道名称

        Returns:
            相别标识
        """
        name_upper = channel_name.upper()

        for phase, keywords in PHASE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in name_upper:
                    return phase

        return ''

    def apply_filters(self):
        """应用过滤条件"""
        if not self.current_record:
            return

        search_text = self.filter_widget.get_filter_text()
        type_filter = self.filter_widget.get_type_filter()
        phase_filter = self.filter_widget.get_phase_filter()

        # 遍历所有项目
        def filter_item(item: QTreeWidgetItem):
            if isinstance(item, ChannelItem):
                # 检查搜索文本
                text_match = True
                if search_text:
                    text_match = search_text in item.channel.name.lower()

                # 检查类型过滤
                type_match = True
                if type_filter != '全部':
                    if type_filter == '模拟通道':
                        type_match = item.channel_type == 'analog'
                    elif type_filter == '数字通道':
                        type_match = item.channel_type == 'digital'

                # 检查相别过滤
                phase_match = True
                if phase_filter != '全部':
                    channel_phase = self._identify_phase(item.channel.name)
                    if phase_filter == 'A相':
                        phase_match = channel_phase == 'A'
                    elif phase_filter == 'B相':
                        phase_match = channel_phase == 'B'
                    elif phase_filter == 'C相':
                        phase_match = channel_phase == 'C'
                    elif phase_filter == '中性线':
                        phase_match = channel_phase == 'N'
                    elif phase_filter == '线电压':
                        phase_match = channel_phase in ['AB', 'BC', 'CA']

                # 设置可见性
                visible = text_match and type_match and phase_match
                item.setHidden(not visible)

                return visible
            else:
                # 对于组项目，检查是否有可见的子项目
                visible_children = 0
                for i in range(item.childCount()):
                    child = item.child(i)
                    if filter_item(child):
                        visible_children += 1

                # 如果有可见的子项目，则显示组
                item.setHidden(visible_children == 0)
                return visible_children > 0

        # 应用过滤
        for i in range(self.tree.topLevelItemCount()):
            filter_item(self.tree.topLevelItem(i))

    def on_item_changed(self, item: QTreeWidgetItem, column: int):
        """项目变化处理"""
        if column == 0 and isinstance(item, ChannelItem):
            # 启动延迟定时器
            self.selection_timer.start()
            # 更新选择计数
            self.selection_widget.update_selection_count()

    def emit_selection_changed(self):
        """发送选择变化信号"""
        selected_channels = self.get_selected_channels()
        self.channels_selected.emit(selected_channels)
        self.selection_changed.emit()

    def get_selected_channels(self) -> Dict[str, List[int]]:
        """
        获取选中的通道

        Returns:
            包含选中通道索引的字典 {'analog': [0, 1, 2], 'digital': [0, 1]}
        """
        selected = {'analog': [], 'digital': []}

        def check_item(item: QTreeWidgetItem):
            if isinstance(item, ChannelItem):
                if item.checkState(0) == Qt.CheckState.Checked:
                    if item.channel_type == 'analog':
                        selected['analog'].append(item.channel.index)
                    else:
                        selected['digital'].append(item.channel.index)
            else:
                # 递归检查子项目
                for i in range(item.childCount()):
                    check_item(item.child(i))

        # 检查所有项目
        for i in range(self.tree.topLevelItemCount()):
            check_item(self.tree.topLevelItem(i))

        return selected

    def get_selected_count(self) -> int:
        """获取选中通道数量"""
        selected = self.get_selected_channels()
        return len(selected['analog']) + len(selected['digital'])

    def select_all_channels(self, checked: bool):
        """选择所有通道"""

        def set_check_state(item: QTreeWidgetItem, state: Qt.CheckState):
            if isinstance(item, ChannelItem) and not item.isHidden():
                item.setCheckState(0, state)
            else:
                for i in range(item.childCount()):
                    set_check_state(item.child(i), state)

        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for i in range(self.tree.topLevelItemCount()):
            set_check_state(self.tree.topLevelItem(i), state)

    def invert_selection(self):
        """反转选择"""

        def invert_item(item: QTreeWidgetItem):
            if isinstance(item, ChannelItem) and not item.isHidden():
                current_state = item.checkState(0)
                new_state = Qt.CheckState.Unchecked if current_state == Qt.CheckState.Checked else Qt.CheckState.Checked
                item.setCheckState(0, new_state)
            else:
                for i in range(item.childCount()):
                    invert_item(item.child(i))

        for i in range(self.tree.topLevelItemCount()):
            invert_item(self.tree.topLevelItem(i))

    def select_channels_by_type(self, channel_type: str):
        """
        按类型选择通道

        Args:
            channel_type: 通道类型 ('voltage', 'current')
        """

        def select_type(item: QTreeWidgetItem):
            if isinstance(item, ChannelItem) and not item.isHidden():
                item_type = self._identify_channel_type(item.channel.name)
                if item_type == channel_type:
                    item.setCheckState(0, Qt.CheckState.Checked)
            else:
                for i in range(item.childCount()):
                    select_type(item.child(i))

        for i in range(self.tree.topLevelItemCount()):
            select_type(self.tree.topLevelItem(i))

    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.tree.itemAt(position)
        if not item:
            return

        menu = QMenu(self)

        if isinstance(item, ChannelItem):
            # 通道项目菜单
            check_action = QAction("选中" if item.checkState(0) == Qt.CheckState.Unchecked else "取消选中", self)
            check_action.triggered.connect(lambda: self.toggle_item_check(item))
            menu.addAction(check_action)

            menu.addSeparator()

            info_action = QAction("通道信息", self)
            info_action.triggered.connect(lambda: self.show_channel_info(item))
            menu.addAction(info_action)

        else:
            # 组项目菜单
            expand_action = QAction("展开" if not item.isExpanded() else "折叠", self)
            expand_action.triggered.connect(lambda: item.setExpanded(not item.isExpanded()))
            menu.addAction(expand_action)

            menu.addSeparator()

            select_group_action = QAction("选择组内所有通道", self)
            select_group_action.triggered.connect(lambda: self.select_group_channels(item, True))
            menu.addAction(select_group_action)

            deselect_group_action = QAction("取消选择组内通道", self)
            deselect_group_action.triggered.connect(lambda: self.select_group_channels(item, False))
            menu.addAction(deselect_group_action)

        menu.exec(self.tree.mapToGlobal(position))

    def toggle_item_check(self, item: ChannelItem):
        """切换项目选中状态"""
        current_state = item.checkState(0)
        new_state = Qt.CheckState.Unchecked if current_state == Qt.CheckState.Checked else Qt.CheckState.Checked
        item.setCheckState(0, new_state)

    def select_group_channels(self, group_item: QTreeWidgetItem, checked: bool):
        """选择组内所有通道"""
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked

        def set_group_state(item: QTreeWidgetItem):
            if isinstance(item, ChannelItem):
                item.setCheckState(0, state)
            else:
                for i in range(item.childCount()):
                    set_group_state(item.child(i))

        set_group_state(group_item)

    def show_channel_info(self, item: ChannelItem):
        """显示通道详细信息"""
        # TODO: 实现通道信息对话框
        from PyQt6.QtWidgets import QMessageBox

        channel = item.channel
        info_text = f"通道名称: {channel.name}\n"
        info_text += f"通道索引: {channel.index}\n"
        info_text += f"通道类型: {item.channel_type}\n"

        if hasattr(channel, 'unit') and channel.unit:
            info_text += f"单位: {channel.unit}\n"
        if hasattr(channel, 'phase') and channel.phase:
            info_text += f"相位: {channel.phase}\n"
        if hasattr(channel, 'multiplier'):
            info_text += f"乘数: {channel.multiplier}\n"
        if hasattr(channel, 'offset'):
            info_text += f"偏移: {channel.offset}\n"

        if len(channel.data) > 0:
            info_text += f"\n数据统计:\n"
            info_text += f"数据点数: {len(channel.data)}\n"
            if item.channel_type == 'analog':
                info_text += f"RMS值: {channel.rms_value:.6f}\n"
                info_text += f"峰值: {channel.peak_value:.6f}\n"
                info_text += f"最大值: {float(np.max(channel.data)):.6f}\n"
                info_text += f"最小值: {float(np.min(channel.data)):.6f}\n"
                info_text += f"平均值: {float(np.mean(channel.data)):.6f}\n"
                info_text += f"标准差: {float(np.std(channel.data)):.6f}"

        QMessageBox.information(self, f"通道信息 - {channel.name}", info_text)

    def clear_selection(self):
        """清除所有选择"""
        self.select_all_channels(False)

    def get_channel_by_name(self, name: str) -> Optional[ChannelItem]:
        """根据名称查找通道项"""

        def find_channel(item: QTreeWidgetItem) -> Optional[ChannelItem]:
            if isinstance(item, ChannelItem) and item.channel.name == name:
                return item

            for i in range(item.childCount()):
                result = find_channel(item.child(i))
                if result:
                    return result

            return None

        for i in range(self.tree.topLevelItemCount()):
            result = find_channel(self.tree.topLevelItem(i))
            if result:
                return result

        return None