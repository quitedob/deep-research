# -*- coding: utf-8 -*-
"""
消息系统 - 参考 AgentScope 的 Msg 类
"""
import shortuuid
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Msg:
    """消息类 - 参考 AgentScope"""
    name: str
    content: Union[str, List[Dict[str, Any]]]
    role: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: shortuuid.uuid())
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def get_text_content(self) -> str:
        """获取文本内容"""
        if isinstance(self.content, str):
            return self.content
        elif isinstance(self.content, list):
            texts = []
            for block in self.content:
                if isinstance(block, dict) and block.get("type") == "text":
                    texts.append(block.get("text", ""))
            return "\n".join(texts)
        return ""
    
    def get_content_blocks(self, block_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取内容块"""
        if isinstance(self.content, list):
            if block_type:
                return [b for b in self.content if b.get("type") == block_type]
            return self.content
        return []
    
    def has_content_blocks(self, block_type: str) -> bool:
        """检查是否有特定类型的内容块"""
        return len(self.get_content_blocks(block_type)) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "content": self.content,
            "role": self.role,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Msg":
        """从字典创建"""
        return cls(
            name=data["name"],
            content=data["content"],
            role=data["role"],
            metadata=data.get("metadata", {}),
            id=data.get("id", shortuuid.uuid()),
            timestamp=data.get("timestamp", datetime.now().isoformat())
        )


# 内容块类型定义
@dataclass
class TextBlock:
    """文本块"""
    type: str = "text"
    text: str = ""


@dataclass
class ToolUseBlock:
    """工具使用块"""
    type: str = "tool_use"
    id: str = field(default_factory=lambda: shortuuid.uuid())
    name: str = ""
    input: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResultBlock:
    """工具结果块"""
    type: str = "tool_result"
    id: str = ""
    name: str = ""
    output: Any = None
