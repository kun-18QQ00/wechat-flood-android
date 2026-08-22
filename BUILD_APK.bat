@echo off
echo ========================================
echo   微信刷屏助手 APK 构建工具
echo ========================================
echo.

echo [1/4] 检查 Python...
python --version
if errorlevel 1 (
    echo 请先安装 Python 3.11: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [2/4] 安装依赖...
pip install buildozer cython==3.0.12

echo [3/4] 构建 APK (需要 30-60 分钟)...
echo 请耐心等待...
buildozer android debug

echo [4/4] 完成！
echo APK 文件在 bin 目录下
explorer bin
pause
