# -*- coding: utf-8 -*-
"""
AgentScope v1.0 MCP 客户端实现
支持 HttpStatefulClient、HttpStatelessClient 和 StdIO 传输协议
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class MCPTransport(ABC):
    """MCP 传输协议基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    async def connect(self) -> None:
        """建立连接"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        pass

    @abstractmethod
    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """发送消息"""
        pass


class StdIOTransport(MCPTransport):
    """StdIO 传输协议实现"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.process = None
        self.command = config.get("command")
        self.args = config.get("args", [])
        self.env = config.get("env", {})

    async def connect(self) -> None:
        """启动 StdIO 进程"""
        try:
            import subprocess
            import asyncio

            # 启动子进程
            self.process = await asyncio.create_subprocess_exec(
                self.command,
                *self.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**self.env},
            )
            logger.info(f"StdIO transport connected: {self.command}")
        except Exception as e:
            logger.error(f"Failed to connect StdIO transport: {e}")
            raise

    async def disconnect(self) -> None:
        """终止 StdIO 进程"""
        if self.process:
            try:
                self.process.terminate()
                await self.process.wait()
                logger.info("StdIO transport disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting StdIO transport: {e}")

    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """通过 StdIO 发送消息"""
        if not self.process:
            raise RuntimeError("StdIO transport not connected")

        try:
            import json

            # 发送消息
            message_json = json.dumps(message) + "\n"
            self.process.stdin.write(message_json.encode())
            await self.process.stdin.drain()

            # 读取响应
            response_line = await self.process.stdout.readline()
            response = json.loads(response_line.decode().strip())

            return response

        except Exception as e:
            logger.error(f"Error sending message via StdIO: {e}")
            raise


class HttpTransport(MCPTransport):
    """HTTP 传输协议基类"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.url = config.get("url")
        self.headers = config.get("headers", {})
        self.timeout = config.get("timeout", 30)
        self.session = None

    async def connect(self) -> None:
        """初始化 HTTP 客户端会话"""
        try:
            import aiohttp

            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
            logger.info(f"HTTP transport connected: {self.url}")
        except ImportError:
            logger.error("aiohttp not installed. Please install with: pip install aiohttp")
            raise

    async def disconnect(self) -> None:
        """关闭 HTTP 客户端会话"""
        if self.session:
            await self.session.close()
            logger.info("HTTP transport disconnected")

    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """通过 HTTP 发送消息"""
        if not self.session:
            raise RuntimeError("HTTP transport not connected")

        try:
            import aiohttp
            import json

            async with self.session.post(
                self.url,
                json=message,
                headers={"Content-Type": "application/json"}
            ) as response:
                response.raise_for_status()
                return await response.json()

        except Exception as e:
            logger.error(f"Error sending message via HTTP: {e}")
            raise


class HttpStatefulTransport(HttpTransport):
    """有状态 HTTP 传输协议"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.session_id = None

    async def connect(self) -> None:
        """建立有状态连接"""
        await super().connect()

        # 初始化会话
        init_message = {"type": "initialize", "protocol_version": "1.0"}
        response = await self.send_message(init_message)

        if response.get("type") == "initialize_response":
            self.session_id = response.get("session_id")
            logger.info(f"Stateful HTTP session initialized: {self.session_id}")
        else:
            raise RuntimeError("Failed to initialize stateful HTTP session")

    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """发送带会话ID的消息"""
        if self.session_id:
            message["session_id"] = self.session_id

        return await super().send_message(message)


class HttpStatelessTransport(HttpTransport):
    """无状态 HTTP 传输协议"""

    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """直接发送消息（无会话状态）"""
        return await super().send_message(message)


