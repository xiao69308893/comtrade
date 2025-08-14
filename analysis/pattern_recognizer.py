#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模式识别模块
用于识别电力系统中的典型波形模式和故障特征
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from models.data_models import ComtradeRecord, ChannelInfo, FaultEvent, FaultType
from utils.logger import get_logger

logger = get_logger(__name__)


class PatternType(Enum):
    """模式类型枚举"""
    NORMAL_OPERATION = "正常运行"
    FAULT_INITIATION = "故障起始"
    FAULT_CLEARING = "故障清除"
    TRANSIENT_RECOVERY = "暂态恢复"
    OSCILLATION = "振荡"
    CAPACITOR_SWITCHING = "电容器投切"
    TRANSFORMER_ENERGIZING = "变压器励磁"
    MOTOR_STARTING = "电机启动"
    UNKNOWN = "未知模式"


@dataclass
class PatternFeature:
    """模式特征"""
    name: str
    value: float
    weight: float = 1.0
    description: str = ""


@dataclass
class RecognizedPattern:
    """识别出的模式"""
    pattern_type: PatternType
    confidence: float  # 置信度 0-1
    start_time: float
    end_time: float
    features: List[PatternFeature]
    description: str = ""

    @property
    def duration(self) -> float:
        """模式持续时间"""
        return self.end_time - self.start_time


class PatternTemplate:
    """模式模板"""

    def __init__(self, pattern_type: PatternType, features: Dict[str, Tuple[float, float]]):
        """
        初始化模式模板

        Args:
            pattern_type: 模式类型
            features: 特征字典 {feature_name: (min_value, max_value)}
        """
        self.pattern_type = pattern_type
        self.features = features
        self.weight = 1.0

    def match_score(self, input_features: Dict[str, float]) -> float:
        """
        计算匹配分数

        Args:
            input_features: 输入特征

        Returns:
            匹配分数 0-1
        """
        # TODO: 实现更复杂的模式匹配算法
        total_score = 0.0
        matched_features = 0

        for feature_name, (min_val, max_val) in self.features.items():
            if feature_name in input_features:
                value = input_features[feature_name]
                if min_val <= value <= max_val:
                    total_score += 1.0
                else:
                    # 计算偏离度
                    if value < min_val:
                        deviation = (min_val - value) / min_val
                    else:
                        deviation = (value - max_val) / max_val

                    # 偏离越小，分数越高
                    score = max(0.0, 1.0 - deviation)
                    total_score += score

                matched_features += 1

        return total_score / matched_features if matched_features > 0 else 0.0


