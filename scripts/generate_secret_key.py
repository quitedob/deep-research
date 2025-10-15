#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全密钥生成工具
用于生成强随机密钥以保护系统安全
"""

import secrets
import sys
import argparse


def generate_secret_key(length: int = 32) -> str:
    """生成安全的随机密钥"""
    return secrets.token_urlsafe(length)


def main():
    parser = argparse.ArgumentParser(description="生成安全的随机密钥")
    parser.add_argument(
        "--length",
        type=int,
        default=32,
        help="密钥长度（默认32字符）"
    )
    parser.add_argument(
        "--format",
        choices=["env", "export", "raw"],
        default="env",
        help="输出格式（默认env）"
    )

    args = parser.parse_args()

    try:
        # 生成密钥
        secret_key = generate_secret_key(args.length)

        # 根据格式输出
        if args.format == "env":
            print(f"DEEP_RESEARCH_SECURITY_SECRET_KEY={secret_key}")
        elif args.format == "export":
            print(f"export DEEP_RESEARCH_SECURITY_SECRET_KEY={secret_key}")
        else:  # raw
            print(secret_key)

        print(f"\n✅ 成功生成 {args.length} 字符长度的安全密钥")
        print(f"📝 请将此密钥设置为环境变量以保护您的系统安全")
        print(f"⚠️  请妥善保管此密钥，不要提交到版本控制系统")

    except Exception as e:
        print(f"❌ 生成密钥失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()