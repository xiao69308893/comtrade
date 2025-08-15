@echo off
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
