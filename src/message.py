# -*- coding: utf-8 -*-
"""
增强消息系统 - 基于 tech.txt 策略的结构化内容块
支持复杂的消息交互、工具调用、多模态内容和推理链
"""

try:
    import shortuuid
    SHORTUUID_AVAILABLE = True
except ImportError:
    SHORTUUID_AVAILABLE = False
    import uuid
    shortuuid = None
import json
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """内容类型枚举"""
    TEXT = "text"
    THINKING = "thinking"  # 思维链推理 (策略一)
    REFERENCE = "reference"  # 参考资料 (策略二)
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    FILE = "file"
    CODE = "code"
    TABLE = "table"
    CHART = "chart"
    STEPS = "steps"  # 任务分解步骤 (策略三)
    METADATA = "metadata"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class MessageRole(Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
    OBSERVER = "observer"


@dataclass
class ContentBlock:
    """基础内容块类"""
    type: ContentType
    id: str = field(default_factory=lambda: shortuuid.uuid() if SHORTUUID_AVAILABLE else str(uuid.uuid4()) if SHORTUUID_AVAILABLE else str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type.value,
            "id": self.id,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContentBlock":
        """从字典创建"""
        block_type = ContentType(data.get("type", "text"))
        if block_type == ContentType.TEXT:
            return TextBlock.from_dict(data)
        elif block_type == ContentType.THINKING:
            return ThinkingBlock.from_dict(data)
        elif block_type == ContentType.REFERENCE:
            return ReferenceBlock.from_dict(data)
        elif block_type == ContentType.TOOL_USE:
            return ToolUseBlock.from_dict(data)
        elif block_type == ContentType.TOOL_RESULT:
            return ToolResultBlock.from_dict(data)
        elif block_type == ContentType.IMAGE:
            return ImageBlock.from_dict(data)
        elif block_type == ContentType.CODE:
            return CodeBlock.from_dict(data)
        elif block_type == ContentType.STEPS:
            return StepsBlock.from_dict(data)
        else:
            return cls(
                type=block_type,
                id=data.get("id", shortuuid.uuid() if SHORTUUID_AVAILABLE else str(uuid.uuid4())),
                metadata=data.get("metadata", {}),
                timestamp=data.get("timestamp", datetime.now().isoformat())
            )


@dataclass
class TextBlock(ContentBlock):
    """文本块 - 支持格式化文本和分段"""
    type: ContentType = ContentType.TEXT
    text: str = ""
    format: str = "plain"  # plain, markdown, html
    language: str = "auto"  # auto, zh, en
    sections: List[str] = field(default_factory=list)  # 文本分段

    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = ContentType(self.type)

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "text": self.text,
            "format": self.format,
            "language": self.language,
            "sections": self.sections
        })
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TextBlock":
        return cls(
            type=ContentType(data.get("type", "text")),
            id=data.get("id", shortuuid.uuid() if SHORTUUID_AVAILABLE else str(uuid.uuid4())),
            text=data.get("text", ""),
            format=data.get("format", "plain"),
            language=data.get("language", "auto"),
            sections=data.get("sections", []),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", datetime.now().isoformat())
        )


@dataclass
class ThinkingBlock(ContentBlock):
    """思维链推理块 (策略一：思维链提示)"""
    type: ContentType = ContentType.THINKING
    reasoning: str = ""
    step_number: int = 0
    step_type: str = "general"  # understand, analyze, plan, execute, verify
    confidence: float = 0.0
    chain_of_thought: List[str] = field(default_factory=list)

    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = ContentType(self.type)

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "reasoning": self.reasoning,
            "step_number": self.step_number,
            "step_type": self.step_type,
            "confidence": self.confidence,
            "chain_of_thought": self.chain_of_thought
        })
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThinkingBlock":
        return cls(
            type=ContentType(data.get("type", "thinking")),
            id=data.get("id", shortuuid.uuid() if SHORTUUID_AVAILABLE else str(uuid.uuid4())),
            reasoning=data.get("reasoning", ""),
            step_number=data.get("step_number", 0),
            step_type=data.get("step_type", "general"),
            confidence=data.get("confidence", 0.0),
            chain_of_thought=data.get("chain_of_thought", []),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", datetime.now().isoformat())
        )


