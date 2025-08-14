#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数学工具函数
提供信号处理和数学计算相关的工具函数
"""

import numpy as np
import scipy.signal as signal
import scipy.fft as fft
from typing import Tuple, List, Optional, Union
from scipy.signal import butter, filtfilt, hilbert


def calculate_rms(data: np.ndarray) -> float:
    """
    计算信号的RMS值

    Args:
        data: 输入信号

    Returns:
        RMS值
    """
    if len(data) == 0:
        return 0.0
    return float(np.sqrt(np.mean(data ** 2)))


def calculate_peak_to_peak(data: np.ndarray) -> float:
    """
    计算峰峰值

    Args:
        data: 输入信号

    Returns:
        峰峰值
    """
    if len(data) == 0:
        return 0.0
    return float(np.max(data) - np.min(data))


def calculate_crest_factor(data: np.ndarray) -> float:
    """
    计算波峰因子（峰值/RMS值）

    Args:
        data: 输入信号

    Returns:
        波峰因子
    """
    rms_val = calculate_rms(data)
    if rms_val == 0:
        return 0.0
    peak_val = np.max(np.abs(data))
    return float(peak_val / rms_val)


def calculate_form_factor(data: np.ndarray) -> float:
    """
    计算波形因子（RMS值/平均值）

    Args:
        data: 输入信号

    Returns:
        波形因子
    """
    mean_val = np.mean(np.abs(data))
    if mean_val == 0:
        return 0.0
    rms_val = calculate_rms(data)
    return float(rms_val / mean_val)


def find_zero_crossings(data: np.ndarray) -> np.ndarray:
    """
    查找信号的过零点

    Args:
        data: 输入信号

    Returns:
        过零点的索引数组
    """
    if len(data) < 2:
        return np.array([])

    # 查找符号变化的点
    sign_changes = np.diff(np.sign(data))
    zero_crossings = np.where(sign_changes != 0)[0]

    return zero_crossings


def butter_filter(data: np.ndarray, cutoff: Union[float, List[float]],
                  fs: float, order: int = 5,
                  filter_type: str = 'low') -> np.ndarray:
    """
    Butterworth数字滤波器

    Args:
        data: 输入信号
        cutoff: 截止频率（Hz），对于带通/带阻滤波器使用[low, high]
        fs: 采样频率（Hz）
        order: 滤波器阶数
        filter_type: 滤波器类型 ('low', 'high', 'band', 'bandstop')

    Returns:
        滤波后的信号
    """
    nyquist = fs / 2

    if isinstance(cutoff, (list, tuple)):
        normal_cutoff = [c / nyquist for c in cutoff]
    else:
        normal_cutoff = cutoff / nyquist

    # 设计滤波器
    b, a = butter(order, normal_cutoff, btype=filter_type, analog=False)

    # 应用滤波器（双向滤波，零相位）
    filtered_data = filtfilt(b, a, data)

    return filtered_data


def moving_average(data: np.ndarray, window_size: int) -> np.ndarray:
    """
    移动平均滤波

    Args:
        data: 输入信号
        window_size: 窗口大小

    Returns:
        滤波后的信号
    """
    if window_size <= 1 or window_size > len(data):
        return data.copy()

    # 使用卷积实现移动平均
    kernel = np.ones(window_size) / window_size

    # 边缘处理：使用 'same' 模式保持输出长度与输入相同
    smoothed = np.convolve(data, kernel, mode='same')

    return smoothed


def calculate_thd(harmonics: dict, fundamental_magnitude: float) -> float:
    """
    计算总谐波畸变率（THD）

    Args:
        harmonics: 谐波字典 {order: (magnitude, phase)}
        fundamental_magnitude: 基波幅值

    Returns:
        THD百分比
    """
    if fundamental_magnitude == 0:
        return 0.0

    # 计算谐波功率和（排除基波）
    harmonic_power_sum = 0
    for order, (magnitude, _) in harmonics.items():
        if order > 1:  # 排除基波
            harmonic_power_sum += magnitude ** 2

    # THD = sqrt(sum of harmonic powers) / fundamental
    thd = np.sqrt(harmonic_power_sum) / fundamental_magnitude * 100

    return float(thd)


def calculate_snr(signal_data: np.ndarray, noise_data: np.ndarray) -> float:
    """
    计算信噪比（SNR）

    Args:
        signal_data: 信号数据
        noise_data: 噪声数据

    Returns:
        SNR（dB）
    """
    signal_power = np.mean(signal_data ** 2)
    noise_power = np.mean(noise_data ** 2)

    if noise_power == 0:
        return float('inf')

    snr_linear = signal_power / noise_power
    snr_db = 10 * np.log10(snr_linear)

    return float(snr_db)


def fft_analysis(data: np.ndarray, fs: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    FFT频谱分析

    Args:
        data: 输入信号
        fs: 采样频率

    Returns:
        频率数组和对应的幅值数组
    """
    # 计算FFT
    fft_data = fft.fft(data)
    freqs = fft.fftfreq(len(data), 1 / fs)

    # 只取正频率部分
    positive_freqs = freqs[:len(freqs) // 2]
    positive_magnitudes = np.abs(fft_data[:len(fft_data) // 2]) * 2 / len(data)

    # DC分量不需要乘以2
    if len(positive_magnitudes) > 0:
        positive_magnitudes[0] /= 2

    return positive_freqs, positive_magnitudes


def window_function(data: np.ndarray, window_type: str = 'hann') -> np.ndarray:
    """
    应用窗函数

    Args:
        data: 输入信号
        window_type: 窗函数类型 ('hann', 'hamming', 'blackman', 'kaiser')

    Returns:
        加窗后的信号
    """
    N = len(data)

    if window_type == 'hann':
        window = signal.windows.hann(N)
    elif window_type == 'hamming':
        window = signal.windows.hamming(N)
    elif window_type == 'blackman':
        window = signal.windows.blackman(N)
    elif window_type == 'kaiser':
        window = signal.windows.kaiser(N, beta=8.6)
    else:
        window = np.ones(N)  # 矩形窗

    return data * window


def resample_signal(data: np.ndarray, original_fs: float,
                    target_fs: float) -> np.ndarray:
    """
    信号重采样

    Args:
        data: 原始信号
        original_fs: 原始采样频率
        target_fs: 目标采样频率

    Returns:
        重采样后的信号
    """
    if original_fs == target_fs:
        return data.copy()

    # 计算重采样比例
    ratio = target_fs / original_fs
    new_length = int(len(data) * ratio)

    # 使用scipy的resample函数
    resampled_data = signal.resample(data, new_length)

    return resampled_data


def detect_peaks(data: np.ndarray, height: Optional[float] = None,
                 distance: Optional[int] = None,
                 prominence: Optional[float] = None) -> Tuple[np.ndarray, dict]:
    """
    峰值检测

    Args:
        data: 输入信号
        height: 最小峰值高度
        distance: 峰值间最小距离
        prominence: 最小峰值突出度

    Returns:
        峰值位置和属性字典
    """
    peaks, properties = signal.find_peaks(
        data,
        height=height,
        distance=distance,
        prominence=prominence
    )

    return peaks, properties


def calculate_phase_difference(signal1: np.ndarray, signal2: np.ndarray,
                               fs: float) -> float:
    """
    计算两个信号间的相位差

    Args:
        signal1: 信号1
        signal2: 信号2
        fs: 采样频率

    Returns:
        相位差（度）
    """
    # 使用希尔伯特变换获取解析信号
    analytic1 = hilbert(signal1)
    analytic2 = hilbert(signal2)

    # 计算瞬时相位
    phase1 = np.angle(analytic1)
    phase2 = np.angle(analytic2)

    # 计算相位差（取平均值）
    phase_diff = np.mean(phase1 - phase2)

    # 转换为度并规范到[-180, 180]
    phase_diff_deg = np.rad2deg(phase_diff)
    phase_diff_deg = ((phase_diff_deg + 180) % 360) - 180

    return float(phase_diff_deg)


def calculate_envelope(data: np.ndarray) -> np.ndarray:
    """
    计算信号包络

    Args:
        data: 输入信号

    Returns:
        信号包络
    """
    # 使用希尔伯特变换
    analytic_signal = hilbert(data)
    envelope = np.abs(analytic_signal)

    return envelope


def remove_dc_component(data: np.ndarray) -> np.ndarray:
    """
    去除直流分量

    Args:
        data: 输入信号

    Returns:
        去除直流分量后的信号
    """
    return data - np.mean(data)


def normalize_signal(data: np.ndarray, method: str = 'minmax') -> np.ndarray:
    """
    信号归一化

    Args:
        data: 输入信号
        method: 归一化方法 ('minmax', 'zscore', 'unit')

    Returns:
        归一化后的信号
    """
    if method == 'minmax':
        # 最小-最大归一化 [0, 1]
        min_val = np.min(data)
        max_val = np.max(data)
        if max_val != min_val:
            return (data - min_val) / (max_val - min_val)
        else:
            return np.zeros_like(data)

    elif method == 'zscore':
        # Z-score标准化（均值为0，标准差为1）
        mean_val = np.mean(data)
        std_val = np.std(data)
        if std_val != 0:
            return (data - mean_val) / std_val
        else:
            return data - mean_val

    elif method == 'unit':
        # 单位向量归一化
        norm = np.linalg.norm(data)
        if norm != 0:
            return data / norm
        else:
            return np.zeros_like(data)

    else:
        return data.copy()


def sliding_window_analysis(data: np.ndarray, window_size: int,
                            step_size: int, analysis_func) -> list:
    """
    滑动窗口分析

    Args:
        data: 输入信号
        window_size: 窗口大小
        step_size: 步长
        analysis_func: 分析函数

    Returns:
        分析结果列表
    """
    results = []

    for start in range(0, len(data) - window_size + 1, step_size):
        window_data = data[start:start + window_size]
        result = analysis_func(window_data)
        results.append(result)

    return results


def calculate_correlation(signal1: np.ndarray, signal2: np.ndarray,
                          mode: str = 'full') -> np.ndarray:
    """
    计算两个信号的互相关

    Args:
        signal1: 信号1
        signal2: 信号2
        mode: 相关模式 ('full', 'valid', 'same')

    Returns:
        互相关结果
    """
    correlation = np.correlate(signal1, signal2, mode=mode)
    return correlation


def estimate_frequency_fft(data: np.ndarray, fs: float) -> float:
    """
    使用FFT估计信号主频率

    Args:
        data: 输入信号
        fs: 采样频率

    Returns:
        估计的频率（Hz）
    """
    # 应用窗函数减少频谱泄漏
    windowed_data = window_function(data, 'hann')

    # FFT分析
    freqs, magnitudes = fft_analysis(windowed_data, fs)

    # 找到最大幅值对应的频率（排除DC分量）
    if len(magnitudes) > 1:
        max_idx = np.argmax(magnitudes[1:]) + 1  # 排除DC分量
        dominant_frequency = freqs[max_idx]
    else:
        dominant_frequency = 0.0

    return float(dominant_frequency)


def bandpass_filter(data: np.ndarray, low_freq: float, high_freq: float,
                    fs: float, order: int = 5) -> np.ndarray:
    """
    带通滤波器

    Args:
        data: 输入信号
        low_freq: 低截止频率
        high_freq: 高截止频率
        fs: 采样频率
        order: 滤波器阶数

    Returns:
        滤波后的信号
    """
    return butter_filter(data, [low_freq, high_freq], fs, order, 'band')


def highpass_filter(data: np.ndarray, cutoff_freq: float,
                    fs: float, order: int = 5) -> np.ndarray:
    """
    高通滤波器

    Args:
        data: 输入信号
        cutoff_freq: 截止频率
        fs: 采样频率
        order: 滤波器阶数

    Returns:
        滤波后的信号
    """
    return butter_filter(data, cutoff_freq, fs, order, 'high')


def lowpass_filter(data: np.ndarray, cutoff_freq: float,
                   fs: float, order: int = 5) -> np.ndarray:
    """
    低通滤波器

    Args:
        data: 输入信号
        cutoff_freq: 截止频率
        fs: 采样频率
        order: 滤波器阶数

    Returns:
        滤波后的信号
    """
    return butter_filter(data, cutoff_freq, fs, order, 'low')


def energy_calculation(data: np.ndarray) -> float:
    """
    计算信号能量

    Args:
        data: 输入信号

    Returns:
        信号能量
    """
    return float(np.sum(data ** 2))


def power_calculation(data: np.ndarray) -> float:
    """
    计算信号功率（平均能量）

    Args:
        data: 输入信号

    Returns:
        信号功率
    """
    return float(np.mean(data ** 2))