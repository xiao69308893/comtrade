#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMTRADE文件读取器
支持读取和解析IEEE C37.111标准的COMTRADE文件
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass

try:
    import comtrade

    COMTRADE_AVAILABLE = True
except ImportError:
    COMTRADE_AVAILABLE = False

from models.data_models import ChannelInfo, ComtradeRecord
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FileInfo:
    """文件信息"""
    cfg_file: str
    dat_file: str
    hdr_file: Optional[str] = None
    inf_file: Optional[str] = None
    file_size: int = 0
    modified_time: datetime = None


class ComtradeReader:
    """COMTRADE文件读取器"""

    def __init__(self):
        self.current_record: Optional[ComtradeRecord] = None
        self.file_info: Optional[FileInfo] = None

        if not COMTRADE_AVAILABLE:
            logger.warning("comtrade库未安装，部分功能可能不可用")

    def load_file(self, file_path: str) -> bool:
        """
        加载COMTRADE文件

        Args:
            file_path: 文件路径，可以是.cfg或.dat文件

        Returns:
            bool: 加载是否成功
        """
        try:
            if not COMTRADE_AVAILABLE:
                raise ImportError("comtrade库未安装")

            # 解析文件路径
            file_info = self._parse_file_paths(file_path)
            if not file_info:
                return False

            # 读取COMTRADE数据
            logger.info(f"正在加载COMTRADE文件: {file_info.cfg_file}")

            # 使用comtrade库读取
            comtrade_data = comtrade.load(file_info.cfg_file)

            # 创建记录对象
            self.current_record = self._create_record(comtrade_data, file_info)
            self.file_info = file_info

            logger.info(f"成功加载COMTRADE文件: {len(self.current_record.analog_channels)}个模拟通道, "
                        f"{len(self.current_record.digital_channels)}个数字通道")

            return True

        except Exception as e:
            logger.error(f"加载COMTRADE文件失败: {e}")
            return False

    def _parse_file_paths(self, file_path: str) -> Optional[FileInfo]:
        """解析文件路径，找到所有相关文件"""
        file_path = Path(file_path)

        if not file_path.exists():
            logger.error(f"文件不存在: {file_path}")
            return None

        # 获取基础文件名（不含扩展名）
        base_name = file_path.stem
        base_dir = file_path.parent

        # 确定CFG和DAT文件路径
        if file_path.suffix.lower() == '.cfg':
            cfg_file = str(file_path)
            dat_file = str(base_dir / f"{base_name}.dat")
        elif file_path.suffix.lower() == '.dat':
            cfg_file = str(base_dir / f"{base_name}.cfg")
            dat_file = str(file_path)
        else:
            # 尝试自动检测
            cfg_file = str(base_dir / f"{base_name}.cfg")
            dat_file = str(base_dir / f"{base_name}.dat")

        # 检查必需文件是否存在
        if not Path(cfg_file).exists():
            logger.error(f"CFG文件不存在: {cfg_file}")
            return None

        if not Path(dat_file).exists():
            logger.error(f"DAT文件不存在: {dat_file}")
            return None

        # 检查可选文件
        hdr_file = str(base_dir / f"{base_name}.hdr")
        inf_file = str(base_dir / f"{base_name}.inf")

        if not Path(hdr_file).exists():
            hdr_file = None
        if not Path(inf_file).exists():
            inf_file = None

        # 获取文件信息
        file_size = Path(cfg_file).stat().st_size + Path(dat_file).stat().st_size
        modified_time = datetime.fromtimestamp(Path(cfg_file).stat().st_mtime)

        return FileInfo(
            cfg_file=cfg_file,
            dat_file=dat_file,
            hdr_file=hdr_file,
            inf_file=inf_file,
            file_size=file_size,
            modified_time=modified_time
        )

    def _create_record(self, comtrade_data, file_info: FileInfo) -> ComtradeRecord:
        """从comtrade数据创建记录对象"""

        # 提取基本信息
        station_name = getattr(comtrade_data, 'station_name', 'Unknown')
        rec_dev_id = getattr(comtrade_data, 'rec_dev_id', 'Unknown')
        rev_year = getattr(comtrade_data, 'rev_year', 1999)

        # 时间信息
        start_timestamp = getattr(comtrade_data, 'start_timestamp', None)
        trigger_timestamp = getattr(comtrade_data, 'trigger_timestamp', None)

        # 采样信息
        sample_rates = getattr(comtrade_data, 'sample_rates', [(1, 1)])
        frequency = getattr(comtrade_data, 'frequency', 50.0)

        # 时间轴
        time_axis = np.array(comtrade_data.time)

        # 处理模拟通道
        analog_channels = []
        if hasattr(comtrade_data, 'analog') and comtrade_data.analog is not None:
            for i, data in enumerate(comtrade_data.analog):
                channel = ChannelInfo(
                    index=i,
                    name=comtrade_data.analog_channel_ids[i] if i < len(
                        comtrade_data.analog_channel_ids) else f'Analog_{i}',
                    phase=getattr(comtrade_data, 'analog_phases', [''])[i] if i < len(
                        getattr(comtrade_data, 'analog_phases', [])) else '',
                    unit=comtrade_data.analog_units[i] if i < len(comtrade_data.analog_units) else '',
                    multiplier=comtrade_data.analog_multiplier[i] if i < len(comtrade_data.analog_multiplier) else 1.0,
                    offset=comtrade_data.analog_offset[i] if i < len(comtrade_data.analog_offset) else 0.0,
                    min_value=getattr(comtrade_data, 'analog_min', [0])[i] if i < len(
                        getattr(comtrade_data, 'analog_min', [])) else 0,
                    max_value=getattr(comtrade_data, 'analog_max', [0])[i] if i < len(
                        getattr(comtrade_data, 'analog_max', [])) else 0,
                    primary=getattr(comtrade_data, 'analog_primary', [1])[i] if i < len(
                        getattr(comtrade_data, 'analog_primary', [])) else 1,
                    secondary=getattr(comtrade_data, 'analog_secondary', [1])[i] if i < len(
                        getattr(comtrade_data, 'analog_secondary', [])) else 1,
                    data=np.array(data)
                )
                analog_channels.append(channel)

        # 处理数字通道
        digital_channels = []
        if hasattr(comtrade_data, 'digital') and comtrade_data.digital is not None:
            for i, data in enumerate(comtrade_data.digital):
                channel = ChannelInfo(
                    index=i,
                    name=comtrade_data.digital_channel_ids[i] if i < len(
                        comtrade_data.digital_channel_ids) else f'Digital_{i}',
                    phase=getattr(comtrade_data, 'digital_phases', [''])[i] if i < len(
                        getattr(comtrade_data, 'digital_phases', [])) else '',
                    unit='',
                    data=np.array(data, dtype=bool)
                )
                digital_channels.append(channel)

        # 创建记录对象
        record = ComtradeRecord(
            station_name=station_name,
            rec_dev_id=rec_dev_id,
            rev_year=rev_year,
            start_timestamp=start_timestamp,
            trigger_timestamp=trigger_timestamp,
            sample_rates=sample_rates,
            frequency=frequency,
            time_axis=time_axis,
            analog_channels=analog_channels,
            digital_channels=digital_channels,
            file_info=file_info
        )

        return record

    def get_channel_data(self, channel_type: str, channel_index: int) -> Optional[np.ndarray]:
        """
        获取指定通道的数据

        Args:
            channel_type: 通道类型 ('analog' 或 'digital')
            channel_index: 通道索引

        Returns:
            通道数据数组，如果失败返回None
        """
        if not self.current_record:
            return None

        try:
            if channel_type == 'analog':
                if 0 <= channel_index < len(self.current_record.analog_channels):
                    return self.current_record.analog_channels[channel_index].data
            elif channel_type == 'digital':
                if 0 <= channel_index < len(self.current_record.digital_channels):
                    return self.current_record.digital_channels[channel_index].data

            return None

        except Exception as e:
            logger.error(f"获取通道数据失败: {e}")
            return None

    def get_time_range(self) -> Tuple[float, float]:
        """获取时间范围"""
        if not self.current_record or len(self.current_record.time_axis) == 0:
            return 0.0, 1.0

        return float(self.current_record.time_axis[0]), float(self.current_record.time_axis[-1])

    def get_data_summary(self) -> Dict[str, Any]:
        """获取数据摘要信息"""
        if not self.current_record:
            return {}

        time_start, time_end = self.get_time_range()
        duration = time_end - time_start

        return {
            '文件路径': self.file_info.cfg_file if self.file_info else '',
            '站点名称': self.current_record.station_name,
            '设备ID': self.current_record.rec_dev_id,
            '开始时间': self.current_record.start_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[
                        :-3] if self.current_record.start_timestamp else '未知',
            '触发时间': self.current_record.trigger_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[
                        :-3] if self.current_record.trigger_timestamp else '未知',
            '记录时长': f"{duration:.4f} 秒",
            '采样频率': f"{self.current_record.frequency} Hz",
            '模拟通道数': len(self.current_record.analog_channels),
            '数字通道数': len(self.current_record.digital_channels),
            '数据点数': len(self.current_record.time_axis),
            '文件大小': f"{self.file_info.file_size / 1024:.2f} KB" if self.file_info else '未知'
        }

    def export_to_csv(self, file_path: str, selected_channels: Dict[str, List[int]] = None) -> bool:
        """
        导出数据到CSV文件

        Args:
            file_path: 输出文件路径
            selected_channels: 选中的通道 {'analog': [0, 1, 2], 'digital': [0, 1]}

        Returns:
            bool: 导出是否成功
        """
        try:
            if not self.current_record:
                return False

            # 准备数据
            data_dict = {'Time': self.current_record.time_axis}

            # 添加模拟通道
            analog_indices = selected_channels.get('analog', []) if selected_channels else range(
                len(self.current_record.analog_channels))
            for i in analog_indices:
                if i < len(self.current_record.analog_channels):
                    channel = self.current_record.analog_channels[i]
                    data_dict[f"{channel.name} ({channel.unit})"] = channel.data

            # 添加数字通道
            digital_indices = selected_channels.get('digital', []) if selected_channels else range(
                len(self.current_record.digital_channels))
            for i in digital_indices:
                if i < len(self.current_record.digital_channels):
                    channel = self.current_record.digital_channels[i]
                    data_dict[channel.name] = channel.data.astype(int)

            # 创建DataFrame并保存
            df = pd.DataFrame(data_dict)
            df.to_csv(file_path, index=False, encoding='utf-8-sig')

            logger.info(f"数据已导出到: {file_path}")
            return True

        except Exception as e:
            logger.error(f"导出CSV失败: {e}")
            return False

    def close(self):
        """关闭当前文件"""
        self.current_record = None
        self.file_info = None
        logger.info("COMTRADE文件已关闭")