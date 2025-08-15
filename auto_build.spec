# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

# 项目根目录
project_root = Path('.').absolute()

# 隐藏导入
hiddenimports = [
    'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets',
    'PyQt6.QtOpenGL', 'PyQt6.QtPrintSupport',
    'matplotlib', 'matplotlib.backends.backend_qt6agg',
    'matplotlib.backends.backend_agg', 'matplotlib.figure',
    'numpy', 'numpy.core', 'numpy.lib', 'numpy.random',
    'pandas', 'pandas.core', 'pandas.io',
    'scipy', 'scipy.signal', 'scipy.fft', 'scipy.optimize',
    'comtrade', 'chardet', 'encodings',
    'pkg_resources.py2_warn'
]

# 数据文件
datas = [
    ('config', 'config'),
    ('gui', 'gui'),
    ('core', 'core'),
    ('models', 'models'),
    ('analysis', 'analysis'),
    ('utils', 'utils'),
]

# 添加资源文件
if (project_root / 'assets').exists():
    datas.append(('assets', 'assets'))

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'] if Path('runtime_hook.py').exists() else [],
    excludes=['tkinter', 'test', 'tests'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 单文件exe配置
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
    upx=True,  # 启用UPX压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/app.ico' if Path('assets/icons/app.ico').exists() else 'assets/icons/app.png' if Path('assets/icons/app.png').exists() else None,
)
