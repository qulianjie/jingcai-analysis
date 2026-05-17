# -*- coding: utf-8 -*-
"""
小红书温暖治愈系内容自动生成器 v8（热点抚慰版）
每日流程：
  1. Agent 通过 web_search 搜索今日热点，保存到热点文件
  2. 本脚本读取热点文件
  3. 筛选负面情绪热点 + 匹配合适的治愈主题
  4. 生成3份抚慰疗愈内容

输出目录：自媒体/每日内容/YYYY-MM-DD/
"""
import json, os, urllib.request, sys, codecs, time, random, re
from datetime import datetime

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

# ===== 配置 =====
DEEPSEEK_API_KEY = 'sk-17de3b2f97be421db0996102d66a94ed'
YERPLAN_API_KEY = 'sk-EVf76W31pVpo3eUIuZ9mqfcpc36BQ55B2glLyNwqglUgjg7V'
YERPLAN_BASE_URL = 'https://api.qiyue999.com/v1'
YERPLAN_MODEL = 'MiniMax-M2.7'

workspace = os.path.join(os.environ['USERPROFILE'], '.openclaw', 'workspace')
base_dir = os.path.join(workspace, '自媒体', '每日内容')

# ===== 主题库 =====
themes = [
    {'title': '童年的夏夜', 'theme_desc': '小时候在外乘凉，躺在凉席上看星星，奶奶扇着蒲扇，蝉鸣蛙叫，单纯到觉得世界很简单', 'video_style': '夏夜庭院，暖黄灯光，怀旧色调', 'is_childhood': True},
    {'title': '童年的小卖部', 'theme_desc': '放学后冲进小卖部，买一毛钱的辣条或者冰棍，和老板熟到赊账，觉得自己是全世界最富有的人', 'video_style': '街道小卖部，阳光斑驳，怀旧氛围', 'is_childhood': True},
    {'title': '童年的大雪', 'theme_desc': '冬天早上醒来窗外一片雪白，激动地穿上棉衣冲出去，堆雪人打雪仗，脸冻得通红但心里热乎乎的', 'video_style': '雪后清晨，银装素裹，童年纯真', 'is_childhood': True},
    {'title': '童年的大雨', 'theme_desc': '夏天突如其来的暴雨，街上的人四处奔逃，自己撑着伞踩水坑，水溅了一身但笑得很开心', 'video_style': '雨天街道，水花飞溅，童年快乐', 'is_childhood': True},
    {'title': '童年的大巴', 'theme_desc': '第一次坐大巴去远方，贴着车窗看外面风景飞速后退，觉得外面的世界一定很精彩', 'video_style': '车内视角望向窗外，街景流动，憧憬感', 'is_childhood': True},
    {'title': '童年的赶集', 'theme_desc': '跟大人去镇上赶集，人山人海，各种叫卖声，糖葫芦和棉花糖，觉得好热闹好幸福', 'video_style': '热闹集市，人群涌动，烟火气', 'is_childhood': True},
    {'title': '童年的年夜饭', 'theme_desc': '除夕夜一家人围在一起，大人在厨房忙，小孩在客厅闹，电视放着春晚，窗外烟花炮竹', 'video_style': '除夕夜，室内温馨，窗外烟花', 'is_childhood': True},
    {'title': '童年的动画片', 'theme_desc': '守着电视机等动画片开播，大头儿子小头爸爸西游记，觉得快乐很简单', 'video_style': '电视前，室内昏暗只有屏幕发光，专注', 'is_childhood': True},
    {'title': '童年的巷子口', 'theme_desc': '巷子口的老槐树，放学后在树下跳皮筋打陀螺，天黑了还不舍得回家', 'video_style': '傍晚巷子口，槐树斑驳光影，童年时光', 'is_childhood': True},
    {'title': '青春散场', 'theme_desc': '高中生街头聚会，人慢慢散了，最后只剩一个人蹲在原地回望青春', 'video_style': '黄昏老街，电影感，暖色调', 'is_childhood': False},
    {'title': '下班路上', 'theme_desc': '第一人称视角，下班后疲惫地走在回家路上，城市从喧闹到安静', 'video_style': '黄昏城市街道，电影感暖色调', 'is_childhood': False},
    {'title': '深夜emo', 'theme_desc': '深夜窗边独处，窗外稀疏灯光，安静的房间，一杯冷掉的咖啡', 'video_style': '深夜室内，冷色调转暖', 'is_childhood': False},
    {'title': '雨天公交', 'theme_desc': '坐在公交车最后一排靠窗，窗外下雨，车厢零星几人，路灯模糊', 'video_style': '雨天车厢内向外看，电影感雨景', 'is_childhood': False},
    {'title': '清晨地铁', 'theme_desc': '清晨天没亮，空旷的地铁站，零星的早起打工人，地铁进站', 'video_style': '清晨地铁站，冷色调', 'is_childhood': False},
    {'title': '周末空房', 'theme_desc': '周末出租屋，阳光从窗帘缝隙照进来，安静的房间，窗外的笑声', 'video_style': '室内自然光，温暖安静', 'is_childhood': False},
    {'title': '深夜食堂', 'theme_desc': '深夜路边小吃摊，昏黄灯光，热气腾腾，一个人安静吃着', 'video_style': '深夜街头，温暖烟火气', 'is_childhood': False},
    {'title': '老街散步', 'theme_desc': '黄昏老街散步，梧桐叶落，小店关门，老人摇蒲扇，孩子追逐', 'video_style': '黄昏老街，怀旧色调', 'is_childhood': False},
    {'title': '电梯里的陌生人', 'theme_desc': '深夜写字楼电梯，只剩自己一个人，从1楼走出去，空荡的大堂', 'video_style': '写字楼内部到门口，冷到暖', 'is_childhood': False},
    {'title': '阳台抽烟', 'theme_desc': '深夜阳台抽烟，远处城市灯火，风吹过来，一个人安静地抽完', 'video_style': '深夜阳台，城市夜景', 'is_childhood': False},
]

