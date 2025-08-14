#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据预处理模块
提供信号预处理、滤波、重采样等功能
"""

import numpy as np
import scipy.signal as signal
from typing import Tuple, Optional, List, Dict, Any

from models.data_models import ComtradeRecord, ChannelInfo
from utils.math_utils import (
    butter_filter, moving_average, remove_dc_component,
    normalize_signal, resample_signal
)
from utils.logger import get_logger

logger = get_logger(__name__)


class DataProcessor:
    """数据预处理器"""

    def __init__(self):
        """初始化数据处理器"""
        self.processing_history = []  # 处理历史记录

    def preprocess_record(self, record: ComtradeRecord,
                          config: Optional[Dict[str, Any]] = None) -> ComtradeRecord:
        """
        预处理COMTRADE记录

        Args:
            record: 原始COMTRADE记录
            config: 预处理配置

        Returns:
            预处理后的记录
        """
        try:
            logger.info(f"开始预处理COMTRADE记录: {record.station_name}")

            # 使用默认配置
            if config is None:
                config = self._get_default_config()

            # 创建记录副本
            processed_record = self._copy_record(record)

            # 预处理模拟通道
            if config.get('process_analog', True):
                self._preprocess_analog_channels(processed_record, config)

            # 预处理数字通道
            if config.get('process_digital', True):
                self._preprocess_digital_channels(processed_record, config)

            # 时间轴预处理
            if config.get('process_time', True):
                self._preprocess_time_axis(processed_record, config)

            logger.info(f"COMTRADE记录预处理完成")
            return processed_record

        except Exception as e:
            logger.error(f"数据预处理失败: {e}")
            return record  # 返回原始记录

    def _preprocess_analog_channels(self, record: ComtradeRecord, config: Dict[str, Any]):
        """预处理模拟通道"""
        for channel in record.analog_channels:
            try:
                # 去除直流分量
                if config.get('remove_dc', True):
                    channel.data = remove_dc_component(channel.data)

                # 滤波处理
                if config.get('apply_filter', False):
                    filter_config = config.get('filter_config', {})
                    channel.data = self._apply_filter(channel.data,
                                                      record.frequency,
                                                      filter_config)

                # 归一化
                if config.get('normalize', False):
                    normalize_method = config.get('normalize_method', 'minmax')
                    channel.data = normalize_signal(channel.data, normalize_method)

                # 重采样
                if config.get('resample', False):
                    target_fs = config.get('target_sampling_rate', record.frequency)
                    if target_fs != record.frequency:
                        original_fs = 1.0 / (record.time_axis[1] - record.time_axis[0])
                        channel.data = resample_signal(channel.data, original_fs, target_fs)

            except Exception as e:
                logger.warning(f"通道 {channel.name} 预处理失败: {e}")

    def _preprocess_digital_channels(self, record: ComtradeRecord, config: Dict[str, Any]):
        """预处理数字通道"""
        # TODO: 实现数字通道预处理
        # 数字通道通常不需要太多预处理，主要是数据清洗和格式转换
        for channel in record.digital_channels:
            try:
                # 确保数据为布尔类型
                if channel.data.dtype != bool:
                    channel.data = channel.data.astype(bool)

                # 去除毛刺（可选）
                if config.get('remove_spikes', False):
                    channel.data = self._remove_digital_spikes(channel.data)

            except Exception as e:
                logger.warning(f"数字通道 {channel.name} 预处理失败: {e}")

    def _preprocess_time_axis(self, record: ComtradeRecord, config: Dict[str, Any]):
        """预处理时间轴"""
        # TODO: 实现时间轴预处理
        # 通常包括时间对齐、重采样等
        pass

    def _apply_filter(self, data: np.ndarray, sampling_freq: float,
                      filter_config: Dict[str, Any]) -> np.ndarray:
        """应用滤波器"""
        filter_type = filter_config.get('type', 'lowpass')
        cutoff_freq = filter_config.get('cutoff', sampling_freq * 0.4)
        order = filter_config.get('order', 5)

        try:
            if filter_type == 'lowpass':
                return butter_filter(data, cutoff_freq, sampling_freq, order, 'low')
            elif filter_type == 'highpass':
                return butter_filter(data, cutoff_freq, sampling_freq, order, 'high')
            elif filter_type == 'bandpass':
                low_freq = filter_config.get('low_freq', cutoff_freq * 0.5)
                high_freq = filter_config.get('high_freq', cutoff_freq)
                return butter_filter(data, [low_freq, high_freq], sampling_freq, order, 'band')
            elif filter_type == 'moving_average':
                window_size = filter_config.get('window_size', 5)
                return moving_average(data, window_size)
            else:
                logger.warning(f"未知的滤波器类型: {filter_type}")
                return data

        except Exception as e:
            logger.error(f"滤波失败: {e}")
            return data

    def _remove_digital_spikes(self, data: np.ndarray) -> np.ndarray:
        """去除数字信号中的毛刺"""
        # TODO: 实现数字信号去毛刺算法
        # 简单的中值滤波
        if len(data) < 3:
            return data

        filtered_data = data.copy()
        for i in range(1, len(data) - 1):
            # 如果当前点与前后点都不同，则认为是毛刺
            if data[i] != data[i - 1] and data[i] != data[i + 1] and data[i - 1] == data[i + 1]:
                filtered_data[i] = data[i - 1]

        return filtered_data

    def _copy_record(self, record: ComtradeRecord) -> ComtradeRecord:
        """创建记录的深拷贝"""
        # 创建新的通道列表
        analog_channels = []
        for channel in record.analog_channels:
            new_channel = ChannelInfo(
                index=channel.index,
                name=channel.name,
                phase=channel.phase,
                unit=channel.unit,
                multiplier=channel.multiplier,
                offset=channel.offset,
                min_value=channel.min_value,
                max_value=channel.max_value,
                primary=channel.primary,
                secondary=channel.secondary,
                data=channel.data.copy()  # 复制数据
            )
            analog_channels.append(new_channel)

        digital_channels = []
        for channel in record.digital_channels:
            new_channel = ChannelInfo(
                index=channel.index,
                name=channel.name,
                phase=channel.phase,
                unit=channel.unit,
                data=channel.data.copy()  # 复制数据
            )
            digital_channels.append(new_channel)

        # 创建新记录
        new_record = ComtradeRecord(
            station_name=record.station_name,
            rec_dev_id=record.rec_dev_id,
            rev_year=record.rev_year,
            start_timestamp=record.start_timestamp,
            trigger_timestamp=record.trigger_timestamp,
            sample_rates=record.sample_rates.copy(),
            frequency=record.frequency,
            time_axis=record.time_axis.copy(),
            analog_channels=analog_channels,
            digital_channels=digital_channels,
            file_info=record.file_info
        )

        return new_record

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认预处理配置"""
        return {
            'process_analog': True,
            'process_digital': True,
            'process_time': False,
            'remove_dc': True,
            'apply_filter': False,
            'normalize': False,
            'resample': False,
            'remove_spikes': False,
            'filter_config': {
                'type': 'lowpass',
                'cutoff': 1000.0,
                'order': 5
            },
            'normalize_method': 'minmax',
            'target_sampling_rate': None
        }

    def detect_anomalies(self, record: ComtradeRecord) -> Dict[str, List[int]]:
        """
        检测数据异常

        Args:
            record: COMTRADE记录

        Returns:
            异常点字典 {channel_name: [anomaly_indices]}
        """
        # TODO: 实现异常检测算法
        anomalies = {}

        for channel in record.analog_channels:
            channel_anomalies = []

            # 简单的统计异常检测
            data = channel.data
            if len(data) > 0:
                mean_val = np.mean(data)
                std_val = np.std(data)

                # 3-sigma规则
                threshold = 3 * std_val
                anomaly_indices = np.where(np.abs(data - mean_val) > threshold)[0]
                channel_anomalies.extend(anomaly_indices.tolist())

            if channel_anomalies:
                anomalies[channel.name] = channel_anomalies

        return anomalies

    def calculate_quality_metrics(self, record: ComtradeRecord) -> Dict[str, Dict[str, float]]:
        """
        计算数据质量指标

        Args:
            record: COMTRADE记录

        Returns:
            质量指标字典
        """
        # TODO: 实现数据质量评估
        quality_metrics = {}

        for channel in record.analog_channels:
            metrics = {
                'completeness': 1.0,  # 数据完整性
                'consistency': 1.0,  # 数据一致性
                'accuracy': 1.0,  # 数据准确性
                'snr': 0.0,  # 信噪比
                'outlier_ratio': 0.0  # 异常值比例
            }

            # 计算简单的质量指标
            data = channel.data
            if len(data) > 0:
                # 检查数据完整性（非NaN值的比例）
                valid_data = ~np.isnan(data) if np.issubdtype(data.dtype, np.floating) else np.ones(len(data),
                                                                                                    dtype=bool)
                metrics['completeness'] = np.sum(valid_data) / len(data)

                # 估算信噪比（简化计算）
                if np.var(data) > 0:
                    signal_power = np.mean(data ** 2)
                    noise_power = np.var(data) * 0.1  # 假设噪声为方差的10%
                    metrics['snr'] = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else 60.0

            quality_metrics[channel.name] = metrics

        return quality_metrics

    def export_preprocessing_report(self, input_record: ComtradeRecord,
                                    output_record: ComtradeRecord) -> str:
        """
        导出预处理报告

        Args:
            input_record: 原始记录
            output_record: 处理后记录

        Returns:
            预处理报告文本
        """
        # TODO: 实现预处理报告生成
        report = "COMTRADE数据预处理报告\n"
        report += "=" * 40 + "\n\n"

        report += f"原始数据:\n"
        report += f"  站点: {input_record.station_name}\n"
        report += f"  持续时间: {input_record.duration:.3f}s\n"
        report += f"  采样点数: {len(input_record.time_axis)}\n"
        report += f"  模拟通道数: {len(input_record.analog_channels)}\n"
        report += f"  数字通道数: {len(input_record.digital_channels)}\n\n"

        report += f"处理后数据:\n"
        report += f"  持续时间: {output_record.duration:.3f}s\n"
        report += f"  采样点数: {len(output_record.time_axis)}\n"
        report += f"  模拟通道数: {len(output_record.analog_channels)}\n"
        report += f"  数字通道数: {len(output_record.digital_channels)}\n\n"

        # TODO: 添加详细的处理步骤和质量指标

        return report