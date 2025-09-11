# -*- coding: utf-8 -*-
"""
Markdown导出器
将内容导出为Markdown格式
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class MarkdownExporter:
    """Markdown格式导出器"""
    
    def __init__(self, template: Optional[str] = None):
        self.template = template or "default"
    
    def export(self, content: str, title: str = "导出文档", metadata: Optional[Dict[str, Any]] = None) -> str:
        """导出为Markdown格式
        
        Args:
            content: 要导出的内容
            title: 文档标题
            metadata: 元数据信息
            
        Returns:
            Markdown格式的字符串
        """
        metadata = metadata or {}
        
        # 构建Markdown文档
        md_content = []
        
        # 标题
        md_content.append(f"# {title}\n")
        
        # 元数据
        if metadata:
            md_content.append("> **文档信息**")
            for key, value in metadata.items():
                md_content.append(f"> - **{key}**: {value}")
            md_content.append("")
        
        # 导出时间
        export_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        md_content.append(f"> 导出时间: {export_time}\n")
        
        # 分隔线
        md_content.append("---\n")
        
        # 主要内容
        md_content.append(content)
        
        # 页脚
        md_content.append("\n---")
        md_content.append("*由 AgentWork AI研究助手 生成*")
        
        return "\n".join(md_content)
    
    def save_to_file(self, content: str, title: str, output_path: Path, **kwargs) -> Path:
        """保存到文件
        
        Args:
            content: 内容
            title: 标题
            output_path: 输出路径
            **kwargs: 其他参数
            
        Returns:
            保存的文件路径
        """
        md_content = self.export(content, title, **kwargs)
        
        # 确保目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        output_path.write_text(md_content, encoding='utf-8')
        
        return output_path
