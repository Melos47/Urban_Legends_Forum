from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
import jwt
import os
import json
import threading
import time
import random
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-horror')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ai_urban_legends.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app, resources={r"/api/*": {"origins": "*"}})
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    avatar = db.Column(db.String(200), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.relationship('Comment', backref='author', lazy=True)
    
class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='urban')
    location = db.Column(db.String(100))
    is_ai_generated = db.Column(db.Boolean, default=False)
    ai_persona = db.Column(db.String(100))
    current_state = db.Column(db.String(50), default='init')
    state_data = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    views = db.Column(db.Integer, default=0)
    comments = db.relationship('Comment', backref='story', lazy=True, cascade='all, delete-orphan')
    evidence = db.relationship('Evidence', backref='story', lazy=True, cascade='all, delete-orphan')
    
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)  # 回复的评论ID
    is_ai_response = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    parent = db.relationship('Comment', remote_side=[id], backref='replies')
    
class Evidence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    evidence_type = db.Column(db.String(20))
    file_path = db.Column(db.String(500))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'story_id', name='_user_story_uc'),)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    notification_type = db.Column(db.String(50), nullable=False) # e.g., 'new_reply', 'story_update', 'evidence_generated'
    notification_category = db.Column(db.String(50), default='comment') # 'comment', 'evidence', or other categories
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CategoryClick(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    click_count = db.Column(db.Integer, default=1)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'category', name='_user_category_uc'),)

# ============================================
# 真实用户名生成函数
# ============================================

def generate_realistic_username():
    """生成看起来真实的网友用户名（更网络化风格）"""
    prefixes = [
        '夜行', '孤独', '寂静', '流浪', '迷失', '追寻', '沉默', '破晓', '暮色', '星空',
        '都市', '午夜', '深夜', '凌晨', '黄昏', '月光', '影子', '幽灵', '漂泊', '守望',
        '旧事', '回忆', '故人', '陌生', '匿名', '过客', '听风', '看雨', '等待', '寻觅'
    ]
    
    suffixes = [
        '者', '人', '客', '侠', '猫', '狗', '鸟', '鱼', '龙', '凤',
        '少年', '青年', '旅人', '过客', '浪人', '游子', '行者'
    ]
    
    # 生成更网络化的用户名
    style = random.randint(1, 5)
    
    if style == 1:
        # 前缀 + 下划线 + 数字 (例: 夜行_2024)
        return f"{random.choice(prefixes)}_{random.randint(2020, 2024)}"
    elif style == 2:
        # 前缀 + 数字 + 后缀 (例: 孤独666者)
        return f"{random.choice(prefixes)}{random.choice(['520', '666', '888', '999', '123'])}{random.choice(suffixes)}"
    elif style == 3:
        # 前缀 + 后缀 + 数字 (例: 流浪客2023)
        return f"{random.choice(prefixes)}{random.choice(suffixes)}{random.randint(10, 9999)}"
    elif style == 4:
        # 前缀 + 数字 (例: 凌晨3619)
        return f"{random.choice(prefixes)}{random.randint(100, 9999)}"
    else:
        # 前缀 + 点 + 后缀 (例: 月光.行者)
        return f"{random.choice(prefixes)}.{random.choice(suffixes)}"

def get_or_create_fake_user():
    """获取或创建一个虚假用户账号用于生成评论"""
    # 获取所有非真实用户的账号（没有密码的用户）
    fake_users = User.query.filter(
        User.username.notlike('%testuser%'),
        User.email.like('%fake@example.com%')
    ).all()
    
    # 如果虚假用户少于 50 个，创建新的（增加用户池）
    if len(fake_users) < 50:
        username = generate_realistic_username()
        # 确保用户名不重复
        while User.query.filter_by(username=username).first():
            username = generate_realistic_username()
        
        fake_user = User(
            username=username,
            email=f'{username}@fake.example.com',
            password_hash='',  # 虚假用户不需要密码
            avatar=''
        )
        db.session.add(fake_user)
        db.session.commit()
        return fake_user
    
    # 随机返回一个已存在的虚假用户
    return random.choice(fake_users)

