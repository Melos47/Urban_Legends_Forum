import os
import random
from datetime import datetime
from openai import OpenAI
from anthropic import Anthropic
import requests
from PIL import Image
from io import BytesIO

# Initialize AI clients
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Horror story personas for AI
AI_PERSONAS = [
    {'name': '深夜目击者', 'emoji': '👁️', 'style': 'witness'},
    {'name': '都市调查员', 'emoji': '��', 'style': 'investigator'},
    {'name': '匿名举报人', 'emoji': '🕵️', 'style': 'whistleblower'},
    {'name': '失踪者日记', 'emoji': '📔', 'style': 'victim'},
    {'name': '地铁守夜人', 'emoji': '🚇', 'style': 'worker'}
]

# Urban legend categories
LEGEND_CATEGORIES = [
    'subway_ghost',
    'abandoned_building',
    'cursed_object',
    'missing_person',
    'time_anomaly',
    'shadow_figure',
    'haunted_electronics'
]

# Locations in Hong Kong
CITY_LOCATIONS = [
    '旺角金鱼街',
    '油麻地戏院',
    '中环至半山自动扶梯',
    '彩虹邨',
    '怪兽大厦 (鲗鱼涌)',
    '重庆大厦',
    '达德学校 (元朗屏山)',
    '西贡结界',
    '大埔铁路博物馆',
    '高街鬼屋 (西营盘社区综合大楼)'
]

def generate_story_prompt(category, location, persona):
    """Generate prompt for AI story creation"""
    prompts = {
        'subway_ghost': f"作为{persona['name']}，讲述你在港铁{location}站深夜遭遇的诡异经历。描述具体的时间、空无一人的车厢、听到的怪声或看到的异常倒影。语气要真实，像在论坛上分享亲身经历。",
        'abandoned_building': f"你是{persona['name']}，最近在{location}探险时发现了令人不安的秘密。详细描述建筑内部的荒废景象、发现的旧物件（例如80年代的报纸、奇怪的符咒）、以及让你毛骨悚然的超自然现象。",
        'cursed_object': f"作为{persona['name']}，你在{location}附近的一个小摊上买到了一个被诅咒的物品（如一个旧罗盘、一个玉佩）。讲述物品的来历、获得的过程、以及之后发生的连串怪事。",
        'missing_person': f"你是{persona['name']}，正在调查一宗发生在{location}的离奇失踪案。提供案件细节、失踪者最后的行踪（例如CCTV最后拍到的画面）、以及你发现的无法用常理解释的线索。",
        'time_anomaly': f"作为{persona['name']}，你在{location}的某条后巷经历了时间错位。描述周围环境的瞬间变化（例如，广告牌变成了旧样式）、手机时间的跳跃、以及重复经历的几分钟。",
        'shadow_figure': f"你是{persona['name']}，最近几晚总在{location}的窗外看到一个无法形容的黑影。详细描述黑影的形态、它如何移动、以及它似乎在对你做什么。",
        'haunted_electronics': f"作为{persona['name']}，你在{location}居住时，家里的电子设备开始出现恐怖的现象。描述电视里出现的奇怪人脸、收音机里传出的非人话语、以及手机自动播放的诡异视频。"
    }
    
    return prompts.get(category, prompts['subway_ghost'])

def generate_ai_story():
    """Generate a complete AI-driven urban legend story"""
    try:
        # Random story elements
        category = random.choice(LEGEND_CATEGORIES)
        location = random.choice(CITY_LOCATIONS)
        persona = random.choice(AI_PERSONAS)
        
        # Generate story title and content
        prompt = generate_story_prompt(category, location, persona)
        
        model = os.getenv('AI_MODEL', 'gpt-4-turbo-preview')
        
        if 'gpt' in model.lower():
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个都市传说讲述者，擅长创作真实感极强的恐怖故事。使用第一人称，加入具体的时间、地点、人物细节，让读者感觉这是真实发生的事件。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_tokens=800
            )
            content = response.choices[0].message.content
        else:
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=800,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.content[0].text
        
        # Generate story title
        title_prompt = f"为以下都市传说故事生成一个简短（5-10字）、吸引人、略带悬疑的标题。不要加引号。\n\n{content[:200]}"
        
        if 'gpt' in model.lower():
            title_response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": title_prompt}],
                temperature=0.7,
                max_tokens=20
            )
            title = title_response.choices[0].message.content.strip().replace('"', '').replace('"', '').replace('"', '')
        else:
            title_response = anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=20,
                messages=[{"role": "user", "content": title_prompt}]
            )
            title = title_response.content[0].text.strip()
        
        return {
            'title': title,
            'content': content,
            'category': category,
            'location': location,
            'ai_persona': f"{persona['emoji']} {persona['name']}",
            'persona_style': persona['style']
        }
        
    except Exception as e:
        print(f"Error generating AI story: {e}")
        return None

