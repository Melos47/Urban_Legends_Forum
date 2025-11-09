#!/usr/bin/env python3
"""
调试脚本：测试音频生成和LM Studio连接
"""
import os
import sys

print("=" * 60)
print("🔍 诊断测试开始")
print("=" * 60)

# 测试1: 检查音频生成依赖
print("\n【测试1】检查音频生成依赖")
print("-" * 60)

try:
    import numpy as np
    print("✅ numpy 已安装:", np.__version__)
except ImportError as e:
    print("❌ numpy 未安装:", e)

try:
    from scipy.io import wavfile
    from scipy import signal
    print("✅ scipy 已安装")
except ImportError as e:
    print("❌ scipy 未安装:", e)

try:
    from pydub import AudioSegment
    from pydub.generators import Sine
    print("✅ pydub 已安装")
except ImportError as e:
    print("⚠️  pydub 未安装（备用方案）:", e)

# 测试2: 尝试生成音频
print("\n【测试2】尝试生成音频文件")
print("-" * 60)

try:
    from ai_engine import generate_evidence_audio
    
    print("📝 调用 generate_evidence_audio('测试音频生成')...")
    audio_path = generate_evidence_audio("测试音频生成 - 香港都市传说")
    
    if audio_path:
        print(f"✅ 函数返回路径: {audio_path}")
        
        # 检查实际文件
        full_path = f"static{audio_path}" if audio_path.startswith('/') else audio_path
        if os.path.exists(full_path):
            file_size = os.path.getsize(full_path)
            print(f"✅ 文件已创建: {full_path}")
            print(f"   文件大小: {file_size:,} 字节 ({file_size/1024:.1f} KB)")
        else:
            print(f"❌ 文件不存在: {full_path}")
    else:
        print("❌ 函数返回 None")
        
except Exception as e:
    print(f"❌ 音频生成失败: {e}")
    import traceback
    traceback.print_exc()

# 测试3: 检查 LM Studio 连接
print("\n【测试3】检查 LM Studio 连接")
print("-" * 60)

try:
    from dotenv import load_dotenv
    load_dotenv()
    
    lm_studio_url = os.getenv('LM_STUDIO_URL', 'http://localhost:1234/v1')
    print(f"📡 LM Studio URL: {lm_studio_url}")
    
    # 尝试连接
    import requests
    print(f"   尝试连接到 {lm_studio_url}/models ...")
    
    try:
        response = requests.get(
            f"{lm_studio_url}/models",
            timeout=5
        )
        print(f"   响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ LM Studio 服务器在线")
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                print(f"   可用模型数量: {len(data['data'])}")
                for model in data['data'][:3]:  # 只显示前3个
                    print(f"   - {model.get('id', 'unknown')}")
            else:
                print("⚠️  没有加载的模型")
        else:
            print(f"⚠️  服务器响应异常: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到 LM Studio 服务器")
        print(f"   请确认:")
        print(f"   1. LM Studio 是否正在运行？")
        print(f"   2. URL 是否正确？当前: {lm_studio_url}")
        print(f"   3. 如果是远程服务器 (192.168.x.x)，网络是否连通？")
        
    except requests.exceptions.Timeout:
        print("❌ 连接超时")
        print(f"   LM Studio 可能正在启动或响应缓慢")
        
except ImportError as e:
    print(f"❌ 缺少依赖: {e}")
    print("   需要安装: pip install requests python-dotenv")

# 测试4: 测试 AI 响应生成
print("\n【测试4】测试 AI 响应生成")
print("-" * 60)

try:
    from ai_engine import generate_ai_response
    from models import Story, Comment, User
    from app import app, db
    
    with app.app_context():
        # 获取第一个故事和评论进行测试
        story = Story.query.first()
        comment = Comment.query.first()
        
        if story and comment:
            print(f"📖 测试故事: {story.title}")
            print(f"💬 测试评论: {comment.content[:50]}...")
            print(f"🤖 调用 generate_ai_response()...")
            
            response = generate_ai_response(story, comment)
            
            print(f"\n生成的回复:")
            print("-" * 60)
            print(response)
            print("-" * 60)
            
            # 检查是否是模板回复
            if "【楼主回复】" in response and ("刚去现场拍了照" in response or "谢谢" in response):
                print("⚠️  这是模板回复（fallback），不是 LM Studio 生成的")
                print("   原因: LM Studio 连接失败或未配置")
            else:
                print("✅ 这看起来是 AI 生成的回复")
        else:
            print("⚠️  数据库中没有故事或评论，无法测试")
            
except Exception as e:
    print(f"❌ AI 响应测试失败: {e}")
    import traceback
    traceback.print_exc()

# 总结
print("\n" + "=" * 60)
print("📊 诊断总结")
print("=" * 60)

print("""
请根据上面的测试结果进行修复:

【音频问题】
- 如果 scipy 未安装: pip install scipy numpy
- 如果文件未创建但无错误: 检查 static/generated/ 目录权限
- 如果有异常: 查看详细错误信息

【LM Studio 问题】
- 如果连接失败:
  1. 启动 LM Studio 应用
  2. 在 LM Studio 中加载一个模型（推荐 Qwen 或 Llama）
  3. 确保 "Start Server" 已开启
  4. 检查端口是否是 1234
  5. 如果是远程服务器，检查防火墙和网络

- 修改配置:
  编辑 .env 文件，设置:
  LM_STUDIO_URL=http://localhost:1234/v1  # 本地
  # 或
  LM_STUDIO_URL=http://192.168.10.145:1234/v1  # 远程

- 测试连接:
  curl http://localhost:1234/v1/models
  # 应该返回已加载的模型列表
""")

print("=" * 60)
print("🏁 诊断测试完成")
print("=" * 60)
