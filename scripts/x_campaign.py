#!/usr/bin/env python3
"""
X 平台获客技能 - 统一编排入口
功能：发帖 + 评论区获客
"""

import os
import sys
import argparse
import json
from typing import Optional

# 导入子模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from x_post import create_post
from x_comment_acquisition import acquire_comments

# 版本信息
VERSION = "1.0.0"


def init_config():
    """初始化配置文件"""
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
    os.makedirs(config_dir, exist_ok=True)
    
    # keywords.json
    keywords_file = os.path.join(config_dir, "keywords.json")
    if not os.path.exists(keywords_file):
        with open(keywords_file, "w", encoding="utf-8") as f:
            json.dump({
                "seed_keywords": ["AI", "工具", "效率", "automation", "productivity"],
                "default_product_url": "",
                "default_product_name": ""
            }, f, ensure_ascii=False, indent=2)
        print(f"[INFO] Created: {keywords_file}")
    
    # filter.json
    filter_file = os.path.join(config_dir, "filter.json")
    if not os.path.exists(filter_file):
        with open(filter_file, "w", encoding="utf-8") as f:
            json.dump({
                "min_score": 60,
                "max_comments_per_run": 5,
                "max_comments_per_day": 20,
                "min_comment_interval": 180,
                "banned_keywords": ["spam", "scam", "fake"]
            }, f, ensure_ascii=False, indent=2)
        print(f"[INFO] Created: {filter_file}")
    
    print("[INFO] Configuration initialized")


def run_all(product_url: str, product_name: str = "", dry_run: bool = False, max_comments: int = 5):
    """
    运行完整流程：发帖 + 评论区获客
    
    Args:
        product_url: 产品链接
        product_name: 产品名称
        dry_run: 测试模式
        max_comments: 最大评论数
    """
    print(f"\n{'='*60}")
    print(f"X 平台获客全链路")
    print(f"Product: {product_url}")
    print(f"Mode: {'DRY-RUN' if dry_run else 'LIVE'}")
    print(f"{'='*60}\n")
    
    results = {
        "post": None,
        "comments": None
    }
    
    # 1. 发帖
    print("【步骤 1/2】自动发帖")
    print("-" * 40)
    post_result = create_post(
        product_url=product_url,
        product_name=product_name,
        dry_run=dry_run
    )
    results["post"] = post_result
    
    if post_result["success"]:
        print(f"✓ Post created successfully")
        if post_result.get("url"):
            print(f"  URL: {post_result['url']}")
    else:
        print(f"✗ Post creation failed: {post_result.get('message', 'Unknown error')}")
    
    print()
    
    # 2. 评论区获客
    print("【步骤 2/2】评论区获客")
    print("-" * 40)
    comment_result = acquire_comments(
        product_url=product_url,
        product_name=product_name,
        max_comments=max_comments,
        dry_run=dry_run
    )
    results["comments"] = comment_result
    
    if comment_result["success"]:
        print(f"✓ Comment acquisition completed: {comment_result['total']} comments")
    else:
        print(f"✗ Comment acquisition failed")
    
    # 汇总
    print(f"\n{'='*60}")
    print(f"执行完成")
    print(f"{'='*60}")
    print(f"发帖: {'✓' if results['post']['success'] else '✗'}")
    print(f"评论: {results['comments']['total']} 条")
    print(f"{'='*60}\n")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="X 平台获客技能 - 统一编排",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 初始化配置
  python3 x_campaign.py --init-config
  
  # 测试模式 - 发帖
  python3 x_campaign.py --post --product-url "https://example.com" --dry-run
  
  # 测试模式 - 评论区获客
  python3 x_campaign.py --acquire --product-url "https://example.com" --dry-run
  
  # 完整流程
  python3 x_campaign.py --all --product-url "https://example.com"
  
  # 指定关键词获客
  python3 x_campaign.py --acquire --product-url "https://example.com" --keywords "AI,工具,效率"
        """
    )
    
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("--init-config", action="store_true", help="初始化配置文件")
    
    # 功能选择
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument("--post", action="store_true", help="仅发帖")
    action_group.add_argument("--acquire", action="store_true", help="仅评论区获客")
    action_group.add_argument("--all", action="store_true", help="完整流程（发帖+获客）")
    
    # 参数
    parser.add_argument("--product-url", help="产品链接")
    parser.add_argument("--product-name", default="", help="产品名称")
    parser.add_argument("--keywords", default="", help="关键词，逗号分隔")
    parser.add_argument("--max-comments", type=int, default=5, help="最大评论数（默认5）")
    parser.add_argument("--min-score", type=int, default=60, help="最低评分阈值（默认60）")
    parser.add_argument("--dry-run", action="store_true", help="测试模式，不实际发布")
    parser.add_argument("--content", default="", help="手动指定发帖内容（跳过AI生成）")
    
    args = parser.parse_args()
    
    # 初始化配置
    if args.init_config:
        init_config()
        return
    
    # 检查必要参数
    if not args.product_url and not args.init_config:
        parser.error("--product-url is required (unless using --init-config)")
    
    # 默认执行完整流程
    if not args.post and not args.acquire and not args.all:
        args.all = True
    
    # 执行对应功能
    if args.post:
        # 仅发帖
        result = create_post(
            product_url=args.product_url,
            product_name=args.product_name,
            dry_run=args.dry_run,
            skip_generation=bool(args.content),
            content=args.content
        )
        print(f"\n{'='*50}")
        print(f"发帖结果: {'✓ Success' if result['success'] else '✗ Failed'}")
        if result.get('url'):
            print(f"URL: {result['url']}")
        print(f"{'='*50}")
    
    elif args.acquire:
        # 仅评论区获客
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
        print(f"评论获客结果: {result['total']} 条评论")
        print(f"{'='*50}")
    
    else:
        # 完整流程
        run_all(
            product_url=args.product_url,
            product_name=args.product_name,
            dry_run=args.dry_run,
            max_comments=args.max_comments
        )


if __name__ == "__main__":
    main()
