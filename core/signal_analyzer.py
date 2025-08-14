#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信号分析核心模块
提供信号分析的核心算法和功能
"""

import numpy as np
import scipy.signal as signal
import scipy.fft as fft
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from models.data_models import (
    ComtradeRecord, ChannelInfo, SignalFeatures,
    AnalysisResult, PowerQualityMetrics
)
from analysis.feature_extractor import FeatureExtractor
from analysis.fault_detector import FaultDetector, FaultDetectionConfig
from utils.math_utils import fft_analysis, calculate_rms
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AnalysisConfig:
    """分析配置"""
    # 特征提取配置
    extract_features: bool = True
    extract_harmonics: bool = True
    max_harmonic_order: int = 20

    # 故障检测配置
    detect_faults: bool = True
    fault_config: Optional[FaultDetectionConfig] = None

    # 电能质量分析
    analyze_power_quality: bool = True

    # 对称分量分析
    analyze_symmetrical_components: bool = False

    # 频谱分析
    perform_fft: bool = True
    fft_window: str = 'hann'

    # 并行处理
    use_parallel: bool = False
    max_workers: int = 4


class SignalAnalyzer:
    """信号分析器"""

    def __init__(self, config: Optional[AnalysisConfig] = None):
        """
        初始化信号分析器

        Args:
            config: 分析配置
        """
        self.config = config or AnalysisConfig()
        self.feature_extractor = None
        self.fault_detector = None

        # 分析结果缓存
        self.last_analysis_result = None

    def analyze_record(self, record: ComtradeRecord) -> AnalysisResult:
        """
        分析COMTRADE记录

        Args:
            record: COMTRADE记录

        Returns:
            分析结果
        """
        try:
            from datetime import datetime
            start_time = datetime.now()

            logger.info(f"开始分析COMTRADE记录: {record.station_name}")

            # 初始化分析器
            self._initialize_analyzers(record)

            # 创建分析结果对象
            result = AnalysisResult(
                timestamp=start_time,
                record_info={
                    'station_name': record.station_name,
                    'duration': record.duration,
                    'sample_count': len(record.time_axis),
                    'analog_channels': len(record.analog_channels),
                    'digital_channels': len(record.digital_channels)
                }
            )

            # 特征提取
            if self.config.extract_features:
                result.channel_features = self._extract_all_features(record)

            # 故障检测
            if self.config.detect_faults:
                result.fault_events = self._detect_faults(record)

            # 电能质量分析
            if self.config.analyze_power_quality:
                self._analyze_power_quality(record, result)

            # 系统级分析
            self._analyze_system_metrics(record, result)

            # 对称分量分析
            if self.config.analyze_symmetrical_components:
                self._analyze_symmetrical_components(record, result)

            # 计算分析耗时
            end_time = datetime.now()
            result.analysis_duration = (end_time - start_time).total_seconds()

            self.last_analysis_result = result
            logger.info(f"分析完成，耗时: {result.analysis_duration:.2f}秒")

            return result

        except Exception as e:
            logger.error(f"信号分析失败: {e}", exc_info=True)
            # 返回空的分析结果
            from datetime import datetime
            return AnalysisResult(
                timestamp=datetime.now(),
                record_info={'error': str(e)},
                errors=[str(e)]
            )

    def _initialize_analyzers(self, record: ComtradeRecord):
        """初始化分析器"""
        # 计算采样频率
        if len(record.time_axis) > 1:
            sampling_rate = 1.0 / (record.time_axis[1] - record.time_axis[0])
        else:
            sampling_rate = 1000.0  # 默认采样率

        # 初始化特征提取器
        self.feature_extractor = FeatureExtractor(
            sampling_rate=sampling_rate,
            nominal_frequency=record.frequency
        )

        # 初始化故障检测器
        fault_config = self.config.fault_config or FaultDetectionConfig()
        self.fault_detector = FaultDetector(fault_config)

    def _extract_all_features(self, record: ComtradeRecord) -> Dict[str, SignalFeatures]:
        """提取所有通道特征"""
        logger.info("开始特征提取...")

        # 提取模拟通道特征
        features = self.feature_extractor.extract_batch_features(record.analog_channels)

        # TODO: 如果需要，也可以提取数字通道的特征

        logger.info(f"特征提取完成，处理了 {len(features)} 个通道")
        return features

    def _detect_faults(self, record: ComtradeRecord) -> List:
        """检测故障事件"""
        logger.info("开始故障检测...")

        fault_events = self.fault_detector.detect_faults(record)

        logger.info(f"故障检测完成，检测到 {len(fault_events)} 个故障事件")
        return fault_events

    def _analyze_power_quality(self, record: ComtradeRecord, result: AnalysisResult):
        """分析电能质量"""
        # TODO: 实现电能质量分析
        logger.info("开始电能质量分析...")

        # 查找电压和电流通道
        voltage_channels = [ch for ch in record.analog_channels
                            if any(kw in ch.name.upper() for kw in ['V', 'VOLT', 'U'])]
        current_channels = [ch for ch in record.analog_channels
                            if any(kw in ch.name.upper() for kw in ['I', 'CURR', 'A'])]

        # 计算电压RMS
        for channel in voltage_channels:
            if len(channel.data) > 0:
                rms_value = calculate_rms(channel.data)
                result.voltage_rms[channel.name] = rms_value

        # 计算电流RMS
        for channel in current_channels:
            if len(channel.data) > 0:
                rms_value = calculate_rms(channel.data)
                result.current_rms[channel.name] = rms_value

        # TODO: 计算功率因数、THD等指标
        result.power_factor = 0.95  # 占位符

        logger.info("电能质量分析完成")

    def _analyze_system_metrics(self, record: ComtradeRecord, result: AnalysisResult):
        """分析系统级指标"""
        logger.info("开始系统指标分析...")

        # 系统频率分析
        result.system_frequency = self._estimate_system_frequency(record)

        # 三相不平衡度分析
        result.system_unbalance = self._calculate_unbalance(record)

        logger.info("系统指标分析完成")

    def _analyze_symmetrical_components(self, record: ComtradeRecord, result: AnalysisResult):
        """分析对称分量"""
        # TODO: 实现对称分量分析
        logger.info("开始对称分量分析...")

        # 查找三相电压/电流通道
        phases = {'A': [], 'B': [], 'C': []}

        for channel in record.analog_channels:
            phase = self._identify_phase(channel.name)
            if phase in phases:
                phases[phase].append(channel)

        # 检查是否有完整的三相数据
        if all(len(channels) > 0 for channels in phases.values()):
            # TODO: 计算正序、负序、零序分量
            pass

        logger.info("对称分量分析完成")

    def _estimate_system_frequency(self, record: ComtradeRecord) -> float:
        """估计系统频率"""
        # 选择一个主要的电压通道进行频率分析
        voltage_channels = [ch for ch in record.analog_channels
                            if any(kw in ch.name.upper() for kw in ['V', 'VOLT', 'U'])]

        if not voltage_channels:
            return record.frequency  # 返回标称频率

        main_channel = voltage_channels[0]

        # 使用FFT估计频率
        try:
            from utils.math_utils import estimate_frequency_fft
            if len(record.time_axis) > 1:
                sampling_rate = 1.0 / (record.time_axis[1] - record.time_axis[0])
                estimated_freq = estimate_frequency_fft(main_channel.data, sampling_rate)
                return float(estimated_freq)
        except Exception as e:
            logger.warning(f"频率估计失败: {e}")

        return record.frequency

    def _calculate_unbalance(self, record: ComtradeRecord) -> float:
        """计算三相不平衡度"""
        # 查找三相电压通道
        voltage_channels = [ch for ch in record.analog_channels
                            if any(kw in ch.name.upper() for kw in ['V', 'VOLT', 'U'])]

        if len(voltage_channels) < 3:
            return 0.0

        # 按相别分组
        phases = {'A': [], 'B': [], 'C': []}
        for channel in voltage_channels:
            phase = self._identify_phase(channel.name)
            if phase in phases:
                phases[phase].append(channel)

        # 检查是否有完整的三相数据
        if not all(len(channels) > 0 for channels in phases.values()):
            return 0.0

        try:
            # 计算各相RMS值
            rms_a = calculate_rms(phases['A'][0].data)
            rms_b = calculate_rms(phases['B'][0].data)
            rms_c = calculate_rms(phases['C'][0].data)

            # 计算不平衡度
            avg_rms = (rms_a + rms_b + rms_c) / 3
            if avg_rms > 0:
                max_deviation = max(
                    abs(rms_a - avg_rms),
                    abs(rms_b - avg_rms),
                    abs(rms_c - avg_rms)
                )
                unbalance = (max_deviation / avg_rms) * 100
                return float(unbalance)

        except Exception as e:
            logger.warning(f"不平衡度计算失败: {e}")

        return 0.0

    def _identify_phase(self, channel_name: str) -> str:
        """识别通道相别"""
        name_upper = channel_name.upper()

        if 'A' in name_upper and 'B' not in name_upper and 'C' not in name_upper:
            return 'A'
        elif 'B' in name_upper:
            return 'B'
        elif 'C' in name_upper:
            return 'C'

        return ''

    def analyze_channel_correlation(self, record: ComtradeRecord) -> Dict[str, Dict[str, float]]:
        """
        分析通道间相关性

        Args:
            record: COMTRADE记录

        Returns:
            相关性矩阵
        """
        # TODO: 实现通道相关性分析
        logger.info("开始通道相关性分析...")

        correlation_matrix = {}
        analog_channels = record.analog_channels

        for i, ch1 in enumerate(analog_channels):
            correlation_matrix[ch1.name] = {}
            for j, ch2 in enumerate(analog_channels):
                if i == j:
                    correlation_matrix[ch1.name][ch2.name] = 1.0
                else:
                    # 计算皮尔逊相关系数
                    try:
                        corr_coef = np.corrcoef(ch1.data, ch2.data)[0, 1]
                        if np.isnan(corr_coef):
                            corr_coef = 0.0
                        correlation_matrix[ch1.name][ch2.name] = float(corr_coef)
                    except:
                        correlation_matrix[ch1.name][ch2.name] = 0.0

        logger.info("通道相关性分析完成")
        return correlation_matrix

    def perform_spectral_analysis(self, channel: ChannelInfo,
                                  record: ComtradeRecord) -> Dict[str, Any]:
        """
        执行频谱分析

        Args:
            channel: 通道信息
            record: COMTRADE记录

        Returns:
            频谱分析结果
        """
        # TODO: 实现详细的频谱分析
        logger.info(f"开始频谱分析: {channel.name}")

        try:
            # 计算采样频率
            if len(record.time_axis) > 1:
                sampling_rate = 1.0 / (record.time_axis[1] - record.time_axis[0])
            else:
                sampling_rate = 1000.0

            # FFT分析
            freqs, magnitudes = fft_analysis(channel.data, sampling_rate)

            # 功率谱密度
            psd_freqs, psd = signal.welch(channel.data, fs=sampling_rate,
                                          window=self.config.fft_window)

            result = {
                'frequencies': freqs.tolist(),
                'magnitudes': magnitudes.tolist(),
                'psd_frequencies': psd_freqs.tolist(),
                'psd': psd.tolist(),
                'dominant_frequency': float(freqs[np.argmax(magnitudes[1:]) + 1]) if len(magnitudes) > 1 else 0.0,
                'frequency_resolution': float(freqs[1] - freqs[0]) if len(freqs) > 1 else 0.0
            }

            logger.info(f"频谱分析完成: {channel.name}")
            return result

        except Exception as e:
            logger.error(f"频谱分析失败 {channel.name}: {e}")
            return {}

    def export_analysis_summary(self, result: AnalysisResult) -> str:
        """
        导出分析摘要

        Args:
            result: 分析结果

        Returns:
            分析摘要文本
        """
        summary = f"COMTRADE信号分析摘要\n"
        summary += f"=" * 40 + "\n\n"

        summary += f"分析时间: {result.timestamp}\n"
        summary += f"分析耗时: {result.analysis_duration:.2f}秒\n\n"

        # 记录信息
        if result.record_info:
            summary += f"记录信息:\n"
            for key, value in result.record_info.items():
                summary += f"  {key}: {value}\n"
            summary += "\n"

        # 故障统计
        if result.fault_events:
            summary += f"故障检测结果:\n"
            summary += f"  检测到故障事件: {len(result.fault_events)}个\n"

            fault_types = {}
            for event in result.fault_events:
                fault_type = event.fault_type.value
                fault_types[fault_type] = fault_types.get(fault_type, 0) + 1

            for fault_type, count in fault_types.items():
                summary += f"    {fault_type}: {count}次\n"
            summary += "\n"

        # 系统指标
        summary += f"系统指标:\n"
        summary += f"  系统频率: {result.system_frequency:.3f}Hz\n"
        summary += f"  三相不平衡度: {result.system_unbalance:.2f}%\n"

        if result.voltage_rms:
            summary += f"  电压RMS:\n"
            for channel, rms in result.voltage_rms.items():
                summary += f"    {channel}: {rms:.3f}V\n"

        return summary