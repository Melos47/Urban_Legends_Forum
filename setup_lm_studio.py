#!/usr/bin/env python3
"""
快速配置脚本：切换 LM Studio 本地/远程
"""
import os

print("=" * 60)
print("⚙️  LM Studio 配置工具")
print("=" * 60)

print("\n请选择 LM Studio 运行方式:")
print("1. 本地运行（推荐）- http://localhost:1234")
print("2. 远程服务器 - http://192.168.10.145:1234")
print("3. 自定义 URL")
print("4. 禁用 LM Studio（使用模板回复）")

choice = input("\n请输入选项 (1-4): ").strip()

if choice == "1":
    url = "http://localhost:1234/v1"
    print(f"\n✅ 设置为本地: {url}")
    
elif choice == "2":
    url = "http://192.168.10.145:1234/v1"
    print(f"\n✅ 设置为远程: {url}")
    print("⚠️  注意：确保远程服务器的 LM Studio 已启动且网络连通")
    
elif choice == "3":
    url = input("\n请输入 LM Studio URL (例如 http://192.168.1.100:1234/v1): ").strip()
    if not url.endswith('/v1'):
        url += '/v1'
    print(f"\n✅ 设置为自定义: {url}")
    
elif choice == "4":
    url = None
    print("\n⚠️  已禁用 LM Studio，将使用模板回复")
    
else:
    print("\n❌ 无效选项，退出")
    exit(1)

# 读取 .env 文件
env_file = '.env'
if not os.path.exists(env_file):
    print(f"\n❌ 找不到 {env_file} 文件")
    exit(1)

with open(env_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 更新配置
new_lines = []
found_url = False
found_use = False

for line in lines:
    if line.startswith('LM_STUDIO_URL='):
        if url:
            new_lines.append(f'LM_STUDIO_URL={url}\n')
        else:
            new_lines.append('# LM_STUDIO_URL=http://localhost:1234/v1\n')
        found_url = True
    elif line.startswith('USE_LM_STUDIO='):
        if url:
            new_lines.append('USE_LM_STUDIO=true\n')
        else:
            new_lines.append('USE_LM_STUDIO=false\n')
        found_use = True
    else:
        new_lines.append(line)

# 如果没找到配置，添加到末尾
if not found_url and url:
    new_lines.append(f'\nLM_STUDIO_URL={url}\n')
if not found_use:
    new_lines.append(f'USE_LM_STUDIO={str(url is not None).lower()}\n')

# 写回文件
with open(env_file, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"\n✅ 配置已保存到 {env_file}")

# 测试连接
if url:
    print("\n🔍 测试连接...")
    import requests
    
    try:
        response = requests.get(f"{url}/models", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                print(f"✅ 连接成功！发现 {len(data['data'])} 个模型")
                for model in data['data']:
                    print(f"   - {model.get('id', 'unknown')}")
            else:
                print("⚠️  连接成功但没有模型")
                print("   请在 LM Studio 中加载一个模型")
        else:
            print(f"⚠️  服务器响应异常: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败：无法连接到服务器")
        print("\n请确保:")
        print("  1. LM Studio 应用正在运行")
        print("  2. 已点击 'Start Server'")
        print("  3. 端口号正确（默认 1234）")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

print("\n" + "=" * 60)
print("📖 接下来的步骤:")
print("=" * 60)

if url:
    print("""
1. 确保 LM Studio 正在运行
2. 在 LM Studio 中加载一个模型（推荐 Qwen2.5-7B）
3. 点击 'Start Server' 启动服务器
4. 重启 Flask 应用:
   python app.py
5. 测试 AI 回复功能
""")
else:
    print("""
当前使用模板回复模式。
如需启用 AI 回复：
1. 重新运行此脚本选择选项 1 或 2
2. 或直接编辑 .env 文件修改 LM_STUDIO_URL
""")

print("=" * 60)
