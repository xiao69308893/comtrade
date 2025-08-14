#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
特征提取器
从信号中提取时域和频域特征
"""

import numpy as np
import scipy.signal as signal
import scipy.fft as fft
from typing import Dict, List, Optional, Tuple

from models.data_models import ChannelInfo, SignalFeatures
from utils.math_utils import (
    calculate_rms, calculate_peak_to_peak, calculate_crest_factor,
    calculate_form_factor, find_zero_crossings, fft_analysis,
    calculate_thd, window_function, estimate_frequency_fft
)
from utils.logger import get_logger

logger = get_logger(__name__)


class FeatureExtractor:
    """信号特征提取器"""

    def __init__(self, sampling_rate: float, nominal_frequency: float = 50.0):
        """
        初始化特征提取器

        Args:
            sampling_rate: 采样频率
            nominal_frequency: 额定频率
        """
        self.sampling_rate = sampling_rate
        self.nominal_frequency = nominal_frequency
        self.nyquist_frequency = sampling_rate / 2

    def extract_features(self, channel: ChannelInfo) -> SignalFeatures:
        """
        提取通道特征

        Args:
            channel: 通道信息

        Returns:
            信号特征对象
        """
        try:
            data = channel.data
            if len(data) == 0:
                return SignalFeatures()

            # 创建特征对象
            features = SignalFeatures()

            # 提取时域特征
            self._extract_time_domain_features(data, features)

            # 提取频域特征
            self._extract_frequency_domain_features(data, features)

            # 提取谐波特征
            self._extract_harmonic_features(data, features)

            logger.debug(f"通道 {channel.name} 特征提取完成")
            return features

        except Exception as e:
            logger.error(f"特征提取失败 {channel.name}: {e}")
            return SignalFeatures()

    def _extract_time_domain_features(self, data: np.ndarray, features: SignalFeatures):
        """提取时域特征"""
        # 基本统计特征
        features.mean = float(np.mean(data))
        features.std = float(np.std(data))
        features.rms = calculate_rms(data)
        features.peak = float(np.max(np.abs(data)))
        features.peak_to_peak = calculate_peak_to_peak(data)

        # 波形特征
        features.crest_factor = calculate_crest_factor(data)
        features.form_factor = calculate_form_factor(data)

        # 过零点特征
        zero_crossings = find_zero_crossings(data)
        features.zero_crossings = len(zero_crossings)

        # 能量特征
        features.energy = float(np.sum(data ** 2))

    def _extract_frequency_domain_features(self, data: np.ndarray, features: SignalFeatures):
        """提取频域特征"""
        # 应用窗函数
        windowed_data = window_function(data, 'hann')

        # FFT分析
        freqs, magnitudes = fft_analysis(windowed_data, self.sampling_rate)

        if len(freqs) == 0:
            return

        # 主导频率
        features.dominant_frequency = estimate_frequency_fft(windowed_data, self.sampling_rate)

        # 基波分析
        self._extract_fundamental_component(freqs, magnitudes, features)

    def _extract_harmonic_features(self, data: np.ndarray, features: SignalFeatures):
        """提取谐波特征"""
        # TODO: 实现更精确的谐波分析
        # 当前使用简化的方法，后续可以改进为更精确的算法

        # 应用窗函数
        windowed_data = window_function(data, 'hann')

        # FFT分析
        freqs, magnitudes = fft_analysis(windowed_data, self.sampling_rate)

        if len(freqs) == 0:
            return

        # 寻找谐波分量
        harmonics = {}
        fundamental_freq = self.nominal_frequency

        # 分析前20次谐波
        for order in range(1, 21):
            harmonic_freq = fundamental_freq * order

            # 在FFT结果中寻找最接近的频率点
            freq_idx = np.argmin(np.abs(freqs - harmonic_freq))

            if freq_idx < len(magnitudes) and np.abs(freqs[freq_idx] - harmonic_freq) < 2.0:
                magnitude = magnitudes[freq_idx]

                # 计算相位（简化处理）
                phase = 0.0  # TODO: 实现精确的相位计算

                harmonics[order] = (float(magnitude), float(phase))

        features.harmonics = harmonics

        # 计算基波幅值和相位
        if 1 in harmonics:
            features.fundamental_magnitude = harmonics[1][0]
            features.fundamental_phase = harmonics[1][1]

        # 计算THD
        features.thd = calculate_thd(harmonics, features.fundamental_magnitude)

    def _extract_fundamental_component(self, freqs: np.ndarray, magnitudes: np.ndarray,
                                       features: SignalFeatures):
        """提取基波分量"""
        # 寻找基波频率附近的最大分量
        freq_tolerance = 5.0  # Hz
        fundamental_mask = np.abs(freqs - self.nominal_frequency) <= freq_tolerance

        if np.any(fundamental_mask):
            fundamental_indices = np.where(fundamental_mask)[0]
            max_idx = fundamental_indices[np.argmax(magnitudes[fundamental_indices])]

            features.fundamental_magnitude = float(magnitudes[max_idx])
            # TODO: 计算精确的基波相位
            features.fundamental_phase = 0.0

    def extract_batch_features(self, channels: List[ChannelInfo]) -> Dict[str, SignalFeatures]:
        """
        批量提取多个通道的特征

        Args:
            channels: 通道列表

        Returns:
            通道特征字典
        """
        features_dict = {}

        for channel in channels:
            features = self.extract_features(channel)
            features_dict[channel.name] = features

        logger.info(f"批量特征提取完成，处理了 {len(channels)} 个通道")
        return features_dict

    def calculate_power_quality_metrics(self, voltage_channels: List[ChannelInfo],
                                        current_channels: List[ChannelInfo]) -> Dict[str, float]:
        """
        计算电能质量指标

        Args:
            voltage_channels: 电压通道列表
            current_channels: 电流通道列表

        Returns:
            电能质量指标字典
        """
        # TODO: 实现电能质量指标计算
        metrics = {
            'voltage_thd': 0.0,
            'current_thd': 0.0,
            'power_factor': 0.0,
            'frequency_deviation': 0.0,
            'voltage_unbalance': 0.0
        }

        logger.info("电能质量指标计算完成")
        return metrics

    def analyze_symmetrical_components(self, three_phase_channels: List[ChannelInfo]) -> Dict[str, complex]:
        """
        分析对称分量

        Args:
            three_phase_channels: 三相通道列表（必须是3个）

        Returns:
            对称分量字典
        """
        # TODO: 实现对称分量分析
        if len(three_phase_channels) != 3:
            logger.warning("对称分量分析需要3个相通道")
            return {}

        components = {
            'positive_sequence': 0.0 + 0.0j,
            'negative_sequence': 0.0 + 0.0j,
            'zero_sequence': 0.0 + 0.0j
        }

        logger.info("对称分量分析完成")
        return components