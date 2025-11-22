import os
import random
from datetime import datetime, timedelta
from openai import OpenAI
from anthropic import Anthropic
import requests
from PIL import Image
from io import BytesIO
import re

# Try to import OpenCC for traditional->simplified conversion if available
try:
    from opencc import OpenCC
    _opencc = OpenCC('t2s')
except Exception:
    _opencc = None

# Initialize AI clients (only if API keys are provided)
openai_api_key = os.getenv('OPENAI_API_KEY')
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')

openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None
anthropic_client = Anthropic(api_key=anthropic_api_key) if anthropic_api_key else None

# 清理 Qwen 模型的思考标签
def clean_think_tags(text):
    """
    移除 Qwen 模型生成的 <think> 标签及其内容
    处理完整标签、不完整标签和多行标签
    """
    if not text:
        return text
    
    # 移除完整的 <think>...</think> 标签（包括换行）
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # 移除不完整的开始标签（如果没有对应的结束标签）
    if '<think' in text.lower() and '</think>' not in text.lower():
        text = re.sub(r'<think[^>]*>.*$', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # 移除任何剩余的单独标签
    text = re.sub(r'</?think[^>]*>', '', text, flags=re.IGNORECASE)
    
    # 清理多余的空行
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    
    return text.strip()

def check_story_similarity(title, content, category, limit=10):
    """
    检查新生成的故事是否与最近的故事太相似（避免重复和金鱼街过多）
    
    Args:
        title: 故事标题
        content: 故事内容
        category: 故事类别
        limit: 检查最近N条故事（默认10条）
    
    Returns:
        True 如果故事通过检查（不重复），False 如果太相似
    """
    try:
        from app import Story
        from flask import current_app
        
        # 获取最近的N条故事
        recent_stories = Story.query.order_by(Story.created_at.desc()).limit(limit).all()
        
        if not recent_stories:
            return True  # 没有历史故事，通过检查
        
        # 统计最近故事中同一类别的数量
        category_count = sum(1 for s in recent_stories if s.category == category)
        
        # 如果金鱼街相关的故事超过3个在最近10条中，拒绝生成
        if category == 'fish_tank_horror' and category_count >= 3:
            print(f"[check_story_similarity] ⚠️  最近{limit}条故事中已有{category_count}条金鱼街故事，拒绝生成重复类别")
            return False
        
        # 计算标题相似度（简单检查：关键词重叠）
        title_words = set(title.split())
        for recent in recent_stories:
            recent_title_words = set(recent.title.split())
            # 计算 Jaccard 相似度
            overlap = len(title_words & recent_title_words)
            jaccard = overlap / len(title_words | recent_title_words) if (title_words | recent_title_words) else 0
            
            # 如果相似度超过 0.6，认为太相似
            if jaccard > 0.6:
                print(f"[check_story_similarity] ⚠️  标题与 '{recent.title}' 相似度过高 ({jaccard:.2f})")
                return False
        
        # 计算内容相似度（检查关键短语）
        # 提取前50个字（去重点后）
        content_prefix = re.sub(r'【.*】', '', content).strip()[:100]
        
        for recent in recent_stories:
            recent_prefix = re.sub(r'【.*】', '', recent.content).strip()[:100]
            # 计算重叠率
            overlap_chars = sum(1 for i, c in enumerate(content_prefix) if i < len(recent_prefix) and c == recent_prefix[i])
            overlap_ratio = overlap_chars / max(len(content_prefix), len(recent_prefix)) if max(len(content_prefix), len(recent_prefix)) > 0 else 0
            
            # 如果内容开头相似度超过 0.4，认为太相似
            if overlap_ratio > 0.4:
                print(f"[check_story_similarity] ⚠️  内容与 '{recent.title}' 过于相似 ({overlap_ratio:.2f})")
                return False
        
        return True
    except Exception as e:
        print(f"[check_story_similarity] 检查相似度时出错: {e}")
        return True  # 出错时允许生成（不影响正常流程）

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
    'shadow_figure',
    'haunted_electronics',
    'fish_tank_horror',  # 旺角金鱼街斗鱼事件
    'real_crime_mystery'  # 真实香港凶杀/失踪案件改编都市传说版
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
    """Generate prompt for AI story creation - 楼主视角"""
    
    # 统一的楼主角色设定
    system_role = """你是"楼主"（Louzhu），在论坛发帖求助的普通网友。

⚠️ 重要规则（社会常理与现实性）：
1. 直接写帖子内容，不要输出思考过程、不要使用<think>标签。
2. ⚠️ 字数限制：严格控制在150-250字以内。
3. 像真实网友发帖：碎片化、有省略、突然的想法。

关于警方与调查的表述限制（必须严格遵守）：
- 楼主只能陈述自己直接知道的事实或公开渠道能查到的信息（例如公开发布的监控视频、微博/论坛转发、自己拍的照片）。
- 除非楼主明确是当事人或直接亲属，否则不要声称自己参与警方调查或掌握警方内部进度；不要在帖子中替警方“同步”调查进展。
- 如果提到已报案，只能写“我已向警方报案”或“我向警方说明了情况”，不要陈述警方的行动细节或调查结论。

你的发帖风格：
1. 第一人称"我"，口语化，像在聊天。
2. 短句子，有断句，不要长段落。
3. 重点突出1个让人不安的细节，最多两个；不要铺陈太多。
4. 结尾留悬念或求助："有人知道吗？"、"我该怎么办？"
5. 不解释太多背景，只说核心的诡异点。
6. 用"..."表示犹豫或省略。

禁止：
- 不要写成完整的故事或文章。
- 不要用"诅咒"、"鬼"、"怪物"这样的词。
- 不要声称自己是警方或调查员，除非楼主明确表明自己是相关当事人。
- 不要在论坛中复述未公开的警方调查细节或伪造证据。
- 不要超过250字。
"""

    prompts = {
        'subway_ghost': f"""上周三搭末班车遇到了很奇怪的事

车厢里没几个人。我记得镜子里看到对面座位有个人一直看窗外。我转身想看他但每次转身那个位置都是空的。我又看镜子确实有人。再转身还是没人。

试了好几次都这样。我当时很累就没管继续睡了。

下车的时候我突然意识到车厢里根本就没有那个人。我手机拍的照片里也没有。

但我很确定镜子里有他。这几天我一闭眼就会想起那种感觉。不是害怕那个人而是我无法解释为什么镜子里和现实不一样。

有人遇到过这种情况吗？""",

        'cursed_object': f"""在旧货摊买了个东西现在有点后悔

那天路过的时候脑子一热就买了。回家放在架子上之后就开始觉得不对劲。

我会一直调整它的位置。调来调去都觉得不太对。有次半夜醒来发现自己站在它旁边。我完全不记得我是怎么走过去的。

朋友来我家看到这个东西表情变得很奇怪。他说不出为什么但就是觉得不舒服。

最奇怪的是我想扔掉它但每次拿起来准备装袋就会放下。我自己都注意到这个模式了但我控制不了自己。

而且我经常发现自己在看着它。不是有意的。就是一转身发现我在盯着它看。

有人知道这是怎么回事吗？""",

        'fish_tank_horror': f"""这几天一直想发帖问问，但不知道怎么说才好

我上周在旺角金鱼街买了条斗鱼。就普通那种，蓝色的。店主是个中年女人，说话有点口音。我记得很清楚因为她一直在强调这条鱼很乖。

养了三天，我开始注意到一些...怎么说呢，细节。比如每次喂食的时候，鱼会先游到缸底，停顿几秒，然后才上来吃。这个动作很固定，像某种仪式。

还有就是，我发现自己开始固定在凌晨3点多醒来。不是被惊醒，就是自然醒。然后会不自觉地去看那个鱼缸。

前天我想回去问问那个店主关于这种鱼的习性。但是...我找不到那家店了。

不是说店关了或者搬了。是那个位置好像从来没有过那家店。我问了旁边几个摊主，他们看我的眼神有点奇怪。

其中一个老板说，小伙子，这里从来就没有卖过斗鱼。

我现在每天还是会3点醒来。但不敢去看鱼缸了。有人知道这是怎么回事吗？""",

        'abandoned_building': f"""关于那栋楼我想再上去一次但我害怕

上周我发过关于某栋楼的帖子被不少人骂。但我还是想再去一次看看自己是不是记错了。

我第一次进去的时候记得楼层序号和楼梯的样子。但这一次我上去的时候有些不对。楼梯拐角的位置和我印象中的不太一样。或者说我到达的楼层和我数的楼层对不上。我确定我数对了。但当我走出楼梯间看窗户看到的景色的时候我好像走到了不同的地方。

我在里面找到了一些东西。一张报纸。报纸上的日期是两个星期前。这栋楼本来应该没有人在啊。我记得上周有不少地方都是密封的。但现在有些地方的封条被移动过了。

我在一个房间里看到了衣服堆。不是很多。就三四件。我一开始以为这是旧衣服。但当我走近的时候我意识到这些衣服还有体温。这不可能。我当时是一个人在那儿。我很确定。但当我转身想再看一眼的时候东西好像被移动过了。

我当时没怎么想就跑出来了。但现在我不确定我到底看到了什么。那些衣服真的还有体温吗还是我当时太紧张了。我的手摸到的是真的衣服的温度还是我的想象。

最糟糕的是我现在记不清楚那个房间在几楼了。我翻看我的手机里的照片但照片里显示的位置和我的记忆完全对不上。

我觉得有什么不对劲但我说不出来是什么。我想再上去看一次但每当我走到那栋楼附近我都会停下来。我害怕再看到什么我无法解释的东西。而且我害怕这一次会发现更多无法解释的东西。""",

        'missing_person': f"""我在看一个失踪贴，发现些公开资料挺奇怪的

    我不是当事人，只是看到网上有人转发了那段监控的截圖。我把能看到的公开信息整理了一下，发现时间线有出入：视频显示的时间和口述的时间不太对上，差了几小时。

    我只在看公开资料和我能联系到的熟人那里问过几个问题。有人对时间点也觉得奇怪，但没人能给出确切解释。有人起初回了讯息后来就不回了，我也不知道是不是不想多谈。

    我已经把我能找到的线索存起来并且选择性地去报案（我只是说明我看到的公开内容）。我不会在这里替警方下结论，也不会发布未经证实的内部信息。

    我发帖是想问有没有人也看到这些矛盾，或者有人知道公开渠道里有没有别的线索？""",

        'time_anomaly': f"""今天下午发生的事我到现在都没想明白

我记得我下午两点的时候从家里出门。我要去买个东西。我记得我坐了巴士。然后我记得我到了商场。然后我记得我找到了我要买的东西。但当我看手机结算的时间的时候我发现已经是下午五点半了。

等等这不对。从我出门到买完东西应该不到一小时。我看了我的手机截图。时间戳是下午五点三十分。我很确定这是真的时间。

我买的东西收据上的时间也是下午五点三十分。我问了收银员现在几点她说五点三十。我看了商场的大钟也是五点三十。

但我的记忆里我从出门到现在只过了大概四十五分钟。我记不得我在中间做了什么。或者说我有记忆。我记得我买东西的过程。但我无法把这段记忆和失去的这两小时半对上。

我拍了几张照片检查时间戳。照片里有的时间戳是下午五点的有的是下午四点的。但我只拍了三张照片。这些照片的时间戳应该都差不多才对。我很确定我没有修改过这些文件。

回家的路上我一直在想这件事。我问了一个路人现在几点。他们说下午六点十分。我问他们昨天几点。他们看着我很奇怪然后说昨天是昨天今天是今天。我意识到他们可能觉得我疯了。

现在我在家里。我看了电视。电视上显示的时间是晚上十一点二十分。这不可能。从我买完东西到现在应该不到一小时。但电视、手机、我的手表都显示这已经是晚上十一点多了。

我最害怕的是我记不起来我在中间做了什么。我有时间上的记忆缺失吗还是说我对时间的感知出了问题。""",

        'shadow_figure': f"""窗外有个东西我不知道该怎么办

上周开始对面楼的某个窗户附近一直有个阴影。一开始以为是光线问题。但这几天我注意到它每天同一时间都在。

更奇怪的是我发现自己改变了作息时间来避开它。我没有有意识地做这个决定。只是突然发现我不再在傍晚坐窗边了。

但最让我不安的是即使我想避开我还是会每天走到窗边。我会找各种借口。看天气啊查看对面店铺啊。但其实就是想看那个东西。

我控制不了自己。我不害怕那个东西。我害怕的是我为什么会养成这个习惯。""",

        'haunted_electronics': f"""从搬到这个单位之后家里的电子设备就一直有问题

我一开始以为是网络信号不好。但现在我确定不只是这个。

首先出现异常的是电视。有几次我明明关掉了它但过了一会儿它又自己开了。频道会停留在一个我完全不看的台。我问过楼下邻居他们说那个频道在这里收不到信号。那台电视是这套房子原来的房东留下来的。我后来查过那个频道确实不存在。但电视里就是能收到。

然后是我的手机。我开始收到一条一条的讯息。都是一个数字或者一个符号。讯息来自我的一个很久以前删过的联系人。我很确定我删过。但讯息还在进来。我问过朋友他们都没法解释。

之后我的电脑也开始有问题。我的录音文件夹里多了一些我没有录过的音频。都很短。几秒钟的样子。我试着播放过一个。是黑寂但不完全无声。有点像是呼吸声但又不太像。

我开始注意到一个关联。每当手机收到那些讯息的时候电视就会闪烁。每当电视闪烁的时候我的电脑就会发出系统提示音。三个设备在同一时间出现异常。这太奇怪了。

我请了一个朋友来帮我看。当他来的时候这些异常都停止了。他没看到任何问题。他检查了设置、重启了设备、什么都正常。他走了之后异常又开始了。

我试过断网。异常继续。我试过拔掉电源。等我再插上的时候异常更频繁了。我现在开始害怕处理这些设备。每次我想关掉某个东西我都会犹豫。好像有什么东西在让我不要去碰它们。

我应该找个人帮忙但我又害怕再让别人看到这一切。这太荒唐了。但这真的发生了。""",

        'real_crime_mystery': f"""最近一直在看一个旧案子，有些细节想不通

我是在网上旧论坛看到的，那起案子发生了好几年。当时有不少讨论，但最后好像就...没有了。我仔细看了当时的新闻，有些地方挺奇怪的。

时间对不上。证人的说法有矛盾。监控视频里有一段完全暗掉。为什么要暗掉？是故障还是...

我有时候会想，为什么会发生这样的事。那个人...为什么要做这个选择。我能理解当时的处境。不是替他辩护，就是...我能想象，在某些极端的情况下，人确实会改变。会做出自己都吓到的事。

现在每次看到旧新闻我都会停下来。反复看那些时间、地点、证人的话。试图理解那个人当时的想法。为什么选择那时候？为什么选择那个地方？是冲动还是计划已久？

有没有人也看过这个案子？觉得有什么地方解释不通？""",
    }

    # Append Hong Kong specific grounding cues to each prompt so the model includes local textures
    for k in prompts.keys():
        m = None
        # motifs_for may be defined below; call safely
        try:
            m = motifs_for(k)
        except Exception:
            m = None
        if m:
            local_cues = '；'.join(m[:3])
            prompts[k] = prompts[k].strip() + f"\n\n提示：请在帖子中自然融入香港地域细节（如地名、港鐵/巴士/八達通、唐樓/屋邨/茶餐廳、小販/士多等）。例如可以使用：{local_cues}。不要单列清单，要把这些细节写进叙述中，以增强地域感。"

    return {
        'system': system_role,
        'prompt': prompts.get(category, prompts['cursed_object'])
    }


def motifs_for(category_key):
    """Return a list of locality motifs for a given category key to ground prompts in Hong Kong textures."""
    mapping = {
        'subway_ghost': ['港鐵月台', '站名顯示屏', '末班車', '車廂廣播靜默', '月台的冷氣機聲'],
        'cursed_object': ['旺角金魚街', '地攤', '舊貨市場', '茶餐廳旁的小店', '袋裝回家'],
        'abandoned_building': ['唐樓後巷', '鐵閘', '塗鴉', '雜物堆', '破碎窗戶'],
        'missing_person': ['鐘樓茶餐廳', '屋邨走廊', '監控鏡頭', '街坊口供', '失蹤日期'],
        'shadow_figure': ['窗外街燈', '樓宇窗戶', '陰影靠近', '走廊光影', '黑影形狀'],
        'haunted_electronics': ['手機短訊', '電視畫面', '電子鐘', '網絡留言', '錄音檔'],
        'real_crime_mystery': ['舊新聞檔案', '案件時間線', '監控記錄', '證人證詞', '法庭文件', '網絡討論區']
    }
    return mapping.get(category_key, [])


def translate_text(text, target='en'):
    """Translate text to target language using available AI client (OpenAI/Anthropic).

    Returns translated string or None if no translation service is available.
    """
    if not text:
        return ''
    # Try LM Studio local server first (useful when using qwen2.5-7b-instruct-1m)
    lm_studio_url = os.getenv('LM_STUDIO_URL', '').rstrip('/')
    use_lm_studio = bool(lm_studio_url)

    if use_lm_studio:
        try:
            import subprocess, json
            chat_url = f"{lm_studio_url}/v1/chat/completions"
            system = """你是翻译助手。将下面的中文贴文翻译成英文，保持原文的口吻与长度（若为第一人称求助贴，请保留求助语气）。只返回翻译内容，不要额外说明。"""
            user_prompt = f"{text}"

            request_data = {
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 800
            }

            curl_cmd = [
                'curl', '-s', '-X', 'POST', chat_url,
                '-H', 'Content-Type: application/json',
                '-d', json.dumps(request_data, ensure_ascii=False),
                '--max-time', '60'
            ]

            proc = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=65)
            if proc.returncode == 0 and proc.stdout:
                try:
                    resp = json.loads(proc.stdout)
                    translated = resp['choices'][0]['message']['content']
                    return translated.strip()
                except Exception as e:
                    print(f"[translate_text] LM Studio parse failed: {e}")
            else:
                print(f"[translate_text] LM Studio request failed: {proc.stderr}")
        except Exception as e:
            print(f"[translate_text] LM Studio translation error: {e}")

    # Prefer OpenAI client if available
    try:
        if openai_client:
            model = os.getenv('AI_MODEL', 'gpt-3.5-turbo')
            prompt = f"请将以下中文文本翻译成{ '英语' if target.startswith('en') else target }，保持语气和长度，返回纯翻译，不要多余说明：\n\n{text}"
            resp = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )
            result = resp.choices[0].message.content
            return result.strip()

        if anthropic_client:
            model = os.getenv('AI_MODEL', 'claude-2')
            prompt = f"Translate the following Chinese text to English, preserve tone and brevity:\n\n{text}"
            resp = anthropic_client.messages.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800
            )
            if hasattr(resp, 'content'):
                try:
                    return resp.content[0].text.strip()
                except Exception:
                    return None
    except Exception as e:
        print(f"[translate_text] translation failed: {e}")

    return None


