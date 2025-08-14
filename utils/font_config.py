# 创建 utils/font_config.py - matplotlib中文字体配置

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
matplotlib中文字体配置模块
解决matplotlib无法显示中文的问题
"""

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform
import warnings
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


def setup_chinese_font():
    """配置matplotlib中文字体"""
    try:
        # 禁用字体警告
        warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

        # 获取系统平台
        system = platform.system()
        logger.info(f"检测到系统: {system}")

        # 首先尝试加载assets目录下的字体
        font_set = _load_custom_fonts()
        
        if not font_set:
            # 根据不同系统选择合适的中文字体
            chinese_fonts = []

            if system == "Windows":
                chinese_fonts = [
                    'Microsoft YaHei',  # 微软雅黑
                    'SimHei',  # 黑体
                    'SimSun',  # 宋体
                    'KaiTi',  # 楷体
                    'FangSong'  # 仿宋
                ]
            elif system == "Darwin":  # macOS
                chinese_fonts = [
                    'PingFang SC',  # 苹方
                    'Heiti SC',  # 黑体
                    'STSong',  # 华文宋体
                    'STKaiti',  # 华文楷体
                    'Arial Unicode MS'  # 包含中文的字体
                ]
            else:  # Linux
                chinese_fonts = [
                    'WenQuanYi Micro Hei',  # 文泉驿微米黑
                    'WenQuanYi Zen Hei',  # 文泉驿正黑
                    'Noto Sans CJK SC',  # Google Noto字体
                    'Source Han Sans CN',  # 思源黑体
                    'DejaVu Sans'  # 默认字体
                ]

            # 尝试设置中文字体
            available_fonts = [f.name for f in fm.fontManager.ttflist]

            for font_name in chinese_fonts:
                if font_name in available_fonts:
                    try:
                        # 设置matplotlib字体
                        plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif']
                        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

                        # 设置全局字体配置
                        matplotlib.rcParams['font.family'] = 'sans-serif'
                        matplotlib.rcParams['font.sans-serif'] = [font_name] + matplotlib.rcParams['font.sans-serif']
                        matplotlib.rcParams['axes.unicode_minus'] = False

                        logger.info(f"成功设置中文字体: {font_name}")
                        font_set = True
                        break
                    except Exception as e:
                        logger.warning(f"设置字体 {font_name} 失败: {e}")
                        continue

        if not font_set:
            logger.warning("未找到合适的中文字体，尝试下载安装")
            # 尝试自动下载并安装中文字体
            if _download_chinese_font():
                # 重新尝试设置字体
                setup_chinese_font()
            else:
                # 使用fallback方案
                _setup_fallback_font()
        else:
            # 验证字体设置
            _verify_font_setup()

    except Exception as e:
        logger.error(f"配置中文字体失败: {e}")
        _setup_fallback_font()


def _load_custom_fonts():
    """加载assets目录下的自定义字体"""
    try:
        # 获取项目根目录
        current_dir = Path(__file__).parent.parent
        assets_fonts_dir = current_dir / 'assets' / 'fonts'
        
        logger.info(f"查找字体目录: {assets_fonts_dir}")
        
        if not assets_fonts_dir.exists():
            logger.warning(f"字体目录不存在: {assets_fonts_dir}")
            return False
            
        # 优先使用的字体文件列表
        priority_fonts = [
            'MicrosoftYaHeiBold.ttc',
            'MicrosoftYaHeiNormal.ttc',
            'STHeitiMedium.ttc',
            'STHeitiLight.ttc'
        ]
        
        # 尝试加载优先字体
        for font_file in priority_fonts:
            font_path = assets_fonts_dir / font_file
            if font_path.exists():
                try:
                    # 添加字体到matplotlib字体管理器
                    fm.fontManager.addfont(str(font_path))
                    
                    # 获取字体属性
                    font_prop = fm.FontProperties(fname=str(font_path))
                    font_name = font_prop.get_name()
                    
                    # 设置matplotlib字体
                    plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif']
                    plt.rcParams['axes.unicode_minus'] = False
                    
                    # 设置全局字体配置
                    matplotlib.rcParams['font.family'] = 'sans-serif'
                    matplotlib.rcParams['font.sans-serif'] = [font_name] + matplotlib.rcParams['font.sans-serif']
                    matplotlib.rcParams['axes.unicode_minus'] = False
                    
                    logger.info(f"成功加载自定义字体: {font_name} (文件: {font_file})")
                    return True
                    
                except Exception as e:
                    logger.warning(f"加载字体文件 {font_file} 失败: {e}")
                    continue
        
        # 如果优先字体都失败，尝试加载目录下的所有字体文件
        font_extensions = ['.ttf', '.ttc', '.otf']
        for font_file in assets_fonts_dir.iterdir():
            if font_file.suffix.lower() in font_extensions and font_file.name not in priority_fonts:
                try:
                    # 添加字体到matplotlib字体管理器
                    fm.fontManager.addfont(str(font_file))
                    
                    # 获取字体属性
                    font_prop = fm.FontProperties(fname=str(font_file))
                    font_name = font_prop.get_name()
                    
                    # 设置matplotlib字体
                    plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif']
                    plt.rcParams['axes.unicode_minus'] = False
                    
                    # 设置全局字体配置
                    matplotlib.rcParams['font.family'] = 'sans-serif'
                    matplotlib.rcParams['font.sans-serif'] = [font_name] + matplotlib.rcParams['font.sans-serif']
                    matplotlib.rcParams['axes.unicode_minus'] = False
                    
                    logger.info(f"成功加载自定义字体: {font_name} (文件: {font_file.name})")
                    return True
                    
                except Exception as e:
                    logger.warning(f"加载字体文件 {font_file.name} 失败: {e}")
                    continue
        
        logger.warning("未找到可用的自定义字体文件")
        return False
        
    except Exception as e:
        logger.error(f"加载自定义字体失败: {e}")
        return False


def _download_chinese_font():
    """下载中文字体（如果需要的话）"""
    try:
        import requests
        import io

        logger.info("尝试下载中文字体...")

        # 使用一个免费的中文字体
        font_url = "https://github.com/adobe-fonts/source-han-sans/raw/release/SubsetOTF/CN/SourceHanSansCN-Regular.otf"

        # 下载字体文件
        response = requests.get(font_url, timeout=30)
        if response.status_code == 200:
            # 保存字体文件到临时目录
            font_dir = Path.home() / '.matplotlib' / 'fonts'
            font_dir.mkdir(parents=True, exist_ok=True)

            font_path = font_dir / 'SourceHanSansCN-Regular.otf'
            with open(font_path, 'wb') as f:
                f.write(response.content)

            # 刷新字体缓存
            fm._rebuild()

            logger.info(f"字体已下载到: {font_path}")
            return True
    except Exception as e:
        logger.warning(f"下载字体失败: {e}")
        return False


def _setup_fallback_font():
    """设置备用字体方案"""
    try:
        logger.info("使用备用字体方案")

        # 尝试使用DejaVu Sans作为基础字体
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Liberation Sans', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False

        # 对于中文文本，使用unicode转义或者拼音替代
        matplotlib.rcParams['font.family'] = 'sans-serif'
        matplotlib.rcParams['axes.unicode_minus'] = False

        logger.info("备用字体方案已设置")

    except Exception as e:
        logger.error(f"设置备用字体失败: {e}")


def _verify_font_setup():
    """验证字体设置是否成功"""
    try:
        # 创建一个测试图形
        fig, ax = plt.subplots(figsize=(1, 1))
        ax.text(0.5, 0.5, '测试中文', ha='center', va='center')

        # 如果没有异常，说明字体设置成功
        plt.close(fig)
        logger.info("中文字体验证成功")
        return True

    except Exception as e:
        logger.warning(f"中文字体验证失败: {e}")
        return False


def get_available_chinese_fonts():
    """获取系统中可用的中文字体列表"""
    try:
        all_fonts = [f.name for f in fm.fontManager.ttflist]

        # 中文字体的常见关键词
        chinese_keywords = [
            'Hei', 'Song', 'Kai', 'Fang', 'Microsoft', 'SimSun', 'SimHei',
            'YaHei', 'PingFang', 'Noto', 'Source Han', 'WenQuanYi'
        ]

        chinese_fonts = []
        for font in all_fonts:
            if any(keyword in font for keyword in chinese_keywords):
                chinese_fonts.append(font)

        logger.info(f"找到 {len(chinese_fonts)} 个中文字体")
        return chinese_fonts

    except Exception as e:
        logger.error(f"获取中文字体列表失败: {e}")
        return []


def create_safe_text(text: str) -> str:
    """创建安全的文本，避免字体问题"""
    if text is None:
        return ""
    return str(text)


# 初始化字体配置
def init_font_config():
    """初始化字体配置"""
    try:
        logger.info("初始化matplotlib中文字体配置...")
        setup_chinese_font()
        logger.info("字体配置完成")
    except Exception as e:
        logger.error(f"字体配置初始化失败: {e}")


# 模块导入时自动执行
if __name__ != "__main__":
    init_font_config()