@dataclass
class ReferenceBlock(ContentBlock):
    """参考资料块 (策略二：提供参考资料)"""
    type: ContentType = ContentType.REFERENCE
    title: str = ""
    content: str = ""
    source: str = ""
    url: Optional[str] = None
    credibility_score: float = 0.0  # 可信度评分
    reference_type: str = "general"  # academic, news, web, document, expert
    authors: List[str] = field(default_factory=list)
    publication_date: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = ContentType(self.type)

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "url": self.url,
            "credibility_score": self.credibility_score,
            "reference_type": self.reference_type,
            "authors": self.authors,
            "publication_date": self.publication_date,
            "tags": self.tags
        })
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReferenceBlock":
        return cls(
            type=ContentType(data.get("type", "reference")),
            id=data.get("id", shortuuid.uuid() if SHORTUUID_AVAILABLE else str(uuid.uuid4())),
            title=data.get("title", ""),
            content=data.get("content", ""),
            source=data.get("source", ""),
            url=data.get("url"),
            credibility_score=data.get("credibility_score", 0.0),
            reference_type=data.get("reference_type", "general"),
            authors=data.get("authors", []),
            publication_date=data.get("publication_date"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", datetime.now().isoformat())
        )


@dataclass
class ToolUseBlock(ContentBlock):
    """工具使用块"""
    type: ContentType = ContentType.TOOL_USE
    name: str = ""
    input: Dict[str, Any] = field(default_factory=dict)
    tool_type: str = "function"  # function, api, builtin
    parameters: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = ContentType(self.type)

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "name": self.name,
            "input": self.input,
            "tool_type": self.tool_type,
            "parameters": self.parameters
        })
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolUseBlock":
        return cls(
            type=ContentType(data.get("type", "tool_use")),
            id=data.get("id", shortuuid.uuid() if SHORTUUID_AVAILABLE else str(uuid.uuid4())),
            name=data.get("name", ""),
            input=data.get("input", {}),
            tool_type=data.get("tool_type", "function"),
            parameters=data.get("parameters", {}),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", datetime.now().isoformat())
        )


@dataclass
class ToolResultBlock(ContentBlock):
    """工具结果块"""
    type: ContentType = ContentType.TOOL_RESULT
    tool_use_id: str = ""
    name: str = ""
    output: Any = None
    success: bool = True
    error: Optional[str] = None
    execution_time: float = 0.0

    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = ContentType(self.type)

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "tool_use_id": self.tool_use_id,
            "name": self.name,
            "output": self.output,
            "success": self.success,
            "error": self.error,
            "execution_time": self.execution_time
        })
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolResultBlock":
        return cls(
            type=ContentType(data.get("type", "tool_result")),
            id=data.get("id", shortuuid.uuid() if SHORTUUID_AVAILABLE else str(uuid.uuid4())),
            tool_use_id=data.get("tool_use_id", ""),
            name=data.get("name", ""),
            output=data.get("output"),
            success=data.get("success", True),
            error=data.get("error"),
            execution_time=data.get("execution_time", 0.0),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", datetime.now().isoformat())
        )


@dataclass
class ImageBlock(ContentBlock):
    """图像块"""
    type: ContentType = ContentType.IMAGE
    url: str = ""
    alt_text: str = ""
    format: str = "unknown"  # jpeg, png, gif, webp
    size: Dict[str, int] = field(default_factory=dict)  # width, height
    description: str = ""

    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = ContentType(self.type)

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "url": self.url,
            "alt_text": self.alt_text,
            "format": self.format,
            "size": self.size,
            "description": self.description
        })
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImageBlock":
        return cls(
            type=ContentType(data.get("type", "image")),
            id=data.get("id", shortuuid.uuid() if SHORTUUID_AVAILABLE else str(uuid.uuid4())),
            url=data.get("url", ""),
            alt_text=data.get("alt_text", ""),
            format=data.get("format", "unknown"),
            size=data.get("size", {}),
            description=data.get("description", ""),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", datetime.now().isoformat())
        )


@dataclass
class CodeBlock(ContentBlock):
    """代码块"""
    type: ContentType = ContentType.CODE
    code: str = ""
    language: str = "python"
    explanation: str = ""
    executable: bool = True
    execution_result: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = ContentType(self.type)

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "code": self.code,
            "language": self.language,
            "explanation": self.explanation,
            "executable": self.executable,
            "execution_result": self.execution_result
        })
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeBlock":
        return cls(
            type=ContentType(data.get("type", "code")),
            id=data.get("id", shortuuid.uuid() if SHORTUUID_AVAILABLE else str(uuid.uuid4())),
            code=data.get("code", ""),
            language=data.get("language", "python"),
            explanation=data.get("explanation", ""),
            executable=data.get("executable", True),
            execution_result=data.get("execution_result"),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", datetime.now().isoformat())
        )