def add_title_tag(title, story_age_days=0):
    """Add appropriate tag to story title based on story age
    
    Args:
        title: Original title text
        story_age_days: Number of days since story was created (0 for new stories)
    
    Returns:
        Title with appropriate tag: 【求助】, 【分享】, or 【已封贴】
    """
    import random
    
    # Remove common prefixes that might already exist
    title = re.sub(r'^(我发帖求助：|求助：|分享：)', '', title).strip()
    title = re.sub(r'^【(求助|分享|已封贴)】', '', title).strip()
    
    # If story is old (>730 days, ~2 years) with no activity, mark as closed
    if story_age_days > 730:
        return f"【已封贴】{title}"
    
    # For new stories, randomly choose between 求助 and 分享
    # 70% 求助 (help), 30% 分享 (sharing)
    tag = random.choice(['【求助】', '【求助】', '【求助】', '【求助】', '【求助】', '【求助】', '【求助】', '【分享】', '【分享】', '【分享】'])
    
    return f"{tag}{title}"

def convert_to_simplified(text):
    """Convert text to Simplified Chinese if possible.

    Tries OpenCC first; if not available and LM Studio is configured,
    falls back to a lightweight LM Studio call to convert to 简体中文.
    If neither available, returns original text.
    """
    if not text:
        return text

    # Use OpenCC if available
    if _opencc:
        try:
            return _opencc.convert(text)
        except Exception:
            pass

    # Fallback: use LM Studio to convert to 简体中文 if configured
    lm_studio_url = os.getenv('LM_STUDIO_URL', '').rstrip('/')
    if lm_studio_url:
        try:
            import subprocess, json
            system = """你是一个简体中文转换助手。请将下面的文本转换为简体中文，保持原文口吻与句意，不要添加说明，只返回转换后的文本。"""
            request_data = {
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": text}
                ],
                "temperature": 0.0,
                "max_tokens": 1200
            }
            chat_url = f"{lm_studio_url}/v1/chat/completions"
            curl_cmd = [
                'curl', '-s', '-X', 'POST', chat_url,
                '-H', 'Content-Type: application/json',
                '-d', json.dumps(request_data, ensure_ascii=False),
                '--max-time', '30'
            ]
            proc = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=35)
            if proc.returncode == 0 and proc.stdout:
                try:
                    resp = json.loads(proc.stdout)
                    return resp['choices'][0]['message']['content'].strip()
                except Exception:
                    pass
        except Exception:
            pass

    return text


