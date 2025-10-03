# -*- coding: utf-8 -*-
"""
RAG 配置模块：基于 rag_example.txt 的配置实现
"""

import os
import re
from pathlib import Path

# --- 基础路径配置 ---
# BASE_DIR 是项目的根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# RAG_DATA_DIR 是所有RAG相关数据的根目录
RAG_DATA_DIR = BASE_DIR / "rag_data"
# KB_ROOT_PATH 是所有知识库的存储目录
KB_ROOT_PATH = RAG_DATA_DIR / "knowledge_bases"
# CHROMA_PERSIST_DIR 是ChromaDB持久化数据的存储目录
CHROMA_PERSIST_DIR = RAG_DATA_DIR / "chroma_db"

# --- 知识库配置 ---
# MAX_KBS 最大知识库数量
MAX_KBS = 10
# KB_NAME_PATTERN 知识库名称的正则表达式 (英文+数字, 3-20个字符)
KB_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9]{3,20}$")
# MAX_FILE_SIZE_MB 单个上传文件的最大大小 (MB)
MAX_FILE_SIZE_MB = 50
# ALLOWED_EXTENSIONS 允许上传的文件扩展名
ALLOWED_EXTENSIONS = [".pdf", ".docx", ".doc", ".txt", ".md", ".ppt", ".pptx", ".png", ".jpg", ".jpeg"]

# --- RAG 核心配置 ---
# DEFAULT_RAG_MODE 默认是否开启RAG模式
DEFAULT_RAG_MODE = False
# DEFAULT_SYSTEM_PROMPT 默认的系统级提示词 (不可修改部分)
DEFAULT_SYSTEM_PROMPT_PREFIX = "你是芝麻编程的编程老师，请你以芝麻编程老师的身份回答问题。"
# DYNAMIC_PROMPT_FILE 存储用户可修改的动态提示词的文件路径
DYNAMIC_PROMPT_FILE = RAG_DATA_DIR / "dynamic_prompt.txt"
# OLLAMA_URL Ollama服务的API地址
OLLAMA_URL = "http://localhost:11434/api/chat"
# OLLAMA_MODEL_NAME 用于RAG的Ollama模型名称
OLLAMA_MODEL_NAME = "gemma3:4b"

# --- 文本处理与向量化配置 ---
# CHUNK_SIZE 文本分块的大小（适配 ~2k token 上下文；中文约350字）
CHUNK_SIZE = 350
# CHUNK_OVERLAP 文本分块的重叠大小
CHUNK_OVERLAP = 100
# 嵌入统一使用 Ollama 的 nomic-embed-text:v1.5
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:v1.5")
# 嵌入批量与超时（可通过环境变量覆盖）
OLLAMA_EMBED_BATCH_SIZE = int(os.getenv("OLLAMA_EMBED_BATCH_SIZE", "16"))
OLLAMA_EMBED_TIMEOUT_SEC = float(os.getenv("OLLAMA_EMBED_TIMEOUT_SEC", "60"))
# OCR_LANGUAGE OCR识别时使用的语言
OCR_LANGUAGE = "chi_sim+eng"

# --- API 与任务管理配置 ---
# TASK_STATUS_POLL_INTERVAL_S 前端轮询任务状态的建议间隔时间 (秒)
TASK_STATUS_POLL_INTERVAL_S = 5

def initialize_rag_directories():
    """
    初始化所有RAG功能所需的目录。
    Initializes all directories required for RAG functionality.
    """
    RAG_DATA_DIR.mkdir(exist_ok=True)
    KB_ROOT_PATH.mkdir(exist_ok=True)
    CHROMA_PERSIST_DIR.mkdir(exist_ok=True)

# 在模块加载时执行初始化
initialize_rag_directories()