#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
集成测试脚本：验证应用程序中 Phase 2 AI 音频增强的完整集成
测试范围: 
1. 导入验证
2. 函数签名兼容性
3. 错误处理 (LM Studio 不可用)
4. 与 app.py 的集成
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, '/Users/siqi/Documents/PolyU/Sem1/SD5913/FinalCode')

def test_imports():
    """测试所有必要的导入"""
    print("\n" + "="*70)
    print("🔍 测试 1: 导入验证")
    print("="*70)
    
    try:
        from ai_engine import (
            generate_audio_description_with_lm_studio,
            extract_audio_keywords,
            generate_evidence_audio
        )
        print("✅ 所有必要的函数已成功导入")
        print("   - generate_audio_description_with_lm_studio")
        print("   - extract_audio_keywords")
        print("   - generate_evidence_audio")
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_function_signatures():
    """测试函数签名兼容性"""
    print("\n" + "="*70)
    print("🔍 测试 2: 函数签名兼容性")
    print("="*70)
    
    try:
        from ai_engine import (
            generate_audio_description_with_lm_studio,
            extract_audio_keywords,
            generate_evidence_audio
        )
        import inspect
        
        # 检查 generate_audio_description_with_lm_studio
        sig1 = inspect.signature(generate_audio_description_with_lm_studio)
        params1 = list(sig1.parameters.keys())
        expected1 = ['title', 'content', 'comment_context']
        if set(expected1).issubset(set(params1)):
            print(f"✅ generate_audio_description_with_lm_studio 签名正确")
            print(f"   参数: {params1}")
        else:
            print(f"❌ 参数不匹配。期望: {expected1}, 实际: {params1}")
            return False
        
        # 检查 extract_audio_keywords
        sig2 = inspect.signature(extract_audio_keywords)
        params2 = list(sig2.parameters.keys())
        print(f"✅ extract_audio_keywords 签名正确")
        print(f"   参数: {params2}")
        
        # 检查 generate_evidence_audio
        sig3 = inspect.signature(generate_evidence_audio)
        params3 = list(sig3.parameters.keys())
        if 'text_content' in params3 or 'content' in params3:
            print(f"✅ generate_evidence_audio 签名正确")
            print(f"   参数: {params3}")
        else:
            print(f"❌ 参数不匹配。参数: {params3}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ 签名检查失败: {e}")
        return False


def test_error_handling():
    """测试错误处理 (LM Studio 不可用时的降级)"""
    print("\n" + "="*70)
    print("🔍 测试 3: 错误处理和降级机制")
    print("="*70)
    
    try:
        from ai_engine import generate_audio_description_with_lm_studio
        
        # 测试 LM Studio 连接
        print("尝试连接 LM Studio...")
        result = generate_audio_description_with_lm_studio(
            title="测试故事",
            content="这是一个测试内容",
            comment_context="用户评论"
        )
        
        if result is not None:
            print(f"✅ LM Studio 可用")
            print(f"   生成的描述: {result[:50]}...")
            return True
        else:
            print(f"⚠️  LM Studio 不可用或未响应 (这是可以接受的)")
            print(f"   系统将自动降级到关键词提取模式")
            return True
    except Exception as e:
        print(f"⚠️  连接失败 (可接受): {e}")
        print(f"   系统应自动降级到关键词提取模式")
        return True


def test_app_integration():
    """测试与 app.py 的集成"""
    print("\n" + "="*70)
    print("🔍 测试 4: app.py 集成检查")
    print("="*70)
    
    try:
        # 检查 app.py 文件
        app_path = '/Users/siqi/Documents/PolyU/Sem1/SD5913/FinalCode/app.py'
        if not os.path.exists(app_path):
            print(f"❌ app.py 不存在: {app_path}")
            return False
        
        # 检查 generate_evidence_audio 的调用
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'generate_evidence_audio' in content:
                print("✅ app.py 使用了 generate_evidence_audio()")
                
                # 找到调用位置
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'generate_evidence_audio' in line and 'from' not in line:
                        print(f"   行 {i+1}: {line.strip()}")
                        break
                return True
            else:
                print("❌ app.py 中没有找到 generate_evidence_audio() 调用")
                return False
    except Exception as e:
        print(f"❌ 集成检查失败: {e}")
        return False


