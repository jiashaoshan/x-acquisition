#!/usr/bin/env python3
"""
X 平台评论区获客模块
功能：搜索帖子 → AI评分 → 生成评论 → 自动评论
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any

import requests

# 导入 LLM 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from x_llm import generate_keywords, generate_comment, score_post

# BrowserWing 配置
BW_EXECUTOR_URL = os.getenv("BROWSERWING_EXECUTOR_URL", "http://127.0.0.1:8080")
BW_SEARCH_SCRIPT_ID = "d38f7868-bf25-4943-8cc3-87bc48617c41"
BW_COMMENT_SCRIPT_ID = "529333b7-d324-409b-8812-3285b3a12cd0"

# 数据目录
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
HISTORY_FILE = os.path.join(DATA_DIR, "commented-history.json")

# 风控配置
MAX_COMMENTS_PER_RUN = 5
MAX_COMMENTS_PER_DAY = 20
MIN_SCORE_THRESHOLD = 60  # 最低评分阈值


def load_history() -> list:
    """加载已评论历史"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_history(history: list):
    """保存评论历史"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def search_posts(keyword: str) -> List[Dict[str, Any]]:
    """
    调用 BrowserWing 脚本搜索帖子
    
    Args:
        keyword: 搜索关键词
    
    Returns:
        帖子列表，每个包含 url, content, author 等
    """
    url = f"{BW_EXECUTOR_URL}/api/v1/scripts/{BW_SEARCH_SCRIPT_ID}/play"
    
    payload = {
        "params": {
            "关键词": keyword
        }
    }
    
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"[INFO] Search result keys: {result.keys()}")
        
        # 从 result.result.extracted_data 中提取数据
        extracted_data = {}
        if "result" in result and isinstance(result["result"], dict):
            if "extracted_data" in result["result"]:
                extracted_data = result["result"]["extracted_data"]
        
        # 合并 result0, result1, result2
        all_posts = []
        for key in ["result0", "result1", "result2"]:
            if key in extracted_data and extracted_data[key]:
                try:
                    posts = extracted_data[key]
                    if isinstance(posts, list):
                        all_posts.extend(posts)
                    elif isinstance(posts, dict):
                        all_posts.append(posts)
                except Exception as e:
                    print(f"[WARN] Failed to parse {key}: {e}")
        
        # 去重（基于 URL）
        seen_urls = set()
        unique_posts = []
        for post in all_posts:
            post_url = post.get("url", "") or post.get("link", "")
            if post_url and post_url not in seen_urls:
                seen_urls.add(post_url)
                unique_posts.append(post)
        
        print(f"[INFO] Found {len(unique_posts)} unique posts")
        return unique_posts
    
    except Exception as e:
        print(f"[ERROR] Search failed: {e}")
        return []


def comment_on_post(post_url: str, content: str, dry_run: bool = False) -> dict:
    """
    调用 BrowserWing 脚本发表评论
    
    Args:
        post_url: 帖子链接
        content: 评论内容
        dry_run: 是否仅测试
    
    Returns:
        {"success": bool, "message": str}
    """
    if dry_run:
        print(f"[DRY-RUN] Would comment on {post_url}: {content[:50]}...")
        return {"success": True, "message": "Dry run mode"}
    
    url = f"{BW_EXECUTOR_URL}/api/v1/scripts/{BW_COMMENT_SCRIPT_ID}/play"
    
    payload = {
        "params": {
            "内容": content,
            "帖子链接": post_url
        }
    }
    
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"[INFO] Comment result: {result}")
        return {
            "success": True,
            "message": "Comment posted",
            "raw": result
        }
    except Exception as e:
        print(f"[ERROR] Failed to comment: {e}")
        return {"success": False, "message": str(e)}


def acquire_comments(
    product_url: str,
    product_name: str = "",
    keywords: List[str] = None,
    max_comments: int = MAX_COMMENTS_PER_RUN,
    dry_run: bool = False,
    min_score: int = MIN_SCORE_THRESHOLD
) -> dict:
    """
    评论区获客主流程
    
    Args:
        product_url: 产品链接
        product_name: 产品名称
        keywords: 指定关键词列表（可选）
        max_comments: 本次最多评论数
        dry_run: 测试模式
        min_score: 最低评分阈值
    
    Returns:
        {"success": bool, "total": int, "comments": list}
    """
    print(f"[INFO] Starting comment acquisition for: {product_url}")
    print(f"[INFO] Max comments: {max_comments}, Min score: {min_score}")
    
    # 1. 生成关键词
    if not keywords:
        print(f"[INFO] Generating keywords...")
        keywords = generate_keywords(product_url, product_name)
    print(f"[INFO] Keywords: {keywords}")
    
    # 2. 加载历史记录
    history = load_history()
    commented_urls = {item.get("post_url", "") for item in history}
    print(f"[INFO] Already commented on {len(commented_urls)} posts")
    
    # 3. 搜索帖子
    all_posts = []
    for keyword in keywords[:3]:  # 最多用前3个关键词
        print(f"[INFO] Searching with keyword: {keyword}")
        posts = search_posts(keyword)
        all_posts.extend(posts)
    
    # 去重
    seen_urls = set()
    unique_posts = []
    for post in all_posts:
        url = post.get("url", "") or post.get("link", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_posts.append(post)
    
    print(f"[INFO] Total unique posts: {len(unique_posts)}")
    
    # 4. 过滤已评论
    new_posts = [p for p in unique_posts if (p.get("url") or p.get("link")) not in commented_urls]
    print(f"[INFO] New posts (not commented): {len(new_posts)}")
    
    # 5. AI 评分和排序
    scored_posts = []
    for post in new_posts[:20]:  # 最多评分前20个
        post_content = post.get("content", "") or post.get("text", "")
        post_url = post.get("url", "") or post.get("link", "")
        
        if not post_content or not post_url:
            continue
        
        score_result = score_post(post_content, product_url)
        post["_score"] = score_result.get("score", 0)
        post["_score_reason"] = score_result.get("reason", "")
        scored_posts.append(post)
    
    # 按评分排序
    scored_posts.sort(key=lambda x: x.get("_score", 0), reverse=True)
    
    # 6. 评论高价值帖子
    comments_made = []
    for post in scored_posts[:max_comments]:
        post_url = post.get("url", "") or post.get("link", "")
        post_content = post.get("content", "") or post.get("text", "")
        score = post.get("_score", 0)
        
        if score < min_score:
            print(f"[INFO] Skipping low score post ({score}): {post_url[:50]}...")
            continue
        
        print(f"[INFO] Processing post (score: {score}): {post_url[:50]}...")
        
        # 生成评论
        print(f"[INFO] Generating comment...")
        comment = generate_comment(post_content, product_url, product_name)
        print(f"[INFO] Generated comment: {comment[:100]}...")
        
        # 发表评论
        result = comment_on_post(post_url, comment, dry_run)
        
        if result["success"]:
            comments_made.append({
                "post_url": post_url,
                "post_content": post_content[:200],
                "comment": comment,
                "score": score,
                "commented_at": datetime.now().isoformat()
            })
            
            # 记录历史
            if not dry_run:
                history.append({
                    "post_url": post_url,
                    "comment": comment,
                    "score": score,
                    "commented_at": datetime.now().isoformat()
                })
                save_history(history)
            
            print(f"[INFO] ✓ Commented on post ({len(comments_made)}/{max_comments})")
        else:
            print(f"[ERROR] Failed to comment: {result.get('message')}")
    
    print(f"[INFO] Comment acquisition completed: {len(comments_made)} comments")
    
    return {
        "success": True,
        "total": len(comments_made),
        "comments": comments_made
    }


def main():
    parser = argparse.ArgumentParser(description="X 平台评论区获客工具")
    parser.add_argument("--product-url", required=True, help="产品链接")
    parser.add_argument("--product-name", default="", help="产品名称")
    parser.add_argument("--keywords", default="", help="关键词，逗号分隔")
    parser.add_argument("--max-comments", type=int, default=MAX_COMMENTS_PER_RUN, help="最大评论数")
    parser.add_argument("--min-score", type=int, default=MIN_SCORE_THRESHOLD, help="最低评分阈值")
    parser.add_argument("--dry-run", action="store_true", help="测试模式")
    
    args = parser.parse_args()
    
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()] if args.keywords else None
    
    result = acquire_comments(
        product_url=args.product_url,
        product_name=args.product_name,
        keywords=keywords,
        max_comments=args.max_comments,
        dry_run=args.dry_run,
        min_score=args.min_score
    )
    
    print(f"\n{'='*50}")
    print(f"Total comments: {result['total']}")
    for i, c in enumerate(result['comments'], 1):
        print(f"\n[{i}] Score: {c['score']}")
        print(f"    Post: {c['post_url']}")
        print(f"    Comment: {c['comment'][:80]}...")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
