#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可折叠组件
提供可折叠的UI组件，用于节省界面空间
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QFont, QIcon
from typing import Optional


class CollapsibleSection(QWidget):
    """可折叠的区域组件"""
    
    # 信号定义
    toggled = pyqtSignal(bool)  # 折叠状态改变信号
    
    def __init__(self, title: str = "", icon: str = "", collapsed: bool = False):
        super().__init__()
        self.title = title
        self.icon = icon
        self._collapsed = collapsed
        self._content_widget = None
        self._animation = None
        
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 创建标题栏
        self.create_header()
        
        # 创建内容区域
        self.create_content_area()
        
        # 设置初始状态
        self.set_collapsed(self._collapsed, animate=False)
        
    def create_header(self):
        """创建标题栏"""
        self.header_frame = QFrame()
        self.header_frame.setFrameStyle(QFrame.Shape.Box)
        self.header_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 3px;
            }
            QFrame:hover {
                background-color: #e8e8e8;
            }
        """)
        
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(8, 4, 8, 4)
        
        # 折叠/展开按钮
        self.toggle_button = QPushButton()
        self.toggle_button.setFixedSize(16, 16)
        self.toggle_button.setFlat(True)
        self.toggle_button.clicked.connect(self.toggle)
        self.update_toggle_button()
        
        # 图标（如果有）
        if self.icon:
            icon_label = QLabel(self.icon)
            icon_label.setFixedSize(16, 16)
            header_layout.addWidget(icon_label)
        
        # 标题
        self.title_label = QLabel(self.title)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(9)
        self.title_label.setFont(title_font)
        
        header_layout.addWidget(self.toggle_button)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        # 让整个标题栏可点击
        self.header_frame.mousePressEvent = lambda event: self.toggle()
        
        self.main_layout.addWidget(self.header_frame)
        
    def create_content_area(self):
        """创建内容区域"""
        self.content_frame = QFrame()
        self.content_frame.setFrameStyle(QFrame.Shape.Box)
        self.content_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #d0d0d0;
                border-top: none;
                background-color: white;
            }
        """)
        
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.main_layout.addWidget(self.content_frame)
        
    def set_content_widget(self, widget: QWidget):
        """设置内容组件"""
        if self._content_widget:
            self.content_layout.removeWidget(self._content_widget)
            
        self._content_widget = widget
        if widget:
            self.content_layout.addWidget(widget)
            
    def toggle(self):
        """切换折叠状态"""
        self.set_collapsed(not self._collapsed)
        
    def set_collapsed(self, collapsed: bool, animate: bool = True):
        """设置折叠状态"""
        if self._collapsed == collapsed:
            return
            
        self._collapsed = collapsed
        self.update_toggle_button()
        
        if animate and self._content_widget:
            self.animate_toggle()
        else:
            self.content_frame.setVisible(not collapsed)
            
        self.toggled.emit(collapsed)
        
    def animate_toggle(self):
        """动画切换"""
        if not self._content_widget:
            return
            
        # 停止之前的动画
        if self._animation:
            self._animation.stop()
            
        # 创建动画
        self._animation = QPropertyAnimation(self.content_frame, b"maximumHeight")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        if self._collapsed:
            # 折叠
            start_height = self.content_frame.height()
            self._animation.setStartValue(start_height)
            self._animation.setEndValue(0)
            self._animation.finished.connect(lambda: self.content_frame.setVisible(False))
        else:
            # 展开
            self.content_frame.setVisible(True)
            self.content_frame.setMaximumHeight(0)
            
            # 计算内容的理想高度
            content_height = self._content_widget.sizeHint().height()
            if content_height <= 0:
                content_height = 200  # 默认高度
                
            self._animation.setStartValue(0)
            self._animation.setEndValue(content_height)
            self._animation.finished.connect(lambda: self.content_frame.setMaximumHeight(16777215))
            
        self._animation.start()
        
    def update_toggle_button(self):
        """更新折叠按钮图标"""
        if self._collapsed:
            self.toggle_button.setText("▶")
            self.toggle_button.setToolTip("展开")
        else:
            self.toggle_button.setText("▼")
            self.toggle_button.setToolTip("折叠")
            
    def is_collapsed(self) -> bool:
        """获取折叠状态"""
        return self._collapsed
        
    def set_title(self, title: str):
        """设置标题"""
        self.title = title
        self.title_label.setText(title)
        
    def get_content_widget(self) -> Optional[QWidget]:
        """获取内容组件"""
        return self._content_widget


class CollapsibleContainer(QWidget):
    """可折叠容器，包含多个可折叠区域"""
    
    def __init__(self):
        super().__init__()
        self.sections = []
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)
        
        # 添加弹性空间
        self.layout.addStretch()
        
    def add_section(self, section: CollapsibleSection):
        """添加可折叠区域"""
        self.sections.append(section)
        # 在弹性空间之前插入
        self.layout.insertWidget(len(self.sections) - 1, section)
        
    def remove_section(self, section: CollapsibleSection):
        """移除可折叠区域"""
        if section in self.sections:
            self.sections.remove(section)
            self.layout.removeWidget(section)
            section.setParent(None)
            
    def collapse_all(self):
        """折叠所有区域"""
        for section in self.sections:
            section.set_collapsed(True)
            
    def expand_all(self):
        """展开所有区域"""
        for section in self.sections:
            section.set_collapsed(False)
            
    def get_sections(self) -> list:
        """获取所有区域"""
        return self.sections.copy()