class PatternRecognizer:
    """模式识别器"""

    def __init__(self):
        """初始化模式识别器"""
        self.templates = self._create_default_templates()
        self.min_confidence = 0.6  # 最小置信度阈值

    def _create_default_templates(self) -> List[PatternTemplate]:
        """创建默认模式模板"""
        templates = []

        # 正常运行模式
        normal_template = PatternTemplate(
            PatternType.NORMAL_OPERATION,
            {
                'rms_stability': (0.95, 1.05),  # RMS稳定性
                'frequency_deviation': (0.0, 1.0),  # 频率偏差
                'thd': (0.0, 5.0),  # 总谐波畸变
                'voltage_variation': (0.0, 0.1)  # 电压变化率
            }
        )
        templates.append(normal_template)

        # 故障起始模式
        fault_init_template = PatternTemplate(
            PatternType.FAULT_INITIATION,
            {
                'current_surge': (2.0, 20.0),  # 电流突增
                'voltage_drop': (0.1, 0.9),  # 电压跌落
                'frequency_change': (0.5, 5.0),  # 频率变化
                'change_rate': (10.0, 1000.0)  # 变化率
            }
        )
        templates.append(fault_init_template)

        # 故障清除模式
        fault_clear_template = PatternTemplate(
            PatternType.FAULT_CLEARING,
            {
                'current_recovery': (0.1, 2.0),  # 电流恢复
                'voltage_recovery': (0.8, 1.2),  # 电压恢复
                'transient_duration': (0.01, 0.5),  # 暂态持续时间
                'oscillation_frequency': (0.5, 10.0)  # 振荡频率
            }
        )
        templates.append(fault_clear_template)

        # 电容器投切模式
        capacitor_template = PatternTemplate(
            PatternType.CAPACITOR_SWITCHING,
            {
                'voltage_step': (0.01, 0.1),  # 电压阶跃
                'transient_frequency': (100.0, 2000.0),  # 暂态频率
                'damping_ratio': (0.1, 0.8),  # 阻尼比
                'duration': (0.001, 0.1)  # 持续时间
            }
        )
        templates.append(capacitor_template)

        # TODO: 添加更多模式模板

        return templates

    def recognize_patterns(self, record: ComtradeRecord) -> List[RecognizedPattern]:
        """
        识别记录中的模式

        Args:
            record: COMTRADE记录

        Returns:
            识别出的模式列表
        """
        try:
            logger.info(f"开始模式识别: {record.station_name}")

            patterns = []

            # 分段分析
            segments = self._segment_signal(record)

            for segment in segments:
                # 提取段特征
                features = self._extract_segment_features(segment, record)

                # 模式匹配
                recognized = self._match_patterns(features, segment)
                if recognized:
                    patterns.append(recognized)

            logger.info(f"模式识别完成，识别出 {len(patterns)} 个模式")
            return patterns

        except Exception as e:
            logger.error(f"模式识别失败: {e}")
            return []

    def _segment_signal(self, record: ComtradeRecord) -> List[Dict[str, Any]]:
        """
        信号分段

        Args:
            record: COMTRADE记录

        Returns:
            信号段列表
        """
        # TODO: 实现智能信号分段算法
        # 当前使用简单的固定时间窗口分段

        segments = []
        window_size = 0.1  # 100ms窗口

        if len(record.time_axis) == 0:
            return segments

        dt = record.time_axis[1] - record.time_axis[0] if len(record.time_axis) > 1 else 0.001
        samples_per_window = int(window_size / dt)

        for i in range(0, len(record.time_axis) - samples_per_window, samples_per_window // 2):
            start_idx = i
            end_idx = min(i + samples_per_window, len(record.time_axis))

            segment = {
                'start_time': record.time_axis[start_idx],
                'end_time': record.time_axis[end_idx - 1],
                'start_idx': start_idx,
                'end_idx': end_idx,
                'data': {}
            }

            # 提取各通道在此段的数据
            for channel in record.analog_channels:
                segment['data'][channel.name] = channel.data[start_idx:end_idx]

            segments.append(segment)

        return segments

    def _extract_segment_features(self, segment: Dict[str, Any],
                                  record: ComtradeRecord) -> Dict[str, float]:
        """
        提取段特征

        Args:
            segment: 信号段
            record: COMTRADE记录

        Returns:
            特征字典
        """
        features = {}

        try:
            # 查找主要的电压和电流通道
            voltage_channels = [ch for ch in record.analog_channels
                                if any(kw in ch.name.upper() for kw in ['V', 'VOLT', 'U'])]
            current_channels = [ch for ch in record.analog_channels
                                if any(kw in ch.name.upper() for kw in ['I', 'CURR', 'A'])]

            # 电压特征
            if voltage_channels:
                v_data = segment['data'].get(voltage_channels[0].name, np.array([]))
                if len(v_data) > 0:
                    features['voltage_rms'] = float(np.sqrt(np.mean(v_data ** 2)))
                    features['voltage_peak'] = float(np.max(np.abs(v_data)))
                    features['voltage_variation'] = float(
                        np.std(v_data) / np.mean(np.abs(v_data)) if np.mean(np.abs(v_data)) > 0 else 0)

            # 电流特征
            if current_channels:
                i_data = segment['data'].get(current_channels[0].name, np.array([]))
                if len(i_data) > 0:
                    features['current_rms'] = float(np.sqrt(np.mean(i_data ** 2)))
                    features['current_peak'] = float(np.max(np.abs(i_data)))

                    # 电流突增检测
                    if len(current_channels) > 0:
                        # 简单的突增检测
                        mean_current = np.mean(np.abs(i_data))
                        max_current = np.max(np.abs(i_data))
                        features['current_surge'] = float(max_current / mean_current if mean_current > 0 else 1.0)

            # 时域特征
            duration = segment['end_time'] - segment['start_time']
            features['duration'] = float(duration)

            # TODO: 添加更多特征
            # - 频域特征
            # - 波形畸变特征
            # - 相位特征

        except Exception as e:
            logger.warning(f"特征提取失败: {e}")

        return features

    def _match_patterns(self, features: Dict[str, float],
                        segment: Dict[str, Any]) -> Optional[RecognizedPattern]:
        """
        模式匹配

        Args:
            features: 特征字典
            segment: 信号段

        Returns:
            识别出的模式，如果没有匹配则返回None
        """
        best_match = None
        best_score = 0.0

        for template in self.templates:
            score = template.match_score(features)

            if score > best_score and score >= self.min_confidence:
                best_score = score
                best_match = template

        if best_match:
            # 创建模式特征列表
            pattern_features = []
            for feature_name, value in features.items():
                pattern_features.append(
                    PatternFeature(
                        name=feature_name,
                        value=value,
                        description=f"{feature_name}: {value:.3f}"
                    )
                )

            # 创建识别结果
            pattern = RecognizedPattern(
                pattern_type=best_match.pattern_type,
                confidence=best_score,
                start_time=segment['start_time'],
                end_time=segment['end_time'],
                features=pattern_features,
                description=f"识别为{best_match.pattern_type.value}，置信度{best_score:.2f}"
            )

            return pattern

        return None

    def classify_fault_type(self, fault_features: Dict[str, float]) -> FaultType:
        """
        基于特征分类故障类型

        Args:
            fault_features: 故障特征

        Returns:
            故障类型
        """
        # TODO: 实现基于机器学习的故障分类
        # 当前使用简单的规则基础方法

        try:
            # 电流水平判断
            current_level = fault_features.get('current_surge', 1.0)

            # 电压水平判断
            voltage_level = fault_features.get('voltage_drop', 0.0)

            # 简单的分类规则
            if current_level > 10.0 and voltage_level > 0.7:
                return FaultType.THREE_PHASE
            elif current_level > 5.0 and voltage_level > 0.5:
                return FaultType.PHASE_TO_PHASE
            elif current_level > 3.0:
                return FaultType.SINGLE_PHASE_GROUND
            elif voltage_level > 0.1:
                return FaultType.VOLTAGE_SAG
            else:
                return FaultType.UNKNOWN

        except Exception as e:
            logger.warning(f"故障分类失败: {e}")
            return FaultType.UNKNOWN

    def detect_oscillations(self, record: ComtradeRecord) -> List[Dict[str, Any]]:
        """
        检测振荡

        Args:
            record: COMTRADE记录

        Returns:
            振荡检测结果列表
        """
        # TODO: 实现振荡检测算法
        oscillations = []

        logger.info("开始振荡检测...")

        # 简单的振荡检测示例
        for channel in record.analog_channels:
            if len(channel.data) > 100:
                # 使用滑动窗口检测周期性变化
                window_size = 50
                for i in range(len(channel.data) - window_size):
                    window_data = channel.data[i:i + window_size]

                    # 检测周期性
                    autocorr = np.correlate(window_data, window_data, mode='full')

                    # TODO: 完善振荡检测逻辑

        logger.info(f"振荡检测完成，检测到 {len(oscillations)} 个振荡")
        return oscillations

    def add_custom_template(self, template: PatternTemplate):
        """
        添加自定义模式模板

        Args:
            template: 模式模板
        """
        self.templates.append(template)
        logger.info(f"添加自定义模式模板: {template.pattern_type.value}")

    def train_from_examples(self, training_data: List[Tuple[Dict[str, float], PatternType]]):
        """
        从示例数据训练模式识别器

        Args:
            training_data: 训练数据列表 [(features, pattern_type), ...]
        """
        # TODO: 实现机器学习训练功能
        logger.info(f"开始训练模式识别器，训练样本数: {len(training_data)}")

        # 这里可以实现各种机器学习算法
        # 如神经网络、SVM、随机森林等

        logger.info("模式识别器训练完成")

    def export_recognition_report(self, patterns: List[RecognizedPattern]) -> str:
        """
        导出识别报告

        Args:
            patterns: 识别出的模式列表

        Returns:
            识别报告文本
        """
        report = "模式识别报告\n"
        report += "=" * 30 + "\n\n"

        if not patterns:
            report += "未识别出任何模式\n"
            return report

        # 统计各种模式
        pattern_counts = {}
        for pattern in patterns:
            pattern_type = pattern.pattern_type.value
            pattern_counts[pattern_type] = pattern_counts.get(pattern_type, 0) + 1

        report += f"识别摘要:\n"
        report += f"总计识别出 {len(patterns)} 个模式\n\n"

        for pattern_type, count in pattern_counts.items():
            report += f"  {pattern_type}: {count} 次\n"

        report += f"\n详细信息:\n"
        report += f"-" * 30 + "\n"

        for i, pattern in enumerate(patterns, 1):
            report += f"{i}. {pattern.pattern_type.value}\n"
            report += f"   时间: {pattern.start_time:.4f}s - {pattern.end_time:.4f}s\n"
            report += f"   置信度: {pattern.confidence:.3f}\n"
            report += f"   描述: {pattern.description}\n\n"

        return report