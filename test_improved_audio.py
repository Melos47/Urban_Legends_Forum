#!/usr/bin/env python3
"""测试改进后的音频生成系统 - 验证 LM Studio 集成和多样性"""

import sys
sys.path.insert(0, '/Users/siqi/Documents/PolyU/Sem1/SD5913/FinalCode')

from ai_engine import generate_evidence_audio, generate_audio_description_with_lm_studio
from datetime import datetime

# 测试故事
test_stories = [
    {
        'title': '地铁诡异声音',
        'content': '昨晚我在地铁车厢里听到了奇怪的声音，像是有人在低吟...',
        'comments': '听起来很恐怖 / 我也听到过类似的'
    },
    {
        'title': '午夜敲门声',
        'content': '凌晨3点，传来了敲门声，但没人在外面...',
        'comments': '敲门的声音很规律 / 听起来像心跳'
    },
    {
        'title': '诡异的呻吟',
        'content': '房间里传来很微弱的呻吟声，但我独自一人在家...',
        'comments': '听起来像人的声音 / 让人毛骨悚然'
    },
]

print("【测试改进后的音频生成系统】\n")
print("=" * 70)

for i, story in enumerate(test_stories, 1):
    print(f"\n测试 {i}: {story['title']}")
    print("-" * 70)
    
    # 1. 生成 AI 音频描述
    print("1️⃣  生成 AI 音频描述...")
    ai_description = generate_audio_description_with_lm_studio(
        story['title'],
        story['content'],
        story['comments']
    )
    
    if ai_description:
        print(f"   ✅ AI 描述: {ai_description[:80]}...")
    else:
        print(f"   ⚠️  AI 描述生成失败，使用关键词提取")
    
    # 2. 生成多个音频来测试多样性
    print("\n2️⃣  生成多个音频测试多样性...")
    for j in range(3):
        audio_path = generate_evidence_audio(
            story['title'],
            f"{story['content']}\n\n{story['comments']}"
        )
        
        if audio_path:
            print(f"   ✅ 音频 {j+1}: {audio_path}")
        else:
            print(f"   ❌ 音频 {j+1} 生成失败")
    
    print()

print("=" * 70)
print("\n✅ 测试完成！")
print("\n检查生成的文件:")
print("ls -lh static/generated/eerie_sound_*.wav | tail -10")