def generate_evidence_image(story_title, story_content):
    """Generate horror-themed evidence image using DALL-E"""
    try:
        # Create prompt for horror evidence
        prompt = f"A creepy, dark, grainy photo that serves as evidence for this urban legend: {story_title}. Style: found footage, security camera, low quality, authentic looking, horror atmosphere, realistic"
        
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        image_url = response.data[0].url
        
        # Download and save image
        img_response = requests.get(image_url)
        img = Image.open(BytesIO(img_response.content))
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"evidence_{timestamp}.png"
        filepath = f"static/generated/{filename}"
        
        img.save(filepath)
        
        return f"/generated/{filename}"
        
    except Exception as e:
        print(f"Error generating evidence image: {e}")
        return None

def generate_evidence_audio(text_content):
    """Generate spooky audio narration using OpenAI TTS"""
    try:
        # Limit text length for TTS
        narration_text = text_content[:500]
        
        response = openai_client.audio.speech.create(
            model="tts-1",
            voice="onyx",  # Deep, serious voice
            input=narration_text
        )
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"audio_{timestamp}.mp3"
        filepath = f"static/generated/{filename}"
        
        response.stream_to_file(filepath)
        
        return f"/generated/{filename}"
        
    except Exception as e:
        print(f"Error generating audio: {e}")
        return None

def generate_ai_response(story, user_comment):
    """Generate AI chatbot response to user comment"""
    
    # Check if LM Studio local server is configured
    lm_studio_url = os.getenv('LM_STUDIO_URL', 'http://localhost:1234/v1')
    use_lm_studio = os.getenv('USE_LM_STUDIO', 'true').lower() == 'true'
    
    if use_lm_studio:
        print(f"[generate_ai_response] 使用 LM Studio 本地服务器: {lm_studio_url}")
        try:
            from openai import OpenAI
            # LM Studio 兼容 OpenAI API
            local_client = OpenAI(base_url=lm_studio_url, api_key="lm-studio")
            
            prompt = f"""你是故事"{story.title}"的讲述者（{story.ai_persona}）。

故事摘要：
{story.content[:300]}...

用户评论：
{user_comment.content}

作为故事的讲述者，请用1-3句话回复用户的评论。你可以：
1. 透露更多细节或线索
2. 表达恐惧或担忧
3. 提出新的疑问
4. 描述后续发展

保持神秘感和紧张氛围，不要完全揭示真相。请直接回复，不要加"【楼主回复】"前缀。"""

            response = local_client.chat.completions.create(
                model="local-model",  # LM Studio 会使用当前加载的模型
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=200
            )
            
            ai_reply = response.choices[0].message.content.strip()
            print(f"[generate_ai_response] LM Studio 回复: {ai_reply[:50]}...")
            return f"【楼主回复】{ai_reply}"
            
        except Exception as e:
            print(f"[generate_ai_response] LM Studio 调用失败: {e}")
            print("[generate_ai_response] 回退到模板回复")
    
    # Check if cloud API keys are configured
    openai_key = os.getenv('OPENAI_API_KEY', '')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY', '')
    
    # If no valid API keys, use template responses
    if (not openai_key or openai_key == 'your-openai-api-key-here') and \
       (not anthropic_key or anthropic_key == 'your-anthropic-api-key-here'):
        print("[generate_ai_response] 使用模板回复（API密钥未配置）")
        
        # Template responses based on story location
        responses = [
            f"【楼主回复】谢谢关心！刚才又去了一趟，情况越来越诡异了...我发现了一些新线索，但不敢轻举妄动。",
            f"【楼主回复】各位，我现在有点害怕...刚才发生的事情完全超出我的理解。我会继续更新的，大家帮我分析一下。",
            f"【楼主回复】更新来了！今天又有新发现，这件事比我想象的要复杂得多。有没有懂行的朋友给点建议？",
            f"【楼主回复】感谢大家的支持！说实话我现在很纠结要不要继续调查下去...但好奇心驱使我想弄清楚真相。",
            f"【楼主回复】刚才又去现场看了，确实很不对劲。我拍了几张照片，但手机总是莫名其妙地卡顿...诡异。"
        ]
        
        # Return random response
        import random
        return random.choice(responses)
    
    try:
        # Create context-aware response
        prompt = f"""你是故事"{story.title}"的讲述者（{story.ai_persona}）。

故事摘要：
{story.content[:300]}...

用户评论：
{user_comment.content}

作为故事的讲述者，请用1-3句话回复用户的评论。你可以：
1. 透露更多细节或线索
2. 表达恐惧或担忧
3. 提出新的疑问
4. 描述后续发展

保持神秘感和紧张氛围，不要完全揭示真相。"""

        model = os.getenv('AI_MODEL', 'gpt-4-turbo-preview')
        
        if 'gpt' in model.lower():
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=200
            )
            return response.choices[0].message.content
        else:
            response = anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
            
    except Exception as e:
        print(f"Error generating AI response: {e}")
        # Fallback to template response
        import random
        responses = [
            f"【楼主回复】谢谢关心！情况有新进展了...",
            f"【楼主回复】各位，事情越来越诡异了...",
            f"【楼主回复】更新：刚才又发现了新线索！"
        ]
        return random.choice(responses)

def should_generate_new_story():
    """Determine if it's time to generate a new story"""
    from app import Story, db
    
    # Check active stories count
    active_stories = Story.query.filter(
        Story.current_state != 'ended'
    ).count()
    
    max_active = int(os.getenv('MAX_ACTIVE_STORIES', 5))
    
    return active_stories < max_active