def generate_contextual_comment(story_title, story_content, existing_comments):
    """根据故事内容生成相关的评论"""
    # 提取故事关键词
    combined_text = (story_title + " " + story_content).lower()
    
    # 关键词匹配的评论模板（更丰富、更具体）
    contextual_templates = {
        # 地铁相关
        '地铁|车厢|月台|港铁': [
            '我也经常坐这条线，有时候真的会有种怪怪的感觉',
            '深夜地铁确实容易让人胡思乱想，但你说的太具体了...',
            '地铁工作人员应该知道点什么吧？',
            '末班车的时候人少，确实诡异',
            '我记得那个站台好像以前出过事',
        ],
        # 镜子相关
        '镜子|倒影|洗手间|浴室': [
            '镜子这种东西，晚上还是少看为妙',
            '我家也有面老镜子，总觉得反光不太对',
            '会不会是灯光角度问题？但听起来不像...',
            '建议把镜子换掉，别管值不值钱',
            '镜子里的东西有时候确实和现实不一样',
        ],
        # 敲门/脚步声相关
        '敲门|脚步|走廊|楼梯': [
            '楼上楼下的邻居问过吗？',
            '装个监控看看到底是什么情况',
            '我以前住的地方也有类似的声音，后来搬走了',
            '凌晨的声音最让人不安了',
            '建议先排查一下管道和结构问题',
        ],
        # 金鱼/宠物相关
        '金鱼|鱼缸|宠物|斗鱼': [
            '养鱼的人都知道，鱼是有灵性的',
            '那家店我知道，但我没见过你说的那个老板',
            '鱼缸位置是不是不对？风水上有讲究',
            '我也在金鱼街买过东西，那里有些店确实很奇怪',
            '动物有时候能感知到人类感知不到的东西',
        ],
        # 窗户/窗外相关
        '窗|窗外|人影|阴影': [
            '窗帘拉上吧，别想太多',
            '对面楼的住户你认识吗？',
            '可能是光影效果，但小心点总没错',
            '我也遇到过类似的，后来发现是树影',
            '人影这种事，看到了就别再回头看',
        ],
        # 声音相关
        '声音|听到|响|噪音': [
            '录下来听听看，说不定能发现什么',
            '会不会是幻听？压力大的时候容易这样',
            '我朋友也说过类似的经历',
            '声音从哪个方向来的？',
            '建议找人陪你一起确认一下',
        ],
        # 时间相关
        '凌晨|深夜|午夜|3点': [
            '凌晨3点是最阴的时候，尽量别醒',
            '你的作息是不是有问题？',
            '深夜容易产生幻觉，注意休息',
            '那个时间段确实容易遇到怪事',
            '半夜还是少折腾，早点睡',
        ],
    }
    
    # 通用评论（作为后备）
    generic_templates = [
        '这个我也遇到过类似的情况...',
        '楼主说的地方我知道，确实有点诡异',
        '听起来确实不太对劲',
        '会不会是巧合？但你说得太详细了',
        '我也住那附近，没遇到过，可能是个例',
        '有点吓人，楼主小心点',
        '可能是心理作用，但也说不准',
        '这个地方晚上最好别去',
        '我朋友说过类似的事',
        '真的假的？有点不可思议',
        '楼主多保重',
        '不敢相信居然还有这种事',
        '感觉背后有什么原因',
        '建议远离那个地方',
        '我之前听说过类似的传说',
        '细思极恐啊',
        '有没有可能是误会？',
        '这种事情宁可信其有',
        '感觉不太妙，注意安全',
        '有机会我也想去看看',
    ]
    
    # 根据关键词匹配选择相关评论
    matched_templates = []
    for keywords, templates in contextual_templates.items():
        if any(kw in combined_text for kw in keywords.split('|')):
            matched_templates.extend(templates)
    
    # 如果有匹配的关键词，80%概率使用相关评论，20%使用通用评论
    if matched_templates and random.random() < 0.8:
        available_templates = matched_templates
    else:
        available_templates = generic_templates
    
    # 去重：确保不和已有评论重复
    existing_contents = {c.content for c in existing_comments}
    available_templates = [t for t in available_templates if t not in existing_contents]
    
    # 如果所有模板都用过了，生成变体
    if not available_templates:
        # 简单变体：加上"也"、"好像"等词
        base_comment = random.choice(generic_templates)
        variations = [
            f"我{base_comment}",
            f"好像{base_comment}",
            f"{base_comment}吧",
            f"感觉{base_comment}",
        ]
        return random.choice(variations)
    
    return random.choice(available_templates)

def maybe_add_fake_comment(story_id):
    """有概率为故事添加1-2条虚假用户评论（增加互动感）"""
    # 50% 的概率添加虚假评论（提高概率）
    if random.random() > 0.5:
        return
    
    # 随机添加1-2条评论
    num_comments = random.choices([1, 2], weights=[0.7, 0.3])[0]
    
    # 获取故事信息和已有评论
    story = Story.query.get(story_id)
    if not story:
        return
    
    existing_comments = Comment.query.filter_by(story_id=story_id).all()
    
    # 添加评论
    for _ in range(num_comments):
        fake_user = get_or_create_fake_user()
        
        # 30%概率回复AI楼主的评论
        parent_comment = None
        if existing_comments and random.random() < 0.3:
            ai_comments = [c for c in existing_comments if c.is_ai_response]
            if ai_comments:
                parent_comment = random.choice(ai_comments)
        
        # 生成与故事相关的评论
        if parent_comment:
            # 简短回复AI
            reply_templates = [
                "楼主说得对...",
                "我也这么觉得",
                "楼主保重!",
                "楼主小心点",
                "希望楼主平安",
                "楼主后续呢？"
            ]
            comment_content = random.choice(reply_templates)
        else:
            comment_content = generate_contextual_comment(
                story.title,
                story.content,
                existing_comments
            )
        
        fake_comment = Comment(
            content=comment_content,
            story_id=story_id,
            author_id=fake_user.id,
            parent_id=parent_comment.id if parent_comment else None,
            is_ai_response=False
        )
        
        db.session.add(fake_comment)
        existing_comments.append(fake_comment)  # 更新列表避免后续重复
        
        if parent_comment:
            print(f"[fake_comment] 虚拟用户 {fake_user.username} 回复了楼主: {comment_content}")
        else:
            print(f"[fake_comment] 为故事 {story_id} ({story.title[:20]}) 添加了虚假评论: {comment_content}")
    
    db.session.commit()