class StreamableHttpTransport(HttpTransport):
    """可流式 HTTP 传输协议"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.websocket = None

    async def connect(self) -> None:
        """建立 WebSocket 连接"""
        try:
            import aiohttp

            # 尝试 WebSocket 连接用于流式传输
            ws_url = self.url.replace("http", "ws").replace("https", "wss")
            self.websocket = await self.session.ws_connect(ws_url)
            logger.info(f"Streamable HTTP transport connected: {ws_url}")

        except Exception as e:
            logger.warning(f"WebSocket connection failed, falling back to HTTP: {e}")
            # 回退到普通 HTTP
            await super().connect()

    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """通过 WebSocket 或 HTTP 发送消息"""
        if self.websocket:
            # 使用 WebSocket 流式传输
            import json
            await self.websocket.send_json(message)

            # 接收流式响应
            responses = []
            async for msg in self.websocket:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    response = json.loads(msg.data)
                    responses.append(response)

                    # 检查是否为最终响应
                    if response.get("type") == "final":
                        break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    raise RuntimeError(f"WebSocket error: {self.websocket.exception()}")

            return {"responses": responses}
        else:
            # 使用普通 HTTP
            return await super().send_message(message)

    async def disconnect(self) -> None:
        """断开 WebSocket 或 HTTP 连接"""
        if self.websocket:
            await self.websocket.close()
        await super().disconnect()


class MCPClient:
    """AgentScope v1.0 MCP 客户端"""

    def __init__(self, server_config: Dict[str, Any]):
        self.server_config = server_config
        self.transport = None
        self.connected = False
        self.tools = []
        self.resources = []

    async def connect(self) -> None:
        """连接到 MCP 服务器"""
        try:
            transport_config = self.server_config.copy()

            # 根据传输类型创建传输对象
            transport_type = transport_config.pop("transport", "stdio")

            if transport_type == "stdio":
                self.transport = StdIOTransport(transport_config)
            elif transport_type == "http_stateful":
                self.transport = HttpStatefulTransport(transport_config)
            elif transport_type == "http_stateless":
                self.transport = HttpStatelessTransport(transport_config)
            elif transport_type == "streamable_http":
                self.transport = StreamableHttpTransport(transport_config)
            else:
                raise ValueError(f"Unsupported transport type: {transport_type}")

            # 建立连接
            await self.transport.connect()

            # 初始化 MCP 会话
            await self._initialize_mcp()

            self.connected = True
            logger.info(f"MCP client connected with transport: {transport_type}")

        except Exception as e:
            logger.error(f"Failed to connect MCP client: {e}")
            raise

    async def disconnect(self) -> None:
        """断开 MCP 服务器连接"""
        if self.transport:
            await self.transport.disconnect()
        self.connected = False
        logger.info("MCP client disconnected")

    async def _initialize_mcp(self) -> None:
        """初始化 MCP 会话"""
        try:
            # 发送初始化消息
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "1.0",
                    "capabilities": {
                        "tools": {},
                        "resources": {}
                    },
                    "clientInfo": {
                        "name": "AgentScope",
                        "version": "1.0"
                    }
                }
            }

            response = await self.transport.send_message(init_message)

            if response.get("error"):
                raise RuntimeError(f"MCP initialization failed: {response['error']}")

            # 获取可用工具
            await self._discover_tools()

            # 获取可用资源
            await self._discover_resources()

            logger.info("MCP session initialized successfully")

        except Exception as e:
            logger.error(f"MCP initialization failed: {e}")
            raise

    async def _discover_tools(self) -> None:
        """发现可用工具"""
        try:
            tools_message = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }

            response = await self.transport.send_message(tools_message)

            if response.get("result") and response["result"].get("tools"):
                self.tools = response["result"]["tools"]
                logger.info(f"Discovered {len(self.tools)} tools")
            else:
                self.tools = []
                logger.info("No tools discovered")

        except Exception as e:
            logger.warning(f"Failed to discover tools: {e}")
            self.tools = []

    async def _discover_resources(self) -> None:
        """发现可用资源"""
        try:
            resources_message = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "resources/list",
                "params": {}
            }

            response = await self.transport.send_message(resources_message)

            if response.get("result") and response["result"].get("resources"):
                self.resources = response["result"]["resources"]
                logger.info(f"Discovered {len(self.resources)} resources")
            else:
                self.resources = []
                logger.info("No resources discovered")

        except Exception as e:
            logger.warning(f"Failed to discover resources: {e}")
            self.resources = []

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具"""
        if not self.connected:
            raise RuntimeError("MCP client not connected")

        try:
            tool_call_message = {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }

            response = await self.transport.send_message(tool_call_message)

            if response.get("error"):
                raise RuntimeError(f"Tool call failed: {response['error']}")

            return response.get("result", {})

        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            raise

    async def read_resource(self, resource_uri: str) -> Dict[str, Any]:
        """读取资源"""
        if not self.connected:
            raise RuntimeError("MCP client not connected")

        try:
            resource_message = {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "resources/read",
                "params": {
                    "uri": resource_uri
                }
            }

            response = await self.transport.send_message(resource_message)

            if response.get("error"):
                raise RuntimeError(f"Resource read failed: {response['error']}")

            return response.get("result", {})

        except Exception as e:
            logger.error(f"Resource read failed: {e}")
            raise

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        return self.tools.copy()

    def get_available_resources(self) -> List[Dict[str, Any]]:
        """获取可用资源列表"""
        return self.resources.copy()


