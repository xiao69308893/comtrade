#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型定义
定义COMTRADE数据和分析结果的数据结构
"""

import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from utils.logger import get_logger

logger = get_logger(__name__)
class ChannelType(Enum):
    """通道类型枚举"""
    ANALOG = "analog"
    DIGITAL = "digital"


class FaultType(Enum):
    """故障类型枚举"""
    NONE = "无故障"
    SINGLE_PHASE_GROUND = "单相接地"
    PHASE_TO_PHASE = "相间短路"
    TWO_PHASE_GROUND = "两相接地"
    THREE_PHASE = "三相短路"
    OVERVOLTAGE = "过电压"
    UNDERVOLTAGE = "欠电压"
    OVERCURRENT = "过电流"
    FREQUENCY_DEVIATION = "频率偏差"
    HARMONIC_DISTORTION = "谐波畸变"
    VOLTAGE_SAG = "电压暂降"
    VOLTAGE_SWELL = "电压暂升"
    TRANSIENT = "暂态扰动"
    UNKNOWN = "未知故障"


@dataclass
class ChannelInfo:
    """通道信息"""
    index: int
    name: str
    phase: str = ""
    unit: str = ""
    multiplier: float = 1.0
    offset: float = 0.0
    min_value: float = 0.0
    max_value: float = 0.0
    primary: float = 1.0
    secondary: float = 1.0
    data: np.ndarray = field(default_factory=lambda: np.array([]))

    @property
    def channel_type(self) -> ChannelType:
        """根据数据类型判断通道类型"""
        if self.data.dtype == bool or np.all(np.isin(self.data, [0, 1])):
            return ChannelType.DIGITAL
        return ChannelType.ANALOG

    @property
    def scaled_data(self) -> np.ndarray:
        """获取按比例缩放的数据"""
        return self.data * self.multiplier + self.offset

    # 修复 models/data_models.py 中的RMS计算问题

    @property
    def rms_value(self) -> float:
        """计算RMS值（仅适用于模拟通道）- 防止溢出版本"""
        if self.channel_type == ChannelType.ANALOG and len(self.data) > 0:
            try:
                # 清理数据，移除无效值
                clean_data = np.nan_to_num(self.scaled_data, nan=0.0, posinf=0.0, neginf=0.0)

                # 检查数据范围，防止平方后溢出
                max_abs_val = np.max(np.abs(clean_data))
                if max_abs_val > 1e6:  # 如果数值太大，先进行缩放
                    scale_factor = 1e6 / max_abs_val
                    clean_data = clean_data * scale_factor
                    need_scale_back = True
                else:
                    need_scale_back = False
                    scale_factor = 1.0

                # 使用安全的方式计算RMS
                with np.errstate(over='ignore', invalid='ignore'):
                    squared_data = clean_data ** 2

                # 检查平方后的数据
                squared_data = np.nan_to_num(squared_data, nan=0.0, posinf=0.0, neginf=0.0)

                # 计算平均值
                mean_squared = np.mean(squared_data)

                # 计算RMS
                if mean_squared >= 0:
                    rms = np.sqrt(mean_squared)

                    # 如果之前进行了缩放，需要还原
                    if need_scale_back:
                        rms = rms / scale_factor

                    # 检查结果的有效性
                    if not np.isfinite(rms):
                        logger.warning(f"通道RMS计算结果无效，返回0")
                        return 0.0

                    return float(rms)
                else:
                    return 0.0

            except Exception as e:
                logger.warning(f"RMS计算失败: {e}")
                return 0.0
        return 0.0

    @property
    def peak_value(self) -> float:
        """计算峰值（仅适用于模拟通道）- 防止溢出版本"""
        if self.channel_type == ChannelType.ANALOG and len(self.data) > 0:
            try:
                # 清理数据
                clean_data = np.nan_to_num(self.scaled_data, nan=0.0, posinf=0.0, neginf=0.0)

                # 计算峰值
                peak = np.max(np.abs(clean_data))

                # 检查结果的有效性
                if not np.isfinite(peak):
                    return 0.0

                return float(peak)
            except Exception as e:
                logger.warning(f"峰值计算失败: {e}")
                return 0.0
        return 0.0


@dataclass
class ComtradeRecord:
    """COMTRADE记录"""
    station_name: str
    rec_dev_id: str
    rev_year: int
    start_timestamp: Optional[datetime]
    trigger_timestamp: Optional[datetime]
    sample_rates: List[Tuple[int, int]]
    frequency: float
    time_axis: np.ndarray
    analog_channels: List[ChannelInfo]
    digital_channels: List[ChannelInfo]
    file_info: Any = None

    @property
    def total_channels(self) -> int:
        """总通道数"""
        return len(self.analog_channels) + len(self.digital_channels)

    @property
    def duration(self) -> float:
        """记录时长（秒）"""
        if len(self.time_axis) > 1:
            return float(self.time_axis[-1] - self.time_axis[0])
        return 0.0

    @property
    def sample_count(self) -> int:
        """采样点数"""
        return len(self.time_axis)

    def get_channel_by_name(self, name: str) -> Optional[ChannelInfo]:
        """根据名称获取通道"""
        for channel in self.analog_channels + self.digital_channels:
            if channel.name == name:
                return channel
        return None

    def get_channels_by_phase(self, phase: str) -> List[ChannelInfo]:
        """根据相别获取通道"""
        channels = []
        for channel in self.analog_channels:
            if channel.phase.upper() == phase.upper():
                channels.append(channel)
        return channels

    def get_time_window(self, start_time: float, end_time: float) -> Tuple[int, int]:
        """获取时间窗口对应的索引范围"""
        start_idx = np.searchsorted(self.time_axis, start_time, side='left')
        end_idx = np.searchsorted(self.time_axis, end_time, side='right')
        return max(0, start_idx), min(len(self.time_axis), end_idx)


@dataclass
class SignalFeatures:
    """信号特征"""
    # 基本统计特征
    mean: float = 0.0
    std: float = 0.0
    rms: float = 0.0
    peak: float = 0.0
    peak_to_peak: float = 0.0
    crest_factor: float = 0.0  # 峰值因子
    form_factor: float = 0.0  # 波形因子

    # 频域特征
    fundamental_magnitude: float = 0.0
    fundamental_phase: float = 0.0
    thd: float = 0.0  # 总谐波畸变
    thd_f: float = 0.0  # 基于基波的THD
    dominant_frequency: float = 0.0

    # 谐波分量
    harmonics: Dict[int, Tuple[float, float]] = field(default_factory=dict)  # {次数: (幅值, 相位)}

    # 时间特征
    zero_crossings: int = 0
    energy: float = 0.0

    def get_harmonic_magnitude(self, order: int) -> float:
        """获取指定次谐波幅值"""
        return self.harmonics.get(order, (0.0, 0.0))[0]

    def get_harmonic_phase(self, order: int) -> float:
        """获取指定次谐波相位"""
        return self.harmonics.get(order, (0.0, 0.0))[1]


@dataclass
class FaultEvent:
    """故障事件"""
    start_time: float
    end_time: float
    fault_type: FaultType
    affected_channels: List[str]
    severity: float  # 严重程度 0-1
    confidence: float  # 置信度 0-1
    description: str = ""
    features: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float:
        """故障持续时间"""
        return self.end_time - self.start_time

    def __str__(self) -> str:
        return f"{self.fault_type.value} ({self.start_time:.4f}s - {self.end_time:.4f}s)"


@dataclass
class AnalysisResult:
    """分析结果"""
    timestamp: datetime
    record_info: Dict[str, Any]

    # 通道特征
    channel_features: Dict[str, SignalFeatures] = field(default_factory=dict)

    # 故障检测结果
    fault_events: List[FaultEvent] = field(default_factory=list)

    # 系统级分析
    system_frequency: float = 0.0
    system_unbalance: float = 0.0  # 不平衡度

    # 电能质量指标
    voltage_rms: Dict[str, float] = field(default_factory=dict)  # 各相电压RMS
    current_rms: Dict[str, float] = field(default_factory=dict)  # 各相电流RMS
    power_factor: float = 0.0  # 功率因数

    # 统计信息
    analysis_duration: float = 0.0  # 分析耗时
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def add_warning(self, message: str):
        """添加警告"""
        self.warnings.append(message)

    def add_error(self, message: str):
        """添加错误"""
        self.errors.append(message)

    def get_fault_summary(self) -> Dict[FaultType, int]:
        """获取故障类型统计"""
        summary = {}
        for event in self.fault_events:
            fault_type = event.fault_type
            summary[fault_type] = summary.get(fault_type, 0) + 1
        return summary

    def get_most_severe_fault(self) -> Optional[FaultEvent]:
        """获取最严重的故障"""
        if not self.fault_events:
            return None
        return max(self.fault_events, key=lambda x: x.severity)


@dataclass
class TimeSeriesPoint:
    """时间序列数据点"""
    time: float
    value: float
    channel_name: str = ""

    def __lt__(self, other):
        return self.time < other.time


@dataclass
class FrequencyComponent:
    """频率分量"""
    frequency: float
    magnitude: float
    phase: float

    def __str__(self) -> str:
        return f"f={self.frequency:.2f}Hz, |X|={self.magnitude:.4f}, ∠={self.phase:.2f}°"


@dataclass
class PowerQualityMetrics:
    """电能质量指标"""
    # 电压指标
    voltage_deviation: float = 0.0  # 电压偏差
    voltage_unbalance: float = 0.0  # 电压不平衡度
    voltage_fluctuation: float = 0.0  # 电压波动

    # 频率指标
    frequency_deviation: float = 0.0  # 频率偏差

    # 谐波指标
    voltage_thd: float = 0.0  # 电压总谐波畸变
    current_thd: float = 0.0  # 电流总谐波畸变

    # 功率指标
    active_power: float = 0.0  # 有功功率
    reactive_power: float = 0.0  # 无功功率
    apparent_power: float = 0.0  # 视在功率
    power_factor: float = 0.0  # 功率因数

    # 暂态指标
    voltage_sag_count: int = 0  # 电压暂降次数
    voltage_swell_count: int = 0  # 电压暂升次数
    interruption_count: int = 0  # 中断次数

    def is_within_limits(self, limits: Dict[str, Tuple[float, float]]) -> Dict[str, bool]:
        """检查指标是否在限值范围内"""
        results = {}
        for metric_name, (min_limit, max_limit) in limits.items():
            if hasattr(self, metric_name):
                value = getattr(self, metric_name)
                results[metric_name] = min_limit <= value <= max_limit
        return results