def maybe_add_fake_reply(story_id, parent_comment):
    """虚拟用户有40%概率回复其他评论"""
    if random.random() > 0.4:
        return
    
    # 不要回复自己
    if parent_comment.author and parent_comment.author.username.startswith('user_'):
        return
    
    story = Story.query.get(story_id)
    if not story:
        return
    
    fake_user = get_or_create_fake_user()
    
    # 生成简短回复（针对评论内容）
    reply_templates = [
        "我也遇到过类似的情况...",
        "这也太诡异了吧!",
        "楼主保重!",
        "有点吓人啊",
        "真的假的？",
        "我觉得你应该离开那里",
        "建议报警",
        "不会吧不会吧...",
        "细思极恐",
        "这种事情真的存在吗？"
    ]
    
    reply_content = random.choice(reply_templates)
    
    fake_reply = Comment(
        content=reply_content,
        story_id=story_id,
        author_id=fake_user.id,
        parent_id=parent_comment.id,
        is_ai_response=False
    )
    
    db.session.add(fake_reply)
    db.session.commit()
    
    print(f"[fake_reply] 虚拟用户 {fake_user.username} 回复了评论 #{parent_comment.id}: {reply_content}")

def init_default_stories():
    """初始化默认的三个故事（如果数据库为空）"""
    if Story.query.count() == 0:
        print("📝 创建默认故事...")
        
        default_stories = [
            {
                'title': '深夜地铁的第13节车厢',
                'content': '''昨晚加班到凌晨，赶最后一班地铁回家。车厢里只有零星几个人，我坐在靠门的位置刷手机。

列车停靠在"老街站"时，我无意间抬头看了一眼站台显示屏——上面显示这是"13号车厢"。
可是我明明记得这条线路只有12节车厢...

我环顾四周，发现其他乘客都低着头，一动不动。窗外的站台空无一人，但月台上的电子钟显示的时间是"25:73"。
车门缓缓关上，列车继续前行。我想站起来走到其他车厢，但双腿像灌了铅一样沉重。

最诡异的是，我发现窗户上倒映着我的脸，但表情却不是我现在的样子——镜中的我在笑，笑得很诡异...

各位，我该怎么办？现在列车还在行驶，但导航显示我的位置一直在"老街站"没有移动...''',
                'category': 'subway_ghost',
                'location': '地铁2号线',
                'is_ai_generated': True,
                'ai_persona': 'paranoid_reporter',
                'current_state': 'initial'
            },
            {
                'title': '出租屋镜子里的"室友"',
                'content': '''刚搬进这个老小区的单间已经三天了，房租便宜到离谱，房东说之前的租客"搬走了"。

第一天晚上洗漱时，我注意到浴室镜子有点模糊，就用毛巾擦了擦。擦完后，镜子里好像有什么东西一闪而过，但我以为是眼花。

第二天，我发现镜子上有一个手印，五根手指细长，明显不是我的。我把它擦掉了，心里有点发毛。

今天早上，我在镜子里看到了...一个模糊的人影站在我身后。我猛地转身，身后什么都没有。但当我再次看向镜子时，那个人影还在，而且...它在对我笑。

最可怕的是，我发现它的嘴型在说："别走，陪我玩玩..."

现在我不敢回头看镜子了，但又不敢离开浴室。它会跟出来吗？有人知道该怎么办吗？求助!''',
                'category': 'cursed_object',
                'location': '老城区单身公寓',
                'is_ai_generated': True,
                'ai_persona': 'scared_witness',
                'current_state': 'initial'
            },
            {
                'title': '凌晨三点的敲门声',
                'content': '''我住在7楼，这栋楼一共只有6层。

事情是这样的：上周开始，每天凌晨3:00整，我都会听到有人敲我家门。"咚、咚、咚"，三下，很有节奏。

第一次我以为是邻居搞错了，开门一看，走廊空荡荡的。门上的猫眼是坏的，从里面看出去一片漆黑。

第二次我装了监控，结果凌晨3点监控突然黑屏，只录到了敲门声，画面恢复时已经3:05了。

昨晚，我决定不睡觉，就坐在门口等着。2:59分，我听到楼梯间传来脚步声，很轻，但很清晰地在往上走...走...走到7楼。

我的门外传来了呼吸声。

我透过门缝往外看，看到了一双腿...但那双腿是悬空的，离地至少有20厘米。

"咚、咚、咚"——敲门声又响了。

我没敢开门，现在天亮了，但我发现门把手上有一个血手印...

各位，我该报警吗？还是搬家？有人遇到过类似的事情吗？''',
                'category': 'apartment_mystery',
                'location': '某住宅小区',
                'is_ai_generated': True,
                'ai_persona': 'investigator',
                'current_state': 'initial'
            }
        ]
        
        for story_data in default_stories:
            story = Story(**story_data)
            db.session.add(story)
        
        db.session.commit()
        print("✅ 默认故事创建完成")

with app.app_context():
    db.create_all()
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('static/generated', exist_ok=True)
    init_default_stories()