# ===== 工具函数 =====
def log(msg):
    print(f'[{datetime.now().strftime("%H:%M:%S")}] {msg}')

def call_deepseek(messages):
    url = 'https://api.deepseek.com/chat/completions'
    headers = {'Authorization': f'Bearer {DEEPSEEK_API_KEY}', 'Content-Type': 'application/json'}
    body = json.dumps({'model': 'deepseek-chat', 'messages': messages, 'temperature': 0.8}).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    resp = urllib.request.urlopen(req, timeout=60)
    return json.loads(resp.read().decode('utf-8'))['choices'][0]['message']['content']

def call_yerplan(messages, model=None):
    model = model or YERPLAN_MODEL
    url = f'{YERPLAN_BASE_URL}/chat/completions'
    headers = {'Authorization': f'Bearer {YERPLAN_API_KEY}', 'Content-Type': 'application/json'}
    body = json.dumps({'model': model, 'messages': messages, 'temperature': 0.8}).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    resp = urllib.request.urlopen(req, timeout=60)
    return json.loads(resp.read().decode('utf-8'))['choices'][0]['message']['content']

def call_llm(messages, label='LLM'):
    """统一LLM调用，DeepSeek优先，失败回退YerPlan"""
    try:
        result = call_deepseek(messages)
        log(f'  {label} 来源: DeepSeek')
        return result
    except Exception as e:
        log(f'  {label} DeepSeek失败: {str(e)[:60]}')
        for model in [YERPLAN_MODEL, 'qwen3.6-plus']:
            try:
                result = call_yerplan(messages, model=model)
                log(f'  {label} 来源: YerPlan({model})')
                return result
            except Exception as e2:
                log(f'  {label} YerPlan({model})失败: {str(e2)[:40]}')
                continue
    raise Exception(f'{label}: 所有模型均失败')

