#!/usr/bin/env python3
"""
X 平台获客技能 - LLM API 封装
支持 DeepSeek API，用于生成帖子内容、评论、关键词
"""

import os
import json
import requests
from typing import Optional, List, Dict, Any

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"  # 或 deepseek-v4-flash


def call_llm(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    json_mode: bool = False
) -> str:
    """
    调用 DeepSeek LLM API
    
    Args:
        prompt: 用户提示词
        system_prompt: 系统提示词
        temperature: 随机性 (0-2)
        max_tokens: 最大生成 token 数
        json_mode: 是否强制 JSON 输出
    
    Returns:
        LLM 生成的文本
    """
    if not DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY environment variable not set")
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[ERROR] LLM API call failed: {e}")
        raise


def generate_post_content(product_url: str, product_name: str = "") -> Dict[str, str]:
    """
    生成 X 平台帖子内容
    
    Returns:
        {"content": "帖子内容"}
    """
    system_prompt = """你是 X (Twitter) 平台的内容运营专家。根据产品信息生成吸引人的推文内容。
要求：
1. 内容简洁有力，适合 X 平台风格（严格限制 280 字符以内）
2. 自然融入产品链接
3. 可以包含相关话题标签
4. 语言风格：专业但亲切，有吸引力
5. 输出 JSON 格式：{"content": "帖子内容"}
6. 【重要】总长度必须严格控制在 280 字符以内（含链接和标签）"""

    prompt = f"""请为以下产品生成 X 平台推文：

产品链接：{product_url}
产品名称：{product_name or "未指定"}

要求：
- 生成 1 条推文内容
- 【严格限制】总长度不超过 280 字符（包含链接和标签）
- 如果内容+链接+标签超过 280 字符，请精简内容
- 包含自然的产品推广
- 可添加 1-3 个相关话题标签（标签也计入字符数）

直接输出 JSON：{{"content": "推文内容"}}"""

    try:
        response = call_llm(prompt, system_prompt, json_mode=True)
        # 尝试解析 JSON
        result = json.loads(response)
        return result
    except json.JSONDecodeError:
        # 如果不是 JSON，直接包装
        return {"content": response.strip()}


def detect_language(text: str) -> str:
    """
    检测文本语言
    
    Args:
        text: 待检测文本
    
    Returns:
        语言代码 (zh, ja, en, ko, etc.)
    """
    import re
    
    # 优先级1: 韩文（最优先，避免被其他检测覆盖）
    # 韩文音节 (Hangul Syllables): U+AC00-U+D7AF
    # 韩文 Jamo: U+1100-U+11FF, U+3130-U+318F
    if re.search(r'[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f]', text):
        return 'ko'
    
    # 优先级2: 日文假名
    elif re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):  # 平假名/片假名
        return 'ja'
    
    # 优先级3: 中日韩汉字（CJK）
    elif re.search(r'[\u4e00-\u9fff]', text):
        # 如果包含假名，前面已经返回 ja 了
        # 检查是否有韩文特有的汉字用法或韩文
        ko_specific = ['합니다', '입니다', '감사합니다', '안녕하세요', '그런데']
        if any(kw in text for kw in ko_specific):
            return 'ko'
        return 'zh'  # 默认中文
    
    # 优先级4: 其他语言
    elif re.search(r'[\u0400-\u04ff]', text):  # 俄文
        return 'ru'
    elif re.search(r'[\u0600-\u06ff]', text):  # 阿拉伯文
        return 'ar'
    elif re.search(r'[a-zA-Z]', text):  # 英文
        return 'en'
    else:
        return 'en'  # 默认英文


def get_language_name(lang_code: str) -> str:
    """获取语言名称"""
    lang_map = {
        'zh': '中文',
        'ja': '日语',
        'en': '英语',
        'ko': '韩语',
        'ru': '俄语',
        'ar': '阿拉伯语',
        'fr': '法语',
        'de': '德语',
        'es': '西班牙语',
        'pt': '葡萄牙语',
        'it': '意大利语',
    }
    return lang_map.get(lang_code, 'auto')