def generate_token(user_id):
    return jwt.encode({
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=30)
    }, app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    try:
        data = jwt.decode(token.replace('Bearer ', ''), app.config['SECRET_KEY'], algorithms=['HS256'])
        return data['user_id']
    except:
        return None
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/<path:path>')
def serve_other(path):
    return send_from_directory('static', path)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password)
    )
    
    db.session.add(user)
    db.session.commit()
    
    token = generate_token(user.id)
    
    return jsonify({
        'token': token,
        'user': {'id': user.id, 'username': user.username, 'avatar': user.avatar}
    })

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data.get('username')).first()
    
    if not user or not check_password_hash(user.password_hash, data.get('password')):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    token = generate_token(user.id)
    
    return jsonify({
        'token': token,
        'user': {'id': user.id, 'username': user.username, 'avatar': user.avatar}
    })

@app.route('/api/stories', methods=['GET'])
def get_stories():
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)  # 每页10个故事
    
    # 查询总数
    total = Story.query.count()
    
    # 分页查询
    pagination = Story.query.order_by(Story.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    stories = pagination.items
    
    return jsonify({
        'stories': [{
            'id': s.id,
            'title': s.title,
            'content': s.content[:200] + '...' if len(s.content) > 200 else s.content,
            'category': s.category,
            'location': s.location,
            'is_ai_generated': s.is_ai_generated,
            'ai_persona': s.ai_persona,
            'current_state': s.current_state,
            'created_at': s.created_at.isoformat(),
            'views': s.views,
            'comments_count': len(s.comments),
            'evidence_count': len(s.evidence)
        } for s in stories],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'prev_page': pagination.prev_num if pagination.has_prev else None,
            'next_page': pagination.next_num if pagination.has_next else None
        }
    })

@app.route('/api/stories/<int:story_id>', methods=['GET'])
def get_story(story_id):
    story = Story.query.get_or_404(story_id)
    story.views += 1
    db.session.commit()
    
    return jsonify({
        'id': story.id,
        'title': story.title,
        'content': story.content,
        'category': story.category,
        'location': story.location,
        'is_ai_generated': story.is_ai_generated,
        'ai_persona': story.ai_persona,
        'current_state': story.current_state,
        'created_at': story.created_at.isoformat(),
        'views': story.views,
        'evidence': [{
            'id': e.id,
            'type': e.evidence_type,
            'file_path': e.file_path,
            'description': e.description,
            'created_at': e.created_at.isoformat()
        } for e in story.evidence],
        'comments': [{
            'id': c.id,
            'content': c.content,
            'is_ai_response': c.is_ai_response,
            'parent_id': c.parent_id,
            'author': {
                'id': c.author.id if c.author else None,
                'username': c.author.username if c.author else (story.ai_persona if c.is_ai_response else 'AI'),
                'avatar': c.author.avatar if c.author else ''
            },
            'created_at': c.created_at.isoformat()
        } for c in story.comments]
    })

@app.route('/api/stories/<int:story_id>/comments', methods=['POST'])
def add_comment(story_id):
    token = request.headers.get('Authorization')
    user_id = verify_token(token) if token else None
    
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    story = Story.query.get_or_404(story_id)
    # Block comments when story is locked (坟帖等状态) or has 【已封贴】tag
    if story.current_state == 'locked' or '【已封贴】' in story.title:
        return jsonify({'error': '该帖子已封贴，无法评论'}), 403
    
    parent_id = data.get('parent_id')  # 获取父评论ID（如果是回复）
    
    comment = Comment(
        content=data.get('content'),
        story_id=story_id,
        author_id=user_id,
        parent_id=parent_id,
        is_ai_response=False
    )
    
    db.session.add(comment)
    
    # Record user interaction for state machine
    from story_engine import record_user_interaction
    record_user_interaction(story)
    
    db.session.commit()
    
    # Create notification for user's own comment (for AI response)
    create_notifications_for_followers(story, comment)

    # 启动后台线程，5秒后生成AI回复（测试用）
    print(f"[add_comment] 启动后台线程，5秒后生成AI回复...")
    threading.Thread(
        target=delayed_ai_response,
        args=(story_id, comment.id, 5),  # 5秒延迟（测试）
        daemon=True
    ).start()
    
    # 如果是顶级评论，尝试添加虚拟用户评论（40%概率）
    if not parent_id:
        maybe_add_fake_comment(story_id)
    # 如果是回复，虚拟用户有30%概率也回复
    elif parent_id:
        parent_comment = Comment.query.get(parent_id)
        if parent_comment:
            maybe_add_fake_reply(story_id, parent_comment)
    
    # 检查是否达到证据生成阈值（只统计用户评论，不包括AI回复）
    user_comment_count = Comment.query.filter_by(story_id=story_id, is_ai_response=False).count()
    evidence_threshold = int(os.getenv('EVIDENCE_COMMENT_THRESHOLD', 3))  # 改为3
    
    print(f"[add_comment] 当前用户评论数: {user_comment_count}, 证据阈值: {evidence_threshold}")
    
    # 每达到阈值的倍数就生成新证据（例如：3,6,9,12...条评论时）
    if user_comment_count >= evidence_threshold and user_comment_count % evidence_threshold == 0:
        print(f"[add_comment] ✅ 用户评论数达到阈值倍数 ({user_comment_count})，启动证据生成...")
        threading.Thread(
            target=generate_evidence_for_story,
            args=(story_id, comment.id),  # 传递触发评论的ID
            daemon=True
        ).start()
    else:
        print(f"[add_comment] 未达到证据生成条件 (用户评论数: {user_comment_count}, 需要: {evidence_threshold}的倍数)")
    
    return jsonify({
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'author': {
                'id': comment.author.id,
                'username': comment.author.username,
                'avatar': comment.author.avatar
            },
            'created_at': comment.created_at.isoformat()
        },
        'ai_response_pending': True,
        'message': 'AI楼主正在思考回复，请稍候...'
    }), 201

