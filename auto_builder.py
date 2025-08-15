#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMTRADE波形分析器 - 一键自动打包脚本
自动完成所有打包步骤，生成高性能的exe文件
"""

import os
import sys
import shutil
import subprocess
import time
from pathlib import Path


class AutoBuilder:
    """自动构建器"""

    def __init__(self):
        self.project_root = Path.cwd()
        self.venv_path = self.project_root / 'venv'
        self.dist_path = self.project_root / 'dist'
        self.build_path = self.project_root / 'build'

    def print_header(self, text):
        """打印标题"""
        print("\n" + "=" * 60)
        print(f"  {text}")
        print("=" * 60 + "\n")

    def check_python_version(self):
        """检查Python版本"""
        self.print_header("检查Python版本")
        version = sys.version_info
        print(f"当前Python版本: {version.major}.{version.minor}.{version.micro}")

        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print("❌ 错误: 需要Python 3.8或更高版本!")
            return False
        print("✅ Python版本符合要求")
        return True

    def check_system_requirements(self):
        """检查系统要求"""
        self.print_header("检查系统环境")
        
        # 检查操作系统
        if sys.platform != 'win32':
            print("⚠️ 警告: 此脚本主要为Windows系统设计")
        else:
            print("✅ Windows系统检测通过")
        
        # 检查磁盘空间
        try:
            free_space = shutil.disk_usage(self.project_root).free / (1024**3)
            print(f"📁 可用磁盘空间: {free_space:.2f} GB")
            if free_space < 2:
                print("⚠️ 警告: 磁盘空间不足2GB，可能影响打包")
            else:
                print("✅ 磁盘空间充足")
        except Exception as e:
            print(f"⚠️ 无法检查磁盘空间: {e}")
        
        # 检查主要文件是否存在
        required_files = ['main.py', 'gui', 'core', 'config']
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ 缺少必要文件/目录: {', '.join(missing_files)}")
            return False
        else:
            print("✅ 项目文件检查通过")
        
        return True

    def create_requirements(self):
        """创建requirements.txt文件"""
        self.print_header("创建依赖文件")

        requirements = """PyQt6>=6.5.0
