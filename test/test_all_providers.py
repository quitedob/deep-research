# -*- coding: utf-8 -*-
"""
Comprehensive Provider Integration Test
所有提供商的完整集成测试

测试内容：
1. Ollama (本地) - 免费本地模型
2. DeepSeek (云端) - 强大推理和编码能力
3. Doubao (豆包) - 联网搜索和视觉理解
4. ZhipuAI (智谱AI) - GLM-4.6旗舰模型和免费模型
5. Kimi (月之暗面) - 长上下文和联网搜索
"""

import os
import asyncio
import json
import logging
from typing import Dict, Any, List, Tuple
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# 导入所有provider
from src.llms.providers.ollama_llm import OllamaProvider
from src.llms.providers.deepseek_llm import DeepSeekProvider
from src.llms.providers.doubao_llm import DoubaoProvider
from src.llms.providers.zhipuai_llm import ZhipuAIProvider
from src.llms.providers.kimi_llm import KimiProvider

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProviderTestSuite:
    """所有提供商的完整测试套件"""

    def __init__(self):
        self.providers = {}
        self.test_results = {}

    async def setup_providers(self):
        """初始化所有提供商"""
        logger.info("=== 初始化所有提供商 ===")

        # Ollama (本地)
        try:
            self.providers["ollama"] = OllamaProvider(
                model_name="qwen2.5:7b",
                base_url="http://localhost:11434"
            )
            logger.info("✅ Ollama provider 初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ Ollama provider 初始化失败: {e}")

        # DeepSeek (云端)
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_key:
            try:
                self.providers["deepseek"] = DeepSeekProvider(
                    model_name="deepseek-chat",
                    api_key=deepseek_key,
                    base_url="https://api.deepseek.com/v1"
                )
                logger.info("✅ DeepSeek provider 初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ DeepSeek provider 初始化失败: {e}")
        else:
            logger.warning("⚠️ DEEPSEEK_API_KEY 未配置")

        # Doubao (豆包)
        doubao_key = os.getenv("DOUBAO_API_KEY")
        if doubao_key:
            try:
                self.providers["doubao"] = DoubaoProvider(
                    model_name="doubao-seed-1-6-flash-250615",
                    api_key=doubao_key,
                    base_url="https://ark.cn-beijing.volces.com/api/v3"
                )
                logger.info("✅ Doubao provider 初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ Doubao provider 初始化失败: {e}")
        else:
            logger.warning("⚠️ DOUBAO_API_KEY 未配置")

        # ZhipuAI (智谱AI)
        zhipuai_key = os.getenv("ZHIPUAI_API_KEY")
        if zhipuai_key:
            try:
                self.providers["zhipuai"] = ZhipuAIProvider(
                    model_name="glm-4.5-air",  # 使用高性价比模型
                    api_key=zhipuai_key,
                    base_url="https://open.bigmodel.cn/api/paas/v4"
                )
                logger.info("✅ ZhipuAI provider 初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ ZhipuAI provider 初始化失败: {e}")
        else:
            logger.warning("⚠️ ZHIPUAI_API_KEY 未配置")

        # Kimi (月之暗面)
        kimi_key = os.getenv("MOONSHOT_API_KEY")
        if kimi_key:
            try:
                self.providers["kimi"] = KimiProvider(
                    model_name="moonshot-v1-8k",
                    api_key=kimi_key,
                    base_url="https://api.moonshot.cn/v1"
                )
                logger.info("✅ Kimi provider 初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ Kimi provider 初始化失败: {e}")
        else:
            logger.warning("⚠️ MOONSHOT_API_KEY 未配置")

        logger.info(f"总共初始化了 {len(self.providers)} 个提供商")

    async def test_health_checks(self) -> Dict[str, bool]:
        """测试所有提供商的健康检查"""
        logger.info("\n=== 健康检查测试 ===")
        results = {}

        for name, provider in self.providers.items():
            try:
                ok, message = await provider.health_check()
                results[name] = ok
                status = "✅ 健康" if ok else f"❌ 异常: {message}"
                logger.info(f"{name:12} {status}")
            except Exception as e:
                results[name] = False
                logger.error(f"{name:12} ❌ 健康检查失败: {str(e)}")

        return results

    async def test_basic_generation(self) -> Dict[str, bool]:
        """测试基础文本生成"""
        logger.info("\n=== 基础生成测试 ===")
        results = {}

        test_message = [{"role": "user", "content": "你好，请用一句话介绍一下你自己。"}]

        for name, provider in self.providers.items():
            try:
                response = await provider.generate(
                    messages=test_message,
                    temperature=0.7,
                    max_tokens=100
                )

                if response and response.content:
                    results[name] = True
                    content_preview = response.content[:50] + "..." if len(response.content) > 50 else response.content
                    logger.info(f"{name:12} ✅ 生成成功: {content_preview}")
                else:
                    results[name] = False
                    logger.error(f"{name:12} ❌ 生成内容为空")
            except Exception as e:
                results[name] = False
                logger.error(f"{name:12} ❌ 生成失败: {str(e)}")

        return results

    async def test_code_generation(self) -> Dict[str, bool]:
        """测试代码生成能力"""
        logger.info("\n=== 代码生成测试 ===")
        results = {}

        code_message = [{
            "role": "user",
            "content": "请用Python写一个简单的函数，计算斐波那契数列的第n项。"
        }]

        for name, provider in self.providers.items():
            try:
                response = await provider.generate(
                    messages=code_message,
                    temperature=0.1,  # 低温度用于代码生成
                    max_tokens=200
                )

                if response and response.content:
                    # 检查是否包含代码
                    has_code = ("def " in response.content or
                               "function" in response.content or
                               "代码" in response.content)
                    results[name] = has_code
                    status = "✅ 包含代码" if has_code else "⚠️ 可能不包含代码"
                    logger.info(f"{name:12} {status}")
                else:
                    results[name] = False
                    logger.error(f"{name:12} ❌ 代码生成失败")
            except Exception as e:
                results[name] = False
                logger.error(f"{name:12} ❌ 代码生成异常: {str(e)}")

        return results

    async def test_reasoning(self) -> Dict[str, bool]:
        """测试推理能力"""
        logger.info("\n=== 推理能力测试 ===")
        results = {}

        reasoning_message = [{
            "role": "user",
            "content": "一个农场有鸡和牛共35头，脚总共有94只。鸡和牛各有多少头？请给出推理过程。"
        }]

        for name, provider in self.providers.items():
            try:
                response = await provider.generate(
                    messages=reasoning_message,
                    temperature=0.3,
                    max_tokens=300
                )

                if response and response.content:
                    # 检查是否包含推理过程
                    has_reasoning = ("23" in response.content and "12" in response.content) or \
                                   ("推理" in response.content or "因此" in response.content or "所以" in response.content)
                    results[name] = has_reasoning
                    status = "✅ 包含推理" if has_reasoning else "⚠️ 推理不完整"
                    logger.info(f"{name:12} {status}")
                else:
                    results[name] = False
                    logger.error(f"{name:12} ❌ 推理测试失败")
            except Exception as e:
                results[name] = False
                logger.error(f"{name:12} ❌ 推理测试异常: {str(e)}")

        return results

    async def test_search_capabilities(self) -> Dict[str, bool]:
        """测试搜索能力（支持搜索的提供商）"""
        logger.info("\n=== 搜索能力测试 ===")
        results = {}

        search_message = [{
            "role": "user",
            "content": "搜索并总结2025年人工智能发展的最新趋势。"
        }]

        # 测试支持搜索的提供商
        search_providers = {
            "zhipuai": self.providers.get("zhipuai"),
            "doubao": self.providers.get("doubao"),
            "kimi": self.providers.get("kimi")
        }

        for name, provider in search_providers.items():
            if not provider:
                continue

            try:
                if name == "zhipuai":
                    # ZhipuAI 网络搜索
                    search_config = {
                        "search_engine": "search_pro",
                        "count": "5",
                        "content_size": "medium"
                    }
                    response = await provider.generate_with_web_search(
                        messages=search_message,
                        search_config=search_config
                    )
                elif name == "doubao":
                    # Doubao 搜索
                    response = await provider.generate_with_search(
                        messages=search_message,
                        search_limit=5
                    )
                elif name == "kimi":
                    # Kimi 搜索（使用函数调用）
                    tools = [{"type": "builtin_function", "function": {"name": "$web_search"}}]
                    response = await provider.generate(
                        messages=search_message,
                        tools=tools
                    )

                if response and response.content:
                    # 检查是否包含搜索结果
                    has_search_results = ("2025" in response.content and
                                        "趋势" in response.content) or \
                                       ("搜索" in response.content or
                                        "根据" in response.content)
                    results[name] = has_search_results
                    status = "✅ 搜索成功" if has_search_results else "⚠️ 搜索结果不明确"
                    logger.info(f"{name:12} {status}")
                else:
                    results[name] = False
                    logger.error(f"{name:12} ❌ 搜索失败")
            except Exception as e:
                results[name] = False
                logger.error(f"{name:12} ❌ 搜索异常: {str(e)}")

        return results

    async def test_provider_specialties(self) -> Dict[str, Dict[str, Any]]:
        """测试各提供商的专长功能"""
        logger.info("\n=== 专长功能测试 ===")
        results = {}

        # DeepSeek 专长：代码
        if "deepseek" in self.providers:
            try:
                response = await self.providers["deepseek"].generate(
                    messages=[{
                        "role": "user",
                        "content": "写一个Python类来实现二叉搜索树。"
                    }],
                    temperature=0.1
                )
                results["deepseek"] = {
                    "code_generation": "class " in response.content if response else False,
                    "success": response is not None
                }
                logger.info(f"DeepSeek    代码生成: {'✅' if results['deepseek']['code_generation'] else '❌'}")
            except Exception as e:
                results["deepseek"] = {"code_generation": False, "success": False}
                logger.error(f"DeepSeek    代码生成失败: {e}")

        # ZhipuAI 专长：推理和搜索
        if "zhipuai" in self.providers:
            try:
                response = await self.providers["zhipuai"].generate(
                    messages=[{
                        "role": "user",
                        "content": "分析一下深度学习模型的训练过程需要考虑哪些因素？"
                    }],
                    temperature=0.5
                )
                has_analysis = response and len(response.content) > 100
                results["zhipuai"] = {
                    "reasoning": has_analysis,
                    "success": response is not None
                }
                logger.info(f"ZhipuAI     推理分析: {'✅' if has_analysis else '❌'}")
            except Exception as e:
                results["zhipuai"] = {"reasoning": False, "success": False}
                logger.error(f"ZhipuAI     推理分析失败: {e}")

        # Ollama 专长：本地快速响应
        if "ollama" in self.providers:
            try:
                import time
                start_time = time.time()
                response = await self.providers["ollama"].generate(
                    messages=[{
                        "role": "user",
                        "content": "简单介绍一下机器学习。"
                    }],
                    temperature=0.7
                )
                response_time = time.time() - start_time
                results["ollama"] = {
                    "local_speed": response_time < 10,  # 10秒内响应
                    "success": response is not None,
                    "response_time": response_time
                }
                logger.info(f"Ollama      本地速度: {'✅' if results['ollama']['local_speed'] else '❌'} ({response_time:.2f}s)")
            except Exception as e:
                results["ollama"] = {"local_speed": False, "success": False, "response_time": 0}
                logger.error(f"Ollama      本地速度测试失败: {e}")

        return results

    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """运行完整的综合测试"""
        logger.info("=========================================")
        logger.info("===      开始综合提供商测试            ===")
        logger.info("=========================================")

        # 初始化提供商
        await self.setup_providers()

        if not self.providers:
            logger.error("❌ 没有可用的提供商，请检查配置")
            return {"success": False, "message": "没有可用的提供商"}

        # 运行所有测试
        health_results = await self.test_health_checks()
        generation_results = await self.test_basic_generation()
        code_results = await self.test_code_generation()
        reasoning_results = await self.test_reasoning()
        search_results = await self.test_search_capabilities()
        specialty_results = await self.test_provider_specialties()

        # 汇总结果
        all_results = {
            "health_checks": health_results,
            "basic_generation": generation_results,
            "code_generation": code_results,
            "reasoning": reasoning_results,
            "search_capabilities": search_results,
            "specialty_features": specialty_results,
            "provider_count": len(self.providers),
            "available_providers": list(self.providers.keys())
        }

        # 输出测试总结
        logger.info("\n=========================================")
        logger.info("===           测试结果总结              ===")
        logger.info("=========================================")

        # 健康检查结果
        logger.info(f"\n📊 健康检查 ({sum(health_results.values())}/{len(health_results)} 通过):")
        for provider, status in health_results.items():
            logger.info(f"  {provider:12} {'✅ 正常' if status else '❌ 异常'}")

        # 基础生成结果
        logger.info(f"\n💬 基础生成 ({sum(generation_results.values())}/{len(generation_results)} 通过):")
        for provider, status in generation_results.items():
            logger.info(f"  {provider:12} {'✅ 成功' if status else '❌ 失败'}")

        # 代码生成结果
        logger.info(f"\n💻 代码生成 ({sum(code_results.values())}/{len(code_results)} 通过):")
        for provider, status in code_results.items():
            logger.info(f"  {provider:12} {'✅ 成功' if status else '❌ 失败'}")

        # 推理能力结果
        logger.info(f"\n🧠 推理能力 ({sum(reasoning_results.values())}/{len(reasoning_results)} 通过):")
        for provider, status in reasoning_results.items():
            logger.info(f"  {provider:12} {'✅ 成功' if status else '❌ 失败'}")

        # 搜索能力结果
        logger.info(f"\n🔍 搜索能力 ({sum(search_results.values())}/{len(search_results)} 通过):")
        for provider, status in search_results.items():
            logger.info(f"  {provider:12} {'✅ 成功' if status else '❌ 失败'}")

        # 专长功能结果
        logger.info(f"\n⭐ 专长功能:")
        for provider, features in specialty_results.items():
            success = features.get("success", False)
            logger.info(f"  {provider:12} {'✅ 可用' if success else '❌ 不可用'}")

        # 总体评估
        total_tests = (len(health_results) + len(generation_results) +
                      len(code_results) + len(reasoning_results) +
                      len(search_results))
        total_passed = (sum(health_results.values()) + sum(generation_results.values()) +
                       sum(code_results.values()) + sum(reasoning_results.values()) +
                       sum(search_results.values()))

        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        logger.info(f"\n🎯 总体评估:")
        logger.info(f"  可用提供商: {len(self.providers)} 个 ({', '.join(self.providers.keys())})")
        logger.info(f"  测试通过率: {success_rate:.1f}% ({total_passed}/{total_tests})")

        if success_rate >= 80:
            logger.info("  🎉 系统集成状态: 优秀")
        elif success_rate >= 60:
            logger.info("  ✅ 系统集成状态: 良好")
        elif success_rate >= 40:
            logger.info("  ⚠️  系统集成状态: 一般")
        else:
            logger.info("  ❌ 系统集成状态: 需要改进")

        all_results["success_rate"] = success_rate
        all_results["total_tests"] = total_tests
        all_results["total_passed"] = total_passed

        return all_results


async def main():
    """主函数"""
    test_suite = ProviderTestSuite()
    results = await test_suite.run_comprehensive_test()

    # 保存测试结果到文件
    with open("test_results.json", "w", encoding="utf-8") as f:
        # 转换结果为JSON可序列化格式
        serializable_results = {}
        for key, value in results.items():
            if isinstance(value, dict):
                serializable_results[key] = {k: bool(v) if isinstance(v, bool) else v for k, v in value.items()}
            else:
                serializable_results[key] = value
        json.dump(serializable_results, f, ensure_ascii=False, indent=2)

    logger.info("\n📄 测试结果已保存到 test_results.json")


if __name__ == "__main__":
    asyncio.run(main())