@app.route('/api/stories/<int:story_id>/follow', methods=['POST', 'GET'])
def follow_story(story_id):
    token = request.headers.get('Authorization')
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    story = Story.query.get_or_404(story_id)
    follow = Follow.query.filter_by(user_id=user_id, story_id=story_id).first()

    if request.method == 'GET':
        return jsonify({'followed': bool(follow)})

    if follow:
        db.session.delete(follow)
        db.session.commit()
        return jsonify({'status': 'unfollowed'})
    else:
        new_follow = Follow(user_id=user_id, story_id=story_id)
        db.session.add(new_follow)
        db.session.commit()
        return jsonify({'status': 'followed'})

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    token = request.headers.get('Authorization')
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    
    return jsonify([{
        'id': n.id,
        'content': n.content,
        'story_id': n.story_id,
        'comment_id': n.comment_id,
        'is_read': n.is_read,
        'notification_type': n.notification_type,
        'notification_category': n.notification_category or 'comment',  # 返回分类，默认为 'comment'
        'created_at': n.created_at.isoformat()
    } for n in notifications])


@app.route('/api/translate', methods=['POST'])
def translate_api():
    data = request.json or {}
    text = data.get('text', '')
    target = data.get('target', 'en')

    if not text:
        return jsonify({'translated': ''})

    try:
        from ai_engine import translate_text
        translated = translate_text(text, target=target)
        if translated is None:
            return jsonify({'translated': None, 'error': 'No translation service available'}), 200
        return jsonify({'translated': translated})
    except Exception as e:
        print(f"[translate_api] error: {e}")
        return jsonify({'translated': None, 'error': str(e)}), 500

@app.route('/api/notifications/read', methods=['POST'])
def read_notifications():
    token = request.headers.get('Authorization')
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    notification_ids = data.get('ids', [])

    Notification.query.filter(
        Notification.user_id == user_id,
        Notification.id.in_(notification_ids)
    ).update({'is_read': True}, synchronize_session=False)
    
    db.session.commit()
    return jsonify({'status': 'success'})


@app.route('/api/track-category-click', methods=['POST'])
def track_category_click():
    """追踪用户点击的档案分类"""
    token = request.headers.get('Authorization')
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    category = data.get('category')
    
    if not category:
        return jsonify({'error': 'Category is required'}), 400
    
    # 查找或创建点击记录
    click_record = CategoryClick.query.filter_by(user_id=user_id, category=category).first()
    
    if click_record:
        click_record.click_count += 1
        click_record.updated_at = datetime.utcnow()
    else:
        click_record = CategoryClick(user_id=user_id, category=category, click_count=1)
        db.session.add(click_record)
    
    db.session.commit()
    return jsonify({'status': 'success', 'click_count': click_record.click_count})


@app.route('/api/user-top-categories', methods=['GET'])
def get_user_top_categories():
    """获取用户点击最多的两个分类，以及总点击数和总评论数"""
    token = request.headers.get('Authorization')
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # 查询用户点击最多的前两个分类
    top_categories = CategoryClick.query.filter_by(user_id=user_id)\
        .order_by(CategoryClick.click_count.desc())\
        .limit(2)\
        .all()
    
    # 计算总点击数 (Eyes)
    total_clicks = db.session.query(db.func.sum(CategoryClick.click_count)).filter_by(user_id=user_id).scalar() or 0
    
    # 计算总评论数 (Mouths)
    total_comments = Comment.query.filter_by(author_id=user_id).count()
    
    result = [{'category': cat.category, 'click_count': cat.click_count} for cat in top_categories]
    
    return jsonify({
        'categories': result,
        'stats': {
            'total_clicks': total_clicks,
            'total_comments': total_comments
        }
    })


