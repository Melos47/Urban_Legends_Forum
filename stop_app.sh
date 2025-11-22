#!/bin/bash
# 停止Flask应用

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f flask_app.pid ]; then
    PID=$(cat flask_app.pid)
    
    if ps -p $PID > /dev/null 2>&1; then
        echo "正在停止Flask应用 (PID: $PID)..."
        kill $PID
        sleep 2
        
        # 如果进程还在运行，强制结束
        if ps -p $PID > /dev/null 2>&1; then
            echo "强制结束进程..."
            kill -9 $PID
        fi
        
        rm flask_app.pid
        echo "✅ Flask应用已停止"
    else
        echo "⚠️  进程不存在"
        rm flask_app.pid
    fi
else
    # 尝试通过进程名查找并停止
    PIDS=$(pgrep -f "python.*app.py")
    if [ -n "$PIDS" ]; then
        echo "找到运行中的Flask进程，正在停止..."
        pkill -f "python.*app.py"
        sleep 2
        echo "✅ Flask应用已停止"
    else
        echo "⚠️  没有找到运行中的Flask应用"
    fi
fi