PyQt6-Qt6>=6.5.0
PyQt6-sip>=13.5.1
numpy>=1.24.0
matplotlib>=3.7.0
pandas>=2.0.0
scipy>=1.10.0
comtrade>=0.0.11
chardet>=5.1.0
pyinstaller>=5.13.0
pillow>=9.5.0"""

        with open('requirements.txt', 'w', encoding='utf-8') as f:
            f.write(requirements)
        print("✅ requirements.txt 已创建")

    def setup_virtual_env(self):
        """设置虚拟环境"""
        self.print_header("设置虚拟环境")

        # 创建虚拟环境
        if not self.venv_path.exists():
            print("创建虚拟环境...")
            subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
            print("✅ 虚拟环境创建成功")
        else:
            print("✅ 虚拟环境已存在")

        # 获取pip路径
        if sys.platform == 'win32':
            pip_path = self.venv_path / 'Scripts' / 'pip.exe'
            python_path = self.venv_path / 'Scripts' / 'python.exe'
        else:
            pip_path = self.venv_path / 'bin' / 'pip'
            python_path = self.venv_path / 'bin' / 'python'

        # 升级pip
        print("升级pip...")
        result = subprocess.run([str(python_path), '-m', 'pip', 'install', '--upgrade', 'pip'],
                               capture_output=True, text=True)
        if result.returncode != 0:
            print(f"⚠️ pip升级警告: {result.stderr}")

        # 安装依赖
        print("安装项目依赖...")
        result = subprocess.run([str(pip_path), 'install', '-r', 'requirements.txt'],
                               capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ 依赖安装失败: {result.stderr}")
            raise Exception("依赖安装失败")
        print("✅ 依赖安装完成")

        return python_path

    def create_spec_file(self):
        """创建PyInstaller规格文件"""
        self.print_header("创建打包配置文件")

        spec_content = '''# -*- mode: python ; coding: utf-8 -*-
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
'''

        with open('build.spec', 'w', encoding='utf-8') as f:
            f.write(spec_content)
        print("✅ build.spec 文件已创建")

    def create_runtime_hook(self):
        """创建运行时钩子"""
        self.print_header("创建运行时优化钩子")

        hook_content = '''# -*- coding: utf-8 -*-
"""运行时性能优化钩子"""

import os
import sys

# 优化环境变量
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
os.environ['PYTHONOPTIMIZE'] = '1'
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 设置matplotlib后端
import matplotlib
matplotlib.use('Qt6Agg')

# 禁用numpy警告提升性能
import numpy as np
np.seterr(all='ignore')

# 预加载常用模块减少延迟
import pandas
import scipy.signal
import PyQt6.QtCore
import PyQt6.QtGui
import PyQt6.QtWidgets
'''

        with open('runtime_hook.py', 'w', encoding='utf-8') as f:
            f.write(hook_content)
        print("✅ runtime_hook.py 已创建")

    def clean_old_builds(self):
        """清理旧的构建文件"""
        self.print_header("清理旧的构建文件")

        dirs_to_clean = ['build', 'dist', '__pycache__']

        for dir_name in dirs_to_clean:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"✅ 已删除: {dir_name}/")

    def build_exe(self, python_path):
        """构建exe文件"""
        self.print_header("开始打包程序")

        # 使用虚拟环境中的PyInstaller
        if sys.platform == 'win32':
            pyinstaller_path = self.venv_path / 'Scripts' / 'pyinstaller.exe'
        else:
            pyinstaller_path = self.venv_path / 'bin' / 'pyinstaller'

        # 执行打包命令
        print("正在打包，请稍候...")
        print("这可能需要几分钟时间...")

        result = subprocess.run(
            [str(pyinstaller_path), '--clean', '--noconfirm', 'build.spec'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("✅ 打包成功!")
            return True
        else:
            print("❌ 打包失败!")
            print("错误信息:")
            print(result.stderr)
            return False

    def optimize_exe(self):
        """优化生成的exe文件"""
        self.print_header("优化exe文件")

        exe_path = self.dist_path / 'COMTRADE波形分析器.exe'

        if not exe_path.exists():
            print("❌ 找不到exe文件!")
            return False

        # 获取文件大小
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"📦 文件大小: {size_mb:.2f} MB")

        # 如果有UPX，尝试进一步压缩
        try:
            upx_path = shutil.which('upx')
            if upx_path:
                print("使用UPX进行额外压缩...")
                result = subprocess.run([upx_path, '--best', '--lzma', str(exe_path)],
                                       capture_output=True, text=True)
                if result.returncode == 0:
                    new_size_mb = exe_path.stat().st_size / (1024 * 1024)
                    print(f"📦 压缩后大小: {new_size_mb:.2f} MB")
                    print(f"📦 压缩率: {((size_mb - new_size_mb) / size_mb * 100):.1f}%")
                else:
                    print(f"⚠️ UPX压缩失败: {result.stderr}")
            else:
                print("💡 提示: 安装UPX可以进一步压缩exe文件")
        except Exception as e:
            print(f"⚠️ UPX压缩出错: {e}")

        print("✅ 优化完成")
        return True

    def create_test_script(self):
        """创建测试脚本"""
        self.print_header("创建测试脚本")

        test_content = '''@echo off
chcp 65001 >nul
echo ========================================
echo 测试打包后的程序
echo ========================================
echo.

if not exist "dist\COMTRADE波形分析器.exe" (
    echo ❌ 错误: 找不到exe文件!
    echo 请确保打包成功完成
    pause
    exit /b 1
)

cd dist
echo 启动程序...
start "" "COMTRADE波形分析器.exe"

echo.
echo ✅ 程序已启动，请进行以下测试：
echo 1. 检查界面是否正常显示
echo 2. 测试文件打开功能（可使用tests目录中的示例文件）
echo 3. 测试数据分析功能
echo 4. 检查中文显示是否正常
echo 5. 测试导出功能
echo 6. 检查程序启动速度
echo.
echo 💡 提示: 如果程序无法启动，请检查：
echo    - 是否被杀毒软件拦截
echo    - 是否缺少必要的运行库
echo    - 查看Windows事件日志获取详细错误信息
echo.
pause
'''

        with open('test.bat', 'w', encoding='utf-8') as f:
            f.write(test_content)
        print("✅ test.bat 测试脚本已创建")

    def create_readme(self):
        """创建README文件"""
        self.print_header("创建说明文档")
        
        readme_content = '''# COMTRADE波形分析器 - 打包版本

## 📦 文件说明

- `COMTRADE波形分析器.exe` - 主程序文件
- `test.bat` - 测试脚本
- `README.md` - 本说明文件

## 🚀 使用方法

1. 双击 `COMTRADE波形分析器.exe` 启动程序
2. 或运行 `test.bat` 进行测试

## ⚠️ 注意事项

### 系统要求
- Windows 10/11 (64位)
- 至少 4GB 内存
- 至少 500MB 可用磁盘空间

### 首次运行
- 首次启动可能需要 10-30 秒
- 如果被杀毒软件拦截，请添加信任
- 确保有足够的磁盘空间用于临时文件

### 常见问题

**Q: 程序无法启动？**
A: 检查以下几点：
- 确保系统是Windows 10/11
- 检查杀毒软件是否拦截
- 尝试以管理员身份运行
- 查看Windows事件日志

**Q: 界面显示异常？**
A: 检查以下几点：
- 确保显示缩放设置正常
- 尝试更新显卡驱动
- 检查系统字体是否完整

**Q: 文件打开失败？**
A: 检查以下几点：
- 确保COMTRADE文件格式正确
- 检查文件路径中是否包含特殊字符
- 确保有足够的内存处理大文件

## 📞 技术支持

如遇到问题，请提供以下信息：
- 操作系统版本
- 错误截图或日志
- 操作步骤描述

---

*本程序使用PyInstaller打包，包含所有必要的依赖库*
'''
        
        with open('dist/README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print("✅ README.md 说明文档已创建")

    def run(self):
        """执行完整的打包流程"""
        print("\n" + "🚀" * 30)
        print("  COMTRADE波形分析器 - 自动打包工具")
        print("🚀" * 30)

        try:
            # 1. 检查Python版本
            if not self.check_python_version():
                return False

            # 2. 检查系统环境
            if not self.check_system_requirements():
                return False

            # 3. 检查并创建依赖文件
            if not Path('requirements.txt').exists():
                self.create_requirements()
            else:
                print("✅ requirements.txt 已存在，跳过创建")

            # 4. 设置虚拟环境
            python_path = self.setup_virtual_env()

            # 5. 创建配置文件
            self.create_spec_file()
            self.create_runtime_hook()

            # 6. 清理旧文件
            self.clean_old_builds()

            # 7. 构建exe
            if not self.build_exe(python_path):
                return False

            # 8. 优化exe
            self.optimize_exe()

            # 9. 创建测试脚本和文档
            self.create_test_script()
            self.create_readme()

            # 完成
            self.print_header("🎉 打包完成!")
            exe_path = self.dist_path / 'COMTRADE波形分析器.exe'
            if exe_path.exists():
                file_size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"✅ 输出文件: {exe_path}")
                print(f"📦 文件大小: {file_size_mb:.2f} MB")
                
                # 显示打包统计信息
                print("\n📊 打包统计:")
                dist_files = list(self.dist_path.glob('*'))
                print(f"   - 输出文件数量: {len(dist_files)}")
                print(f"   - 主程序大小: {file_size_mb:.2f} MB")
                
                print("\n🚀 快速开始:")
                print("   1. 运行 test.bat 来测试程序")
                print("   2. 查看 dist/README.md 获取详细说明")
                print("   3. 直接双击 exe 文件启动程序")
                
                print("\n⚠️ 重要提示:")
                print("   • 首次运行可能需要10-30秒启动")
                print("   • 如被杀毒软件拦截，请添加信任")
                print("   • 确保在Windows 10/11系统上运行")
                print("   • 建议在SSD上运行以获得更好性能")
                
                return True
            else:
                print("❌ 未找到输出文件!")
                return False

        except Exception as e:
            print(f"\n❌ 打包过程出错: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    builder = AutoBuilder()
    success = builder.run()

    if success:
        print("\n" + "✅" * 30)
        print("  打包成功！程序已准备就绪")
        print("✅" * 30)
    else:
        print("\n" + "❌" * 30)
        print("  打包失败，请检查错误信息")
        print("❌" * 30)

    input("\n按回车键退出...")