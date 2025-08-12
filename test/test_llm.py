# -*- coding: utf-8 -*-
# 文件路径: D:\python_code\AgentWork\tests\test_llm.py

"""
说明:
这是一个自动化执行脚本，用于依次检查本地 Ollama 模型和 Kimi 模型的服务状态。
它会从项目根目录的 .env 文件加载环境变量。

执行流程:
1. 加载 .env 文件中的配置。
2. 依次请求 OLLAMA_MODELS_TO_TEST 列表中的所有本地模型，并打印结果。
3. 请求 Kimi API，测试其联网搜索功能。
"""
import os
import re  # <-- 新增：引入正则表达式库
import asyncio
import json
import httpx
from openai import AsyncOpenAI
from dotenv import load_dotenv

# --- 全局配置 ---
# 加载项目根目录下的 .env 文件
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# 需要测试的 Ollama 模型列表
OLLAMA_MODELS_TO_TEST = ["qwen3:32b", "gemma3:4b", "qwen2.5vl:7b"]
OLLAMA_API_BASE_URL = "http://localhost:11434/api/chat"

# Kimi 模型配置
KIMI_MODEL_NAME = "moonshot-v1-8k"
KIMI_API_BASE_URL = "https://api.moonshot.cn/v1"


async def run_ollama_checks():
    """
    依次检查所有指定的 Ollama 模型，并过滤掉 <think> 标签。
    """
    print("=========================================")
    print("===          开始检查 Ollama 模型        ===")
    print("=========================================\n")

    async with httpx.AsyncClient(timeout=120.0) as client:
        for model in OLLAMA_MODELS_TO_TEST:
            print(f"--- 正在请求模型: {model} ---")
            try:
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": "你好，请用中文简短介绍一下你自己。"}],
                    "stream": False
                }
                response = await client.post(OLLAMA_API_BASE_URL, json=payload)
                response.raise_for_status()

                response_data = response.json()
                content = response_data.get("message", {}).get("content", "未能获取回复内容。")

                # <-- 【关键改动】使用正则表达式移除 <think> 块
                # re.DOTALL 标志让 '.' 可以匹配包括换行符在内的任意字符
                cleaned_content = re.sub(r'<think>.*?</think>\s*', '', content, flags=re.DOTALL).strip()

                print(f"✅ [{model}] 回复成功:\n{cleaned_content}\n")

            except httpx.ConnectError:
                print(f"❌ 错误: 无法连接到 Ollama 服务 at {OLLAMA_API_BASE_URL}。\n")
                return
            except httpx.HTTPStatusError as e:
                error_body = e.response.text
                print(f"❌ 错误: 请求模型 '{model}' 时发生 HTTP 错误 (状态码: {e.response.status_code})。")
                if "model not found" in error_body:
                    print(f"   提示: 模型未找到，请先运行 'ollama pull {model}' 拉取模型。\n")
                else:
                    print(f"   服务器返回信息: {error_body}\n")
            except Exception as e:
                print(f"❌ 错误: 检查模型 '{model}' 时发生未知错误: {e}\n")


async def run_kimi_check():
    """
    检查 Kimi 模型的联网搜索功能。
    """
    print("\n=========================================")
    print("===          开始检查 Kimi 模型          ===")
    print("=========================================\n")

    api_key = os.getenv("MOONSHOT_API_KEY")

    # <-- 【关键改动】添加调试信息，检查读取到的 API Key
    if api_key:
        # 为了安全，只打印部分key，确认它不是空的
        print(f"🔍 调试信息: 已从 .env 文件读取到 MOONSHOT_API_KEY，开头为: {api_key[:5]}...\n")
    else:
        print("❌ 警告: 未在 .env 文件中找到 'MOONSHOT_API_KEY'。")
        print("   请在 D:\\python_code\\AgentWork\\.env 文件中进行配置。\n")
        return

    try:
        client = AsyncOpenAI(api_key=api_key, base_url=KIMI_API_BASE_URL)
        print(f"--- 使用模型: {KIMI_MODEL_NAME} ---")
        query = "简单介绍一下2025年的大同婚案和各大媒体设论坛的评价是什么？"
        print(f"联网搜索查询: {query}\n")

        tools = [{"type": "builtin_function", "function": {"name": "$web_search"}}]
        messages = [{"role": "user", "content": query}]

        completion = await client.chat.completions.create(model=KIMI_MODEL_NAME, messages=messages, tools=tools)
        choice = completion.choices[0]
        messages.append(choice.message)

        if choice.finish_reason == "tool_calls":
            for tool_call in choice.message.tool_calls:
                tool_call_arguments = json.loads(tool_call.function.arguments)
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": tool_call.function.name,
                                 "content": json.dumps(tool_call_arguments)})

            final_completion = await client.chat.completions.create(model=KIMI_MODEL_NAME, messages=messages)
            final_content = final_completion.choices[0].message.content
            print(f"✅ Kimi 联网搜索回复成功:\n{final_content}\n")
        else:
            print(f"❌ 警告: Kimi 模型未按预期调用搜索工具，直接输出现有内容:\n{choice.message.content}\n")

    except Exception as e:
        print(f"❌ 错误: Kimi 检查过程中发生错误: {e}\n")


async def main():
    """主函数，按顺序执行所有检查任务。"""
    await run_ollama_checks()
    await run_kimi_check()
    print("=========================================")
    print("===         所有检查任务已完成          ===")
    print("=========================================\n")


if __name__ == "__main__":
    asyncio.run(main())