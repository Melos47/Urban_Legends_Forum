#!/usr/bin/env python3
"""手动触发故事生成（用于测试）"""

from app import app, db, Story
from ai_engine import generate_ai_story
from story_engine import initialize_story_state

with app.app_context():
    print("🚀 手动生成新故事...")
    
    story_data = generate_ai_story()
    
    if story_data:
        story = Story(
            title=story_data['title'],
            content=story_data['content'],
            category=story_data['category'],
            location=story_data['location'],
            is_ai_generated=True,
            ai_persona=story_data['ai_persona']
        )
        
        db.session.add(story)
        db.session.flush()
        
        initialize_story_state(story)
        
        db.session.commit()
        
        print(f"✅ 成功生成故事: {story.title}")
        print(f"   ID: {story.id}")
        print(f"   分类: {story.category}")
        print(f"   地点: {story.location}")
        print(f"   作者: {story.ai_persona}")
    else:
        print("❌ 生成故事失败")