@dataclass
class StepsBlock(ContentBlock):
    """任务分解步骤块 (策略三：任务分解)"""
    type: ContentType = ContentType.STEPS
    steps: List[str] = field(default_factory=list)
    current_step: int = 0
    total_steps: int = 0
    step_status: List[str] = field(default_factory=list)  # pending, in_progress, completed, failed
    progress_percentage: float = 0.0

    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = ContentType(self.type)
        if not self.step_status and self.steps:
            self.step_status = ["pending"] * len(self.steps)
            self.total_steps = len(self.steps)
        self.progress_percentage = (self.current_step / max(self.total_steps, 1)) * 100

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "steps": self.steps,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "step_status": self.step_status,
            "progress_percentage": self.progress_percentage
        })
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StepsBlock":
        return cls(
            type=ContentType(data.get("type", "steps")),
            id=data.get("id", shortuuid.uuid() if SHORTUUID_AVAILABLE else str(uuid.uuid4())),
            steps=data.get("steps", []),
            current_step=data.get("current_step", 0),
            total_steps=data.get("total_steps", 0),
            step_status=data.get("step_status", []),
            progress_percentage=data.get("progress_percentage", 0.0),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", datetime.now().isoformat())
        )


@dataclass
class Msg:
    """增强消息类 - 基于tech.txt策略的结构化内容块"""
    name: str
    content: Union[str, List[ContentBlock], List[Dict[str, Any]]]
    role: MessageRole
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: shortuuid.uuid() if SHORTUUID_AVAILABLE else str(uuid.uuid4()) if SHORTUUID_AVAILABLE else str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    parent_id: Optional[str] = None  # 父消息ID，用于构建对话树
    thread_id: Optional[str] = None  # 线程ID，用于多轮对话管理

    def __post_init__(self):
        if isinstance(self.role, str):
            self.role = MessageRole(self.role)

        # 自动转换内容为ContentBlock列表
        if isinstance(self.content, str):
            # 简单文本转换为TextBlock
            self.content = [TextBlock(text=self.content)]
        elif isinstance(self.content, list) and self.content and isinstance(self.content[0], dict):
            # 字典列表转换为ContentBlock列表
            self.content = [ContentBlock.from_dict(block) for block in self.content]

    def get_text_content(self, max_length: Optional[int] = None) -> str:
        """获取所有文本内容"""
        texts = []

        for block in self.get_blocks_by_type(ContentType.TEXT):
            if max_length and len(texts) + len(block.text) > max_length:
                remaining = max_length - len(''.join(texts))
                if remaining > 0:
                    texts.append(block.text[:remaining] + "...")
                break
            texts.append(block.text)

        # 也包含思维链推理内容
        for block in self.get_blocks_by_type(ContentType.THINKING):
            if max_length and len(texts) + len(block.reasoning) > max_length:
                remaining = max_length - len(''.join(texts))
                if remaining > 0:
                    texts.append(f"[推理] {block.reasoning[:remaining]}...")
                break
            texts.append(f"[推理] {block.reasoning}")

        return "\n".join(texts)

    def get_blocks_by_type(self, block_type: ContentType) -> List[ContentBlock]:
        """根据类型获取内容块"""
        if isinstance(self.content, list):
            return [block for block in self.content if isinstance(block, ContentBlock) and block.type == block_type]
        return []

    def get_blocks_by_types(self, block_types: List[ContentType]) -> Dict[ContentType, List[ContentBlock]]:
        """根据多种类型获取内容块"""
        result = {}
        for block_type in block_types:
            result[block_type] = self.get_blocks_by_type(block_type)
        return result

    def has_block_type(self, block_type: ContentType) -> bool:
        """检查是否包含特定类型的内容块"""
        return len(self.get_blocks_by_type(block_type)) > 0

    def add_block(self, block: ContentBlock) -> None:
        """添加内容块"""
        if not isinstance(self.content, list):
            self.content = []
        self.content.append(block)

    def add_text(self, text: str, format: str = "plain") -> None:
        """添加文本块"""
        self.add_block(TextBlock(text=text, format=format))

    def add_thinking(self, reasoning: str, step_number: int = 0, step_type: str = "general", confidence: float = 0.0) -> None:
        """添加思维链推理块 (策略一)"""
        self.add_block(ThinkingBlock(
            reasoning=reasoning,
            step_number=step_number,
            step_type=step_type,
            confidence=confidence
        ))

    def add_reference(self, title: str, content: str, source: str, credibility_score: float = 0.0, **kwargs) -> None:
        """添加参考资料块 (策略二)"""
        self.add_block(ReferenceBlock(
            title=title,
            content=content,
            source=source,
            credibility_score=credibility_score,
            **kwargs
        ))

    def add_tool_use(self, name: str, input_data: Dict[str, Any], tool_type: str = "function") -> ToolUseBlock:
        """添加工具使用块"""
        block = ToolUseBlock(name=name, input=input_data, tool_type=tool_type)
        self.add_block(block)
        return block

    def add_tool_result(self, tool_use_id: str, name: str, output: Any, success: bool = True, error: Optional[str] = None) -> ToolResultBlock:
        """添加工具结果块"""
        block = ToolResultBlock(
            tool_use_id=tool_use_id,
            name=name,
            output=output,
            success=success,
            error=error
        )
        self.add_block(block)
        return block

    def add_steps(self, steps: List[str], current_step: int = 0) -> StepsBlock:
        """添加任务分解步骤块 (策略三)"""
        block = StepsBlock(steps=steps, current_step=current_step)
        self.add_block(block)
        return block

    def get_tool_uses(self) -> List[ToolUseBlock]:
        """获取所有工具使用块"""
        return self.get_blocks_by_type(ContentType.TOOL_USE)

    def get_tool_results(self) -> List[ToolResultBlock]:
        """获取所有工具结果块"""
        return self.get_blocks_by_type(ContentType.TOOL_RESULT)

    def get_references(self) -> List[ReferenceBlock]:
        """获取所有参考资料块"""
        return self.get_blocks_by_type(ContentType.REFERENCE)

    def get_thinking_blocks(self) -> List[ThinkingBlock]:
        """获取所有思维链推理块"""
        return self.get_blocks_by_type(ContentType.THINKING)

    def get_steps_block(self) -> Optional[StepsBlock]:
        """获取任务分解步骤块"""
        steps_blocks = self.get_blocks_by_type(ContentType.STEPS)
        return steps_blocks[0] if steps_blocks else None

    def calculate_complexity_score(self) -> float:
        """计算消息复杂度分数"""
        score = 0.0

        # 基础分数
        if self.get_text_content():
            score += 0.1

        # 各种内容块的权重
        block_weights = {
            ContentType.THINKING: 0.3,
            ContentType.REFERENCE: 0.2,
            ContentType.TOOL_USE: 0.2,
            ContentType.CODE: 0.15,
            ContentType.STEPS: 0.25,
            ContentType.IMAGE: 0.1
        }

        for block_type, weight in block_weights.items():
            blocks = self.get_blocks_by_type(block_type)
            score += len(blocks) * weight

        # 特殊情况的额外分数
        if self.get_steps_block():
            score += 0.1  # 有任务分解

        if len(self.get_references()) > 3:
            score += 0.1  # 大量参考资料

        thinking_blocks = self.get_thinking_blocks()
        if thinking_blocks and any(block.confidence > 0.8 for block in thinking_blocks):
            score += 0.1  # 高置信度推理

        return min(score, 1.0)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "content": [block.to_dict() if isinstance(block, ContentBlock) else block for block in self.content],
            "role": self.role.value,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "parent_id": self.parent_id,
            "thread_id": self.thread_id,
            "complexity_score": self.calculate_complexity_score()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Msg":
        """从字典创建"""
        content = data.get("content", [])
        if isinstance(content, list) and content and isinstance(content[0], dict):
            content = [ContentBlock.from_dict(block) for block in content]
        elif isinstance(content, str):
            content = [TextBlock(text=content)]

        return cls(
            name=data["name"],
            content=content,
            role=MessageRole(data.get("role", "user")),
            metadata=data.get("metadata", {}),
            id=data.get("id", shortuuid.uuid() if SHORTUUID_AVAILABLE else str(uuid.uuid4())),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            parent_id=data.get("parent_id"),
            thread_id=data.get("thread_id")
        )

    def to_llm_format(self) -> List[Dict[str, str]]:
        """转换为LLM API格式"""
        messages = []

        # 主要文本内容
        text_content = self.get_text_content()
        if text_content:
            messages.append({
                "role": self.role.value,
                "content": text_content
            })

        # 如果有思维链推理，添加为系统消息
        thinking_blocks = self.get_thinking_blocks()
        if thinking_blocks:
            thinking_text = "\n".join([f"步骤{block.step_number}({block.step_type}): {block.reasoning}" for block in thinking_blocks])
            messages.append({
                "role": "system",
                "content": f"思维链推理过程:\n{thinking_text}"
            })

        # 如果有参考资料，添加为上下文
        references = self.get_references()
        if references:
            ref_text = "\n".join([f"[{ref.source}] {ref.title}: {ref.content[:200]}..." for ref in references])
            messages.append({
                "role": "system",
                "content": f"参考资料:\n{ref_text}"
            })

        return messages

    @classmethod
    def create_user_message(cls, name: str, content: str, **kwargs) -> "Msg":
        """创建用户消息"""
        return cls(name=name, content=content, role=MessageRole.USER, **kwargs)

    @classmethod
    def create_assistant_message(cls, name: str, content: str, **kwargs) -> "Msg":
        """创建助手消息"""
        return cls(name=name, content=content, role=MessageRole.ASSISTANT, **kwargs)

    @classmethod
    def create_system_message(cls, content: str, **kwargs) -> "Msg":
        """创建系统消息"""
        return cls(name="system", content=content, role=MessageRole.SYSTEM, **kwargs)