class MultiServerMCPClient:
    """多服务器 MCP 客户端管理器"""

    def __init__(self, server_configs: Dict[str, Dict[str, Any]]):
        self.server_configs = server_configs
        self.clients: Dict[str, MCPClient] = {}

    async def connect_all(self) -> None:
        """连接所有 MCP 服务器"""
        for server_name, config in self.server_configs.items():
            try:
                client = MCPClient(config)
                await client.connect()
                self.clients[server_name] = client
                logger.info(f"Connected to MCP server: {server_name}")
            except Exception as e:
                logger.error(f"Failed to connect to MCP server {server_name}: {e}")

    async def disconnect_all(self) -> None:
        """断开所有 MCP 服务器连接"""
        for server_name, client in self.clients.items():
            try:
                await client.disconnect()
                logger.info(f"Disconnected from MCP server: {server_name}")
            except Exception as e:
                logger.error(f"Error disconnecting from MCP server {server_name}: {e}")

        self.clients.clear()

    async def get_tools(self) -> List[Any]:
        """获取所有服务器的工具"""
        all_tools = []

        for server_name, client in self.clients.items():
            try:
                tools = client.get_available_tools()
                # 为工具添加服务器标识
                for tool in tools:
                    tool["server_name"] = server_name
                    # 创建 AgentScope 兼容的工具对象
                    all_tools.append(self._create_agentscope_tool(tool, server_name))
            except Exception as e:
                logger.error(f"Error getting tools from server {server_name}: {e}")

        return all_tools

    def _create_agentscope_tool(self, tool_info: Dict[str, Any], server_name: str) -> Any:
        """创建 AgentScope 兼容的工具对象"""
        try:
            from agentscope.tools import ToolBase

            class MCPTool(ToolBase):
                def __init__(self, tool_info, server_name, client):
                    super().__init__(tool_info["name"])
                    self.tool_info = tool_info
                    self.server_name = server_name
                    self.client = client

                def __call__(self, **kwargs):
                    """同步调用工具"""
                    import asyncio
                    return asyncio.run(self.acall(**kwargs))

                async def acall(self, **kwargs):
                    """异步调用工具"""
                    try:
                        result = await self.client.call_tool(self.name, kwargs)
                        return result
                    except Exception as e:
                        logger.error(f"MCP tool call failed: {e}")
                        raise

                @property
                def schema(self):
                    """工具模式"""
                    return self.tool_info.get("inputSchema", {})

            return MCPTool(tool_info, server_name, self.clients[server_name])

        except Exception as e:
            logger.error(f"Failed to create AgentScope tool: {e}")
            return None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect_all()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect_all()