def generate_comment(post_content: str, product_url: str, product_name: str = "") -> str:
    """
    根据帖子内容生成评论（自动匹配帖子语言）
    
    Args:
        post_content: 帖子内容
        product_url: 产品链接
        product_name: 产品名称
    
    Returns:
        评论内容（与帖子同语言）
    """
    # 检测帖子语言
    detected_lang = detect_language(post_content)
    lang_name = get_language_name(detected_lang)
    
    # 根据语言调整系统提示词
    system_prompt = f"""你是 X 平台的互动专家。根据帖子内容生成自然、有价值的评论。
【重要】帖子语言是 {lang_name}，你必须用 {lang_name} 回复！
要求：
1. 评论与帖子内容相关
2. 自然融入产品信息（不要硬广）
3. 【严格限制】长度 50-280 字符（X 平台限制）
4. 语气友好、专业
5. 可以提出问题或分享观点"""

    prompt = f"""请为以下帖子生成一条评论：

帖子内容：
{post_content[:500]}

产品信息：
- 链接：{product_url}
- 名称：{product_name or "AI工具"}

【重要要求】：
1. 【语言】检测到帖子语言是 {lang_name}，你必须用 {lang_name} 回复！
   - 如果帖子是中文，你用中文回复
   - 如果帖子是日语，你用日语回复（使用敬语）
   - 如果帖子是英语，你用英语回复
   - 以此类推
2. 【长度】评论长度 50-280 字符（包含链接）
3. 【内容】与帖子内容相关，自然提及产品（可选）
4. 【语气】友好、像真实用户

请用 {lang_name} 直接输出评论内容："""

    return call_llm(prompt, system_prompt, temperature=0.8, max_tokens=500)


def generate_keywords(product_url: str, product_name: str = "") -> List[str]:
    """
    根据产品信息生成搜索关键词
    
    Returns:
        关键词列表
    """
    system_prompt = """你是关键词研究专家。根据产品信息生成适合 X 平台搜索的关键词。
要求：
1. 生成 5-10 个相关关键词
2. 关键词应有助于找到目标用户
3. 包含产品类型、行业、使用场景等维度
4. 输出 JSON 数组格式"""

    prompt = f"""请为以下产品生成 X 平台搜索关键词：

产品链接：{product_url}
产品名称：{product_name or "未指定"}

要求：
- 生成 5-10 个关键词
- 中英文混合（X 平台国际化）
- 覆盖不同维度（产品类型、行业、痛点、场景）
- 输出格式：["关键词1", "关键词2", ...]

直接输出 JSON 数组："""

    try:
        response = call_llm(prompt, system_prompt, json_mode=True)
        keywords = json.loads(response)
        if isinstance(keywords, list):
            return keywords
        elif isinstance(keywords, dict) and "keywords" in keywords:
            return keywords["keywords"]
        else:
            return ["AI", "工具", "效率"]  # 默认关键词
    except Exception as e:
        print(f"[WARN] Keyword generation failed: {e}, using defaults")
        return ["AI", "工具", "效率", "productivity", "automation"]


def score_post(post_content: str, product_url: str) -> Dict[str, Any]:
    """
    AI 评分帖子价值
    
    Returns:
        {"score": 总分, "dimensions": {"热度": 分, "相关性": 分, "时效": 分, "质量": 分}, "reason": "评分理由"}
    """
    system_prompt = """你是内容评估专家。根据帖子内容和产品信息评估帖子价值。
评分维度（满分100）：
- 热度（40分）：互动潜力、话题热度
- 相关性（30分）：与产品的相关程度
- 时效（20分）：内容的时效性
- 质量（20分）：内容质量、可信度

输出 JSON 格式：
{
  "score": 总分,
  "dimensions": {"热度": 分, "相关性": 分, "时效": 分, "质量": 分},
  "reason": "评分理由"
}"""

    prompt = f"""请评估以下帖子的获客价值：

帖子内容：
{post_content[:500]}

产品链接：{product_url}

请给出 4 维评分和总分。直接输出 JSON："""

    try:
        response = call_llm(prompt, system_prompt, json_mode=True)
        return json.loads(response)
    except Exception as e:
        print(f"[WARN] Scoring failed: {e}")
        return {
            "score": 50,
            "dimensions": {"热度": 20, "相关性": 15, "时效": 10, "质量": 5},
            "reason": "默认评分（AI评分失败）"
        }


if __name__ == "__main__":
    # 测试
    print("Testing LLM module...")
    
    # 测试发帖内容生成
    result = generate_post_content("https://ai.hcrzx.com", "慧辰AI分析")
    print(f"Generated post: {result}")
    
    # 测试评论生成
    comment = generate_comment("AI is changing the way we work. What tools do you use?", "https://ai.hcrzx.com")
    print(f"Generated comment: {comment}")
    
    # 测试关键词生成
    keywords = generate_keywords("https://ai.hcrzx.com", "慧辰AI分析")
    print(f"Generated keywords: {keywords}")
