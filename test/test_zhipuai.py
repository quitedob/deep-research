# -*- coding: utf-8 -*-
"""
ZhipuAI Provider Tests
智谱AI provider 集成测试

测试内容：
1. 提供商连接性
2. 模型能力
3. 函数调用
4. 网络搜索功能
5. 视觉处理
"""

import os
import asyncio
import json
import logging
from typing import Dict, Any, List

from dotenv import load_dotenv
from src.llms.providers.zhipuai_llm import ZhipuAIProvider

# 加载环境变量
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ZhipuAITestSuite:
    """ZhipuAI 测试套件"""

    def __init__(self):
        self.api_key = os.getenv("ZHIPUAI_API_KEY")
        self.base_url = "https://open.bigmodel.cn/api/paas/v4"
        self.test_models = [
            "glm-4.5-flash",      # 免费聊天模型
            "glm-4.6",            # 旗舰模型
            "glm-4.1v-thinking-flash"  # 视觉模型
        ]
        self.provider = None

    async def setup(self):
        """初始化测试环境"""
        if not self.api_key:
            logger.error("❌ 错误: 未在 .env 文件中找到 'ZHIPUAI_API_KEY'")
            logger.error("   请在 .env 文件中添加: ZHIPUAI_API_KEY=your_api_key_here")
            return False

        self.provider = ZhipuAIProvider(
            model_name="glm-4.5-flash",
            api_key=self.api_key,
            base_url=self.base_url
        )

        logger.info("✅ ZhipuAI provider 初始化成功")
        return True

    async def test_health_check(self) -> bool:
        """测试健康检查"""
        logger.info("=== 测试健康检查 ===")

        try:
            ok, message = await self.provider.health_check()
            if ok:
                logger.info("✅ 健康检查通过")
                return True
            else:
                logger.error(f"❌ 健康检查失败: {message}")
                return False
        except Exception as e:
            logger.error(f"❌ 健康检查异常: {str(e)}")
            return False

    async def test_basic_generation(self, model_name: str = None) -> bool:
        """测试基础生成功能"""
        logger.info(f"=== 测试基础生成 ({model_name or 'default'}) ===")

        try:
            # 如果指定了模型，创建新的provider实例
            provider = self.provider
            if model_name:
                provider = ZhipuAIProvider(
                    model_name=model_name,
                    api_key=self.api_key,
                    base_url=self.base_url
                )

            messages = [
                {"role": "user", "content": "你好，请用中文简短介绍一下你自己。"}
            ]

            resp = await provider.generate(
                messages=messages,
                temperature=0.7,
                max_tokens=100
            )

            logger.info(f"✅ [{model_name or 'default'}] 生成成功:")
            logger.info(f"   模型: {resp.model}")
            logger.info(f"   内容: {resp.content[:100]}...")

            if resp.usage:
                logger.info(f"   Token使用: {resp.usage}")

            return True

        except Exception as e:
            logger.error(f"❌ [{model_name or 'default'}] 生成失败: {str(e)}")
            return False

    async def test_function_calling(self) -> bool:
        """测试函数调用功能"""
        logger.info("=== 测试函数调用 ===")

        try:
            # 定义工具
            tools = [{
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "获取指定城市的天气信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "城市名称，例如：北京、上海"
                            }
                        },
                        "required": ["city"]
                    }
                }
            }]

            messages = [
                {"role": "user", "content": "请问北京今天的天气怎么样？"}
            ]

            resp = await self.provider.generate(
                messages=messages,
                temperature=0.7,
                tools=tools
            )

            logger.info("✅ 函数调用测试成功:")
            logger.info(f"   内容: {resp.content[:200]}...")

            return True

        except Exception as e:
            logger.error(f"❌ 函数调用测试失败: {str(e)}")
            return False

    async def test_web_search(self) -> bool:
        """测试网络搜索功能"""
        logger.info("=== 测试网络搜索 ===")

        try:
            search_config = {
                "search_engine": "search_pro",
                "count": "5",
                "content_size": "medium",
                "search_prompt": "你是一位研究分析师。请总结搜索结果中的关键信息。"
            }

            messages = [
                {"role": "user", "content": "搜索2025年人工智能发展的最新趋势"}
            ]

            resp = await self.provider.generate_with_web_search(
                messages=messages,
                search_config=search_config,
                temperature=0.7
            )

            logger.info("✅ 网络搜索测试成功:")
            logger.info(f"   内容: {resp.content[:300]}...")

            return True

        except Exception as e:
            logger.error(f"❌ 网络搜索测试失败: {str(e)}")
            return False

    async def test_web_search_only(self) -> bool:
        """测试纯网络搜索功能"""
        logger.info("=== 测试纯网络搜索 ===")

        try:
            resp = await self.provider.web_search_only(
                search_query="智谱AI GLM-4模型发布",
                search_engine="search_pro",
                count=5,
                content_size="medium"
            )

            logger.info("✅ 纯网络搜索测试成功:")
            logger.info(f"   查询: {resp.get('query', 'N/A')}")

            if 'response' in resp:
                logger.info(f"   响应: {resp['response'][:200]}...")

            return True

        except Exception as e:
            logger.error(f"❌ 纯网络搜索测试失败: {str(e)}")
            return False

    async def test_model_capabilities(self) -> bool:
        """测试模型能力查询"""
        logger.info("=== 测试模型能力查询 ===")

        try:
            for model in self.test_models:
                info = self.provider.get_model_info(model)
                logger.info(f"📊 {model} 能力:")
                logger.info(f"   上下文窗口: {info.get('context_window', 'N/A')}")
                logger.info(f"   最大输出: {info.get('max_output', 'N/A')}")
                logger.info(f"   函数调用: {info.get('supports_function_calling', False)}")
                logger.info(f"   视觉理解: {info.get('supports_vision', False)}")
                logger.info(f"   免费模型: {info.get('is_free', False)}")
                logger.info("")

            return True

        except Exception as e:
            logger.error(f"❌ 模型能力查询失败: {str(e)}")
            return False

    async def test_available_models(self) -> bool:
        """测试可用模型列表"""
        logger.info("=== 测试可用模型列表 ===")

        try:
            models = self.provider.get_available_models()
            logger.info(f"📋 可用模型: {models}")

            engines = self.provider.get_search_engines()
            logger.info(f"🔍 支持的搜索引擎: {engines}")

            return True

        except Exception as e:
            logger.error(f"❌ 可用模型查询失败: {str(e)}")
            return False

    async def run_all_tests(self) -> Dict[str, bool]:
        """运行所有测试"""
        logger.info("=========================================")
        logger.info("===      开始 ZhipuAI 集成测试        ===")
        logger.info("=========================================")

        # 初始化
        if not await self.setup():
            return {"initialization": False}

        results = {}

        # 基础测试
        results["health_check"] = await self.test_health_check()
        results["model_capabilities"] = await self.test_model_capabilities()
        results["available_models"] = await self.test_available_models()

        # 功能测试
        if results["health_check"]:
            results["basic_generation_flash"] = await self.test_basic_generation("glm-4.5-flash")
            results["basic_generation_46"] = await self.test_basic_generation("glm-4.6")
            results["function_calling"] = await self.test_function_calling()
            results["web_search"] = await self.test_web_search()
            results["web_search_only"] = await self.test_web_search_only()

        # 输出测试结果
        logger.info("\n=========================================")
        logger.info("===         测试结果汇总              ===")
        logger.info("=========================================")

        passed = 0
        total = len(results)

        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"{test_name:25} {status}")
            if result:
                passed += 1

        logger.info(f"\n总计: {passed}/{total} 测试通过")

        if passed == total:
            logger.info("🎉 所有测试通过！ZhipuAI 集成成功")
        else:
            logger.warning("⚠️  部分测试失败，请检查配置和网络连接")

        return results


async def main():
    """主函数"""
    test_suite = ZhipuAITestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())