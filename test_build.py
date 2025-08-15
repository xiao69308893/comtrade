#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的打包测试脚本
用于诊断PyInstaller问题
"""

import subprocess
import sys
from pathlib import Path

def test_pyinstaller():
    """测试PyInstaller打包"""
    print("=" * 60)
    print("  PyInstaller 测试")
    print("=" * 60)
    
    # 检查虚拟环境
    venv_path = Path('venv')
    if sys.platform == 'win32':
        pyinstaller_path = venv_path / 'Scripts' / 'pyinstaller.exe'
    else:
        pyinstaller_path = venv_path / 'bin' / 'pyinstaller'
    
    if not pyinstaller_path.exists():
        print(f"❌ PyInstaller not found at: {pyinstaller_path}")
        return False
    
    print(f"✅ PyInstaller found: {pyinstaller_path}")
    
    # 测试简单打包
    print("\n开始简单打包测试...")
    cmd = [
        str(pyinstaller_path),
        '--onefile',
        '--windowed',
        '--name=COMTRADE_Test',
        'main.py'
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        print(f"\n返回码: {result.returncode}")
        
        if result.stdout:
            print("\n标准输出:")
            print(result.stdout[-2000:])  # 显示最后2000字符
        
        if result.stderr:
            print("\n错误输出:")
            print(result.stderr[-2000:])  # 显示最后2000字符
        
        if result.returncode == 0:
            print("\n✅ 打包成功!")
            # 检查输出文件
            exe_path = Path('dist/COMTRADE_Test.exe')
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"📦 文件大小: {size_mb:.2f} MB")
            return True
        else:
            print("\n❌ 打包失败!")
            return False
            
    except subprocess.TimeoutExpired:
        print("\n❌ 打包超时 (5分钟)")
        return False
    except Exception as e:
        print(f"\n❌ 打包出错: {e}")
        return False

if __name__ == '__main__':
    success = test_pyinstaller()
    if success:
        print("\n🎉 测试成功!")
    else:
        print("\n💥 测试失败!")
    
    input("\n按回车键退出...")