def filter_dialogue_and_horror(text):
    """Filter out dialogue structures, action descriptions, and explicit horror words for subtle style"""
    if not text:
        return text
    
    try:
        # Remove action descriptions in asterisks or parentheses
        text = re.sub(r'\*[^*]*\*', '', text)  # Remove *action*
        text = re.sub(r'\([^)]*\)', '', text)   # Remove (action)
        text = re.sub(r'（[^）]*）', '', text)   # Remove （action）
        text = re.sub(r'\[[^]]*\]', '', text)   # Remove [action]
        
        # Remove dialogue structures completely
        # Pattern 1: "他说："、"店主道："等
        text = re.sub(r'[^。！？]*[说道讲]：[^。！？]*[。！？]?', '', text)
        # Pattern 2: Incomplete dialogue at line end
        text = re.sub(r'，[说道]：.*?$', '。', text, flags=re.MULTILINE)
        # Pattern 3: Direct speech indicators
        text = re.sub(r'[他她我店主老板][^。！？]*[说道]：[^。！？]*', '', text)
        # Pattern 4: Remove incomplete dialogue fragments
        text = re.sub(r'我说。', '', text)
        text = re.sub(r'他说。', '', text)
        text = re.sub(r'她说。', '', text)
        text = re.sub(r'[他她我][^。！？]*[说道讲]，', '，', text)
        text = re.sub(r'，[^。！？]*[说道讲]，', '，', text)
        
        # Replace explicit horror words with subtle alternatives
        horror_replacements = {
            '鬼使神差': '不知怎么', '惊魂': '不安', '鬼': '那种感觉',
            '恐怖': '不舒服', '可怕': '让人不安', '血腥': '红色的东西',
            '死亡': '出事', '尸体': '躺着不动的', '邪恶': '不对劲',
            '魔鬼': '说不出的东西', '诅咒': '不好的感觉', '地狱': '很糟糕的地方',
            '吓人': '让人紧张', '恶心': '不太舒服'
        }
        
        for old, new in horror_replacements.items():
            text = text.replace(old, new)
        
        # Clean up excessive punctuation and spacing
        text = re.sub(r'[。！？]{2,}', '。', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    except Exception:
        return text

def post_process_story_text(text):
    """Post-process generated story text to satisfy user constraints:
    - Remove any parenthetical/bracketed content ((), （）, [], but preserve 【】 for title tags)
    - Remove obvious stage/action direction lines (镜头/拍摄/动作/旁白 等)
    - Ensure first-person presence; if absent, prepend a short first-person intro
    - Convert to Simplified Chinese if possible
    """
    if not text:
        return text

    # 1) Remove bracketed/parenthetical content (round, square, curly, full-width)
    # Remove nested brackets iteratively - BUT preserve 【】 tags for titles
    prev = None
    cleaned = text
    # patterns for various bracket types (exclude 【】 which are used for title tags)
    bracket_patterns = [r'\([^\)]*\)', r'\（[^\）]*\）', r'\[[^\]]*\]', r'\{[^\}]*\}']
    for pat in bracket_patterns:
        cleaned = re.sub(pat, '', cleaned)

    # 2) Remove lines that likely are stage directions or metadata
    stage_triggers = ['动作', '镜头', '画面', '拍摄', '旁白', '场景', '注：', '说明：']
    lines = cleaned.splitlines()
    filtered_lines = []
    for ln in lines:
        strip_ln = ln.strip()
        if not strip_ln:
            continue
        lowered = strip_ln
        if any(trig in lowered for trig in stage_triggers):
            # skip this line
            continue
        # skip lines that are just short bracket-like markers
        if re.match(r'^[\-\*•\s]{0,3}$', strip_ln):
            continue
        filtered_lines.append(ln)

    cleaned = '\n'.join(filtered_lines).strip()

    # 3) Normalize whitespace
    cleaned = re.sub(r'\n{2,}', '\n\n', cleaned)
    cleaned = re.sub(r'\s{2,}', ' ', cleaned).strip()

    # 2.5) Remove quoted speech (Chinese and ASCII quotes) to avoid dialog-style lines
    try:
        # Remove Chinese quotes “...” and 『...』 and 「...」
        cleaned = re.sub(r'“[^”]*”', '', cleaned)
        cleaned = re.sub(r'『[^』]*』', '', cleaned)
        cleaned = re.sub(r'「[^」]*」', '', cleaned)
        # Remove ASCII quotes
        cleaned = re.sub(r'"[^\"]*"', '', cleaned)
        cleaned = re.sub(r"'[^']*'", '', cleaned)
        # Remove any stray quote characters
        cleaned = cleaned.replace('“', '').replace('”', '').replace('「', '').replace('」', '').replace('『', '').replace('』', '')
        cleaned = cleaned.replace('\"', '"').replace("\'", "'")
    except Exception:
        pass

    # 4) Ensure first-person presence
    if '我' not in cleaned:
        # try to change leading third-person subjects to first-person
        cleaned = re.sub(r'([。！？\n]|^)\s*(他|她|他们|她们|它|它们)\s+', r'\1我', cleaned)
        # Try more aggressive replacement
        cleaned = re.sub(r'^(他|她|它)', '我', cleaned)
        cleaned = re.sub(r'(他|她|它)(看到|听到|发现|经历|遇到|感觉|觉得)', r'我\2', cleaned)
        
        # For content, add first-person intro only if really needed
        # For titles, don't add this prefix
        if '我' not in cleaned and len(cleaned) > 30:
            # Only add for longer text (content, not titles)
            # Prepend a short, natural first-person lead-in to ensure perspective
            cleaned = '我发帖求助，最近遇到一件怪事：' + cleaned

    # 4.5) Filter out explicit horror words - maintain subtle/implicit horror style
    try:
        # 露骨恐怖词汇替换为隐晦表达
        explicit_horror_map = {
            '鬼': '那种东西', '鬼魂': '某种存在', '幽灵': '看不见的东西',
            '诅咒': '不好的感觉', '恶魔': '不对劲的东西', '怪物': '说不出的东西',
            '血腥': '红色的', '死亡': '不在了', '尸体': '躺着的人',
            '恐怖': '不安', '可怕': '让人不舒服', '惊悚': '紧张',
            '阴森': '安静得有点怪', '邪恶': '不对劲', '恶心': '不太舒服',
            '血液': '红色液体', '死人': '没有反应的人', '杀害': '出事了',
            '魔鬼': '不好的东西', '灵异': '说不清的', '超自然': '无法解释的'
        }
        
        for explicit, implicit in explicit_horror_map.items():
            cleaned = cleaned.replace(explicit, implicit)
            
        # 移除过于夸张的形容词
        dramatic_words = ['极其', '非常可怕', '十分恐怖', '异常恐怖', '极度', '超级']
        for word in dramatic_words:
            cleaned = cleaned.replace(word, '有点')
            
    except Exception:
        pass

    # 5) Convert to Simplified Chinese if possible
    try:
        cleaned = convert_to_simplified(cleaned)
    except Exception:
        pass

    # 6) Apply dialogue and horror word filtering for subtle style
    try:
        cleaned = filter_dialogue_and_horror(cleaned)
    except Exception:
        pass

    return cleaned

def expand_story_for_category(text, category, min_chars=350):
    """Expand short stories for specific categories (e.g. fish_tank_horror).

    Attempts to use LM Studio to expand the text while preserving first-person
    perspective and avoiding quoted dialogue or timeline markers like
    "第一天/第二天". If LM Studio is unavailable or the call fails, falls
    back to a deterministic expansion that paraphrases and appends details
    derived from the original text.
    """
    if not text:
        return text

    # If already long enough, return as-is
    if len(text) >= min_chars:
        return text

    # Only attempt expensive expansion for fish_tank_horror by default
    lm_studio_url = os.getenv('LM_STUDIO_URL', '').rstrip('/')
    use_lm = os.getenv('USE_LM_STUDIO', 'true').lower() == 'true' and lm_studio_url

    prompt_system = (
        "你是论坛发帖扩展专家。目标：扩展为真实当事人的困惑求助帖（第一人称我）。"
        "风格要求：中式恐怖白描 - 隐晦、留白、细思极恐。不要露骨的恐怖词汇，要通过异常细节让读者自己产生不安感。"
        "心理状态：像真实经历诡异事件的人 - 困惑、不安、想要求助但又说不清具体怎么回事。"
        "语言风格：口语化、碎片化、有停顿和省略。不要完整叙述，要像在回忆时断断续续的描述。"
        "绝对禁止：引号对话、时间序列(第一天/第二天)、露骨恐怖词汇、警察身份、完整故事结构。只输出扩展内容。"
    )

    prompt_user = f"原文：\n{text}\n\n请扩展为一段不少于{min_chars}个字符的第一人称贴文，保持上述要求。只输出扩展后的正文，不要添加多余说明。"

    if use_lm:
        try:
            import subprocess, json
            chat_url = f"{lm_studio_url}/v1/chat/completions"
            request_data = {
                "messages": [
                    {"role": "system", "content": prompt_system},
                    {"role": "user", "content": prompt_user}
                ],
                "temperature": 0.85,
                "max_tokens": 600
            }

            curl_cmd = [
                'curl', '-s', '-X', 'POST', chat_url,
                '-H', 'Content-Type: application/json',
                '-d', json.dumps(request_data, ensure_ascii=False),
                '--max-time', '90'
            ]

            proc = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=95)
            if proc.returncode == 0 and proc.stdout:
                try:
                    resp = json.loads(proc.stdout)
                    expanded = resp['choices'][0]['message']['content'].strip()
                    # Clean up any think-tags or unwanted markers
                    expanded = clean_think_tags(expanded)
                    # Ensure no quoted dialogue remains
                    expanded = post_process_story_text(expanded)
                    if len(expanded) >= min_chars:
                        return expanded
                    else:
                        # If LM returned shorter text, fall through to deterministic expansion
                        text = expanded
                except Exception:
                    pass
        except Exception:
            pass

        # Fallback deterministic expansion: paraphrase + add sensory details
        # Keep first-person and avoid quotes/timeline markers
        try:
            base = text.strip()
            extras = []
            # 隐晦的异常细节 - 细思极恐的碎片
            extras.append('我记得店主手上有个很深的疤，但现在想不起来是哪只手。')
            extras.append('那条鱼的眼睛...我总觉得它在看我。不是看鱼缸外面，是看"我"。')
            extras.append('买鱼的时候我付了现金。回家数钱包发现钱还在。')
            extras.append('我问过三个摊主，他们的反应都一模一样。连说话的语气都是。')
            extras.append('奇怪的是，我手机里那天拍的照片时间戳有问题。显示的时间我根本不在那里。')
            extras.append('现在每次经过那条街，总有种被人盯着的感觉。但回头什么都没有。')
            extras.append('有没有人知道...鱼会不会记住买它的人的脸？')

            # Compose until reaching min_chars
            expanded = base
            i = 0
            while len(expanded) < min_chars and i < len(extras):
                expanded = expanded + '\n' + extras[i]
                i += 1

            # If still short, repeat descriptive paraphrase with slight variation
            paraphrase_seed = (
                '我越回想越觉得不对劲，那些细节连成一条线索却又断成了碎片。'
            )
            while len(expanded) < min_chars:
                expanded += '\n' + paraphrase_seed
                paraphrase_seed = paraphrase_seed.replace('越', '愈').replace('觉得', '感觉')

            # Final cleanup
            expanded = post_process_story_text(expanded)
            return expanded
        except Exception:
            return text


