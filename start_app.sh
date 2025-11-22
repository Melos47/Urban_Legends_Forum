#!/bin/bash
# 启动Flask应用并保持后台运行

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查是否已经在运行
if pgrep -f "python.*app.py" > /dev/null; then
    echo "⚠️  Flask应用已在运行"
    echo "如需重启，请先执行: ./stop_app.sh"
    exit 1
fi

# 激活虚拟环境并启动应用
source .venv/bin/activate

# 使用nohup在后台运行，输出到日志文件
nohup python app.py > flask_app.log 2>&1 &

PID=$!
echo $PID > flask_app.pid

echo "✅ Flask应用已启动"
echo "   进程ID: $PID"
echo "   日志文件: flask_app.log"
echo ""
echo "查看日志: tail -f flask_app.log"
echo "停止应用: ./stop_app.sh"
echo ""
echo "⏰ 每日自动刷新时间: 每天 00:00"
echo "   下次刷新: 明天凌晨"
