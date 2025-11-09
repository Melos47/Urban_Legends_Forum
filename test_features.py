#!/usr/bin/env python3
"""
测试三个功能：
1. 通知系统
2. 证据生成后显示
3. 定时生成故事
"""

from app import app, db, Story, Comment, Evidence, Notification, User
from datetime import datetime

def test_features():
    with app.app_context():
        print("=" * 60)
        print("🧪 功能测试报告")
        print("=" * 60)
        
        # 测试1: 检查通知系统
        print("\n【测试1】通知系统")
        notifications = Notification.query.all()
        print(f"  📊 总通知数: {len(notifications)}")
        unread = Notification.query.filter_by(is_read=False).all()
        print(f"  📬 未读通知: {len(unread)}")
        if unread:
            for n in unread[:3]:
                print(f"    - {n.content} (用户ID: {n.user_id})")
        
        # 测试2: 检查证据生成
        print("\n【测试2】证据系统")
        all_evidence = Evidence.query.all()
        print(f"  📊 总证据数: {len(all_evidence)}")
        
        audio_evidence = Evidence.query.filter_by(evidence_type='audio').all()
        image_evidence = Evidence.query.filter_by(evidence_type='image').all()
        print(f"  🔊 音频证据: {len(audio_evidence)}")
        print(f"  📸 图片证据: {len(image_evidence)}")
        
        # 检查每个故事的证据
        stories_with_evidence = Story.query.join(Evidence).distinct().all()
        print(f"  📚 有证据的故事: {len(stories_with_evidence)}")
        
        for story in stories_with_evidence:
            evidence_count = Evidence.query.filter_by(story_id=story.id).count()
            comments_count = Comment.query.filter_by(story_id=story.id).count()
            print(f"    - 故事#{story.id}: {comments_count}条评论, {evidence_count}个证据")
        
        # 测试3: 检查故事生成
        print("\n【测试3】故事生成")
        all_stories = Story.query.order_by(Story.created_at.desc()).all()
        print(f"  📊 总故事数: {len(all_stories)}")
        
        ai_stories = Story.query.filter_by(is_ai_generated=True).all()
        print(f"  🤖 AI生成故事: {len(ai_stories)}")
        
        if all_stories:
            latest = all_stories[0]
            time_diff = datetime.utcnow() - latest.created_at
            minutes_ago = int(time_diff.total_seconds() / 60)
            print(f"  ⏱️  最新故事: {minutes_ago}分钟前")
            print(f"    标题: {latest.title[:30]}...")
        
        # 检查用户
        print("\n【测试4】用户系统")
        users = User.query.all()
        print(f"  👥 总用户数: {len(users)}")
        for user in users:
            comment_count = Comment.query.filter_by(user_id=user.id).count()
            print(f"    - {user.username}: {comment_count}条评论")
        
        print("\n" + "=" * 60)
        print("✅ 测试完成！")
        print("=" * 60)
        
        # 诊断建议
        print("\n📋 诊断建议:")
        if len(unread) == 0:
            print("  ⚠️  没有未读通知 - 可能需要发表评论触发通知")
        if len(audio_evidence) == 0:
            print("  ⚠️  没有音频证据 - 需要在同一故事上发表>=2条评论")
        if minutes_ago > 10:
            print(f"  ⚠️  最新故事已有{minutes_ago}分钟 - 定时器可能未工作")
        
        print("\n💡 提示:")
        print("  1. 通知需要用户登录后才能看到")
        print("  2. 音频证据在同一故事评论数>=2时生成")
        print("  3. 新故事每6分钟自动生成一次")

if __name__ == '__main__':
    test_features()
