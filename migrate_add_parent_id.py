"""
数据库迁移脚本：为Comment表添加parent_id字段
运行此脚本来更新现有数据库
"""
import sqlite3
import os

def migrate():
    # 尝试多个可能的数据库路径
    possible_paths = [
        'instance/ai_urban_legends.db',
        'ai_urban_legends.db'
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("ℹ️  数据库文件不存在")
        print("💡 这是正常的!首次运行时数据库会自动创建")
        print("📋 请直接运行服务器：./.venv/bin/python app.py")
        print("   服务器启动时会自动创建包含parent_id字段的数据库")
        return
    
    print(f"📂 找到数据库文件: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查parent_id字段是否已存在
        cursor.execute("PRAGMA table_info(comment)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'parent_id' in columns:
            print("✅ parent_id字段已存在，无需迁移")
            return
        
        # 添加parent_id字段
        print("📝 添加parent_id字段到comment表...")
        cursor.execute("""
            ALTER TABLE comment 
            ADD COLUMN parent_id INTEGER 
            REFERENCES comment(id)
        """)
        
        conn.commit()
        print("✅ 数据库迁移完成!")
        print("   - 已添加 comment.parent_id 字段")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    print("🔄 开始数据库迁移...")
    migrate()
