#!/bin/bash
echo "========================================"
echo "组会文献管理系统 - 启动脚本"
echo "========================================"
echo

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "[错误] 虚拟环境不存在，请先运行 ./install.sh"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 启动服务器
echo "启动服务器..."
echo
echo "访问地址: http://localhost:8000"
echo "局域网访问: http://本机IP:8000"
echo "按 Ctrl+C 停止服务器"
echo

python manage.py runserver 0.0.0.0:8000