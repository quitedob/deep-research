# 文件路径：/workspace/ollama_demo/gemma3_describe_image.py
# 功能：使用 Ollama 的 gemma3:4b 多模态模型对本地图片进行描述（支持同步与流式）
# 说明：Ollama Python 客户端支持在 messages 中通过 "images" 传入路径或字节；Gemma3 为多模态模型。  # 中文注释

import os
from ollama import Client  # 官方 Python 客户端  # 中文注释

# === 基本参数（按需修改） =========================================================  # 中文注释
OLLAMA_HOST = 'http://localhost:11434'  # 默认本地服务地址  # 中文注释
MODEL_NAME = 'gemma3:4b'                # 使用多模态 Gemma3 4B  # 中文注释

def describe_image(image_path: str, prompt: str = "用中文详细描述这张图片的主体、场景、文字和细节。") -> str:
    """
    功能：非流式一次性返回图片描述文本  # 中文注释
    参数：image_path - 本地图片绝对路径（支持 Windows 路径）
         prompt     - 对模型的指令（可自定义）  # 中文注释
    返回：图片描述文本  # 中文注释
    """
    # —— 路径检查（避免常见的“找不到文件”错误） ——  # 中文注释
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"未找到图片文件：{image_path}")

    client = Client(host=OLLAMA_HOST)

    # —— 构造多模态消息；images 接受“路径字符串或字节” ——  # 中文注释
    # 注意：Windows 路径建议传原始字符串 r"..." 或用双反斜杠  # 中文注释
    messages = [{
        "role": "user",
        "content": prompt,
        "images": [image_path],  # 也可传入 bytes/base64，官方支持  # 中文注释
    }]

    # —— 发送请求并获取完整响应 ——  # 中文注释
    resp = client.chat(model=MODEL_NAME, messages=messages)
    return resp["message"]["content"]

def describe_image_stream(image_path: str, prompt: str = "用中文详细描述这张图片的主体、场景、文字和细节。"):
    """
    功能：流式增量返回（逐块打印），适合较长描述或需要边出边显  # 中文注释
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"未找到图片文件：{image_path}")

    client = Client(host=OLLAMA_HOST)
    messages = [{
        "role": "user",
        "content": prompt,
        "images": [image_path],
    }]

    # —— 开启流式 ——  # 中文注释
    stream = client.chat(model=MODEL_NAME, messages=messages, stream=True)
    for chunk in stream:
        # 分块字段结构与非流式相同，这里仅输出内容片段  # 中文注释
        print(chunk["message"]["content"], end="", flush=True)

if __name__ == "__main__":
    # —— 你的目标图片（Windows 路径建议 r"" 原始字符串以避免转义问题）——  # 中文注释
    img = r"C:\Users\shuaibi\Downloads\1.png"

    # 非流式：拿到完整结果字符串  # 中文注释
    try:
        text = describe_image(img, "请用中文客观描述这张图片的内容，并列出关键要素（人物/物体、动作、场景、文字、潜在用途）。")
        print("\n=== 图片描述（非流式） ===\n" + text)
    except Exception as e:
        print(f"[非流式] 出错：{e}")

    # 流式：逐块输出（可注释掉）  # 中文注释
    try:
        print("\n=== 图片描述（流式） ===")
        describe_image_stream(img, "逐步描述该图像的可见要素，并在结尾给出一句总结。")
        print()  # 换行  # 中文注释
    except Exception as e:
        print(f"[流式] 出错：{e}")
