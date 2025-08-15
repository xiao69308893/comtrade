#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用程序配置管理
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from PyQt6.QtCore import QSettings


@dataclass
class PlotSettings:
    """绘图配置"""
    line_width: float = 1.0
    grid_enabled: bool = True
    grid_alpha: float = 0.3
    background_color: str = "white"
    figure_dpi: int = 100
    auto_scale: bool = True
    max_points_per_plot: int = 100000  # 防止绘图卡顿


@dataclass
class AnalysisSettings:
    """分析配置"""
    # 故障检测参数
    fault_threshold_multiplier: float = 3.0  # 阈值倍数
    min_fault_duration: float = 0.001  # 最小故障持续时间(s)

    # 谐波分析参数
    fundamental_frequency: float = 50.0  # 基波频率(Hz)
    harmonic_orders: list = None  # 谐波次数

    # 特征提取参数
    window_size: float = 0.02  # 分析窗口大小(s)
    overlap_ratio: float = 0.5  # 窗口重叠比例

    def __post_init__(self):
        if self.harmonic_orders is None:
            self.harmonic_orders = [2, 3, 5, 7, 11, 13]


@dataclass
class UISettings:
    """界面配置"""
    window_width: int = 1920
    window_height: int = 1080
    splitter_sizes: list = None
    recent_files: list = None
    max_recent_files: int = 10
    auto_save_enabled: bool = True
    auto_save_interval: int = 300  # 自动保存间隔(秒)

    def __post_init__(self):
        if self.splitter_sizes is None:
            self.splitter_sizes = [350, 1050]
        if self.recent_files is None:
            self.recent_files = []


class AppSettings:
    """应用程序设置管理器"""

    def __init__(self):
        self.settings = QSettings("COMTRADE分析器", "设置")
        self.config_dir = Path.home() / ".comtrade_analyzer"
        self.config_file = self.config_dir / "config.json"

        # 创建配置目录
        self.config_dir.mkdir(exist_ok=True)

        # 初始化设置
        self.plot_settings = PlotSettings()
        self.analysis_settings = AnalysisSettings()
        self.ui_settings = UISettings()

        # 加载设置
        self.load_settings()

    def load_settings(self):
        """加载设置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                # 加载各部分设置
                if 'plot' in config_data:
                    self._update_dataclass(self.plot_settings, config_data['plot'])

                if 'analysis' in config_data:
                    self._update_dataclass(self.analysis_settings, config_data['analysis'])

                if 'ui' in config_data:
                    self._update_dataclass(self.ui_settings, config_data['ui'])

            # 从QSettings加载窗口几何信息
            self._load_qt_settings()

        except Exception as e:
            print(f"加载设置失败: {e}")

    def save_settings(self):
        """保存设置"""
        try:
            config_data = {
                'plot': asdict(self.plot_settings),
                'analysis': asdict(self.analysis_settings),
                'ui': asdict(self.ui_settings)
            }

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)

            # 保存到QSettings
            self._save_qt_settings()

        except Exception as e:
            print(f"保存设置失败: {e}")

    def _update_dataclass(self, obj, data: Dict[str, Any]):
        """更新数据类实例"""
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)

    def _load_qt_settings(self):
        """从QSettings加载设置"""
        # 窗口几何
        if self.settings.contains("geometry"):
            geometry = self.settings.value("geometry")
            if geometry:
                # 这里可以设置窗口几何信息，在主窗口中使用
                pass

        # 最近文件
        recent_files = self.settings.value("recent_files", [])
        if isinstance(recent_files, list):
            self.ui_settings.recent_files = recent_files[:self.ui_settings.max_recent_files]

    def _save_qt_settings(self):
        """保存到QSettings"""
        self.settings.setValue("recent_files", self.ui_settings.recent_files)

    def add_recent_file(self, file_path: str):
        """添加最近打开的文件"""
        file_path = str(Path(file_path).resolve())

        # 移除已存在的路径
        if file_path in self.ui_settings.recent_files:
            self.ui_settings.recent_files.remove(file_path)

        # 添加到开头
        self.ui_settings.recent_files.insert(0, file_path)

        # 限制数量
        if len(self.ui_settings.recent_files) > self.ui_settings.max_recent_files:
            self.ui_settings.recent_files = self.ui_settings.recent_files[:self.ui_settings.max_recent_files]

        self.save_settings()

    def get_recent_files(self) -> list:
        """获取最近文件列表"""
        # 过滤不存在的文件
        existing_files = [f for f in self.ui_settings.recent_files if Path(f).exists()]
        if len(existing_files) != len(self.ui_settings.recent_files):
            self.ui_settings.recent_files = existing_files
            self.save_settings()

        return self.ui_settings.recent_files

    def reset_to_defaults(self):
        """重置为默认设置"""
        self.plot_settings = PlotSettings()
        self.analysis_settings = AnalysisSettings()
        self.ui_settings = UISettings()
        self.save_settings()

    def export_settings(self, file_path: str):
        """导出设置到文件"""
        config_data = {
            'plot': asdict(self.plot_settings),
            'analysis': asdict(self.analysis_settings),
            'ui': asdict(self.ui_settings)
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)

    def import_settings(self, file_path: str):
        """从文件导入设置"""
        with open(file_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        if 'plot' in config_data:
            self._update_dataclass(self.plot_settings, config_data['plot'])

        if 'analysis' in config_data:
            self._update_dataclass(self.analysis_settings, config_data['analysis'])

        if 'ui' in config_data:
            self._update_dataclass(self.ui_settings, config_data['ui'])

        self.save_settings()


# 全局配置实例
app_settings = AppSettings()