@app.route('/api/admin/reset_ai_stories', methods=['POST'])
def admin_reset_ai_stories():
    """Admin endpoint: delete previous AI-generated stories and seed three starter posts.

    Protect using SECRET key sent in header 'X-ADMIN-KEY'."""
    key = request.headers.get('X-ADMIN-KEY')
    if not key or key != app.config.get('SECRET_KEY'):
        return jsonify({'error': 'Forbidden'}), 403

    # Delete AI-generated stories
    try:
        deleted = Story.query.filter_by(is_ai_generated=True).delete(synchronize_session=False)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '删除旧故事失败', 'detail': str(e)}), 500

    # Also remove any stories categorized as time anomaly (时空异常), and their comments/evidence
    try:
        time_deleted = Story.query.filter(Story.category == 'time_anomaly').all()
        if time_deleted:
            for t in time_deleted:
                # cascade should remove comments/evidence but be explicit
                Comment.query.filter_by(story_id=t.id).delete(synchronize_session=False)
                Evidence.query.filter_by(story_id=t.id).delete(synchronize_session=False)
                db.session.delete(t)
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[admin_reset] 清理时空异常分类失败: {e}")

    # Seed three starter stories using ai_engine.generate_ai_story
    from ai_engine import generate_ai_story

    # helper to create story record safely
    def create_story_from_generated(sdict, fallback):
        data = sdict or fallback
        st = Story(
            title=data.get('title'),
            content=data.get('content'),
            category=data.get('category'),
            location=data.get('location'),
            is_ai_generated=True,
            ai_persona=data.get('ai_persona'),
            current_state='initial'
        )
        db.session.add(st)
        return st

    # 1) 金鱼街
    try:
        s1 = generate_ai_story(category='cursed_object', location='旺角金鱼街')
    except Exception:
        s1 = None
    # Use a deliberate, first-person help-seeking post for the Mong Kok goldfish street seed
    forced_title = '旺角金鱼街买的金鱼一直不对劲，求助'
    forced_content = (
        '大家好，我是真的不知道该不该发这帖，但我现在很慌。上周末我在旺角金鱼街买了一条金鱼，回家后发生了很多奇怪的事。\n\n'
        '当时是下午差不多四点，金鱼档的老板看起来很急促，跟我说这条鱼"挺便宜，要不要拿走"，我也没想太多就带回家了。\n\n'
        '回到家后，水族箱里那条金鱼总是在夜里发出一种很细微的"撞击玻璃"的声音，我起初以为是气泡或泵的问题，可是晚上两三点那声音会连续敲击好几下，像是有人在外面敲玻璃。\n\n'
        '更诡异的是，这条鱼的游动姿态好像在盯着我，每次我走近鱼缸它会转过身来看我，然后停在水面不动，好像在观察我。昨晚我还梦到鱼在窗边朝我招手，醒来时发现鱼缸旁有一张小纸片，上面写了几个潦草的字，但我看不清。\n\n'
        '我不是迷信的人，但这几天家里发生了不少怪事：电子表异常、手机半夜收到一条只有数字的短讯、还有邻居说半夜看到窗边有影子。我把鱼放回原来的袋子想拿回给老板，但开口时老板却摆手说"不要带回来了"，语气很奇怪。\n\n'
        '我现在真的不知道该怎么办了，有没有在旺角金鱼街买过鱼的朋友，或懂养鱼/看风水的朋友能给点建议？谢谢大家。'
    )

    # Prefer generated story if it's clearly first-person and about 旺角金鱼街; otherwise use the forced content
    use_forced = True
    if s1 and isinstance(s1, dict):
        # crude check: ensure generated contains '旺角' and first-person marker '我'
        gen_content = s1.get('content', '')
        if '旺角' in gen_content and ('我' in gen_content or '我在' in gen_content):
            # keep generated
            st1 = create_story_from_generated(s1, None)
            use_forced = False

    if use_forced:
        st1 = Story(
            title=forced_title,
            content=forced_content,
            category='cursed_object',
            location='旺角金魚街',
            is_ai_generated=True,
            ai_persona=generate_realistic_username(),  # 使用真实用户名
            current_state='initial'
        )
        db.session.add(st1)
        
        # 有小概率添加虚假用户评论
        db.session.flush()  # 确保 story 有 ID
        maybe_add_fake_comment(st1.id)

    # 2) 港铁灵异
    try:
        s2 = generate_ai_story(category='subway_ghost', location='港鐵旺角站')
    except Exception:
        s2 = None
    fallback2 = {
        'title': '深夜地铁里的第13节车厢',
        'content': (
            "我在深夜坐港铁的时候遇到了一件很可怕的事，求助。那天是下班后的深夜，快十一点，车厢里很少人。\n"
            "我记得自己在旺角站上车，坐到第13节车厢时，感觉到有人在盯着我看。刚开始我以为是疲倦，但随后有种说不出的寒意从脊背爬上来。\n"
            "列车突然在一个没有广播报站的小站短暂停留，车厢灯光像是被谁调暗过一样，窗外黑得像墨，连隧道的反光都没有。隔壁一位阿伯也僵在那里，嘴唇微动，好像在念什么但听不清。\n"
            "我下定决心要和他搭話，才发现那阿伯的眼神空洞，眼白里有血丝，看起來像是被什麼東西纏住了。當我試圖站起來，身邊的一位年輕女生突然低聲說了一句『不要回頭』。\n"
            "我真的回不了頭，整個人像被什麼壓住。到站後有人把我拉下車，回頭一看，第13節車廂的窗子裡映著一張模糊的臉，像是有人在外面靠近車廂。我不知道那天發生了什麼，只記得從此每次坐深夜港鐵都會心驚。求大家留意，有沒有人也遇過同樣的事？"
        ),
        'category': 'subway_ghost',
        'location': '港鐵旺角站',
        'ai_persona': generate_realistic_username()  # 使用真实用户名
    }
    st2 = create_story_from_generated(s2, fallback2)
    
    # 有小概率添加虚假用户评论
    db.session.flush()
    maybe_add_fake_comment(st2.id)

    # 3) 坟帖（>2 年，评论封锁）
    try:
        s3 = generate_ai_story(category='missing_person', location='某屋邨')
    except Exception:
        s3 = None
    fallback3 = {
        'title': '【已封】关于那起旧失踪案的最后讨论',
        'content': (
            "这是一篇关于多年前那起旧失踪案的最后讨论帖。我把所有我知道的细节放在这里，想求问有没有人能帮忙回忆或补充线索。\n"
            "案发时我还是个邻居，经常在深夜听见不寻常的脚步声和扔东西的声音。失踪者最后一次被看到是在钟楼旁的茶餐厅，之后再无音讯。\n"
            "警方当年调查时封锁了一些目击证词，很多街坊都很害怕谈论此事。现在时间过去很多年，我发这帖是因为最近翻看旧照片时发现了一张奇怪的合影，背景里的楼宇窗户里似乎有个影子，对我来说这太诡异了。\n"
            "帖已封锁，不能再回复——我把重要线索都写在这篇帖子的正文里，如果有人有合法调查渠道或想私下联络，请发私信。希望能把事情理清，让当年的家属有个交代。"
        ),
        'category': 'missing_person',
        'location': '某屋邨',
        'ai_persona': generate_realistic_username()  # 使用真实用户名
    }
    # 坟贴创建时间：3年前
    st3_created = datetime.utcnow() - timedelta(days=365*3)
    
    st3 = Story(
        title=(s3 or fallback3)['title'],
        content=(s3 or fallback3)['content'],
        category=(s3 or fallback3)['category'],
        location=(s3 or fallback3)['location'],
        is_ai_generated=True,
        ai_persona=(s3 or fallback3)['ai_persona'],
        current_state='locked',
        state_data=json.dumps({'comments_locked': True}),
        created_at=st3_created
    )
    db.session.add(st3)
    db.session.flush()  # 获取 story ID
    
    # 为坟贴添加历史人机评论（3-4年前的评论）
    historical_comments = [
        '这个案子我也听说过，当年很轰动',
        '我记得那时候新闻有报道',
        '好像确实有这么回事，细节记不清了',
        '这种旧案很难查了吧',
        '希望真相能大白',
        '当年我还住那附近',
        '时间太久了，很多线索都没了',
    ]
    
    # 添加3-5条历史评论
    num_old_comments = random.randint(3, 5)
    for i in range(num_old_comments):
        fake_user = get_or_create_fake_user()
        # 评论时间：3年前到4年前之间随机
        comment_days_ago = random.randint(365*3, 365*4)
        old_comment = Comment(
            content=random.choice(historical_comments),
            story_id=st3.id,
            author_id=fake_user.id,
            is_ai_response=False,
            created_at=datetime.utcnow() - timedelta(days=comment_days_ago)
        )
        db.session.add(old_comment)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '创建新故事失败', 'detail': str(e)}), 500

    # 清理：确保金鱼贴没有历史用户评论（给人一种全新发帖的感觉）
    try:
        all_stories = Story.query.all()
        for s in all_stories:
            title = (s.title or '')
            loc = (s.location or '')
            if '金鱼' in title or '金魚' in title or '金鱼' in loc or '金魚' in loc:
                # 删除该帖的所有用户评论（保留 AI 回复可选，当前删除全部评论以重置）
                Comment.query.filter_by(story_id=s.id).delete(synchronize_session=False)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[admin_reset] 清理金鱼帖评论失败: {e}")

    return jsonify({'deleted': deleted, 'seeded': [st1.title, st2.title, st3.title]})