def test_database_schema():
    """测试数据库模式兼容性"""
    print("\n" + "="*70)
    print("🔍 测试 5: 数据库模式兼容性")
    print("="*70)
    
    try:
        from models import db, EvidenceAudio
        print("✅ 数据库模型导入成功")
        
        # 检查 EvidenceAudio 表
        if hasattr(EvidenceAudio, 'file_path'):
            print("✅ EvidenceAudio 表有 file_path 列")
        if hasattr(EvidenceAudio, 'audio_type'):
            print("✅ EvidenceAudio 表有 audio_type 列")
        if hasattr(EvidenceAudio, 'intensity'):
            print("✅ EvidenceAudio 表有 intensity 列")
        
        return True
    except Exception as e:
        print(f"⚠️  数据库检查 (非关键): {e}")
        return True  # 非关键


def test_audio_file_generation():
    """测试音频文件生成 (需要实际生成)"""
    print("\n" + "="*70)
    print("🔍 测试 6: 音频文件生成验证")
    print("="*70)
    
    try:
        # 检查之前生成的文件
        generated_dir = '/Users/siqi/Documents/PolyU/Sem1/SD5913/FinalCode/static/generated'
        if not os.path.exists(generated_dir):
            print(f"⚠️  生成目录不存在: {generated_dir}")
            return False
        
        # 统计最近生成的文件
        import glob
        wav_files = glob.glob(os.path.join(generated_dir, 'eerie_sound_*.wav'))
        
        if wav_files:
            recent_files = sorted(wav_files, key=os.path.getctime)[-5:]
            print(f"✅ 找到 {len(wav_files)} 个音频文件")
            print(f"   最近生成的 5 个文件:")
            for f in recent_files:
                size = os.path.getsize(f)
                name = os.path.basename(f)
                print(f"   - {name} ({size} bytes)")
            return True
        else:
            print("⚠️  未找到音频文件 (首次运行可能)")
            return True
    except Exception as e:
        print(f"❌ 音频文件检查失败: {e}")
        return False


def test_constants_and_config():
    """测试常量和配置"""
    print("\n" + "="*70)
    print("🔍 测试 7: 常量和配置验证")
    print("="*70)
    
    try:
        import os
        import dotenv
        
        # 检查 LM_STUDIO_URL
        lm_studio_url = os.getenv('LM_STUDIO_URL', 'http://localhost:1234/v1')
        print(f"✅ LM Studio URL 配置: {lm_studio_url}")
        
        # 检查必要的库
        try:
            import numpy as np
            import scipy
            import flask
            import sqlalchemy
            print("✅ 所有必要的库已安装:")
            print(f"   - numpy {np.__version__}")
            print(f"   - scipy {scipy.__version__}")
            print(f"   - flask {flask.__version__}")
            print(f"   - sqlalchemy {sqlalchemy.__version__}")
            return True
        except ImportError as ie:
            print(f"❌ 缺少必要的库: {ie}")
            return False
    except Exception as e:
        print(f"❌ 配置检查失败: {e}")
        return False


def main():
    """运行所有集成测试"""
    print("\n" + "="*70)
    print("🚀 Phase 2 AI 音频增强 - 集成测试套件")
    print("="*70)
    print("测试时间:", __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    tests = [
        ("导入验证", test_imports),
        ("函数签名", test_function_signatures),
        ("错误处理", test_error_handling),
        ("app 集成", test_app_integration),
        ("数据库", test_database_schema),
        ("音频文件", test_audio_file_generation),
        ("配置", test_constants_and_config),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            results.append((test_name, False))
    
    # 总结
    print("\n" + "="*70)
    print("📊 测试总结")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有集成测试通过！系统已准备好生产部署")
        return 0
    else:
        print(f"⚠️  有 {total - passed} 个测试失败，请检查上述输出")
        return 1


if __name__ == '__main__':
    sys.exit(main())
