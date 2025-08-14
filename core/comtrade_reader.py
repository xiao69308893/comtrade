#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMTRADE文件读取器（修复编码问题）
支持读取和解析IEEE C37.111标准的COMTRADE文件
"""

import os
import numpy as np
import pandas as pd
import chardet
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

    def detect_file_encoding(self, file_path: str) -> str:
        """
        检测文件编码格式

        Args:
            file_path: 文件路径

        Returns:
            检测到的编码格式
        """
        try:
            # 读取文件的前几KB来检测编码
            with open(file_path, 'rb') as f:
                raw_data = f.read(8192)  # 读取前8KB

            # 使用chardet检测编码
            result = chardet.detect(raw_data)
            detected_encoding = result['encoding']
            confidence = result['confidence']

            logger.info(f"检测到文件编码: {detected_encoding} (置信度: {confidence:.2f})")

            # 如果检测置信度太低，使用常见的中文编码
            if confidence < 0.7:
                # 尝试常见的中文编码
                for encoding in ['gbk', 'gb2312', 'utf-8-sig', 'utf-8', 'latin-1']:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            f.read(1024)  # 尝试读取一部分
                        logger.info(f"使用编码 {encoding} 成功读取文件")
                        return encoding
                    except UnicodeDecodeError:
                        continue

                # 如果都失败了，使用latin-1作为最后的选择
                logger.warning("无法确定文件编码，使用latin-1")
                return 'latin-1'

            return detected_encoding or 'utf-8'

        except Exception as e:
            logger.warning(f"编码检测失败: {e}，使用默认编码gbk")
            return 'gbk'

    def convert_file_encoding(self, source_path: str, target_path: str,
                              source_encoding: str, target_encoding: str = 'utf-8') -> bool:
        """
        转换文件编码格式

        Args:
            source_path: 源文件路径
            target_path: 目标文件路径
            source_encoding: 源编码格式
            target_encoding: 目标编码格式

        Returns:
            转换是否成功
        """
        try:
            with open(source_path, 'r', encoding=source_encoding) as source_file:
                content = source_file.read()

            with open(target_path, 'w', encoding=target_encoding) as target_file:
                target_file.write(content)

            logger.info(f"文件编码转换成功: {source_encoding} -> {target_encoding}")
            return True

        except Exception as e:
            logger.error(f"文件编码转换失败: {e}")
            return False

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

            # 检测CFG文件编码
            cfg_encoding = self.detect_file_encoding(file_info.cfg_file)

            # 如果不是UTF-8编码，创建临时的UTF-8版本
            temp_cfg_file = file_info.cfg_file
            temp_files_created = []

            if cfg_encoding.lower() not in ['utf-8', 'utf-8-sig']:
                temp_cfg_file = file_info.cfg_file + '.tmp_utf8'
                if self.convert_file_encoding(file_info.cfg_file, temp_cfg_file,
                                              cfg_encoding, 'utf-8'):
                    temp_files_created.append(temp_cfg_file)
                    logger.info(f"创建临时UTF-8文件: {temp_cfg_file}")
                else:
                    temp_cfg_file = file_info.cfg_file  # 转换失败，使用原文件

            # 读取COMTRADE数据
            logger.info(f"正在加载COMTRADE文件: {temp_cfg_file}")

            try:
                # 使用comtrade库读取
                comtrade_data = comtrade.load(temp_cfg_file)

                # 创建记录对象
                self.current_record = self._create_record(comtrade_data, file_info)
                self.file_info = file_info

                logger.info(f"成功加载COMTRADE文件: {len(self.current_record.analog_channels)}个模拟通道, "
                            f"{len(self.current_record.digital_channels)}个数字通道")

                return True

            except Exception as e:
                # 如果使用临时文件失败，尝试直接使用原文件
                if temp_cfg_file != file_info.cfg_file:
                    logger.warning(f"使用临时文件失败: {e}，尝试直接读取原文件")
                    comtrade_data = comtrade.load(file_info.cfg_file)
                    self.current_record = self._create_record(comtrade_data, file_info)
                    self.file_info = file_info
                    return True
                else:
                    raise e

            finally:
                # 清理临时文件
                for temp_file in temp_files_created:
                    try:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                            logger.debug(f"删除临时文件: {temp_file}")
                    except Exception as e:
                        logger.warning(f"删除临时文件失败: {e}")

        except Exception as e:
            logger.error(f"加载COMTRADE文件失败: {e}")

            # 如果是编码问题，尝试手动解析CFG文件
            if "codec can't decode" in str(e) or "UnicodeDecodeError" in str(e):
                logger.info("尝试手动解析CFG文件...")
                return self._manual_parse_comtrade(file_path)

            return False

    def _manual_parse_comtrade(self, file_path: str) -> bool:
        """
        手动解析COMTRADE文件（处理编码问题）

        Args:
            file_path: 文件路径

        Returns:
            解析是否成功
        """
        try:
            # 解析文件路径
            file_info = self._parse_file_paths(file_path)
            if not file_info:
                return False

            # 检测编码并读取CFG文件
            cfg_encoding = self.detect_file_encoding(file_info.cfg_file)

            logger.info(f"手动解析CFG文件，使用编码: {cfg_encoding}")

            with open(file_info.cfg_file, 'r', encoding=cfg_encoding) as f:
                cfg_lines = [line.strip() for line in f.readlines()]

            # 解析CFG文件内容
            cfg_data = self._parse_cfg_content(cfg_lines)

            # 读取DAT文件
            dat_data = self._read_dat_file(file_info.dat_file, cfg_data)

            # 创建记录对象
            self.current_record = self._create_manual_record(cfg_data, dat_data, file_info)
            self.file_info = file_info

            logger.info(f"手动解析成功: {len(self.current_record.analog_channels)}个模拟通道, "
                        f"{len(self.current_record.digital_channels)}个数字通道")

            return True

        except Exception as e:
            logger.error(f"手动解析COMTRADE文件失败: {e}")
            return False

    def _parse_cfg_content(self, cfg_lines: List[str]) -> Dict[str, Any]:
        """
        解析CFG文件内容

        Args:
            cfg_lines: CFG文件行列表

        Returns:
            解析后的配置数据
        """
        if len(cfg_lines) < 3:
            raise ValueError("CFG文件格式不正确")

        cfg_data = {}

        # 第一行：站点名称和设备ID
        line1_parts = cfg_lines[0].split(',')
        cfg_data['station_name'] = line1_parts[0].strip() if len(line1_parts) > 0 else 'Unknown'
        cfg_data['rec_dev_id'] = line1_parts[1].strip() if len(line1_parts) > 1 else 'Unknown'
        cfg_data['rev_year'] = int(line1_parts[2]) if len(line1_parts) > 2 and line1_parts[
            2].strip().isdigit() else 1999

        # 第二行：通道数量
        line2_parts = cfg_lines[1].split(',')
        total_channels = int(line2_parts[0])
        cfg_data['analog_count'] = int(line2_parts[1].rstrip('A'))
        cfg_data['digital_count'] = int(line2_parts[2].rstrip('D')) if len(line2_parts) > 2 else 0

        # 解析模拟通道
        analog_channels = []
        for i in range(2, 2 + cfg_data['analog_count']):
            if i < len(cfg_lines):
                channel_parts = cfg_lines[i].split(',')
                if len(channel_parts) >= 6:
                    analog_channels.append({
                        'index': int(channel_parts[0]) - 1,  # 转换为0基索引
                        'name': channel_parts[1].strip(),
                        'phase': channel_parts[2].strip(),
                        'unit': channel_parts[4].strip(),
                        'multiplier': float(channel_parts[5]) if channel_parts[5].strip() else 1.0,
                        'offset': float(channel_parts[6]) if len(channel_parts) > 6 and channel_parts[
                            6].strip() else 0.0
                    })

        cfg_data['analog_channels'] = analog_channels

        # 解析数字通道
        digital_channels = []
        start_idx = 2 + cfg_data['analog_count']
        for i in range(start_idx, start_idx + cfg_data['digital_count']):
            if i < len(cfg_lines):
                channel_parts = cfg_lines[i].split(',')
                if len(channel_parts) >= 2:
                    digital_channels.append({
                        'index': int(channel_parts[0]) - 1,  # 转换为0基索引
                        'name': channel_parts[1].strip(),
                        'phase': channel_parts[2].strip() if len(channel_parts) > 2 else ''
                    })

        cfg_data['digital_channels'] = digital_channels

        # 解析其他参数
        freq_line_idx = 2 + cfg_data['analog_count'] + cfg_data['digital_count']
        if freq_line_idx < len(cfg_lines):
            cfg_data['frequency'] = float(cfg_lines[freq_line_idx]) if cfg_lines[freq_line_idx].strip() else 50.0
        else:
            cfg_data['frequency'] = 50.0

        # 采样率信息
        sample_rate_idx = freq_line_idx + 1
        if sample_rate_idx < len(cfg_lines):
            sample_parts = cfg_lines[sample_rate_idx].split(',')
            cfg_data['sample_rates'] = [(int(sample_parts[0]), int(sample_parts[1]))] if len(sample_parts) >= 2 else [
                (1, 1)]
        else:
            cfg_data['sample_rates'] = [(1, 1)]

        return cfg_data

    def _read_dat_file(self, dat_file: str, cfg_data: Dict[str, Any]) -> np.ndarray:
        """
        读取DAT文件数据

        Args:
            dat_file: DAT文件路径
            cfg_data: CFG配置数据

        Returns:
            数据数组
        """
        try:
            # 尝试以二进制格式读取
            data = np.fromfile(dat_file, dtype=np.int16)

            # 计算每行的数据点数
            total_channels = cfg_data['analog_count'] + cfg_data['digital_count'] + 2  # +2 为采样序号和时间戳

            if len(data) % total_channels == 0:
                # 重整数据形状
                num_samples = len(data) // total_channels
                data = data.reshape(num_samples, total_channels)

                logger.info(f"成功读取DAT文件: {num_samples}个采样点, {total_channels}列数据")
                return data
            else:
                logger.warning("DAT文件数据长度与通道数不匹配，尝试CSV格式读取")

        except Exception as e:
            logger.warning(f"二进制读取DAT文件失败: {e}，尝试文本格式")

        # 尝试以文本格式读取
        try:
            # 检测DAT文件编码
            dat_encoding = self.detect_file_encoding(dat_file)

            # 读取为CSV格式
            data = pd.read_csv(dat_file, header=None, encoding=dat_encoding)
            logger.info(f"以文本格式读取DAT文件: {data.shape}")
            return data.values

        except Exception as e:
            logger.error(f"读取DAT文件失败: {e}")
            raise

    def _create_manual_record(self, cfg_data: Dict[str, Any], dat_data: np.ndarray,
                              file_info: FileInfo) -> ComtradeRecord:
        """
        从手动解析的数据创建记录对象

        Args:
            cfg_data: CFG配置数据
            dat_data: DAT数据
            file_info: 文件信息

        Returns:
            COMTRADE记录对象
        """
        # 提取时间轴（通常在第二列）
        if dat_data.shape[1] > 1:
            time_axis = dat_data[:, 1].astype(float) / 1000000.0  # 微秒转秒
        else:
            # 如果没有时间列，根据采样率生成
            sample_rate = cfg_data['sample_rates'][0][0] if cfg_data['sample_rates'] else 1
            time_axis = np.arange(len(dat_data)) / sample_rate

        # 创建模拟通道
        analog_channels = []
        data_col_offset = 2  # 跳过序号和时间戳列

        for i, ch_config in enumerate(cfg_data['analog_channels']):
            if data_col_offset + i < dat_data.shape[1]:
                raw_data = dat_data[:, data_col_offset + i].astype(float)
                # 应用缩放和偏移
                scaled_data = raw_data * ch_config['multiplier'] + ch_config['offset']

                channel = ChannelInfo(
                    index=ch_config['index'],
                    name=ch_config['name'],
                    phase=ch_config['phase'],
                    unit=ch_config['unit'],
                    multiplier=ch_config['multiplier'],
                    offset=ch_config['offset'],
                    data=scaled_data
                )
                analog_channels.append(channel)

        # 创建数字通道
        digital_channels = []
        digital_col_offset = data_col_offset + len(cfg_data['analog_channels'])

        for i, ch_config in enumerate(cfg_data['digital_channels']):
            if digital_col_offset + i < dat_data.shape[1]:
                digital_data = dat_data[:, digital_col_offset + i].astype(bool)

                channel = ChannelInfo(
                    index=ch_config['index'],
                    name=ch_config['name'],
                    phase=ch_config['phase'],
                    unit='',
                    data=digital_data
                )
                digital_channels.append(channel)

        # 创建记录对象
        record = ComtradeRecord(
            station_name=cfg_data['station_name'],
            rec_dev_id=cfg_data['rec_dev_id'],
            rev_year=cfg_data['rev_year'],
            start_timestamp=None,  # 手动解析时暂时不提取时间戳
            trigger_timestamp=None,
            sample_rates=cfg_data['sample_rates'],
            frequency=cfg_data['frequency'],
            time_axis=time_axis,
            analog_channels=analog_channels,
            digital_channels=digital_channels,
            file_info=file_info
        )

        return record

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