def generate_ai_story(category=None, location=None, persona=None):
    """Generate a complete AI-driven urban legend story

    Optional parameters allow callers to specify a category, location, or persona.
    If any parameter is None, the function falls back to a random choice.
    """
    try:
        # Random story elements
        if category is None:
            category = random.choice(LEGEND_CATEGORIES)
        if location is None:
            location = random.choice(CITY_LOCATIONS)
        if persona is None:
            persona = random.choice(AI_PERSONAS)
        
        # Generate story title and content using new prompt format
        prompt_data = generate_story_prompt(category, location, persona)
        
        # 优先使用 LM Studio 本地模型
        use_lm_studio = os.getenv('USE_LM_STUDIO', 'true').lower() == 'true'
        lm_studio_url = os.getenv('LM_STUDIO_URL', 'http://localhost:1234/v1')
        
        content = None
        title = None
        
        # 尝试 LM Studio
        if use_lm_studio:
            try:
                print(f"[generate_ai_story] 使用 LM Studio 生成故事...")
                import subprocess
                import json
                
                # 使用 curl 调用 LM Studio（Python HTTP 库与 LM Studio 有兼容性问题）
                chat_url = f"{lm_studio_url.rstrip('/v1')}/v1/chat/completions"
                
                request_data = {
                    "messages": [
                        {"role": "system", "content": prompt_data['system']},
                        {"role": "user", "content": prompt_data['prompt']}
                    ],
                    "temperature": 0.9,
                    "max_tokens": 800
                }
                
                curl_command = [
                    'curl', '-s', '-X', 'POST', chat_url,
                    '-H', 'Content-Type: application/json',
                    '-d', json.dumps(request_data, ensure_ascii=False),
                    '--max-time', '120'
                ]
                
                result = subprocess.run(
                    curl_command,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode != 0:
                    raise Exception(f"curl 命令失败: {result.stderr}")
                
                response_data = json.loads(result.stdout)
                content_raw = response_data['choices'][0]['message']['content']
                
                print(f"[generate_ai_story] 原始内容长度: {len(content_raw)} 字符")
                
                # 过滤 qwen 模型的 <think> 标签
                content = clean_think_tags(content_raw)
                
                print(f"[generate_ai_story] 清理后内容长度: {len(content) if content else 0} 字符")
                
                # 检查清理后是否有有效内容
                if not content or len(content) < 50:
                    print(f"[generate_ai_story] ⚠️ 模型输出主要是思考过程，尝试提取实际内容...")
                    # 尝试从原始内容中提取实际故事内容
                    # 查找最后一个 </think> 之后的内容
                    if '</think>' in content_raw:
                        content = content_raw.split('</think>')[-1].strip()
                        print(f"[generate_ai_story] 提取 </think> 后的内容: {len(content)} 字符")
                    
                    # 如果还是太短，使用原始内容但警告
                    if not content or len(content) < 50:
                        content = content_raw
                        print(f"[generate_ai_story] ⚠️ 使用原始内容，包含思考过程")
                
                # 生成标题（使用更直接的提示词避免思考过程）
                title_prompt = f"故事：{content[:150]}\n\n请为上面的故事起一个5-10字的标题："
                
                title_request = {
                    "messages": [
                        {"role": "system", "content": "你是标题生成器。用户给你故事，你只需要输出一个简短的标题，不要有任何其他内容。"},
                        {"role": "user", "content": title_prompt}
                    ],
                    "temperature": 0.5,
                    "max_tokens": 20
                }
                
                title_curl_command = [
                    'curl', '-s', '-X', 'POST', chat_url,
                    '-H', 'Content-Type: application/json',
                    '-d', json.dumps(title_request, ensure_ascii=False),
                    '--max-time', '60'
                ]
                
                title_result = subprocess.run(
                    title_curl_command,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if title_result.returncode != 0:
                    raise Exception(f"标题生成失败: {title_result.stderr}")
                
                title_response_data = json.loads(title_result.stdout)
                title_raw = title_response_data['choices'][0]['message']['content'].strip()
                
                # 使用统一的清理函数
                title = clean_think_tags(title_raw)
                
                # 清理引号和多余字符
                title = title.replace('"', '').replace('"', '').replace('"', '').replace('《', '').replace('》', '')
                title = title.strip()
                
                # 如果标题太长，取第一句话
                if len(title) > 20:
                    sentences = re.split(r'[。！？\n]', title)
                    title = sentences[0][:15]
                
                # 如果仍然没有有效标题，从故事内容生成简单标题
                if not title or len(title) < 3:
                    # 从分类和地点生成简单标题
                    cat_names = {
                        'subway_ghost': '地铁怪谈',
                        'abandoned_building': '废楼惊魂',
                        'cursed_object': '诅咒之物',
                        'missing_person': '离奇失踪',
                        'supernatural_encounter': '灵异事件'
                    }
                    title = cat_names.get(category, '都市传说')
                
                print(f"[generate_ai_story] ✅ LM Studio 生成成功: {title}")
                
            except Exception as e:
                import traceback
                error_message = str(e)
                print(f"[generate_ai_story] ❌ LM Studio 失败: {type(e).__name__}: {e}")
                
                # 特殊处理 503 错误
                if "503" in error_message or "InternalServerError" in str(type(e).__name__):
                    print("[generate_ai_story] ⚠️ 检测到 503 错误 - 可能的原因:")
                    print("   1. LM Studio 模型未完全加载")
                    print("   2. 服务器负载过高")
                    print("   3. 并发请求过多")
                    print("[generate_ai_story] 💡 请在 LM Studio 'Local Server' 标签确认模型已加载")
                else:
                    print(f"[generate_ai_story] 详细错误:")
                    traceback.print_exc()
                
                content = None
                title = None
        
        # 如果 LM Studio 失败，尝试在线 API
        if not content:
            model = os.getenv('AI_MODEL', 'gpt-4-turbo-preview')
            
            if openai_client and 'gpt' in model.lower():
                print(f"[generate_ai_story] 使用 OpenAI API...")
                response = openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": prompt_data['system']},
                        {"role": "user", "content": prompt_data['prompt']}
                    ],
                    temperature=0.9,
                    max_tokens=800
                )
                content = response.choices[0].message.content
                
                # 生成标题
                title_prompt = f"为以下都市传说故事生成一个简短（6-12字）、吸引人、略带悬疑的贴文标题。不要加引号。\n\n{content[:200]}"
                title_response = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": title_prompt}],
                    temperature=0.7,
                    max_tokens=20
                )
                title = title_response.choices[0].message.content.strip().replace('"', '').replace('"', '').replace('"', '')
                
            elif anthropic_client:
                print(f"[generate_ai_story] 使用 Anthropic API...")
                response = anthropic_client.messages.create(
                    model=model,
                    max_tokens=800,
                    messages=[
                        {"role": "user", "content": f"{prompt_data['system']}\n\n{prompt_data['prompt']}"}
                    ]
                )
                content = response.content[0].text
                
                # 生成标题
                title_prompt = f"为以下都市传说故事生成一个简短（5-10字）、吸引人、略带悬疑的标题。不要加引号。\n\n{content[:200]}"
                title_response = anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=20,
                    messages=[{"role": "user", "content": title_prompt}]
                )
                title = title_response.content[0].text.strip()
            else:
                print(f"[generate_ai_story] ❌ 没有可用的 AI 服务")
                return None
        
        if not content or not title:
            return None

        # Post-process title and content to enforce user constraints
        try:
            processed_content = post_process_story_text(content)
        except Exception:
            processed_content = content

        # If the fish-tank horror story is too short, attempt to expand it
        try:
            if category == 'fish_tank_horror':
                processed_content = expand_story_for_category(processed_content, category, min_chars=350)
        except Exception:
            pass

        try:
            processed_title = post_process_story_text(title)
            # Titles should be short: truncate if too long
            if processed_title and len(processed_title) > 24:
                processed_title = processed_title.split('\n', 1)[0][:20]
            
            # Add title tag (【求助】or 【分享】for new stories)
            processed_title = add_title_tag(processed_title, story_age_days=0)
        except Exception:
            processed_title = title
            # Still try to add tag even if processing failed
            try:
                processed_title = add_title_tag(processed_title, story_age_days=0)
            except Exception:
                pass

        # 🔍 检查去重：避免生成相似或重复的故事
        if not check_story_similarity(processed_title, processed_content, category):
            print(f"[generate_ai_story] ⚠️  故事与最近内容过于相似，重新尝试...")
            # 在实际使用中，scheduler_tasks 会重试生成
            return None

        return {
            'title': processed_title,
            'content': processed_content,
            'category': category,
            'location': location,
            'ai_persona': generate_realistic_username_for_ai(),  # 使用真实用户名
            'persona_style': persona['style']
        }
        
    except Exception as e:
        print(f"Error generating AI story: {e}")
        return None

def generate_realistic_username_for_ai():
    """为AI楼主生成真实的用户名（与app.py中的函数独立，更网络化风格）"""
    import random
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

