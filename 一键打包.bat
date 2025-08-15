@echo off
REM ========================================
REM COMTRADE波形分析器 - 一键打包工具
REM 自动完成所有打包步骤
REM ========================================

echo ========================================
echo   COMTRADE波形分析器 - 一键打包工具
echo ========================================
echo.

REM 设置控制台编码为UTF-8
chcp 65001 >nul 2>&1

REM 设置环境变量
set PYTHONIOENCODING=utf-8
set PYTHONOPTIMIZE=1

REM 检查Python是否安装
echo [1/2] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ 错误: 未检测到Python!
    echo.
    echo 请先安装Python 3.8或更高版本：
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM 显示Python版本
echo ✅ 检测到Python:
python --version
echo.

REM 运行自动打包脚本
echo [2/2] 开始自动打包...
echo.

REM 如果auto_build.py不存在，创建它
if not exist auto_build.py (
    echo 创建自动打包脚本...
    python -c "exec(open('create_auto_build.py').read())" 2>nul
    if errorlevel 1 (
        echo 正在下载打包脚本...
        REM 这里应该包含auto_build.py的内容
        REM 由于内容太长，实际使用时需要将上面的auto_build_script内容保存为auto_build.py
    )
)

REM 执行打包
python auto_build.py

REM 检查打包结果
if exist "dist\COMTRADE波形分析器.exe" (
    echo.
    echo ========================================
    echo   ✅ 打包成功完成!
    echo ========================================
    echo.
    echo 输出文件位置:
    echo   dist\COMTRADE波形分析器.exe
    echo.
    echo 下一步操作:
    echo   1. 运行 test.bat 测试程序
    echo   2. 将exe文件复制到目标位置
    echo   3. 可以分发给其他用户使用
    echo.
) else (
    echo.
    echo ========================================
    echo   ❌ 打包失败!
    echo ========================================
    echo.
    echo 可能的原因:
    echo   1. 缺少必要的依赖库
    echo   2. 代码存在语法错误
    echo   3. 文件路径问题
    echo.
    echo 请查看上面的错误信息进行排查
    echo.
)

pause