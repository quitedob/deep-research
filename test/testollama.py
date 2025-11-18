# -*- coding: utf-8 -*-
"""
使用指定的两个模型分析3.jpg图像
依次使用: qwen3vl-4b 和 gemma3:4b
"""

import os
import base64
import asyncio
import aiohttp
import json


class OllamaImageAnalyzer:
    """Ollama 图像分析器"""

    def __init__(self, host='http://localhost:11434'):
        self.host = host.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=300)

    def _encode_image_to_base64(self, image_path: str) -> str:
        """将图像文件编码为base64格式"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    async def analyze_image(self, model: str, image_path: str, prompt: str) -> dict:
        """使用指定模型分析图像"""
        image_b64 = self._encode_image_to_base64(image_path)

        data = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_b64]
                }
            ],
            "stream": False
        }

        url = f"{self.host}/api/chat"

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(url, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama API错误: {response.status} - {error_text}")
                return await response.json()


async def analyze_with_two_models():
    """使用两个指定模型依次分析图像"""
    print("=" * 60)
    print("双模型图像分析测试")
    print("使用模型: qwen3-vl:4b, gemma3:4b")
    print("=" * 60)

    # 图像文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(script_dir, "1.png")

    print(f"分析图像: {image_path}")

    if not os.path.exists(image_path):
        print(f"❌ 错误: 图像文件不存在 {image_path}")
        return

    # 指定的两个模型
    models = ["qwen3-vl:4b", "gemma3:4b"]

    # 分析提示词
    prompt = "请详细分析这张图片的内容，包括：\n1. 主要物体和场景\n2. 文字信息\n3. 颜色和布局\n4. 可能的功能和用途"

    # 依次使用两个模型
    for i, model in enumerate(models, 1):
        print(f"\n{'='*25}")
        print(f"模型 {i}: {model}")
        print(f"{'='*25}")

        try:
            print(f"正在使用 {model} 分析图像...")

            analyzer = OllamaImageAnalyzer()
            result = await analyzer.analyze_image(model, image_path, prompt)

            if "message" in result and "content" in result["message"]:
                content = result["message"]["content"]
                print(f"✅ 分析结果:\n{content}")
            else:
                print("❌ 未获取到有效结果")

        except Exception as e:
            print(f"❌ 模型 {model} 分析失败: {e}")
            if "not found" in str(e).lower():
                print(f"💡 建议: 请确保模型已安装 - ollama pull {model}")

    print(f"\n{'='*60}")
    print("双模型分析完成")
    print(f"{'='*60}")


if __name__ == "__main__":
    print("Ollama 双模型图像分析工具")
    print("确保已安装指定模型:")
    print("  ollama pull qwen3-vl:4b")
    print("  ollama pull gemma3:4b")
    print()

    asyncio.run(analyze_with_two_models())