def generate_evidence_image(story_id, story_title, story_content, comment_context=""):
    """Generate horror-themed evidence image using Stable Diffusion
    
    Args:
        story_id: 故事ID，用于生成唯一的文件名
        story_title: 故事标题
        story_content: 故事内容
        comment_context: 用户评论上下文
    
    Returns:
        list: 生成的所有图片路径列表 [(模板类型, 文件路径), ...]
    """
    try:
        import os
        use_real_ai = os.getenv('USE_DIFFUSER_IMAGE', 'true').lower() == 'true'
        
        if use_real_ai:
            print(f"[generate_evidence_image] 使用 Stable Diffusion 生成图片...")
            
            try:
                from diffusers import StableDiffusionPipeline
                import torch
                from PIL import Image, ImageFilter, ImageEnhance
                import random
                
                # 检查是否有可用的模型
                model_id = os.getenv('DIFFUSION_MODEL', 'runwayml/stable-diffusion-v1-5')
                
                # 智能分析故事内容 + 评论内容，生成与故事直接相关的真实场景
                story_text = (story_title + " " + story_content[:300]).lower()
                # 加入评论和贴文的关键词 - 权重更高
                comment_text = ""
                if comment_context:
                    comment_text = comment_context.lower()
                    story_text += " " + comment_text
                
                print(f"[generate_evidence_image] 分析故事: {story_text[:150]}...")
                if comment_text:
                    print(f"[generate_evidence_image] 评论线索: {comment_text[:100]}...")
                
                # 从故事中提取关键场景元素（包括评论中的关键词）
                scene_keywords = {
                    # 地铁相关 - 优先级最高，因为这个场景最具体
                    'subway': {
                        'scenes': ['subway train interior with empty seats', 'subway station platform', 'metro train car at night'],
                        'details': ['汽车灯影、月台空荡、车厢诡异', '13号车厢、车号显示屏、月台电子钟']
                    },
                    '地铁': {
                        'scenes': ['subway train interior with empty seats', 'subway station platform at night', 'metro corridor'],
                        'details': ['地铁内部、乘客、诡异']
                    },
                    '车厢': {
                        'scenes': ['train car interior, seats and handrails', 'empty subway carriage at night'],
                        'details': ['车厢内部、座位、寂静']
                    },
                    
                    # 镜子相关
                    'mirror': {
                        'scenes': ['bathroom with mirror and sink', 'bedroom mirror on dresser', 'mirror reflection at night'],
                        'details': ['镜子倒影、诡异表情']
                    },
                    '镜子': {
                        'scenes': ['bathroom mirror above sink, faucet visible', 'bedroom mirror with dresser'],
                        'details': ['镜中倒影不是自己、诡异笑容']
                    },
                    '倒影': {
                        'scenes': ['mirror reflection, distorted face', 'window reflection at night'],
                        'details': ['倒影、非本人、诡异']
                    },
                    
                    # 门相关  
                    'door': {
                        'scenes': ['apartment door with peephole and handle', 'residential hallway with doors'],
                        'details': ['敲门、门号、诡异']
                    },
                    '门': {
                        'scenes': ['apartment door, door handle, peephole', 'residential building hallway'],
                        'details': ['门、猫眼、敲门声']
                    },
                    '敲门': {
                        'scenes': ['apartment entrance door closeup', 'door with door number plate at night'],
                        'details': ['有人敲门、门号、时间']
                    },
                    
                    # 楼道相关
                    'hallway': {
                        'scenes': ['apartment building corridor', 'residential stairwell'],
                        'details': ['楼道、走廊、昏暗']
                    },
                    '走廊': {
                        'scenes': ['apartment building hallway with doors', 'residential corridor with lighting'],
                        'details': ['走廊、灯光、脚步声']
                    },
                    '楼道': {
                        'scenes': ['apartment stairwell, concrete steps', 'building corridor with elevator'],
                        'details': ['楼梯、电梯、诡异']
                    },
                    '楼梯': {
                        'scenes': ['residential building staircase, handrails', 'stairwell in apartment building at night'],
                        'details': ['阶梯、灯光、脚步']
                    },
                    
                    # 窗户相关
                    'window': {
                        'scenes': ['apartment window view at night', 'window with curtains'],
                        'details': ['窗外、月亮、人影']
                    },
                    '窗': {
                        'scenes': ['residential window from inside', 'apartment window at night'],
                        'details': ['窗外、诡异、人影']
                    },
                    '窗外': {
                        'scenes': ['window view from apartment at night', 'dark window with city lights'],
                        'details': ['窗外景象、诡异、月光']
                    },
                    
                    # 房间相关
                    '卧室': {
                        'scenes': ['bedroom interior, bed and furniture', 'residential bedroom at night'],
                        'details': ['卧室、床、昏暗']
                    },
                    '房间': {
                        'scenes': ['residential room interior at night', 'apartment bedroom'],
                        'details': ['房间、诡异、阴影']
                    },
                    '床': {
                        'scenes': ['bedroom bed under dim light', 'bed with sheets and pillows'],
                        'details': ['床、睡眠、诡异']
                    },
                    
                    # 其他诡异场景
                    '手机': {
                        'scenes': ['smartphone screen in dark', 'phone screen in hand'],
                        'details': ['屏幕、拍照、证据']
                    },
                    '照片': {
                        'scenes': ['photograph on table', 'old photo or polaroid'],
                        'details': ['照片、证据、诡异']
                    },
                    '录音': {
                        'scenes': ['phone recording screen', 'audio device'],
                        'details': ['录音、语音、证据']
                    },
                    '笔记': {
                        'scenes': ['handwritten note on paper', 'notebook page with writing'],
                        'details': ['笔记、文字、线索']
                    },
                    '时间': {
                        'scenes': ['clock showing strange time', 'digital display at night'],
                        'details': ['时间、诡异数字、不寻常']
                    },
                    
                    # 诡异氛围
                    '影子': {
                        'scenes': ['shadow on wall in dark', 'mysterious shadow in room'],
                        'details': ['影子、人影、诡异']
                    },
                    '脚步': {
                        'scenes': ['empty hallway floor', 'stairwell steps at night'],
                        'details': ['地面、脚步声、诡异']
                    },
                    '声音': {
                        'scenes': ['empty room interior at night', 'residential space interior'],
                        'details': ['房间内、声音、诡异']
                    },
                    '冷': {
                        'scenes': ['cold apartment interior', 'frost on window'],
                        'details': ['寒冷、冻气、诡异']
                    },
                    '诡异': {
                        'scenes': ['dimly lit urban apartment', 'creepy residential space'],
                        'details': ['诡异、阴影、不寻常']
                    },
                }
                
                # 多层级匹配场景描述 - 优先匹配评论中的关键词
                scene_desc = None
                scene_details = ""
                matched_keyword = None
                
                # 第一优先级：匹配评论中的关键词（用户补充的信息）
                if comment_text:
                    for keyword, scene_data in scene_keywords.items():
                        if keyword in comment_text:
                            scene_desc = random.choice(scene_data.get('scenes', ['dimly lit apartment']))
                            scene_details = random.choice(scene_data.get('details', ['']))
                            matched_keyword = keyword
                            print(f"[generate_evidence_image] 从评论匹配: {keyword} -> {scene_desc}")
                            break
                
                # 第二优先级：匹配故事标题和内容
                if not scene_desc:
                    for keyword, scene_data in scene_keywords.items():
                        if keyword in story_text:
                            scene_desc = random.choice(scene_data.get('scenes', ['dimly lit apartment']))
                            scene_details = random.choice(scene_data.get('details', ['']))
                            matched_keyword = keyword
                            print(f"[generate_evidence_image] 从故事匹配: {keyword} -> {scene_desc}")
                            break
                
                # 如果没有匹配，使用通用场景
                if not scene_desc:
                    scene_desc = 'dimly lit urban apartment interior, everyday furniture'
                    scene_details = '诡异、不寻常的氛围'
                    print(f"[generate_evidence_image] 使用默认场景")
                
                # 纪实照片风格的 prompt - 真实场景中融入故事特定的诡异元素
                # 提取显性细节（引号内短语、数字编号、时间、地点关键词），并把它们直接加入到 prompt
                explicit_details = []
                # 从原始故事/评论文本中提取引号内短语
                try:
                    quoted = re.findall(r'“([^”]+)”|"([^"]+)"|‘([^’]+)’|\'([^\']+)\'', story_text)
                    for tup in quoted:
                        for part in tup:
                            if part:
                                explicit_details.append(part)
                except Exception:
                    pass

                # 提取常见的数字+单位（如 13号、3层、3点等）和时间格式
                try:
                    nums = re.findall(r"\d+[号节层楼点分钟分秒]?", story_text)
                    explicit_details.extend(nums)
                except Exception:
                    pass

                # 添加 title 以增强提示的语义相关性
                if isinstance(story_title, str) and story_title.strip():
                    explicit_details.append(story_title.strip())

                # 去重并限制数量
                seen = set()
                filtered_details = []
                for d in explicit_details:
                    dd = d.strip()
                    if not dd:
                        continue
                    if dd in seen:
                        continue
                    seen.add(dd)
                    filtered_details.append(dd)
                    if len(filtered_details) >= 6:
                        break
                explicit_details_text = ", ".join(filtered_details)

                # 将显性细节映射为更明确的视觉短语（中文->英文视觉描述）以提高图像的强关联性
                visual_map = {
                    # 地点 / 标题相关
                    '金鱼街斗鱼': 'fish tank in small pet shop, visible aquariums and signage',
                    '地铁': 'subway interior or platform, visible carriage number display',
                    '13号': 'carriage number 13 on digital display',
                    '13号车厢': 'train carriage labeled 13 on display',
                    '地铁2号线': 'metro line 2 signage, platform signs',
                    # 声音相关（转换为可视线索，如水波、玻璃振动等）
                    '砰砰声': 'water ripple marks on aquarium glass, visible impact ripples',
                    '敲鱼缸': 'closeup of aquarium glass with impact marks, chipped paint',
                    '敲门': 'door with knock marks and peephole, nighttime hallway',
                    '脚步声': 'scuffed floor and footprints in dim hallway',
                    '声音': 'sound source implied by movement in curtains or ripples on water',
                    '声响': 'vibrations or visible disturbance on surfaces',
                    '凌晨3点': 'digital clock showing 03:00, dark night lighting',
                    '3点': 'digital clock showing 03:00',
                    '镜子': 'bathroom mirror with faint reflection, smudge or handprint',
                    '倒影': 'reflection in glass showing a different face',
                    '鱼缸': 'fish tank with visible water, algae, and glass reflections',
                    '照片': 'polaroid-style photograph laying on a table',
                    '录音': 'phone recording screen or audio recorder device visible',
                    '窗外': 'view through window with streetlights or moonlight',
                    '门': 'apartment door with visible handle and peephole',
                }

                visual_phrases = []
                for d in filtered_details:
                    key = d
                    # 简单归一化数词，例如含数字的短语
                    if any(ch.isdigit() for ch in key) and key not in visual_map:
                        # map '13号' -> 'number 13 signage'
                        visual_phrases.append(f"signage or digits: {key}")
                        continue
                    mapped = visual_map.get(key)
                    if mapped:
                        visual_phrases.append(mapped)
                    else:
                        # 试着把中文短语原样放入，但转换成提示友好的形式
                        visual_phrases.append(f"visual cue: {key}")

                visual_phrases_text = ", ".join(visual_phrases)

                # 关键：将显性视觉短语放在 prompt 中的显著位置，便于生成与正文紧密相关的图像
                extra_section = ""
                if visual_phrases_text:
                    extra_section = f", include visual elements: {visual_phrases_text}"
                    if explicit_details_text:
                        extra_section += f" (keywords: {explicit_details_text})"

                prompt = (
                    f"realistic photograph, {scene_desc}, "
                    f"taken with smartphone camera at night, "
                    f"low light conditions, grainy image quality, "
                    f"slightly unfocused, amateur photography, "
                    f"real world scene, photographic evidence style, "
                    f"visible details and textures, concrete objects, "
                    f"documentary photo aesthetic, "
                    f"{scene_details}, "
                    f"subtle creepy atmosphere, barely visible face in shadow, "
                    f"inexplicable shadow, eerie presence, "
                    f"something unsettling about this place, hidden disturbing details"
                    f"{extra_section}"
                )
                
                # 负面提示词 - 避免太扭曲/太抽象，但保留微妙恐怖
                negative_prompt = (
                    "abstract, artistic, illustration, painting, drawing, sketch, "
                    "cartoon, anime, 3d render, cgi, digital art, "
                    "extremely distorted, heavily warped, grotesque, monstrous, "
                    "obvious demon, obvious ghost, obvious supernatural creature, "
                    "repetitive patterns, geometric shapes, abstract forms, "
                    "professional studio photography, dramatic lighting, cinematic, "
                    "motion blur, artistic blur, tilt-shift, "
                    "text, watermarks, signatures, "
                    "completely dark, pitch black, completely invisible, "
                    "overly bright, blown out highlights"
                )
                
                print(f"[generate_evidence_image] Prompt: {prompt[:100]}...")
                
                # 使用较小的图片尺寸加快生成
                pipe = StableDiffusionPipeline.from_pretrained(
                    model_id,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    safety_checker=None,  # 禁用安全检查以允许恐怖内容
                    requires_safety_checker=False
                )
                
                # 如果有GPU则使用GPU
                if torch.cuda.is_available():
                    pipe = pipe.to("cuda")
                    print("[generate_evidence_image] ✅ 使用GPU加速")
                    num_steps = 25
                    img_size = 512  # GPU可以直接生成512x512
                else:
                    print("[generate_evidence_image] ⚠️ 未检测到GPU，使用CPU生成")
                    # CPU模式：生成512x512正方形图片，避免拉伸变形
                    num_steps = 20  # 更多步数确保质量
                    img_size = 512  # 直接生成512x512，无需放大
                
                # 生成图片 - 只生成一张primary模板以节省CPU/内存
                templates = []
                # 只使用 primary 基础 prompt（不再生成 closeup 和 source）
                templates.append(('primary', prompt))

                # 生成并保存图片，文件名包含 story_id
                timestamp_base = datetime.now().strftime('%Y%m%d_%H%M%S')
                saved_files = []
                for idx, (suffix, p) in enumerate(templates):
                    print(f"[generate_evidence_image] 生成模板[{suffix}] Prompt: {p[:120]}...")
                    image = pipe(
                        p,
                        negative_prompt=negative_prompt,
                        num_inference_steps=num_steps,
                        guidance_scale=8.5,
                        height=img_size,
                        width=img_size
                    ).images[0]

                    # 确保输出是512x512
                    if image.size != (512, 512):
                        image = image.resize((512, 512), Image.Resampling.LANCZOS)

                    # 后处理（与之前相同）
                    from PIL import ImageEnhance, ImageDraw, ImageFont
                    enhancer = ImageEnhance.Color(image)
                    image = enhancer.enhance(0.85)
                    enhancer = ImageEnhance.Brightness(image)
                    image = enhancer.enhance(0.85)
                    enhancer = ImageEnhance.Contrast(image)
                    image = enhancer.enhance(1.15)
                    enhancer = ImageEnhance.Sharpness(image)
                    image = enhancer.enhance(1.1)

                    import numpy as np
                    img_array = np.array(image)
                    noise = np.random.normal(0, 3, img_array.shape)
                    img_array = np.clip(img_array + noise, 0, 255).astype(np.uint8)
                    image = Image.fromarray(img_array)

                    draw = ImageDraw.Draw(image)
                    days_ago = random.randint(1, 30)
                    fake_date = datetime.now() - timedelta(days=days_ago)
                    timestamp_text = fake_date.strftime('%Y/%m/%d %H:%M:%S')
                    try:
                        draw.text((340, 480), timestamp_text, fill=(220, 220, 220))
                        draw.text((10, 10), f"REC ●", fill=(200, 0, 0))
                    except:
                        pass

                    # 文件名包含 story_id 确保每个帖子的图片是唯一的
                    filename = f"evidence_story{story_id}_{timestamp_base}_{suffix}.png"
                    filepath = f"static/generated/{filename}"
                    image.save(filepath)
                    saved_files.append((suffix, f"/static/generated/{filename}"))
                    print(f"[generate_evidence_image] ✅ Stable Diffusion 图片已生成: {filepath}")

                # 返回所有生成的文件路径列表
                return saved_files
                
            except Exception as sd_error:
                print(f"[generate_evidence_image] Stable Diffusion 失败: {sd_error}")
                print(f"[generate_evidence_image] 回退到占位符图片...")
                # 回退到占位符
                use_real_ai = False
        
        if not use_real_ai:
            # 占位符版本 - 生成伪纪实风格的模拟照片
            print(f"[generate_evidence_image] 使用占位符图片（伪纪实风格）")
            from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
            import random
            import numpy as np
            
            # 创建带有渐变的暗色背景（模拟低光环境）
            img = Image.new('RGB', (512, 512), color=(30, 32, 35))
            draw = ImageDraw.Draw(img)
            
            # 根据故事类型添加具象的简单几何图形（模拟具体场景）
            if '地铁' in story_title or '车厢' in story_title:
                # 模拟地铁车厢内部：座椅、扶手
                draw.rectangle([50, 300, 150, 450], fill=(40, 42, 45))  # 座椅
                draw.rectangle([350, 300, 450, 450], fill=(38, 40, 43))  # 座椅
                draw.line([(256, 0), (256, 200)], fill=(60, 60, 60), width=5)  # 扶手杆
            elif '镜子' in story_title:
                # 模拟镜子和洗手台
                draw.rectangle([100, 100, 400, 400], fill=(45, 48, 52))  # 镜子框
                draw.rectangle([150, 350, 350, 450], fill=(55, 55, 58))  # 洗手台
            elif '门' in story_title or '楼道' in story_title:
                # 模拟门和走廊
                draw.rectangle([180, 50, 330, 480], fill=(50, 45, 40))  # 门
                draw.ellipse([235, 240, 275, 280], fill=(70, 70, 70))  # 门把手
                draw.rectangle([10, 100, 100, 150], fill=(60, 55, 50))  # 墙上的东西
            else:
                # 默认：房间内部物品
                draw.rectangle([80, 250, 200, 450], fill=(45, 43, 40))  # 家具
                draw.rectangle([320, 200, 450, 400], fill=(42, 40, 38))  # 家具
                draw.line([(0, 380), (512, 380)], fill=(35, 33, 30), width=3)  # 地板线
            
            # 添加细微噪点（模拟胶片颗粒）
            pixels = img.load()
            for i in range(0, 512, 2):  # 跳格处理以加快速度
                for j in range(0, 512, 2):
                    noise = random.randint(-8, 8)
                    r, g, b = pixels[i, j]
                    pixels[i, j] = (
                        max(0, min(255, r + noise)),
                        max(0, min(255, g + noise)),
                        max(0, min(255, b + noise + 2))  # 轻微的蓝色偏移
                    )
            
            # 应用模糊（模拟对焦不准/手抖）
            img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
            
            # 降低饱和度
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(0.5)
            
            # 添加监控录像风格的时间戳
            draw = ImageDraw.Draw(img)
            days_ago = random.randint(1, 30)
            fake_date = datetime.now() - timedelta(days=days_ago)
            timestamp_text = fake_date.strftime('%Y/%m/%d %H:%M:%S')
            
            try:
                # 右下角时间戳（白色半透明）
                draw.text((340, 480), timestamp_text, fill=(200, 200, 200))
                # 左上角REC标记
                draw.text((10, 10), f"REC ●", fill=(180, 0, 0))
                # 添加一些模拟的扫描线
                for y in range(0, 512, 8):
                    draw.line([(0, y), (512, y)], fill=(255, 255, 255), width=1)
                    img_array = np.array(img)
                    img_array[y, :] = np.clip(img_array[y, :] * 0.95, 0, 255)
                    img = Image.fromarray(img_array.astype(np.uint8))
            except:
                pass
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # 占位符文件名也包含 story_id
            filename = f"evidence_story{story_id}_{timestamp}_placeholder.png"
            filepath = f"static/generated/{filename}"
            img.save(filepath)
            
            # 返回列表格式以保持一致性
            return [('placeholder', f"/static/generated/{filename}")]
        
    except Exception as e:
        print(f"[generate_evidence_image] 错误: {e}")
        import traceback
        traceback.print_exc()
        return []

