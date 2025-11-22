#!/usr/bin/env python3
"""测试证据生成和显示的完整流程"""

from app import app, db, Story, Comment, Evidence
import os
import json

def test_evidence_flow():
    with app.app_context():
        print("\n" + "="*80)
        print("🔍 证据生成与显示测试")
        print("="*80)
        
        # 1. 检查数据库中的证据
        print("\n1️⃣ 数据库中的证据:")
        evidences = Evidence.query.all()
        print(f"   总共 {len(evidences)} 个证据记录")
        
        for e in evidences[:5]:  # 只显示前5个
            story = db.session.get(Story, e.story_id)
            file_exists = os.path.exists(f".{e.file_path}")
            print(f"\n   故事 #{e.story_id}: {story.title[:30]}...")
            print(f"   - 证据ID: {e.id}")
            print(f"   - 路径: {e.file_path}")
            print(f"   - 文件存在: {'✅' if file_exists else '❌'}")
        
        # 2. 测试 API 返回
        print("\n2️⃣ 测试 API 返回 (帖子 #11):")
        with app.test_client() as client:
            resp = client.get('/api/stories/11')
            data = resp.get_json()
            
            print(f"   HTTP状态: {resp.status_code}")
            print(f"   故事标题: {data.get('title', 'N/A')}")
            print(f"   证据数量: {len(data.get('evidence', []))}")
            
            if data.get('evidence'):
                print(f"\n   前端将收到的证据:")
                for i, e in enumerate(data['evidence'][:3], 1):
                    print(f"   #{i}: {e.get('file_path')}")
                    print(f"        type: {e.get('type')}")
                    
                    # 测试文件是否可访问
                    file_resp = client.get(e.get('file_path'))
                    print(f"        HTTP访问: {file_resp.status_code} {'✅' if file_resp.status_code == 200 else '❌'}")
        
        # 3. 检查需要生成证据的帖子
        print("\n3️⃣ 需要生成证据的帖子:")
        stories = Story.query.filter_by(is_ai_generated=True).all()
        
        for story in stories:
            user_comments = Comment.query.filter_by(story_id=story.id, is_ai_response=False).all()
            evidences = Evidence.query.filter_by(story_id=story.id).all()
            
            if len(user_comments) >= 2 and len(user_comments) % 2 == 0 and len(evidences) == 0:
                print(f"\n   ⚠️  故事 #{story.id}: {story.title[:30]}...")
                print(f"       评论数: {len(user_comments)} | 证据数: {len(evidences)}")
                print(f"       状态: 应该生成但还未生成")
        
        # 4. 前端显示建议
        print("\n4️⃣ 前端查看步骤:")
        print("   1. 打开浏览器: http://localhost:5002")
        print("   2. 点击帖子 #11 (斗鱼的不寻常仪式)")
        print("   3. 在故事详情页向下滚动")
        print("   4. 应该能看到 '📸 证据' 区域和 3 张图片")
        print("\n   💡 如果看不到:")
        print("   - 按 F12 打开开发者工具")
        print("   - 查看 Console 标签页")
        print("   - 查找 '📸 证据数量' 的日志")
        print("   - 检查 Network 标签页确认图片是否加载")
        
        print("\n" + "="*80)

if __name__ == '__main__':
    test_evidence_flow()
