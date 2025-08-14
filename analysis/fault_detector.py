#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
故障检测器
基于波形特征和模式识别检测电力系统故障
"""

import numpy as np
import scipy.signal as signal
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from models.data_models import (
    FaultEvent, FaultType, ChannelInfo, ComtradeRecord,
    SignalFeatures, PowerQualityMetrics
)
from analysis.feature_extractor import FeatureExtractor
from utils.math_utils import calculate_rms, moving_average
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FaultDetectionConfig:
    """故障检测配置"""
    # 电压故障阈值
    undervoltage_threshold: float = 0.9  # 90% 额定电压
    overvoltage_threshold: float = 1.1  # 110% 额定电压
    voltage_sag_threshold: float = 0.9  # 电压暂降阈值
    voltage_swell_threshold: float = 1.1  # 电压暂升阈值

    # 电流故障阈值
    overcurrent_threshold: float = 2.0  # 2倍额定电流

    # 频率故障阈值
    frequency_deviation_threshold: float = 1.0  # ±1Hz

    # 谐波阈值
    thd_threshold: float = 5.0  # 5% THD

    # 不平衡度阈值
    unbalance_threshold: float = 2.0  # 2%

    # 时间参数
    min_fault_duration: float = 0.01  # 最小故障持续时间 10ms
    transient_window: float = 0.1  # 暂态检测窗口 100ms

    # 检测灵敏度
    detection_sensitivity: float = 3.0  # 阈值倍数


class FaultDetector:
    """故障检测器"""

    def __init__(self, config: Optional[FaultDetectionConfig] = None):
        """
        初始化故障检测器

        Args:
            config: 检测配置，None表示使用默认配置
        """
        self.config = config or FaultDetectionConfig()
        self.feature_extractor = None

    def detect_faults(self, record: ComtradeRecord) -> List[FaultEvent]:
        """
        检测记录中的故障事件

        Args:
            record: COMTRADE记录

        Returns:
            检测到的故障事件列表
        """
        try:
            # 初始化特征提取器
            if len(record.time_axis) > 1:
                sampling_rate = 1.0 / (record.time_axis[1] - record.time_axis[0])
                self.feature_extractor = FeatureExtractor(sampling_rate, record.frequency)

            fault_events = []

            # 检测各种类型的故障
            fault_events.extend(self._detect_voltage_faults(record))
            fault_events.extend(self._detect_current_faults(record))
            fault_events.extend(self._detect_frequency_faults(record))
            fault_events.extend(self._detect_harmonic_faults(record))
            fault_events.extend(self._detect_unbalance_faults(record))
            fault_events.extend(self._detect_short_circuit_faults(record))
            fault_events.extend(self._detect_transient_faults(record))

            # 合并重叠的故障事件
            fault_events = self._merge_overlapping_events(fault_events)

            # 按时间排序
            fault_events.sort(key=lambda x: x.start_time)

            logger.info(f"检测到 {len(fault_events)} 个故障事件")
            return fault_events

        except Exception as e:
            logger.error(f"故障检测失败: {e}")
            return []

    def _detect_voltage_faults(self, record: ComtradeRecord) -> List[FaultEvent]:
        """检测电压故障"""
        faults = []

        # 查找电压通道
        voltage_channels = self._find_voltage_channels(record)

        for channel in voltage_channels:
            if len(channel.data) == 0:
                continue

            # 计算RMS值序列
            rms_values = self._calculate_rms_sequence(channel.data, record.time_axis)

            # 估计额定电压（使用前几个周期的平均值）
            samples_per_cycle = int(len(channel.data) / (record.duration * record.frequency))
            if samples_per_cycle > 0:
                rated_voltage = np.mean(rms_values[:min(len(rms_values), samples_per_cycle * 3)])
            else:
                rated_voltage = np.mean(rms_values)

            if rated_voltage == 0:
                continue

            # 检测过电压和欠电压
            faults.extend(self._detect_voltage_level_faults(
                rms_values, record.time_axis, rated_voltage, channel.name
            ))

            # 检测电压暂降和暂升
            faults.extend(self._detect_voltage_transient_faults(
                rms_values, record.time_axis, rated_voltage, channel.name
            ))

        return faults

    def _detect_current_faults(self, record: ComtradeRecord) -> List[FaultEvent]:
        """检测电流故障"""
        faults = []

        # 查找电流通道
        current_channels = self._find_current_channels(record)

        for channel in current_channels:
            if len(channel.data) == 0:
                continue

            # 计算RMS值序列
            rms_values = self._calculate_rms_sequence(channel.data, record.time_axis)

            # 估计额定电流（使用稳态部分）
            rated_current = np.median(rms_values)

            if rated_current == 0:
                continue

            # 检测过电流
            overcurrent_mask = rms_values > (rated_current * self.config.overcurrent_threshold)
            fault_intervals = self._find_fault_intervals(overcurrent_mask, record.time_axis)

            for start_time, end_time in fault_intervals:
                if end_time - start_time >= self.config.min_fault_duration:
                    max_current = np.max(rms_values[
                                             (record.time_axis >= start_time) & (record.time_axis <= end_time)
                                             ])
                    severity = min(1.0, (max_current / rated_current - 1.0) / self.config.overcurrent_threshold)

                    fault = FaultEvent(
                        start_time=start_time,
                        end_time=end_time,
                        fault_type=FaultType.OVERCURRENT,
                        affected_channels=[channel.name],
                        severity=severity,
                        confidence=0.8,
                        description=f"过电流故障：{max_current:.2f}A (额定值: {rated_current:.2f}A)"
                    )
                    faults.append(fault)

        return faults

    def _detect_frequency_faults(self, record: ComtradeRecord) -> List[FaultEvent]:
        """检测频率故障"""
        faults = []

        # 选择一个主要的电压通道进行频率分析
        voltage_channels = self._find_voltage_channels(record)
        if not voltage_channels:
            return faults

        main_channel = voltage_channels[0]

        # 计算瞬时频率
        freq_sequence = self._estimate_frequency_sequence(main_channel.data, record.time_axis, record.frequency)

        # 检测频率偏差
        freq_deviation = np.abs(freq_sequence - record.frequency)
        fault_mask = freq_deviation > self.config.frequency_deviation_threshold

        fault_intervals = self._find_fault_intervals(fault_mask, record.time_axis)

        for start_time, end_time in fault_intervals:
            if end_time - start_time >= self.config.min_fault_duration:
                time_mask = (record.time_axis >= start_time) & (record.time_axis <= end_time)
                max_deviation = np.max(freq_deviation[time_mask])
                avg_frequency = np.mean(freq_sequence[time_mask])

                severity = min(1.0, max_deviation / self.config.frequency_deviation_threshold)

                fault = FaultEvent(
                    start_time=start_time,
                    end_time=end_time,
                    fault_type=FaultType.FREQUENCY_DEVIATION,
                    affected_channels=[main_channel.name],
                    severity=severity,
                    confidence=0.7,
                    description=f"频率偏差：{avg_frequency:.2f}Hz (偏差: {max_deviation:.2f}Hz)"
                )
                faults.append(fault)

        return faults

    def _detect_harmonic_faults(self, record: ComtradeRecord) -> List[FaultEvent]:
        """检测谐波故障"""
        faults = []

        if not self.feature_extractor:
            return faults

        # 分析所有电压和电流通道的谐波
        channels_to_analyze = self._find_voltage_channels(record) + self._find_current_channels(record)

        for channel in channels_to_analyze:
            if len(channel.data) == 0:
                continue

            # 提取特征
            features = self.feature_extractor.extract_features(channel)

            # 检测THD超标
            if features.thd > self.config.thd_threshold:
                severity = min(1.0, features.thd / self.config.thd_threshold - 1.0)

                # 找出主要谐波分量
                major_harmonics = [
                    f"{order}次谐波: {mag:.2f}"
                    for order, (mag, _) in features.harmonics.items()
                    if mag > features.fundamental_magnitude * 0.05  # 5%以上的谐波
                ]

                fault = FaultEvent(
                    start_time=0.0,
                    end_time=record.duration,
                    fault_type=FaultType.HARMONIC_DISTORTION,
                    affected_channels=[channel.name],
                    severity=severity,
                    confidence=0.8,
                    description=f"谐波畸变：THD={features.thd:.2f}% (主要谐波: {', '.join(major_harmonics)})"
                )
                faults.append(fault)

        return faults

    def _detect_unbalance_faults(self, record: ComtradeRecord) -> List[FaultEvent]:
        """检测三相不平衡故障"""
        faults = []

        # 查找三相电压通道
        voltage_channels = self._find_voltage_channels(record)
        if len(voltage_channels) < 3:
            return faults

        # 按相别分组
        phase_channels = {'A': [], 'B': [], 'C': []}
        for channel in voltage_channels:
            phase = self._identify_phase(channel.name)
            if phase in phase_channels:
                phase_channels[phase].append(channel)

        # 检查是否有完整的三相数据
        if not all(phase_channels.values()):
            return faults

        # 使用每相的第一个通道
        phase_a = phase_channels['A'][0].data
        phase_b = phase_channels['B'][0].data
        phase_c = phase_channels['C'][0].data

        # 计算三相RMS值
        rms_a = calculate_rms(phase_a)
        rms_b = calculate_rms(phase_b)
        rms_c = calculate_rms(phase_c)

        # 计算不平衡度
        avg_rms = (rms_a + rms_b + rms_c) / 3
        if avg_rms > 0:
            unbalance = max(
                abs(rms_a - avg_rms),
                abs(rms_b - avg_rms),
                abs(rms_c - avg_rms)
            ) / avg_rms * 100

            if unbalance > self.config.unbalance_threshold:
                severity = min(1.0, unbalance / self.config.unbalance_threshold - 1.0)

                fault = FaultEvent(
                    start_time=0.0,
                    end_time=record.duration,
                    fault_type=FaultType.PHASE_TO_PHASE,  # 可能是相间故障导致的不平衡
                    affected_channels=[ch.name for channels in phase_channels.values() for ch in channels],
                    severity=severity,
                    confidence=0.6,
                    description=f"三相不平衡：{unbalance:.2f}% (A相:{rms_a:.2f}, B相:{rms_b:.2f}, C相:{rms_c:.2f})"
                )
                faults.append(fault)

        return faults

    def _detect_short_circuit_faults(self, record: ComtradeRecord) -> List[FaultEvent]:
        """检测短路故障"""
        faults = []

        # 查找电流通道
        current_channels = self._find_current_channels(record)

        for channel in current_channels:
            if len(channel.data) == 0:
                continue

            # 计算电流突变
            current_diff = np.diff(np.abs(channel.data))
            threshold = np.std(current_diff) * self.config.detection_sensitivity

            # 查找突变点
            fault_points = np.where(np.abs(current_diff) > threshold)[0]

            if len(fault_points) > 0:
                # 分析突变是否为短路
                for point in fault_points:
                    start_idx = max(0, point - 10)  # 突变前10个点
                    end_idx = min(len(channel.data), point + 100)  # 突变后100个点

                    pre_fault_current = np.mean(np.abs(channel.data[start_idx:point]))
                    fault_current = np.mean(np.abs(channel.data[point:end_idx]))

                    # 如果电流显著增大，可能是短路
                    if fault_current > pre_fault_current * 3:  # 3倍以上增大
                        start_time = record.time_axis[point] if point < len(record.time_axis) else 0
                        end_time = min(start_time + 0.5, record.duration)  # 假设故障持续0.5秒

                        severity = min(1.0, fault_current / pre_fault_current / 10)  # 以10倍为满分

                        # 尝试识别具体的短路类型
                        fault_type = self._classify_short_circuit_type(record, point)

                        fault = FaultEvent(
                            start_time=start_time,
                            end_time=end_time,
                            fault_type=fault_type,
                            affected_channels=[channel.name],
                            severity=severity,
                            confidence=0.7,
                            description=f"短路故障：电流从{pre_fault_current:.2f}A增至{fault_current:.2f}A"
                        )
                        faults.append(fault)

        return faults

    def _detect_transient_faults(self, record: ComtradeRecord) -> List[FaultEvent]:
        """检测暂态故障"""
        faults = []

        # 分析所有通道的暂态特性
        all_channels = record.analog_channels

        for channel in all_channels:
            if len(channel.data) == 0:
                continue

            # 计算信号的变化率
            signal_diff = np.diff(channel.data)

            # 使用滑动窗口检测突变
            window_size = int(0.01 * len(channel.data))  # 1%的数据长度作为窗口
            if window_size < 5:
                window_size = 5

            for i in range(len(signal_diff) - window_size):
                window_data = signal_diff[i:i + window_size]
                if np.std(window_data) > np.std(signal_diff) * 2:  # 标准差超过2倍
                    start_time = record.time_axis[i] if i < len(record.time_axis) else 0
                    end_time = start_time + self.config.transient_window

                    fault = FaultEvent(
                        start_time=start_time,
                        end_time=min(end_time, record.duration),
                        fault_type=FaultType.TRANSIENT,
                        affected_channels=[channel.name],
                        severity=0.5,
                        confidence=0.5,
                        description=f"暂态扰动检测"
                    )
                    faults.append(fault)
                    break  # 每个通道只报告一次暂态

        return faults

    def _find_voltage_channels(self, record: ComtradeRecord) -> List[ChannelInfo]:
        """查找电压通道"""
        voltage_channels = []
        for channel in record.analog_channels:
            if any(keyword in channel.name.upper() for keyword in ['V', 'VOLT', 'U', '电压']):
                voltage_channels.append(channel)
        return voltage_channels

    def _find_current_channels(self, record: ComtradeRecord) -> List[ChannelInfo]:
        """查找电流通道"""
        current_channels = []
        for channel in record.analog_channels:
            if any(keyword in channel.name.upper() for keyword in ['I', 'CURR', 'A', '电流']):
                current_channels.append(channel)
        return current_channels

    def _identify_phase(self, channel_name: str) -> str:
        """识别通道的相别"""
        name_upper = channel_name.upper()
        if 'A' in name_upper and 'B' not in name_upper and 'C' not in name_upper:
            return 'A'
        elif 'B' in name_upper:
            return 'B'
        elif 'C' in name_upper:
            return 'C'
        return ''

    def _calculate_rms_sequence(self, data: np.ndarray, time_axis: np.ndarray) -> np.ndarray:
        """计算RMS值序列"""
        if len(data) == 0:
            return np.array([])

        # 使用滑动窗口计算RMS
        window_size = max(10, len(data) // 100)  # 1%的数据长度或至少10个点
        rms_values = []

        for i in range(len(data) - window_size + 1):
            window_data = data[i:i + window_size]
            rms_values.append(calculate_rms(window_data))

        return np.array(rms_values)

    def _find_fault_intervals(self, fault_mask: np.ndarray, time_axis: np.ndarray) -> List[Tuple[float, float]]:
        """从布尔掩码中找出故障时间间隔"""
        intervals = []

        # 找到连续的True区间
        diff_mask = np.diff(np.concatenate(([False], fault_mask, [False])).astype(int))
        starts = np.where(diff_mask == 1)[0]
        ends = np.where(diff_mask == -1)[0]

        for start, end in zip(starts, ends):
            if start < len(time_axis) and end <= len(time_axis):
                start_time = time_axis[start]
                end_time = time_axis[end - 1] if end > 0 else time_axis[-1]
                intervals.append((start_time, end_time))

        return intervals

    def _estimate_frequency_sequence(self, data: np.ndarray, time_axis: np.ndarray, nominal_freq: float) -> np.ndarray:
        """估计瞬时频率序列"""
        if len(data) < 10:
            return np.full(len(data), nominal_freq)

        # 使用希尔伯特变换计算瞬时频率
        analytic_signal = signal.hilbert(data)
        instantaneous_phase = np.unwrap(np.angle(analytic_signal))
        instantaneous_frequency = np.diff(instantaneous_phase) / (2.0 * np.pi) / np.diff(time_axis)

        # 补齐长度
        instantaneous_frequency = np.concatenate(([nominal_freq], instantaneous_frequency))

        # 平滑滤波
        instantaneous_frequency = moving_average(instantaneous_frequency, window_size=5)

        return instantaneous_frequency

    def _detect_voltage_level_faults(self, rms_values: np.ndarray, time_axis: np.ndarray,
                                     rated_voltage: float, channel_name: str) -> List[FaultEvent]:
        """检测电压水平故障"""
        faults = []

        # 欠电压检测
        undervoltage_mask = rms_values < (rated_voltage * self.config.undervoltage_threshold)
        intervals = self._find_fault_intervals(undervoltage_mask, time_axis[:len(rms_values)])

        for start_time, end_time in intervals:
            if end_time - start_time >= self.config.min_fault_duration:
                min_voltage = np.min(rms_values[
                                         (time_axis[:len(rms_values)] >= start_time) &
                                         (time_axis[:len(rms_values)] <= end_time)
                                         ])
                severity = (rated_voltage * self.config.undervoltage_threshold - min_voltage) / rated_voltage

                fault = FaultEvent(
                    start_time=start_time,
                    end_time=end_time,
                    fault_type=FaultType.UNDERVOLTAGE,
                    affected_channels=[channel_name],
                    severity=min(1.0, severity),
                    confidence=0.8,
                    description=f"欠电压：{min_voltage:.2f}V (额定值: {rated_voltage:.2f}V)"
                )
                faults.append(fault)

        # 过电压检测
        overvoltage_mask = rms_values > (rated_voltage * self.config.overvoltage_threshold)
        intervals = self._find_fault_intervals(overvoltage_mask, time_axis[:len(rms_values)])

        for start_time, end_time in intervals:
            if end_time - start_time >= self.config.min_fault_duration:
                max_voltage = np.max(rms_values[
                                         (time_axis[:len(rms_values)] >= start_time) &
                                         (time_axis[:len(rms_values)] <= end_time)
                                         ])
                severity = (max_voltage - rated_voltage * self.config.overvoltage_threshold) / rated_voltage

                fault = FaultEvent(
                    start_time=start_time,
                    end_time=end_time,
                    fault_type=FaultType.OVERVOLTAGE,
                    affected_channels=[channel_name],
                    severity=min(1.0, severity),
                    confidence=0.8,
                    description=f"过电压：{max_voltage:.2f}V (额定值: {rated_voltage:.2f}V)"
                )
                faults.append(fault)

        return faults

    def _detect_voltage_transient_faults(self, rms_values: np.ndarray, time_axis: np.ndarray,
                                         rated_voltage: float, channel_name: str) -> List[FaultEvent]:
        """检测电压暂态故障（暂降、暂升）"""
        faults = []

        # 电压暂降检测（短时间内电压下降）
        sag_mask = rms_values < (rated_voltage * self.config.voltage_sag_threshold)
        intervals = self._find_fault_intervals(sag_mask, time_axis[:len(rms_values)])

        for start_time, end_time in intervals:
            # 暂降通常持续时间较短
            if 0.01 <= end_time - start_time <= 1.0:  # 10ms到1s
                min_voltage = np.min(rms_values[
                                         (time_axis[:len(rms_values)] >= start_time) &
                                         (time_axis[:len(rms_values)] <= end_time)
                                         ])
                severity = (rated_voltage * self.config.voltage_sag_threshold - min_voltage) / rated_voltage

                fault = FaultEvent(
                    start_time=start_time,
                    end_time=end_time,
                    fault_type=FaultType.VOLTAGE_SAG,
                    affected_channels=[channel_name],
                    severity=min(1.0, severity),
                    confidence=0.7,
                    description=f"电压暂降：{min_voltage:.2f}V，持续{(end_time - start_time) * 1000:.1f}ms"
                )
                faults.append(fault)

        # 电压暂升检测
        swell_mask = rms_values > (rated_voltage * self.config.voltage_swell_threshold)
        intervals = self._find_fault_intervals(swell_mask, time_axis[:len(rms_values)])

        for start_time, end_time in intervals:
            if 0.01 <= end_time - start_time <= 1.0:
                max_voltage = np.max(rms_values[
                                         (time_axis[:len(rms_values)] >= start_time) &
                                         (time_axis[:len(rms_values)] <= end_time)
                                         ])
                severity = (max_voltage - rated_voltage * self.config.voltage_swell_threshold) / rated_voltage

                fault = FaultEvent(
                    start_time=start_time,
                    end_time=end_time,
                    fault_type=FaultType.VOLTAGE_SWELL,
                    affected_channels=[channel_name],
                    severity=min(1.0, severity),
                    confidence=0.7,
                    description=f"电压暂升：{max_voltage:.2f}V，持续{(end_time - start_time) * 1000:.1f}ms"
                )
                faults.append(fault)

        return faults

    def _classify_short_circuit_type(self, record: ComtradeRecord, fault_point: int) -> FaultType:
        """分类短路故障类型"""
        # 简化的短路分类逻辑
        current_channels = self._find_current_channels(record)

        if len(current_channels) >= 3:
            # 检查三相电流的变化
            fault_currents = []
            for channel in current_channels[:3]:
                if fault_point < len(channel.data):
                    fault_currents.append(abs(channel.data[fault_point]))

            if len(fault_currents) == 3:
                max_current = max(fault_currents)
                fault_phases = sum(1 for i in fault_currents if i > max_current * 0.5)

                if fault_phases == 1:
                    return FaultType.SINGLE_PHASE_GROUND
                elif fault_phases == 2:
                    return FaultType.TWO_PHASE_GROUND
                elif fault_phases == 3:
                    return FaultType.THREE_PHASE

        return FaultType.PHASE_TO_PHASE  # 默认为相间短路

    def _merge_overlapping_events(self, events: List[FaultEvent]) -> List[FaultEvent]:
        """合并重叠的故障事件"""
        if not events:
            return events

        # 按开始时间排序
        events.sort(key=lambda x: x.start_time)

        merged = [events[0]]

        for current in events[1:]:
            last = merged[-1]

            # 如果事件重叠且类型相同，则合并
            if (current.start_time <= last.end_time and
                    current.fault_type == last.fault_type):

                # 合并事件
                last.end_time = max(last.end_time, current.end_time)
                last.severity = max(last.severity, current.severity)
                last.confidence = (last.confidence + current.confidence) / 2
                last.affected_channels = list(set(last.affected_channels + current.affected_channels))
                last.description += f"; {current.description}"
            else:
                merged.append(current)

        return merged