def create_notifications_for_followers(story, comment, ai_response=False):
    # Remove nested context manager - assume already in app context
    followers = Follow.query.filter_by(story_id=story.id).all()
    for follow in followers:
        # Don't notify the user who made the comment
        if not ai_response and follow.user_id == comment.author_id:
            continue

        notification = Notification(
            user_id=follow.user_id,
            story_id=story.id,
            comment_id=comment.id,
            notification_type='new_reply' if not ai_response else 'story_update',
            notification_category='comment',  # 评论通知分类为 'comment'
            content=f'你关注的故事 "{story.title}" 有了新回复。' if not ai_response else f'你关注的故事 "{story.title}" 有了新进展。'
        )
        db.session.add(notification)
    db.session.commit()

def delayed_ai_response(story_id, comment_id, delay_seconds=60):
    """延迟生成AI回复"""
    print(f"[delayed_ai_response] 开始等待 {delay_seconds} 秒... story_id={story_id}, comment_id={comment_id}")
    time.sleep(delay_seconds)
    
    print(f"[delayed_ai_response] 开始生成AI回复...")
    with app.app_context():
        story = Story.query.get(story_id)
        comment = Comment.query.get(comment_id)
        
        if not story or not comment:
            print(f"[delayed_ai_response] ERROR: Story or Comment not found!")
            return
        
        print(f"[delayed_ai_response] 调用 generate_ai_response...")
        from ai_engine import generate_ai_response
        
        # 获取该故事的历史AI回复
        previous_ai_responses = Comment.query.filter_by(
            story_id=story_id,
            is_ai_response=True
        ).order_by(Comment.created_at.desc()).limit(3).all()
        
        ai_response = generate_ai_response(story, comment, previous_ai_responses)
        print(f"[delayed_ai_response] AI回复生成完成: {ai_response[:50]}..." if ai_response else "[delayed_ai_response] AI回复为空!")
        
        if ai_response:
            # 判断是否是回复虚拟用户（简短回复）
            is_fake_user_reply = comment.author and comment.author.username.startswith('user_')
            if is_fake_user_reply and len(ai_response) > 100:
                # 截短AI回复给虚拟用户
                ai_response = ai_response[:80] + '...'
            
            ai_comment = Comment(
                content=ai_response,
                story_id=story_id,
                author_id=None,
                parent_id=comment.id,  # 设置父评论ID
                is_ai_response=True
            )
            db.session.add(ai_comment)
            db.session.commit()
            
            # 创建通知给评论者
            notification = Notification(
                user_id=comment.author_id,
                story_id=story_id,
                comment_id=ai_comment.id,
                notification_type='ai_reply',
                content=f'楼主(@{story.ai_persona})回复了你在 "{story.title}" 中的评论。'
            )
            db.session.add(notification)
            
            # 通知所有关注者
            create_notifications_for_followers(story, ai_comment, ai_response=True)
            
            db.session.commit()

