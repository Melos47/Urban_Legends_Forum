#!/usr/bin/env python3
"""诊断 app.py 启动问题"""

import sys
import os

print("=" * 60)
print("诊断 app.py 启动问题")
print("=" * 60)

# 1. 检查 Python 版本
print(f"\n✓ Python 版本: {sys.version}")

# 2. 检查必要的包
print("\n检查必要的包...")
required_packages = [
    'flask',
    'flask_cors',
    'flask_sqlalchemy',
    'werkzeug',
    'apscheduler',
    'jwt',
    'dotenv',
]

missing_packages = []
for package in required_packages:
    try:
        __import__(package.replace('_', '.'))
        print(f"  ✓ {package}")
    except ImportError:
        print(f"  ✗ {package} - 缺失!")
        missing_packages.append(package)

if missing_packages:
    print(f"\n❌ 缺失的包: {', '.join(missing_packages)}")
    print(f"\n安装命令:")
    print(f"  pip install {' '.join(missing_packages)}")
else:
    print("\n✓ 所有必要的包都已安装")

# 3. 检查端口占用
print("\n检查端口 5001 是否被占用...")
import subprocess

try:
    result = subprocess.run(
        ['lsof', '-i', ':5001'],
        capture_output=True,
        text=True,
        timeout=5
    )
    
    if result.returncode == 0 and result.stdout.strip():
        print("  ⚠️  端口 5001 正在使用中:")
        print(result.stdout)
        print("\n  解决方案:")
        print("  1. 杀掉占用端口的进程:")
        print("     lsof -ti:5001 | xargs kill -9")
        print("  2. 或使用其他端口:")
        print("     python3 app.py --port 5002")
    else:
        print("  ✓ 端口 5001 可用")
except Exception as e:
    print(f"  ⚠️  无法检查端口: {e}")

# 4. 尝试导入主要模块
print("\n检查主要模块...")
try:
    sys.path.insert(0, os.path.dirname(__file__))
    
    print("  导入 ai_engine...")
    import ai_engine
    print("    ✓ ai_engine")
    
    print("  导入 story_engine...")
    import story_engine
    print("    ✓ story_engine")
    
    print("  导入 scheduler_tasks...")
    import scheduler_tasks
    print("    ✓ scheduler_tasks")
    
    print("  导入 app...")
    import app
    print("    ✓ app")
    
    print("\n✓ 所有模块导入成功")
    
except Exception as e:
    print(f"\n❌ 模块导入失败: {e}")
    import traceback
    traceback.print_exc()

# 5. 检查 .env 文件
print("\n检查 .env 配置文件...")
env_file = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_file):
    print(f"  ✓ .env 文件存在")
    with open(env_file, 'r') as f:
        lines = [l.strip() for l in f.readlines() if l.strip() and not l.startswith('#')]
        print(f"  配置项数量: {len(lines)}")
else:
    print(f"  ⚠️  .env 文件不存在")

# 6. 检查数据库
print("\n检查数据库...")
db_file = os.path.join(os.path.dirname(__file__), 'ai_urban_legends.db')
if os.path.exists(db_file):
    size = os.path.getsize(db_file)
    print(f"  ✓ 数据库文件存在 ({size} bytes)")
else:
    print(f"  ⚠️  数据库文件不存在（首次运行时会自动创建）")

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)
