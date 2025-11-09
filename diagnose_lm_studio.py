#!/usr/bin/env python3
"""
LM Studio 连接诊断
"""
import requests
import json

LM_STUDIO_URL = "http://192.168.0.22:1234"

print("=" * 60)
print("🔍 LM Studio 连接诊断")
print("=" * 60)

# 测试1: 检查服务器状态
print("\n【测试1】检查服务器状态")
print(f"URL: {LM_STUDIO_URL}")
try:
    response = requests.get(f"{LM_STUDIO_URL}/v1/models", timeout=5)
    print(f"✅ 状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 可用模型: {len(data['data'])} 个")
        for model in data['data']:
            print(f"   - {model['id']}")
    else:
        print(f"❌ 响应异常: {response.text}")
except Exception as e:
    print(f"❌ 连接失败: {e}")

# 测试2: 测试短文本生成
print("\n【测试2】测试短文本生成")
try:
    payload = {
        "model": "local-model",
        "messages": [{"role": "user", "content": "说一个字"}],
        "max_tokens": 10,
        "temperature": 0.8
    }
    
    print("发送请求...")
    response = requests.post(
        f"{LM_STUDIO_URL}/v1/chat/completions",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=30
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        content = data['choices'][0]['message']['content']
        print(f"✅ 生成成功: {content}")
    elif response.status_code == 503:
        print("❌ 503 Service Unavailable")
        print("可能原因:")
        print("  1. 模型正在加载中")
        print("  2. 服务器资源不足")
        print("  3. 需要在 LM Studio 中重新加载模型")
        print(f"\n响应内容: {response.text}")
    else:
        print(f"❌ 错误: {response.status_code}")
        print(f"响应: {response.text}")
        
except Exception as e:
    print(f"❌ 请求失败: {e}")

# 测试3: 使用 OpenAI 库测试
print("\n【测试3】使用 OpenAI 库测试")
try:
    from openai import OpenAI
    import httpx
    
    client = OpenAI(
        base_url=f"{LM_STUDIO_URL}/v1",
        api_key="lm-studio",
        timeout=httpx.Timeout(60.0, connect=10.0),
        max_retries=0  # 禁用重试，立即看到错误
    )
    
    print("发送请求...")
    response = client.chat.completions.create(
        model="local-model",
        messages=[{"role": "user", "content": "回复：好"}],
        max_tokens=10
    )
    
    print(f"✅ 成功: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"❌ OpenAI 库调用失败: {e}")
    print(f"   错误类型: {type(e).__name__}")

# 测试4: 检查网络延迟
print("\n【测试4】检查网络延迟")
try:
    import time
    start = time.time()
    response = requests.get(f"{LM_STUDIO_URL}/v1/models", timeout=5)
    elapsed = time.time() - start
    print(f"✅ 响应时间: {elapsed:.2f} 秒")
    if elapsed > 2:
        print("⚠️  响应较慢，可能影响生成")
except Exception as e:
    print(f"❌ 测试失败: {e}")

print("\n" + "=" * 60)
print("💡 建议:")
print("=" * 60)
print("""
如果看到 503 错误:
1. 在 LM Studio 中点击 "Unload Model"
2. 等待几秒钟
3. 重新点击 "Load Model"
4. 确保模型完全加载（进度条到 100%）
5. 再次运行此脚本测试

如果一直失败:
1. 尝试重启 LM Studio 应用
2. 检查 LM Studio 是否显示任何错误
3. 尝试加载一个更小的模型（如 3B 或 4B）
""")
print("=" * 60)