# 消息构建器类 - 基于tech.txt策略的便捷消息构建
class MessageBuilder:
    """消息构建器 - 提供便捷的消息构建方法"""

    def __init__(self, name: str, role: MessageRole = MessageRole.USER):
        self.msg = Msg(name=name, content=[], role=role)

    def text(self, content: str, format: str = "plain") -> "MessageBuilder":
        """添加文本"""
        self.msg.add_text(content, format)
        return self

    def thinking(self, reasoning: str, step: int = 0, step_type: str = "general", confidence: float = 0.0) -> "MessageBuilder":
        """添加思维链推理 (策略一)"""
        self.msg.add_thinking(reasoning, step, step_type, confidence)
        return self

    def reference(self, title: str, content: str, source: str, credibility: float = 0.0, **kwargs) -> "MessageBuilder":
        """添加参考资料 (策略二)"""
        self.msg.add_reference(title, content, source, credibility, **kwargs)
        return self

    def tool_use(self, name: str, input_data: Dict[str, Any], tool_type: str = "function") -> "MessageBuilder":
        """添加工具使用"""
        self.msg.add_tool_use(name, input_data, tool_type)
        return self

    def tool_result(self, tool_use_id: str, name: str, output: Any, success: bool = True, error: Optional[str] = None) -> "MessageBuilder":
        """添加工具结果"""
        self.msg.add_tool_result(tool_use_id, name, output, success, error)
        return self

    def steps(self, steps: List[str], current_step: int = 0) -> "MessageBuilder":
        """添加任务分解步骤 (策略三)"""
        self.msg.add_steps(steps, current_step)
        return self

    def code(self, code: str, language: str = "python", explanation: str = "") -> "MessageBuilder":
        """添加代码块"""
        self.msg.add_block(CodeBlock(code=code, language=language, explanation=explanation))
        return self

    def image(self, url: str, alt_text: str = "", description: str = "") -> "MessageBuilder":
        """添加图像块"""
        self.msg.add_block(ImageBlock(url=url, alt_text=alt_text, description=description))
        return self

    def metadata(self, **kwargs) -> "MessageBuilder":
        """添加元数据"""
        self.msg.metadata.update(kwargs)
        return self

    def build(self) -> Msg:
        """构建消息"""
        return self.msg


# 工厂函数
def create_message(role: str, name: str, content: str, **kwargs) -> Msg:
    """创建消息的便捷函数"""
    return Msg(name=name, content=content, role=MessageRole(role), **kwargs)

def create_user_message(name: str, content: str, **kwargs) -> Msg:
    """创建用户消息"""
    return Msg.create_user_message(name, content, **kwargs)

def create_assistant_message(name: str, content: str, **kwargs) -> Msg:
    """创建助手消息"""
    return Msg.create_assistant_message(name, content, **kwargs)
