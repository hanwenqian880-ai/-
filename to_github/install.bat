@echo off
echo ========================================
echo 组会文献管理系统 - 安装脚本
echo ========================================
echo.

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [步骤1] 创建虚拟环境...
python -m venv venv
if errorlevel 1 (
    echo [错误] 创建虚拟环境失败
    pause
    exit /b 1
)

echo [步骤2] 激活虚拟环境...
call venv\Scripts\activate.bat

echo [步骤3] 安装依赖...
pip install -r requirements.txt
if errorlevel 1 (
    echo [警告] 部分依赖安装失败，继续尝试...
)

echo [步骤4] 创建必要目录...
if not exist logs mkdir logs
if not exist media\literature mkdir media\literature

echo [步骤5] 初始化数据库...
python manage.py migrate
if errorlevel 1 (
    echo [错误] 数据库初始化失败
    pause
    exit /b 1
)

echo [步骤6] 初始化系统...
python manage.py init_system
if errorlevel 1 (
    echo [警告] 系统初始化可能已完成
)

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 默认管理员账号: admin / admin123
echo 请在首次登录后立即修改密码！
echo.
echo 启动命令:
echo   venv\Scripts\activate
echo   python manage.py runserver 0.0.0.0:8000
echo.
echo 访问地址: http://localhost:8000
echo 局域网访问: http://本机IP:8000
echo.
pause