# ===== Step 1: 读取热点文件（由 agent 提前搜索并写入） =====
def load_hotspots_from_file(date_dir):
    """从热点文件读取真实搜索到的热点"""
    hotspot_file = os.path.join(date_dir, '热点原始数据.json')
    if os.path.exists(hotspot_file):
        with open(hotspot_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        hotspots = data.get('hotspots', [])
        log(f'  从文件读取到 {len(hotspots)} 条热点')
        return hotspots
    else:
        log(f'  ⚠️ 未找到热点文件 {hotspot_file}，将使用默认主题')
        return []

# ===== Step 2: 筛选负面情绪热点 =====
def filter_negative_hotspots(hotspots):
    """筛选容易引发负面情绪的热点"""
    log('--- Step 2: 筛选负面情绪热点 ---')

    if not hotspots:
        log('  无热点数据，使用默认主题')
        return []

    messages = [
        {'role': 'system', 'content': '你是一个情感分析助手。从以下热点中筛选出最容易引发普通人负面情绪（焦虑、压力、孤独、迷茫等）的3条。返回编号，每行一个。'},
        {'role': 'user', 'content': '请从以下热点中选出3条最容易引发普通人负面情绪的，返回编号：\n\n' + '\n'.join([f'{i+1}. {h["title"]}（{h.get("emotion", "未知")}）- {h.get("desc", "")}' for i, h in enumerate(hotspots)])}
    ]

    try:
        result = call_llm(messages, '情绪筛选')
        selected_indices = []
        for line in result.strip().split('\n'):
            nums = re.findall(r'\d+', line)
            for n in nums:
                idx = int(n) - 1
                if 0 <= idx < len(hotspots) and idx not in selected_indices:
                    selected_indices.append(idx)
        selected = [hotspots[i] for i in selected_indices[:3]]
        log(f'  选中 {len(selected)} 条负面情绪热点')
        return selected
    except Exception as e:
        log(f'  筛选失败: {e}，使用前3条')
        return hotspots[:3]

# ===== Step 3: 匹配治愈主题 =====
def match_healing_themes(hotspots):
    """将负面情绪热点匹配合适的治愈主题"""
    log('--- Step 3: 匹配治愈主题 ---')

    if not hotspots:
        log('  无热点，随机选主题')
        return [{'hotspot': None, 'theme': t, 'reason': '无热点，随机选取'} for t in pick_random_themes(3)]

    theme_list = '\n'.join([f'- {t["title"]}: {t["theme_desc"][:30]}...' for t in themes])
    hotspot_list = '\n'.join([f'{i+1}. {h["title"]}（引发情绪：{h.get("emotion", "未知")}）- {h.get("desc", "")}' for i, h in enumerate(hotspots)])

    messages = [
        {'role': 'system', 'content': '你是一个内容策划助手。每个引发负面情绪的热点，需要匹配一个治愈主题来抚慰。匹配原则：用童年的单纯美好治愈当下的负面情绪。'},
        {'role': 'user', 'content': f'''需要匹配的热点：
{hotspot_list}

可选治愈主题：
{theme_list}

请为每个热点匹配一个治愈主题。返回格式（每行一个）：
热点编号|治愈主题标题|匹配理由（一句话）

示例：
1|童年的夏夜|用夏夜的宁静治愈当下的焦虑
2|童年的小卖部|用童年的简单快乐治愈工作压力
3|童年的年夜饭|用团圆的温暖治愈孤独感'''
        }
    ]

    try:
        result = call_llm(messages, '主题匹配')
        matched = []
        for line in result.strip().split('\n'):
            line = line.strip()
            if '|' not in line:
                continue
            parts = line.split('|')
            if len(parts) < 3:
                continue
            hotspot_idx = int(parts[0].strip()) - 1
            theme_title = parts[1].strip()
            reason = parts[2].strip()

            hotspot = hotspots[hotspot_idx] if 0 <= hotspot_idx < len(hotspots) else None
            theme = next((t for t in themes if t['title'] == theme_title), None)

            if hotspot and theme:
                matched.append({
                    'hotspot': hotspot,
                    'theme': theme,
                    'reason': reason
                })

        log(f'  匹配成功 {len(matched)} 组')
        for m in matched:
            log(f'  → {m["hotspot"]["title"]} → {m["theme"]["title"]}（{m["reason"]}）')
        return matched
    except Exception as e:
        log(f'  匹配失败: {e}，随机匹配')
        return [{'hotspot': h, 'theme': pick_random_theme(), 'reason': '默认匹配'} for h in hotspots[:3]]

# ===== Step 4: 生成抚慰内容 =====
def generate_healing_copywriting(hotspot, theme):
    """生成一份"热点抚慰"文案"""
    USER_PROMPT = f"""【引发负面情绪的热点】
{hotspot['title']}
情绪类型：{hotspot.get('emotion', '未知')}
描述：{hotspot.get('desc', '')}

【治愈主题】
{theme['title']}
描述：{theme['theme_desc']}
视觉风格：{theme['video_style']}

请创作一份小红书抚慰疗愈内容。核心思路：用治愈主题的美好回忆，温柔地抚慰热点带来的负面情绪。

要求：
1. 先共情热点带来的情绪（不要否定，承认这种感受是正常的）
2. 然后自然过渡到治愈主题（"但你还记得吗..."）
3. 用治愈主题的画面感来对冲负面情绪
4. 结尾给一句温暖有力的话

生成4部分：

【1. 标题】
10-20字，能引发共鸣，不要标题党。

【2. 视频描述】
给AI视频生成模型用的分镜头脚本。
- 用【镜头1】【镜头2】【镜头3】...格式
- 每个镜头写清楚：机位、光线、氛围
- 有人物动作和场景细节描写
- 总长度足够生成10秒视频

【3. 视频配文】
显示在视频上的字幕文案。
- 精简短句，每句5-15字
- 4-8句，有节奏感
- 整体让人动容

【4. 发文总结】
发布在小红书上的正文文案。
- 50-100字
- 先共情，再治愈，像朋友在说话
- 结尾引导互动

格式：
===标题===
[标题内容]

===视频描述===
【镜头1：...】
【镜头2：...】

===视频配文===
第1句
第2句
...

===发文总结===
[正文内容]"""

    messages = [
        {'role': 'system', 'content': '你是小红书温暖治愈系博主，擅长用美好的童年回忆和温暖的生活瞬间，抚慰现代人的焦虑、压力和孤独。你的文字像朋友在深夜聊天，温柔但有力量。'},
        {'role': 'user', 'content': USER_PROMPT}
    ]

    result = call_llm(messages, '文案生成')
    return result

def parse_copywriting(result_text, theme_title):
    title = ''
    video_desc = ''
    video_caption = ''
    publish_summary = ''

    section = None
    for line in result_text.split('\n'):
        line = line.strip()
        if line.startswith('===标题==='):
            section = 'title'
        elif line.startswith('===视频描述==='):
            section = 'desc'
        elif line.startswith('===视频配文==='):
            section = 'caption'
        elif line.startswith('===发文总结==='):
            section = 'summary'
        elif section == 'title' and line:
            title = line
        elif section == 'desc' and line:
            video_desc += line + '\n'
        elif section == 'caption' and line:
            video_caption += line + '\n'
        elif section == 'summary' and line:
            publish_summary += line + '\n'

    if not title:
        title = f'那个{theme_title}的夏天，你还记得吗'
    if not video_desc:
        video_desc = ''
    if not video_caption:
        video_caption = '那时候的我们，简单又快乐。'
    if not publish_summary:
        publish_summary = '愿你今天也被温柔以待。'

    caption_lines = [l.strip() for l in video_caption.split('\n') if l.strip()]
    subtitles = [l for l in caption_lines if len(l) < 25][:8]

    tags = f'#温暖 #治愈 #情感语录 #生活感悟 #{theme_title}'

    return {
        'title': title.strip(),
        'video_desc': video_desc.strip(),
        'video_caption': video_caption.strip(),
        'publish_summary': publish_summary.strip(),
        'subtitles': subtitles,
        'tags': tags
    }

def pick_random_themes(n=3):
    childhood = [t for t in themes if t.get('is_childhood')]
    others = [t for t in themes if not t.get('is_childhood')]
    selected = []
    for i in range(n):
        if random.random() < 0.6 and childhood:
            t = random.choice(childhood)
            childhood.remove(t)
        elif others:
            t = random.choice(others)
            others.remove(t)
        elif childhood:
            t = random.choice(childhood)
            childhood.remove(t)
        selected.append(t)
    return selected

def pick_random_theme():
    return random.choice(themes)

# ===== 主流程 =====
def main():
    today = datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(base_dir, today)
    os.makedirs(date_dir, exist_ok=True)

    log(f'=== 开始生成 {today} 的抚慰内容 (v8) ===')

    # Step 1: 读取热点文件（由 agent 提前搜索并写入）
    log('--- Step 1: 读取热点数据 ---')
    hotspots = load_hotspots_from_file(date_dir)

    # Step 2: 筛选负面情绪热点
    negative_hotspots = filter_negative_hotspots(hotspots)

    # Step 3: 匹配治愈主题
    matched = match_healing_themes(negative_hotspots)

    log(f'\n--- Step 4: 生成文案 ---')
    log(f'共 {len(matched)} 组内容')

    for i, item in enumerate(matched, 1):
        theme = item['theme']
        hotspot = item.get('hotspot')
        reason = item.get('reason', '')

        log(f'\n--- 生成第{i}份: {theme["title"]} ---')
        if hotspot:
            log(f'  关联热点: {hotspot["title"]}（{hotspot.get("emotion", "未知")}）')
        log(f'  匹配理由: {reason}')

        try:
            if hotspot:
                result_text = generate_healing_copywriting(hotspot, theme)
            else:
                result_text = generate_fallback_copywriting(theme)
            log(f'  文案生成 ✅')
        except Exception as e:
            log(f'  生成失败: {e}')
            continue

        data = parse_copywriting(result_text, theme['title'])
        log(f'  标题: {data["title"]}')
        log(f'  发文: {data["publish_summary"][:50]}...')

        # 保存
        prefix = str(i)
        files = {
            f'标题{prefix}.txt': data['title'],
            f'视频描述{prefix}.txt': data['video_desc'],
            f'视频配文{prefix}.txt': data['video_caption'],
            f'发文总结{prefix}.txt': data['publish_summary'],
            f'标签{prefix}.txt': data['tags'],
        }
        if hotspot:
            # Include source URL if available
            source = hotspot.get('source', '')
            source_info = f'来源: {source}' if source else ''
            files[f'关联热点{prefix}.txt'] = f'热点: {hotspot["title"]}\n情绪: {hotspot.get("emotion", "未知")}\n描述: {hotspot.get("desc", "")}\n匹配理由: {reason}\n{source_info}'
            # Save source URL separately for Notion sync
            if source:
                files[f'来源{prefix}.txt'] = source

        for fname, content in files.items():
            with open(os.path.join(date_dir, fname), 'w', encoding='utf-8') as f:
                f.write(content)

        log(f'  第{i}份 ✅')

    log(f'\n=== 完成 ===')

def generate_fallback_copywriting(theme):
    """无热点时的标准文案生成"""
    USER_PROMPT = f"""主题：{theme['title']}
描述：{theme['theme_desc']}
风格：{theme['video_style']}

请根据这个主题，生成一份完整的小红书文案，包含4部分：

【1. 标题】10-20字，引发共鸣
【2. 视频描述】分镜头脚本，【镜头1】【镜头2】...格式
【3. 视频配文】4-8句精简短句，每句5-15字
【4. 发文总结】30-60字，简短有力

格式：
===标题===
[标题]
===视频描述===
【镜头1：...】
===视频配文===
第1句
===发文总结===
[正文]"""

    messages = [
        {'role': 'system', 'content': '你是小红书温暖治愈系博主。'},
        {'role': 'user', 'content': USER_PROMPT}
    ]
    result = call_llm(messages, '文案')
    return result

if __name__ == '__main__':
    main()
