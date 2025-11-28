#!/usr/bin/env python3
"""强制为帖子生成证据并监控过程"""

from app import app, db, Story, Comment, Evidence, generate_evidence_for_story
import time
import os

def force_generate_for_story(story_id):
    with app.app_context():
        story = db.session.get(Story, story_id)
        if not story:
            print(f"❌ 故事 #{story_id} 不存在")
            return
        
        user_comments = Comment.query.filter_by(story_id=story_id, is_ai_response=False).all()
        evidences = Evidence.query.filter_by(story_id=story_id).all()
        
        print(f"\n📖 故事: {story.title}")
        print(f"   ID: {story_id}")
        print(f"   评论数: {len(user_comments)}")
        print(f"   当前证据数: {len(evidences)}")
        
        if len(evidences) > 0:
            print(f"\n✅ 该故事已有证据:")
            for e in evidences:
                file_exists = os.path.exists(f".{e.file_path}")
                print(f"   - {e.file_path} {'✅' if file_exists else '❌'}")
            return
        
        if len(user_comments) < 2:
            print(f"\n⚠️  评论数不足 ({len(user_comments)} < 2)，无需生成证据")
            return
        
        print(f"\n🎨 开始生成证据...")
        print(f"⏱️  开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        start_time = time.time()
        
        # 调用生成函数
        generate_evidence_for_story(story_id, user_comments[-1].id if user_comments else None)
        
        elapsed = time.time() - start_time
        
        # 检查结果
        new_evidences = Evidence.query.filter_by(story_id=story_id).all()
        
        print(f"\n⏱️  完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  耗时: {elapsed:.1f} 秒")
        print(f"\n📊 生成结果:")
        print(f"   新增证据数: {len(new_evidences) - len(evidences)}")
        
        if len(new_evidences) > len(evidences):
            print(f"\n✅ 成功生成 {len(new_evidences) - len(evidences)} 个证据:")
            for e in new_evidences:
                file_exists = os.path.exists(f".{e.file_path}")
                file_size = os.path.getsize(f".{e.file_path}") if file_exists else 0
                print(f"   - {e.file_path}")
                print(f"     存在: {'✅' if file_exists else '❌'} | 大小: {file_size:,} bytes")
        else:
            print(f"\n❌ 没有生成新证据!检查日志查看错误")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        story_id = int(sys.argv[1])
    else:
        # 默认为帖子 #10
        story_id = 10
    
    force_generate_for_story(story_id)
