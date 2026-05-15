#!/bin/bash
echo "========================================"
echo "组会文献管理系统 - 安装脚本"
echo "========================================"
echo

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python，请先安装Python 3.10+"
    exit 1
fi

echo "[步骤1] 创建虚拟环境..."
python3 -m venv venv

echo "[步骤2] 激活虚拟环境..."
source venv/bin/activate

echo "[步骤3] 安装依赖..."
pip install -r requirements.txt

echo "[步骤4] 创建必要目录..."
mkdir -p logs media/literature

echo "[步骤5] 初始化数据库..."
python manage.py migrate

echo "[步骤6] 初始化系统..."
python manage.py init_system

echo
echo "========================================"
echo "安装完成！"
echo "========================================"
echo
echo "默认管理员账号: admin / admin123"
echo "请在首次登录后立即修改密码！"
echo
echo "启动命令:"
echo "  source venv/bin/activate"
echo "  python manage.py runserver 0.0.0.0:8000"
echo
echo "访问地址: http://localhost:8000"
echo "局域网访问: http://本机IP:8000"
echo