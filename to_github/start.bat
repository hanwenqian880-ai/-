@echo off
echo ========================================
echo 组会文献管理系统 - 启动脚本
echo ========================================
echo.

:: 检查虚拟环境
if not exist venv (
    echo [错误] 虚拟环境不存在，请先运行 install.bat
    pause
    exit /b 1
)

:: 激活虚拟环境
call venv\Scripts\activate.bat

:: 启动服务器
echo 启动服务器...
echo.
echo 访问地址: http://localhost:8000
echo 局域网访问: http://本机IP:8000
echo 按 Ctrl+C 停止服务器
echo.

python manage.py runserver 0.0.0.0:8000

pause