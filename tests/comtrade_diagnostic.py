#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMTRADE文件诊断工具
用于分析和诊断COMTRADE文件的结构和内容
"""

import os
import sys
import numpy as np
import chardet
from pathlib import Path
from typing import Dict, Any


def analyze_file_encoding(file_path: str) -> str:
    """分析文件编码"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(8192)

        # 检查BOM头
        if raw_data.startswith(b'\xef\xbb\xbf'):
            return 'utf-8-sig'
        elif raw_data.startswith(b'\xff\xfe'):
            return 'utf-16-le'
        elif raw_data.startswith(b'\xfe\xff'):
            return 'utf-16-be'

        # 使用chardet检测
        result = chardet.detect(raw_data)
        return result['encoding'] or 'unknown'

    except Exception as e:
        return f"error: {e}"


def analyze_cfg_file(cfg_path: str) -> Dict[str, Any]:
    """分析CFG文件"""
    result = {
        'exists': False,
        'encoding': None,
        'size': 0,
        'lines': 0,
        'station_name': 'unknown',
        'analog_count': 0,
        'digital_count': 0,
        'frequency': 0,
        'sample_rate': [],
        'first_lines': [],
        'error': None
    }

    try:
        if not os.path.exists(cfg_path):
            result['error'] = 'File not found'
            return result

        result['exists'] = True
        result['size'] = os.path.getsize(cfg_path)
        result['encoding'] = analyze_file_encoding(cfg_path)

        # 尝试读取文件内容
        encodings_to_try = [result['encoding'], 'gbk', 'gb2312', 'utf-8', 'latin-1']
        content = None

        for encoding in encodings_to_try:
            if encoding and encoding != 'unknown':
                try:
                    with open(cfg_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    result['encoding'] = encoding  # 更新为实际成功的编码
                    break
                except:
                    continue

        if content is None:
            result['error'] = 'Could not decode file'
            return result

        lines = [line.strip() for line in content.split('\n') if line.strip()]
        result['lines'] = len(lines)
        result['first_lines'] = lines[:10]  # 前10行

        if len(lines) >= 3:
            # 解析基本信息
            line1_parts = lines[0].split(',')
            result['station_name'] = line1_parts[0] if line1_parts else 'unknown'

            line2_parts = lines[1].split(',')
            if len(line2_parts) >= 2:
                result['analog_count'] = int(line2_parts[1].rstrip('A'))
                if len(line2_parts) >= 3:
                    result['digital_count'] = int(line2_parts[2].rstrip('D'))

            # 查找频率行
            freq_line_idx = 2 + result['analog_count'] + result['digital_count']
            if freq_line_idx < len(lines):
                try:
                    result['frequency'] = float(lines[freq_line_idx])
                except:
                    pass

            # 查找采样率行
            sample_rate_idx = freq_line_idx + 1
            if sample_rate_idx < len(lines):
                try:
                    parts = lines[sample_rate_idx].split(',')
                    if len(parts) >= 2:
                        result['sample_rate'] = [int(parts[0]), int(parts[1])]
                except:
                    pass

    except Exception as e:
        result['error'] = str(e)

    return result


def analyze_dat_file(dat_path: str, total_channels: int = 0) -> Dict[str, Any]:
    """分析DAT文件"""
    result = {
        'exists': False,
        'size': 0,
        'is_binary': False,
        'is_text': False,
        'encoding': None,
        'possible_formats': [],
        'sample_data': [],
        'error': None
    }

    try:
        if not os.path.exists(dat_path):
            result['error'] = 'File not found'
            return result

        result['exists'] = True
        result['size'] = os.path.getsize(dat_path)

        # 读取文件头部
        with open(dat_path, 'rb') as f:
            header = f.read(1024)

        # 判断是否为文本文件
        text_chars = sum(1 for b in header if 32 <= b <= 126 or b in [9, 10, 13])
        text_ratio = text_chars / len(header)

        if text_ratio > 0.7:
            result['is_text'] = True
            result['encoding'] = analyze_file_encoding(dat_path)

            # 尝试读取几行文本
            try:
                with open(dat_path, 'r', encoding=result['encoding'], errors='ignore') as f:
                    lines = [f.readline().strip() for _ in range(5)]
                result['sample_data'] = [line[:100] for line in lines if line]  # 限制长度

                # 分析可能的分隔符
                if result['sample_data']:
                    first_line = result['sample_data'][0]
                    separators = [',', '\t', ' ', ';']
                    for sep in separators:
                        parts = first_line.split(sep)
                        if len(parts) > 5:  # 至少5个字段
                            result['possible_formats'].append(f"Text with '{sep}' separator ({len(parts)} fields)")
            except:
                pass
        else:
            result['is_binary'] = True

            # 分析二进制格式
            for dtype in ['int16', 'int32', 'float32', 'float64']:
                try:
                    data = np.fromfile(dat_path, dtype=dtype, count=100)  # 只读前100个值
                    if len(data) > 0:
                        result['possible_formats'].append(f"Binary {dtype} ({len(data)} values read)")
                except:
                    pass

            # 尝试不同的字节序
            for endian in ['<', '>']:  # 小端，大端
                for dtype in ['i2', 'i4', 'f4', 'f8']:
                    try:
                        full_dtype = endian + dtype
                        data = np.fromfile(dat_path, dtype=full_dtype, count=100)
                        if len(data) > 0:
                            result['possible_formats'].append(f"Binary {full_dtype} ({len(data)} values)")
                    except:
                        pass

    except Exception as e:
        result['error'] = str(e)

    return result


def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python comtrade_diagnostic.py <comtrade_file>")
        print("文件可以是 .cfg 或 .dat")
        return

    input_path = sys.argv[1]
    file_path = Path(input_path)

    if not file_path.exists():
        print(f"错误: 文件不存在 - {input_path}")
        return

    # 确定CFG和DAT文件路径
    if file_path.suffix.lower() == '.cfg':
        cfg_path = str(file_path)
        dat_path = str(file_path.with_suffix('.dat'))
    elif file_path.suffix.lower() == '.dat':
        cfg_path = str(file_path.with_suffix('.cfg'))
        dat_path = str(file_path)
    else:
        base_path = file_path.with_suffix('')
        cfg_path = str(base_path.with_suffix('.cfg'))
        dat_path = str(base_path.with_suffix('.dat'))

    print("COMTRADE文件诊断报告")
    print("=" * 50)
    print(f"输入文件: {input_path}")
    print(f"CFG文件: {cfg_path}")
    print(f"DAT文件: {dat_path}")
    print()

    # 分析CFG文件
    print("CFG文件分析:")
    print("-" * 30)
    cfg_info = analyze_cfg_file(cfg_path)

    if cfg_info['error']:
        print(f"❌ 错误: {cfg_info['error']}")
    else:
        print(f"✅ 文件存在: {cfg_info['exists']}")
        print(f"📁 文件大小: {cfg_info['size']} bytes")
        print(f"🔤 编码格式: {cfg_info['encoding']}")
        print(f"📄 行数: {cfg_info['lines']}")
        print(f"🏢 站点名称: {cfg_info['station_name']}")
        print(f"📊 模拟通道: {cfg_info['analog_count']}")
        print(f"🔢 数字通道: {cfg_info['digital_count']}")
        print(f"⚡ 频率: {cfg_info['frequency']} Hz")
        print(f"📈 采样率: {cfg_info['sample_rate']}")

        if cfg_info['first_lines']:
            print(f"\n前几行内容:")
            for i, line in enumerate(cfg_info['first_lines'][:5], 1):
                print(f"  {i}: {line[:80]}{'...' if len(line) > 80 else ''}")

    print()

    # 分析DAT文件
    print("DAT文件分析:")
    print("-" * 30)
    total_channels = cfg_info.get('analog_count', 0) + cfg_info.get('digital_count', 0)
    dat_info = analyze_dat_file(dat_path, total_channels)

    if dat_info['error']:
        print(f"❌ 错误: {dat_info['error']}")
    else:
        print(f"✅ 文件存在: {dat_info['exists']}")
        print(f"📁 文件大小: {dat_info['size']} bytes")
        print(f"📝 是否文本: {dat_info['is_text']}")
        print(f"🔢 是否二进制: {dat_info['is_binary']}")

        if dat_info['encoding']:
            print(f"🔤 编码格式: {dat_info['encoding']}")

        if dat_info['possible_formats']:
            print(f"🔍 可能的格式:")
            for fmt in dat_info['possible_formats'][:10]:  # 最多显示10个
                print(f"  - {fmt}")

        if dat_info['sample_data']:
            print(f"📋 样本数据:")
            for i, line in enumerate(dat_info['sample_data'][:3], 1):
                print(f"  {i}: {line}")

    print()

    # 给出建议
    print("建议:")
    print("-" * 30)

    if not cfg_info['exists']:
        print("❌ CFG文件不存在，无法进行分析")
    elif not dat_info['exists']:
        print("❌ DAT文件不存在，无法读取数据")
    elif cfg_info['error'] or dat_info['error']:
        print("❌ 文件存在错误，请检查文件完整性")
    else:
        if dat_info['is_text']:
            print("✅ DAT文件是文本格式，尝试文本解析方法")
        elif dat_info['is_binary']:
            print("✅ DAT文件是二进制格式，尝试二进制解析方法")

        expected_cols = total_channels + 2
        print(f"📊 期望数据列数: {expected_cols} (通道数{total_channels} + 序号 + 时间)")

        if dat_info['possible_formats']:
            print("🔧 建议尝试以下格式进行解析:")
            for fmt in dat_info['possible_formats'][:3]:
                print(f"  - {fmt}")


if __name__ == "__main__":
    main()