def generate_evidence_for_story(story_id, trigger_comment_id=None):
    """为故事生成证据（图片）- 每当用户评论数达到2的倍数就生成1张图片
    
    图片生成会传入故事标题、内容和最新评论上下文，确保图片与贴文高度关联。
    """
    # 必须在 app_context 中运行，因为这是后台线程
    with app.app_context():
        print(f"[generate_evidence_for_story] 开始为故事 ID={story_id} 生成图片证据...")
        
        story = Story.query.get(story_id)
        if not story:
            print(f"[generate_evidence_for_story] ERROR: Story not found!")
            return
        
        from ai_engine import generate_evidence_image
        
        # 获取当前证据统计
        total_evidence_count = Evidence.query.filter_by(story_id=story_id).count()
        image_evidence_count = Evidence.query.filter_by(story_id=story_id, evidence_type='image').count()
        user_comment_count = Comment.query.filter_by(story_id=story_id, is_ai_response=False).count()
        
        print(f"[generate_evidence_for_story] 当前证据: 总计{total_evidence_count}个 (图片{image_evidence_count}个)")
        print(f"[generate_evidence_for_story] 当前用户评论数: {user_comment_count}")
        
        # 优先使用触发生成的最新评论，其次是其他评论
        comment_context = ""
        if trigger_comment_id:
            trigger_comment = Comment.query.get(trigger_comment_id)
            if trigger_comment and not trigger_comment.is_ai_response:
                comment_context = trigger_comment.content + " "
                print(f"[generate_evidence_for_story] 使用触发评论: {trigger_comment.content[:50]}...")
        
        # 添加其他用户评论作为补充上下文（取最新4条）
        all_user_comments = Comment.query.filter_by(story_id=story_id, is_ai_response=False).order_by(Comment.id.desc()).limit(4).all()
        other_comments = [c.content for c in all_user_comments if c.id != trigger_comment_id]
        comment_context += " ".join(other_comments[-4:] if len(other_comments) > 4 else other_comments)
        
        # 生成图片证据（可能包含多个模板）
        print(f"[generate_evidence_for_story] 📷 生成图片证据（第{image_evidence_count + 1}批）...")
        
        image_paths = generate_evidence_image(
            story_id,  # 传入 story_id
            story.title,
            story.content,
            comment_context
        )
        
        if image_paths:
            # 仅保存第一张图片作为证据：每次触发只需一张图片以降低生成与存储成本
            template_type, image_path = image_paths[0]
            evidence = Evidence(
                story_id=story_id,
                evidence_type='image',
                file_path=image_path,
                description=f"现场拍摄证据 - {template_type} 视角"
            )
            db.session.add(evidence)
            db.session.commit()
            print(f"[generate_evidence_for_story] ✅ 图片证据已生成 [{template_type}]: {image_path}")
            
            # 更新故事内容（楼主补充证据的真实口吻）
            story.content += f"\n\n【证据更新】\n根据大家的反馈，我又去现场仔细看了看，拍了这张照片。你们看看有没有发现什么异常..."
            story.updated_at = datetime.utcnow()
            db.session.commit()
            
            # 收集需要通知的用户：关注者 + 评论过的用户
            notified_users = set()
            
            # 1. 通知所有关注者
            followers = Follow.query.filter_by(story_id=story_id).all()
            for follow in followers:
                notified_users.add(follow.user_id)
            
            # 2. 通知所有评论过该故事的用户（非AI回复）
            commenters = db.session.query(Comment.author_id).filter(
                Comment.story_id == story_id,
                Comment.is_ai_response == False,
                Comment.author_id.isnot(None)
            ).distinct().all()
            for (commenter_id,) in commenters:
                notified_users.add(commenter_id)
            
            # 创建通知
            for user_id in notified_users:
                notification = Notification(
                    user_id=user_id,
                    story_id=story_id,
                    notification_type='evidence_update',
                    notification_category='evidence',  # 证据通知分类为 'evidence'
                    content=f'故事 "{story.title}" 更新了新的图片/声音证据!'
                )
                db.session.add(notification)
            
            db.session.commit()
            print(f"[generate_evidence_for_story] ✅ 证据生成完成!已通知 {len(notified_users)} 个用户")

if __name__ == '__main__':
    # Start background scheduler for AI story generation
    from scheduler_tasks import start_scheduler
    scheduler = start_scheduler(app)
    
    try:
        app.run(debug=True, port=5001)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
