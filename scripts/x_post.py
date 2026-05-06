#!/usr/bin/env python3
"""
X 平台发帖模块
功能：根据产品链接生成内容并自动发帖
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Optional

import requests

# 导入 LLM 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from x_llm import generate_post_content

# BrowserWing 配置
BW_EXECUTOR_URL = os.getenv("BROWSERWING_EXECUTOR_URL", "http://127.0.0.1:8080")
BW_POST_SCRIPT_ID = "315acb7e-e73e-4af2-b351-575ce7065d9b"

# 数据目录
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
HISTORY_FILE = os.path.join(DATA_DIR, "posted-history.json")


def load_history() -> list:
    """加载已发帖历史"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_history(history: list):
    """保存发帖历史"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def post_to_x(content: str, dry_run: bool = False) -> dict:
    """
    调用 BrowserWing 脚本发帖
    
    Args:
        content: 帖子内容
        dry_run: 是否仅测试不实际发布
    
    Returns:
        {"success": bool, "message": str, "url": str}
    """
    if dry_run:
        print(f"[DRY-RUN] Would post: {content[:100]}...")
        return {"success": True, "message": "Dry run mode", "url": ""}
    
    url = f"{BW_EXECUTOR_URL}/api/v1/scripts/{BW_POST_SCRIPT_ID}/play"
    
    payload = {
        "params": {
            "内容": content
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
        
        print(f"[INFO] Post result: {result}")
        return {
            "success": True,
            "message": "Posted successfully",
            "url": result.get("url", ""),
            "raw": result
        }
    except Exception as e:
        print(f"[ERROR] Failed to post: {e}")
        return {"success": False, "message": str(e), "url": ""}


def create_post(
    product_url: str,
    product_name: str = "",
    dry_run: bool = False,
    skip_generation: bool = False,
    content: str = ""
) -> dict:
    """
    创建并发布帖子
    
    Args:
        product_url: 产品链接
        product_name: 产品名称
        dry_run: 测试模式
        skip_generation: 跳过 AI 生成，使用提供的内容
        content: 手动提供的内容（如果 skip_generation=True）
    
    Returns:
        {"success": bool, "content": str, "url": str}
    """
    print(f"[INFO] Creating post for: {product_url}")
    
    # 1. 生成帖子内容
    if skip_generation and content:
        post_content = content
        print(f"[INFO] Using provided content")
    else:
        print(f"[INFO] Generating content with LLM...")
        result = generate_post_content(product_url, product_name)
        post_content = result.get("content", "")
        if not post_content:
            print("[ERROR] Failed to generate content")
            return {"success": False, "content": "", "url": ""}
        print(f"[INFO] Generated content: {post_content[:100]}...")
    
    # 2. 检查重复
    history = load_history()
    for item in history:
        if item.get("content") == post_content:
            print(f"[WARN] Duplicate post detected, skipping")
            return {"success": False, "content": post_content, "url": "", "reason": "duplicate"}
    
    # 3. 发布帖子
    print(f"[INFO] Posting to X...")
    result = post_to_x(post_content, dry_run)
    
    if result["success"] and not dry_run:
        # 4. 记录历史
        history.append({
            "content": post_content,
            "product_url": product_url,
            "posted_at": datetime.now().isoformat(),
            "post_url": result.get("url", "")
        })
        save_history(history)
        print(f"[INFO] Posted and saved to history")
    
    return {
        "success": result["success"],
        "content": post_content,
        "url": result.get("url", ""),
        "message": result.get("message", "")
    }


def main():
    parser = argparse.ArgumentParser(description="X 平台发帖工具")
    parser.add_argument("--product-url", required=True, help="产品链接")
    parser.add_argument("--product-name", default="", help="产品名称")
    parser.add_argument("--dry-run", action="store_true", help="测试模式，不实际发布")
    parser.add_argument("--content", default="", help="手动指定内容（跳过 AI 生成）")
    
    args = parser.parse_args()
    
    result = create_post(
        product_url=args.product_url,
        product_name=args.product_name,
        dry_run=args.dry_run,
        skip_generation=bool(args.content),
        content=args.content
    )
    
    print(f"\n{'='*50}")
    print(f"Result: {'✓ Success' if result['success'] else '✗ Failed'}")
    print(f"Content: {result['content'][:100]}...")
    if result.get('url'):
        print(f"URL: {result['url']}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
