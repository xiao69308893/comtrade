# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

# 获取项目根目录
project_root = os.path.abspath('.')

# 收集所有需要的模块
hiddenimports = [
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'matplotlib',
    'matplotlib.backends.backend_qt5agg',
    'matplotlib.figure',
    'matplotlib.pyplot',
    'numpy',
    'pandas',
    'scipy',
    'scipy.signal',
    'scipy.fft',
    'comtrade',
    'chardet',
]

# 收集matplotlib和PyQt6的数据文件
datas = []
datas += collect_data_files('matplotlib', subdir='mpl-data')
datas += collect_data_files('PyQt6')

# 添加项目文件
datas += [
    ('config', 'config'),
    ('assets', 'assets'),
    ('gui', 'gui'),
    ('core', 'core'),
    ('models', 'models'),
    ('analysis', 'analysis'),
    ('utils', 'utils'),
]

# 如果有图标和其他资源文件
if os.path.exists('assets/icons'):
    datas.append(('assets/icons', 'assets/icons'))
if os.path.exists('assets/fonts'):
    datas.append(('assets/fonts', 'assets/fonts'))

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],  # 排除不需要的模块
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='COMTRADE波形分析器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 使用UPX压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/app.ico' if os.path.exists('assets/icons/app.ico') else None,
    version='version_info.txt' if os.path.exists('version_info.txt') else None,
)

# 如果需要创建安装程序，取消下面的注释
coll = COLLECT(
     exe,
     a.binaries,
     a.zipfiles,
     a.datas,
     strip=False,
     upx=True,
     upx_exclude=[],
     name='COMTRADE波形分析器',
 )