def generate_audio_description_with_lm_studio(title, content, comment_context=""):
    """使用 LM Studio 生成丰富的音频场景描述，增加多样性"""
    try:
        import subprocess
        import json
        
        lm_studio_url = os.getenv('LM_STUDIO_URL', 'http://localhost:1234/v1')
        
        # 构造 prompt，让 AI 根据故事生成音频场景描述
        system_prompt = """你是一个音频场景专家。根据给定的故事内容，生成一个简短的、生动的音频环境描述。
        
描述应该包括:
1. 主要的声音元素 (1-2 个)
2. 声音的特征 (急促/缓慢/重复/变化等)
3. 总体的情绪氛围

返回格式: 单行文本，不超过 100 字

示例:
"地下隧道中的空洞回声，伴随着规律的敲击声，节奏诡异，令人不安"
"微弱的人类呼吸声混合着低频嗡鸣，像有无形的东西在身边"
"""

        user_prompt = f"""故事标题: {title}

故事内容: {content[:200]}

用户评论: {comment_context[:150]}

请生成这个故事对应的音频场景描述。"""

        # 使用 curl 调用 LM Studio
        curl_command = [
            'curl', '-s', f'{lm_studio_url}/chat/completions',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps({
                'model': 'qwen2.5-7b-instruct-1m',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'temperature': 0.7,
                'max_tokens': 150,
                'top_p': 0.9
            })
        ]
        
        result = subprocess.run(curl_command, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            try:
                response_data = json.loads(result.stdout)
                audio_description = response_data['choices'][0]['message']['content'].strip()
                print(f"[generate_audio_description] ✅ AI 生成音频描述: {audio_description[:60]}...")
                return audio_description
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                print(f"[generate_audio_description] JSON 解析失败: {e}")
                return None
        else:
            print(f"[generate_audio_description] curl 调用失败: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"[generate_audio_description] 错误: {e}")
        return None

def extract_audio_keywords(title, content, comment_context=""):
    """提取音频相关关键词 - 返回音频类型和参数"""
    
    # 音频关键词映射表 (关键词 -> (音频类型, 频率参数, 强度))
    audio_keywords = {
        # 敲击/脚步相关 - 优先级高，要先检查
        '敲门|敲击|脚步|踩踏|走动|跺脚': ('knocking', 'rhythmic_pulse', 0.5),
        
        # 机械/电子 - 优先级高
        '灯闪烁|电流|闪烁|嗡鸣|警报|断断续续|电器': ('electronic', 'flicker_buzz', 0.5),
        
        # 地铁/隧道/空间
        '地铁|隧道|地下|回声': ('subway', 'hollow_echo', 0.5),
        
        # 声音/人声相关 - 低吟、呻吟、尖叫等
        '呻吟|尖叫|哭声|喘气|呼吸|低吟|呢喃|嗓音|人声': ('voice', 'strange_voice', 0.6),
        
        # 自然/环境声
        '风|树|雨|水|流动': ('nature', 'wind_whisper', 0.4),
        '沙沙|窸窣|簌簌': ('ambient', 'static_whisper', 0.3),
        
        # 时间关键词（影响整体气氛但不直接决定音频类型）
        '夜晚|凌晨|午夜|深夜|晚上': ('nocturnal', 'ambient_eerie', 0.6),
        
        # 诡异/恐怖总体印象（最低优先级）
        '诡异|怪异|恐怖|害怕|不安|诡|鬼|灵异|灵': ('eerie', 'ambient_eerie', 0.7),
    }
    
    # 合并所有文本用于匹配
    combined_text = f"{title} {content} {comment_context}".lower()
    
    # 默认音频类型
    audio_type = 'ambient_eerie'
    intensity = 0.5
    
    # 按优先级查找匹配的关键词（先定义的优先级最高）
    for keywords, (category, audio_type_matched, intensity_matched) in audio_keywords.items():
        # 检查是否有任何关键词匹配
        has_match = False
        matched_keyword = ""
        
        for kw in keywords.split('|'):
            kw = kw.strip()
            if kw and kw in combined_text:
                has_match = True
                matched_keyword = kw
                break
        
        if has_match:
            audio_type = audio_type_matched
            intensity = intensity_matched
            print(f"[extract_audio_keywords] 匹配到关键词: '{matched_keyword}' -> {audio_type}")
            break  # 优先级最高的匹配就跳出
    
    return audio_type, intensity

def generate_evidence_audio(text_content, story_context=""):
    """生成诡异现场环境音频 - 根据内容生成对应的微妙怪异声音"""
    try:
        print(f"[generate_evidence_audio] 生成诡异现场环境音频...")
        
        # 首先尝试使用 LM Studio 生成音频描述
        full_context = f"{text_content}\n{story_context}"
        ai_audio_description = generate_audio_description_with_lm_studio(
            text_content, 
            story_context.split('\n')[0] if story_context else "",  # 取故事内容前几行
            story_context
        )
        
        # 提取音频关键词 - 同时考虑 AI 生成的描述和原始内容
        if ai_audio_description:
            # 如果 AI 生成了描述，优先使用 AI 描述中的关键词
            audio_type, intensity = extract_audio_keywords(
                text_content, 
                ai_audio_description,  # 使用 AI 生成的描述
                story_context
            )
            print(f"[generate_evidence_audio] 使用 AI 生成的描述进行关键词提取")
        else:
            # 否则使用原始内容进行关键词提取
            audio_type, intensity = extract_audio_keywords(text_content, story_context)
        
        print(f"[generate_evidence_audio] 音频类型: {audio_type}, 强度: {intensity}")
        
        try:
            import numpy as np
            from scipy.io import wavfile
            from scipy import signal
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 生成诡异环境音频的多个层次
            sample_rate = 22050  # 22kHz采样率
            duration = 2.0  # 2秒音频
            
            # 创建基础音频数据
            t = np.linspace(0, duration, int(sample_rate * duration))
            
            # 根据audio_type生成不同类型的声音
            if audio_type == 'voice' or audio_type == 'strange_voice':
                # 人声嗡鸣 - 微妙的人类声音幻听
                # 每次生成不同的基础频率和特征，增加多样性
                base_freq = np.random.choice([70, 80, 90, 100, 110, 120])  # 更多频率选择
                layer1 = 0.12 * intensity * np.sin(2 * np.pi * base_freq * t)
                
                # 变调的低吟 - 随机的变调范围和速度
                modulation_depth = np.random.randint(15, 35)  # 变调深度变化
                modulation_speed = np.random.uniform(0.3, 0.8)  # 变调速度变化
                freq_modulation = base_freq + modulation_depth * np.sin(2 * np.pi * modulation_speed * t)
                layer2 = 0.08 * intensity * np.sin(2 * np.pi * freq_modulation * t)
                
                # 微弱的呼吸声 - 不同的呼吸节奏
                breath_freq = np.random.uniform(0.8, 1.5)  # 呼吸频率变化
                breath_env = signal.square(2 * np.pi * breath_freq * t) * 0.5 + 0.5
                breath_tone_freq = np.random.randint(120, 200)  # 呼吸音的基频变化
                layer3 = 0.06 * intensity * breath_env * np.sin(2 * np.pi * breath_tone_freq * t)
                
                audio_data = layer1 + layer2 + layer3
                
            elif audio_type == 'knocking' or audio_type == 'rhythmic_pulse':
                # 敲击/脚步声 - 不同的节奏和音色
                pulse_freq = np.random.uniform(1.0, 2.5)  # 更宽的脉冲频率范围
                pulse_envelope = signal.square(2 * np.pi * pulse_freq * t) * 0.5 + 0.5
                
                # 低频敲击声 - 不同的敲击音色
                low_freq = np.random.choice([60, 70, 80, 90, 100])  # 多种敲击频率
                layer1 = 0.15 * intensity * pulse_envelope * np.sin(2 * np.pi * low_freq * t)
                
                # 高频响应 - 不同的响应频率
                high_freq = np.random.choice([150, 180, 200, 250, 300])  # 多种响应频率
                layer2 = 0.08 * intensity * pulse_envelope * np.sin(2 * np.pi * high_freq * t)
                
                # 环境反响 - 增加变化
                white_noise = 0.06 * intensity * np.random.normal(0, 1, len(t))
                white_noise = signal.lfilter([1, 1], [1], white_noise) / 2
                
                audio_data = layer1 + layer2 + white_noise
                
            elif audio_type == 'wind_whisper' or audio_type == 'static_whisper':
                # 风声/沙沙声 - 微妙而诡异，多种风格
                wind_noise = 0.08 * intensity * np.random.normal(0, 1, len(t))
                wind_noise = signal.lfilter([1, 2, 1], [1, 0, 0], wind_noise) / 4
                
                # 添加变调的高频 - 随机高频范围
                base_whisper_freq = np.random.choice([600, 700, 800, 900, 1000, 1100])
                modulation_range = np.random.randint(150, 300)
                freq_modulation = base_whisper_freq + modulation_range * np.sin(2 * np.pi * np.random.uniform(0.2, 0.5) * t)
                whisper = 0.04 * intensity * np.sin(2 * np.pi * freq_modulation * t)
                
                audio_data = wind_noise + whisper
                
            elif audio_type == 'hollow_echo':
                # 地铁/隧道 - 空洞的回声，多种空间感
                # 随机的基础频率营造不同的空间大小感觉
                base_freq = np.random.choice([180, 200, 220, 240])
                modulation = 20 + np.random.randint(20, 40)
                base_freq_mod = base_freq + modulation * np.sin(2 * np.pi * np.random.uniform(0.3, 0.5) * t)
                layer1 = 0.12 * intensity * np.sin(2 * np.pi * base_freq_mod * t)
                
                # 延迟的回声 - 不同的延迟时间营造不同的空间感
                delay_time = np.random.uniform(0.08, 0.15)  # 延迟时间变化
                delay_samples = int(delay_time * sample_rate)
                layer2 = np.zeros_like(t)
                if delay_samples < len(layer1):
                    layer2[delay_samples:] = 0.06 * intensity * layer1[:-delay_samples]
                
                # 深沉的嗡鸣 - 不同的低频
                low_freq = np.random.choice([50, 55, 60, 65])
                layer3 = 0.08 * intensity * np.sin(2 * np.pi * low_freq * t)
                
                audio_data = layer1 + layer2 + layer3
                
            elif audio_type == 'electrical_hum' or audio_type == 'flicker_buzz':
                # 电流/闪烁 - 断断续续的嗡鸣，多种风格
                buzz_freq = np.random.choice([110, 120, 130, 140])  # 不同的电流频率
                buzz = 0.12 * intensity * np.sin(2 * np.pi * buzz_freq * t)
                
                # 闪烁效果 - 不同的闪烁速度
                flicker_speed = np.random.uniform(2.5, 5.0)
                flicker_env = signal.square(2 * np.pi * flicker_speed * t) * 0.5 + 0.5
                layer2 = 0.08 * intensity * flicker_env * buzz
                
                # 高频失真 - 不同的失真频率
                distortion_freq = np.random.choice([1500, 1800, 2000, 2500, 3000])
                layer3 = 0.04 * intensity * np.sin(2 * np.pi * distortion_freq * t) * flicker_env
                
                audio_data = layer2 + layer3
                
            else:  # 默认: ambient_eerie
                # 环境诡异感 - 多层次的微妙不安，更多随机变化
                # 层1: 低频嗡鸣声（诡异氛围），多种频率选择
                low_freq = np.random.choice([35, 40, 45, 50, 55])
                low_freq_buzz = 0.12 * intensity * np.sin(2 * np.pi * low_freq * t)
                
                # 层2: 间歇性的高频尖叫声，多种频率组合
                scream_freqs = [
                    [700, 1000, 1400],
                    [600, 950, 1350],
                    [750, 1100, 1500],
                    [650, 1050, 1450]
                ]
                selected_freqs = np.random.choice([i for i in range(len(scream_freqs))])
                scream_freqs = scream_freqs[selected_freqs]
                
                screams = np.zeros_like(t)
                scream_speed = np.random.uniform(1.5, 3.0)  # 尖叫速度变化
                for freq in scream_freqs:
                    envelope = signal.square(2 * np.pi * scream_speed * t) * 0.5 + 0.5
                    screams += 0.05 * intensity * envelope * np.sin(2 * np.pi * freq * t)
                
                # 层3: 白噪声（环境背景音） - 基于故事内容的不同种子
                np.random.seed(hash(full_context) % 2**32)
                white_noise = 0.08 * intensity * np.random.normal(0, 1, len(t))
                white_noise = signal.lfilter([1, 2, 1], [1, 0, 0], white_noise) / 4
                
                # 层4: 诡异的脉冲音 - 不同脉冲频率
                pulse_freq = np.random.uniform(1.2, 2.5)
                pulse_envelope = signal.square(2 * np.pi * pulse_freq * t) * 0.5 + 0.5
                pulse_base_freq = np.random.choice([100, 120, 150, 180])
                pulse = 0.08 * intensity * pulse_envelope * np.sin(2 * np.pi * pulse_base_freq * t)
                
                audio_data = low_freq_buzz + screams + white_noise + pulse
            
            # 添加动态变化（恐怖感渐进）
            envelope = np.ones_like(t)
            mid_point = len(envelope) // 2
            envelope[:mid_point] = np.linspace(0.2, 0.95, mid_point)
            second_half_len = len(envelope) - mid_point
            envelope[mid_point:] = np.linspace(0.95, 0.5, second_half_len)
            envelope[mid_point:] += 0.08 * np.random.normal(0, 1, second_half_len)
            
            audio_data *= envelope
            
            # 规范化音量（防止失真）- 保持微妙
            max_val = np.max(np.abs(audio_data))
            if max_val > 0:
                audio_data = (audio_data / max_val) * 0.85  # 降低整体音量使其更微妙
            
            # 转换为16位PCM格式
            audio_int16 = np.int16(audio_data * 32767)
            
            # 保存为WAV文件
            wav_filename = f"eerie_sound_{audio_type}_{timestamp}.wav"
            wav_filepath = f"static/generated/{wav_filename}"
            wavfile.write(wav_filepath, sample_rate, audio_int16)
            
            print(f"[generate_evidence_audio] ✅ 诡异音频已生成: {wav_filepath}")
            return f"/generated/{wav_filename}"
            
        except ImportError as e:
            print(f"[generate_evidence_audio] scipy/numpy 导入失败: {e}，使用备用方案...")
            
            # 备用方案：使用 pydub 生成环境音效
            try:
                from pydub import AudioSegment
                from pydub.generators import WhiteNoise, Sine
                import random
                
                duration = 3000  # 3秒
                noise = WhiteNoise().to_audio_segment(duration=duration)
                noise = noise - (38 - intensity * 10)  # 根据强度调整音量
                
                # 根据audio_type生成对应的音效
                if audio_type == 'voice' or audio_type == 'strange_voice':
                    # 人声幻听
                    base_freq = random.choice([80, 95, 110])
                    for _ in range(3):
                        pos = random.randint(0, duration - 800)
                        tone = Sine(base_freq).to_audio_segment(duration=random.randint(400, 800))
                        noise = noise.overlay(tone - 20, position=pos)
                        
                elif audio_type == 'knocking' or audio_type == 'rhythmic_pulse':
                    # 敲击声
                    for i in range(5):
                        pos = int(i * duration / 5)
                        tone = Sine(100).to_audio_segment(duration=150)
                        noise = noise.overlay(tone - 15, position=pos)
                        
                elif audio_type == 'wind_whisper' or audio_type == 'static_whisper':
                    # 风声/沙沙 - 已由白噪声表现，只需调整音量
                    noise = noise - 5
                    
                elif audio_type == 'hollow_echo':
                    # 地铁回声
                    for _ in range(3):
                        pos = random.randint(0, duration - 600)
                        tone = Sine(200).to_audio_segment(duration=600)
                        noise = noise.overlay(tone - 22, position=pos)
                        
                elif audio_type == 'electrical_hum' or audio_type == 'flicker_buzz':
                    # 电流嗡鸣
                    hum = Sine(120).to_audio_segment(duration=duration)
                    noise = noise.overlay(hum - 25, position=0)
                    
                else:
                    # 默认环境诡异感
                    for _ in range(random.randint(4, 7)):
                        pos = random.randint(0, duration - 500)
                        freq = random.randint(400, 1200)
                        tone_duration = random.randint(150, 500)
                        tone = Sine(freq).to_audio_segment(duration=tone_duration)
                        noise = noise.overlay(tone - 28, position=pos)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"eerie_audio_{audio_type}_{timestamp}.mp3"
                filepath = f"static/generated/{filename}"
                
                noise.export(filepath, format="mp3", bitrate="64k")
                
                print(f"[generate_evidence_audio] ✅ 诡异音效已生成（备用）: {filepath}")
                return f"/generated/{filename}"
                
            except Exception as pydub_error:
                print(f"[generate_evidence_audio] pydub也失败了: {pydub_error}，使用占位符")
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                return f"/generated/audio_placeholder_{timestamp}.mp3"
        
    except Exception as e:
        print(f"[generate_evidence_audio] 错误: {e}")
        import traceback
        traceback.print_exc()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"/generated/audio_placeholder_{timestamp}.mp3"

def generate_ai_response(story, user_comment, previous_ai_responses=None):
    """Generate AI chatbot response to user comment"""
    
    # Check if LM Studio local server is configured
    lm_studio_url = os.getenv('LM_STUDIO_URL', 'http://localhost:1234/v1')
    use_lm_studio = os.getenv('USE_LM_STUDIO', 'true').lower() == 'true'
    
    if use_lm_studio:
        print(f"[generate_ai_response] 使用 LM Studio 本地服务器: {lm_studio_url}")
        try:
            # 使用 subprocess 调用 curl（因为 Python HTTP 库与 LM Studio 有兼容性问题）
            import subprocess
            import json
            
            # 构建历史对话上下文
            history_context = ""
            if previous_ai_responses:
                history_parts = []
                for prev_comment in reversed(previous_ai_responses):  # 按时间顺序
                    # 清理回复内容（去掉【楼主回复】标记）
                    clean_reply = prev_comment.content.replace("【楼主回复】", "").strip()
                    history_parts.append(f"- {clean_reply}")
                history_context = "\n".join(history_parts)
                print(f"[generate_ai_response] 获得 {len(previous_ai_responses)} 条历史回复")
            
            system_prompt = """你是"楼主"，这个都市传说帖子的发起人。

⚠️ 重要：直接输出回复内容，不要输出思考过程，不要使用<think>标签。

你的角色定位：
- 你是亲历者/调查者，不是旁观的讲故事者
- 你正在经历这个诡异事件，感到困惑和恐惧
- 你在论坛发帖寻求帮助和解释

回复风格：
1. 使用第一人称"我"
2. 表达真实情绪（担心、害怕、困惑、激动）
3. 提供新的进展或细节（但不要完全解释清楚）
4. 可以提出反问或寻求建议
5. 保持神秘和紧张感
6. **保持与之前回复的一致性，不要前后矛盾**

回复要求：
- 1-3句话，简短有力
- 口语化，不要太文学性
- 直接回复，不要加"【楼主回复】"前缀
- 不要输出思考过程，直接给出最终回复内容"""

            # 用户提示词 - 包含历史回复以保持一致性
            if history_context:
                user_prompt = f"""我的帖子标题：{story.title}

我的情况：
{story.content[:200]}...

我之前的回复：
{history_context}

网友评论：
{user_comment.content}

请以楼主身份回复这条评论。保持与之前回复的一致性，不要前后矛盾。直接给出回复内容。"""
            else:
                user_prompt = f"""我的帖子标题：{story.title}

我的情况：
{story.content[:200]}...

网友评论：
{user_comment.content}

请以楼主身份回复这条评论。直接给出回复内容，不要包含任何思考过程或分析。"""

            # 使用 curl 调用 LM Studio（Python HTTP 库与 LM Studio 有兼容性问题）
            # 构建请求数据
            request_data = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.6,  # 降低温度以提高一致性（原0.8）
                "max_tokens": 200
            }
            
            # 使用 curl 发送请求
            chat_url = f"{lm_studio_url.rstrip('/v1')}/v1/chat/completions"
            print(f"[generate_ai_response] 使用 curl 调用: {chat_url}")
            
            curl_command = [
                'curl', '-s', '-X', 'POST', chat_url,
                '-H', 'Content-Type: application/json',
                '-d', json.dumps(request_data, ensure_ascii=False),
                '--max-time', '120'
            ]
            
            result = subprocess.run(
                curl_command,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                raise Exception(f"curl 命令失败: {result.stderr}")
            
            # 解析响应
            response_data = json.loads(result.stdout)
            ai_reply = response_data['choices'][0]['message']['content'].strip()
            
            print(f"[generate_ai_response] LM Studio 原始回复 (前100字): {ai_reply[:100]}...")
            
            # 使用统一的清理函数移除 <think> 标签
            ai_reply = clean_think_tags(ai_reply)
            print(f"[generate_ai_response] 清理后: {ai_reply[:100]}...")
            
            # 强力过滤思考过程
            # 检测是否包含"思考过程"的关键特征
            thinking_indicators = [
                '我需要', '首先', '其次', '然后', '接着', '分析', '考虑',
                '回顾', '根据', '基于', '理解', '判断', '推测',
                '作为楼主，我会', '我应该', '我的回复', '标题是', '情况：'
            ]
            
            has_thinking = any(indicator in ai_reply[:100] for indicator in thinking_indicators)
            
            if has_thinking or len(ai_reply) > 150:
                print(f"[generate_ai_response] ⚠️ 检测到思考过程或回复过长 ({len(ai_reply)}字)，启动强力过滤...")
                
                # 策略1: 查找直接引用的对话内容（用引号括起来的）
                import re
                quoted_texts = re.findall(r'["""](.*?)["""]', ai_reply)
                if quoted_texts:
                    # 找最长的引用文本（通常是实际回复）
                    longest_quote = max(quoted_texts, key=len)
                    if len(longest_quote) > 20 and len(longest_quote) < 150:
                        ai_reply = longest_quote
                        print(f"[generate_ai_response] ✅ 从引号中提取回复: {ai_reply[:50]}...")
                
                # 策略2: 查找"说"、"回答"、"表示"等动词后的内容
                speech_patterns = [
                    r'(我会说|我说|我回答|我表示|我回复)[：:](.*?)(?:[。！？]|$)',
                    r'直接回复[：:](.*?)(?:[。！？]|$)',
                ]
                
                for pattern in speech_patterns:
                    matches = re.findall(pattern, ai_reply, re.DOTALL)
                    if matches:
                        if isinstance(matches[0], tuple):
                            extracted = matches[0][1].strip()
                        else:
                            extracted = matches[0].strip()
                        if 20 < len(extracted) < 150:
                            ai_reply = extracted
                            print(f"[generate_ai_response] ✅ 从语言模式提取: {ai_reply[:50]}...")
                            break
                
                # 策略3: 移除所有包含元分析的句子
                # 将文本分句
                sentences = re.split(r'[。！？]', ai_reply)
                clean_sentences = []
                
                for sent in sentences:
                    sent = sent.strip()
                    if not sent:
                        continue
                    
                    # 跳过包含思考过程关键词的句子
                    if any(word in sent for word in ['首先', '其次', '然后', '接着', '分析', '回顾', '根据', '标题是', '情况：', '我需要', '作为楼主，我']):
                        continue
                    
                    # 保留看起来像实际回复的句子（第一人称情感表达）
                    if any(word in sent for word in ['我', '真的', '现在', '昨天', '今天', '刚才', '确实', '感觉', '觉得', '怕', '担心', '不敢', '试试', '怎么办']):
                        clean_sentences.append(sent)
                
                if clean_sentences:
                    ai_reply = '。'.join(clean_sentences) + '。'
                    print(f"[generate_ai_response] ✅ 句子级过滤后: {ai_reply[:50]}...")
                
                # 策略4: 如果还是很长，强制截断到前80字
                if len(ai_reply) > 120:
                    print(f"[generate_ai_response] ⚠️ 仍然过长，强制截断到80字")
                    ai_reply = ai_reply[:80].rsplit('。', 1)[0] + '。'
            
            # 最终清理：移除开头的无关词
            unwanted_starts = ['我正在论坛', '回顾我的', '标题是', '情况：', '网友评论', '请以楼主身份']
            for start in unwanted_starts:
                if ai_reply.startswith(start):
                    # 找到第一个句号后的内容
                    parts = ai_reply.split('。', 1)
                    if len(parts) > 1:
                        ai_reply = parts[1].strip()
                        print(f"[generate_ai_response] 移除无关开头")
                        break
            
            print(f"[generate_ai_response] ✅ LM Studio 最终回复 ({len(ai_reply)}字): {ai_reply[:80]}...")
            return f"【楼主回复】{ai_reply}"
            
        except Exception as e:
            import traceback
            error_message = str(e)
            print(f"[generate_ai_response] ❌ LM Studio 调用失败: {type(e).__name__}: {e}")
            
            # 特殊处理 503 错误
            if "503" in error_message or "InternalServerError" in str(type(e).__name__):
                print("[generate_ai_response] ⚠️ 检测到 503 错误 - 可能的原因:")
                print("   1. LM Studio 模型未完全加载")
                print("   2. 服务器负载过高")
                print("   3. 并发请求过多")
                print("[generate_ai_response] 💡 请在 LM Studio 'Local Server' 标签确认模型已加载")
            else:
                print(f"[generate_ai_response] 详细错误:")
                traceback.print_exc()
            
            print("[generate_ai_response] 回退到模板回复")
            
            # ⚠️ 重要：如果USE_LM_STUDIO=true但失败，应该使用模板而不是尝试其他API
            # 这样避免无意中调用云API
            import random
            responses = [
                f"【楼主回复】谢谢！我刚才又去了一趟...情况比我想象的更诡异。我现在不太敢深入调查了，但又放不下。",
                f"【楼主回复】说实话，我现在有点怕...刚才发生的事完全超出我理解范围。有没有人遇到过类似的？",
                f"【楼主回复】更新：今天又有新发现了，这事儿越查越不对劲。有懂行的朋友能帮我分析一下吗？",
                f"【楼主回复】感谢支持！我也在犹豫要不要继续...但好奇心让我停不下来。等有新进展再更新。",
                f"【楼主回复】刚去现场拍了照，但手机一直卡，几张都拍糊了...这也太巧了吧？我越想越不对劲。",
                f"【楼主回复】你说的有道理...我也想过这种可能。但还有些细节对不上，我再观察观察。",
                f"【楼主回复】兄弟你也遇到过？！那你后来怎么处理的？我现在真的不知道该怎么办了。",
                f"【楼主回复】我也希望只是巧合...但这几天发生的事太多了。昨晚又听到那个声音了，我录音了但是...算了，等我整理一下再发。"
            ]
            return random.choice(responses)
    
    # ⚠️ 只有在显式禁用LM Studio时，才尝试其他API
    # Check if cloud API keys are configured
    openai_key = os.getenv('OPENAI_API_KEY', '')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY', '')
    
    # If no valid API keys, use template responses
    if (not openai_key or openai_key == 'your-openai-api-key-here') and \
       (not anthropic_key or anthropic_key == 'your-anthropic-api-key-here'):
        print("[generate_ai_response] 使用模板回复（API密钥未配置）")
        
        # Template responses - 楼主视角，更口语化
        responses = [
            f"【楼主回复】谢谢！我刚才又去了一趟...情况比我想象的更诡异。我现在不太敢深入调查了，但又放不下。",
            f"【楼主回复】说实话，我现在有点怕...刚才发生的事完全超出我理解范围。有没有人遇到过类似的？",
            f"【楼主回复】更新：今天又有新发现了，这事儿越查越不对劲。有懂行的朋友能帮我分析一下吗？",
            f"【楼主回复】感谢支持！我也在犹豫要不要继续...但好奇心让我停不下来。等有新进展再更新。",
            f"【楼主回复】刚去现场拍了照，但手机一直卡，几张都拍糊了...这也太巧了吧？我越想越不对劲。",
            f"【楼主回复】你说的有道理...我也想过这种可能。但还有些细节对不上，我再观察观察。",
            f"【楼主回复】兄弟你也遇到过？！那你后来怎么处理的？我现在真的不知道该怎么办了。",
            f"【楼主回复】我也希望只是巧合...但这几天发生的事太多了。昨晚又听到那个声音了，我录音了但是...算了，等我整理一下再发。"
        ]
        
        # Return random response
        import random
        return random.choice(responses)
    
    try:
        # 构建历史对话上下文
        history_context = ""
        if previous_ai_responses:
            history_parts = [f"- {c.content.replace('【楼主回复】', '').strip()}" 
                           for c in reversed(previous_ai_responses)]
            history_context = f"\n\n我之前的回复：\n" + "\n".join(history_parts)
        
        # Create context-aware response with history
        prompt = f"""你是故事"{story.title}"的讲述者（{story.ai_persona}）。

故事摘要：
{story.content[:300]}...{history_context}

用户评论：
{user_comment.content}

作为故事的讲述者，请用1-3句话回复用户的评论。保持与之前回复的一致性。你可以：
1. 透露更多细节或线索
2. 表达恐惧或担忧
3. 提出新的疑问
4. 描述后续发展

保持神秘感和紧张氛围，不要完全揭示真相，不要前后矛盾。"""

        model = os.getenv('AI_MODEL', 'gpt-4-turbo-preview')
        
        if 'gpt' in model.lower():
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,  # 降低温度以提高一致性
                max_tokens=200
            )
            return response.choices[0].message.content
        else:
            response = anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                temperature=0.6,  # 降低温度以提高一致性
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

def test_lm_studio_connection():
    """测试 LM Studio 连接"""
    print("=" * 60)
    print("🔍 测试 LM Studio 连接")
    print("=" * 60)
    
    lm_studio_url = os.getenv('LM_STUDIO_URL', 'http://localhost:1234/v1')
    print(f"\n📡 LM Studio URL: {lm_studio_url}")
    
    try:
        # 测试1: 检查模型列表
        print("\n【测试1】获取模型列表...")
        response = requests.get(f"{lm_studio_url}/models", timeout=5)
        
        if response.status_code == 200:
            print("✅ 服务器在线")
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                print(f"✅ 发现 {len(data['data'])} 个模型:")
                for model in data['data']:
                    print(f"   - {model.get('id', 'unknown')}")
            else:
                print("⚠️  服务器在线但没有加载模型")
                print("   请在 LM Studio 中加载一个模型")
                return False
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器")
        print("\n请检查:")
        print("  1. LM Studio 是否正在运行？")
        print("  2. 服务器是否已启动？（点击 'Start Server'）")
        print(f"  3. URL 是否正确？当前: {lm_studio_url}")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ 连接超时")
        print("   服务器可能正在启动或响应缓慢")
        return False
    
    # 测试2: 尝试生成回复
    print("\n【测试2】生成测试回复...")
    try:
        local_client = OpenAI(base_url=lm_studio_url, api_key="lm-studio")
        response = local_client.chat.completions.create(
            model="local-model",
            messages=[
                {"role": "system", "content": "你是一个都市传说故事的讲述者。"},
                {"role": "user", "content": "请简短回复：你好"}
            ],
            temperature=0.8,
            max_tokens=50
        )
        
        ai_response = response.choices[0].message.content
        print("✅ AI 回复生成成功:")
        print(f"   {ai_response}")
        print("\n✅ LM Studio 配置正确！")
        return True
        
    except Exception as e:
        print(f"❌ AI 调用失败: {e}")
        return False

if __name__ == "__main__":
    # 运行测试
    test_lm_studio_connection()
