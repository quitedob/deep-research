#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的SQLite数据库封装：用户/聊天日志/使用统计  # 模块说明
"""
import os  # 操作系统接口
import sqlite3  # 内置SQLite数据库
from pathlib import Path  # 路径处理
from typing import Optional, Any, Dict, List, Tuple  # 类型注解

DB_PATH = Path(__file__).parent.parent.parent / "data" / "agentwork.db"  # 数据库路径
DB_PATH.parent.mkdir(parents=True, exist_ok=True)  # 确保目录存在


def get_conn() -> sqlite3.Connection:
    """获取数据库连接（启用行工厂）"""  # 函数说明
    conn = sqlite3.connect(str(DB_PATH))  # 连接数据库
    conn.row_factory = sqlite3.Row  # 结果集返回字典风格
    return conn  # 返回连接


def init_db(default_admin_password_hash: str) -> None:
    """初始化数据表并创建默认管理员账户"""  # 函数说明
    with get_conn() as conn:  # 打开连接
        cur = conn.cursor()  # 获取游标
        # 用户表：基础字段 + 角色
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )  # 创建 users 表

        # 聊天日志表：按会话记录每条消息
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_id TEXT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                model TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )  # 创建 chat_logs 表

        # 使用统计表：记录端点/模型/花费（可扩展）
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                endpoint TEXT NOT NULL,
                model TEXT,
                tokens_input INTEGER DEFAULT 0,
                tokens_output INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )  # 创建 usage_logs 表

        # 创建默认管理员 admin/root123456（如不存在）
        cur.execute("SELECT id FROM users WHERE username=?", ("admin",))  # 查询管理员
        row = cur.fetchone()  # 取结果
        if row is None:  # 若不存在
            cur.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("admin", default_admin_password_hash, "admin"),
            )  # 插入默认管理员
        conn.commit()  # 提交事务


def create_user(username: str, password_hash: str) -> int:
    """创建新用户，返回用户ID"""  # 函数说明
    with get_conn() as conn:  # 连接
        cur = conn.cursor()  # 游标
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'user')",
            (username, password_hash),
        )  # 插入用户
        conn.commit()  # 提交
        return cur.lastrowid  # 返回ID


def get_user_by_username(username: str) -> Optional[sqlite3.Row]:
    """按用户名获取用户记录"""  # 函数说明
    with get_conn() as conn:  # 连接
        cur = conn.cursor()  # 游标
        cur.execute("SELECT * FROM users WHERE username=?", (username,))  # 查询
        return cur.fetchone()  # 返回行


def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
    """按ID获取用户"""  # 函数说明
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
        return cur.fetchone()


def insert_chat_log(user_id: Optional[int], session_id: str, role: str, content: str, model: Optional[str]) -> None:
    """插入一条聊天日志"""  # 函数说明
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO chat_logs (user_id, session_id, role, content, model) VALUES (?, ?, ?, ?, ?)",
            (user_id, session_id, role, content, model),
        )
        conn.commit()


def insert_usage_log(user_id: Optional[int], endpoint: str, model: Optional[str], tokens_in: int = 0, tokens_out: int = 0) -> None:
    """插入一条使用统计记录"""  # 函数说明
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO usage_logs (user_id, endpoint, model, tokens_input, tokens_output) VALUES (?, ?, ?, ?, ?)",
            (user_id, endpoint, model, tokens_in, tokens_out),
        )
        conn.commit()


def list_recent_chats(limit: int = 50) -> List[Dict[str, Any]]:
    """获取最近聊天记录（合并用户名）"""  # 函数说明
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT c.id, c.session_id, c.role, c.content, c.model, c.created_at,
                   u.username
            FROM chat_logs c
            LEFT JOIN users u ON c.user_id = u.id
            ORDER BY c.id DESC LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]


def usage_summary() -> Dict[str, Any]:
    """使用概览：总请求数、按端点分组、按模型分组"""  # 函数说明
    with get_conn() as conn:
        cur = conn.cursor()
        # 总请求数
        cur.execute("SELECT COUNT(*) AS cnt FROM usage_logs")
        total = cur.fetchone()[0]
        # 按端点分组
        cur.execute("SELECT endpoint, COUNT(*) AS cnt FROM usage_logs GROUP BY endpoint ORDER BY cnt DESC")
        by_ep = [dict(zip([d[0] for d in cur.description], row)) for row in cur.fetchall()]
        # 按模型分组
        cur.execute("SELECT model, COUNT(*) AS cnt FROM usage_logs GROUP BY model ORDER BY cnt DESC")
        by_model = [dict(zip([d[0] for d in cur.description], row)) for row in cur.fetchall()]
        return {"total_requests": total, "by_endpoint": by_ep, "by_model": by_model}


