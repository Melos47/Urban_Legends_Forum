#!/usr/bin/env python3
"""快速切换到本地 LM Studio"""
import os

env_file = '.env'
print("🔧 切换到本地 LM Studio...")

# 读取 .env
with open(env_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 更新配置
new_lines = []
for line in lines:
    if line.startswith('LM_STUDIO_URL='):
        new_lines.append('LM_STUDIO_URL=http://localhost:1234/v1\n')
    else:
        new_lines.append(line)

# 写回
with open(env_file, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ 已切换到: http://localhost:1234/v1")
print("\n下一步:")
print("1. 启动 LM Studio 应用")
print("2. 加载一个模型（推荐 Qwen2.5-7B）")
print("3. 点击 'Start Server'")
print("4. 重启 Flask: python app.py")
