# -*- coding: utf-8 -*-
"""
DSL验证器

验证生成的DSL格式是否正确。
"""

import logging
import xml.etree.ElementTree as ET
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)


def validate_dsl(dsl_content: str) -> Tuple[bool, str]:
    """
    验证DSL内容

    参数:
        dsl_content: DSL内容（XML格式）

    返回:
        (是否有效, 错误消息)
    """
    try:
        # 清理内容
        dsl_content = dsl_content.strip()

        # 移除可能的markdown代码块标记
        if dsl_content.startswith("```xml"):
            dsl_content = dsl_content[6:]
        if dsl_content.startswith("```"):
            dsl_content = dsl_content[3:]
        if dsl_content.endswith("```"):
            dsl_content = dsl_content[:-3]
        dsl_content = dsl_content.strip()

        # 检查是否为空
        if not dsl_content:
            return False, "DSL内容为空"

        # 尝试解析XML
        try:
            root = ET.fromstring(dsl_content)
        except ET.ParseError as e:
            return False, f"XML解析错误: {str(e)}"

        # 检查根元素
        if root.tag != "PRESENTATION":
            return False, f"根元素应为PRESENTATION，实际为{root.tag}"

        # 检查是否有SECTION元素
        sections = root.findall(".//SECTION")
        if not sections:
            return False, "未找到SECTION元素"

        # 检查每个SECTION
        for i, section in enumerate(sections):
            # 检查layout属性
            layout = section.get("layout")
            if not layout:
                return False, f"第{i+1}个SECTION缺少layout属性"

            # 检查是否有TITLE
            title = section.find("TITLE")
            if title is None:
                logger.warning(f"第{i+1}个SECTION缺少TITLE元素")

        logger.info(f"DSL验证通过，包含{len(sections)}个SECTION")
        return True, "验证通过"

    except Exception as e:
        logger.error(f"DSL验证异常: {str(e)}")
        return False, f"验证异常: {str(e)}"


def extract_sections_count(dsl_content: str) -> int:
    """
    提取DSL中的SECTION数量

    参数:
        dsl_content: DSL内容

    返回:
        SECTION数量
    """
    try:
        dsl_content = dsl_content.strip()
        if dsl_content.startswith("```"):
            lines = dsl_content.split("\n")
            dsl_content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        root = ET.fromstring(dsl_content)
        sections = root.findall(".//SECTION")
        return len(sections)
    except Exception:
        return 0


def get_dsl_metadata(dsl_content: str) -> Dict[str, Any]:
    """
    提取DSL元数据

    参数:
        dsl_content: DSL内容

    返回:
        元数据字典
    """
    metadata = {
        "title": "",
        "language": "",
        "tone": "",
        "slide_count": 0
    }

    try:
        dsl_content = dsl_content.strip()
        if dsl_content.startswith("```"):
            lines = dsl_content.split("\n")
            dsl_content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        root = ET.fromstring(dsl_content)

        # 提取METADATA
        metadata_elem = root.find("METADATA")
        if metadata_elem is not None:
            title_elem = metadata_elem.find("TITLE")
            if title_elem is not None and title_elem.text:
                metadata["title"] = title_elem.text.strip()

            language_elem = metadata_elem.find("LANGUAGE")
            if language_elem is not None and language_elem.text:
                metadata["language"] = language_elem.text.strip()

            tone_elem = metadata_elem.find("TONE")
            if tone_elem is not None and tone_elem.text:
                metadata["tone"] = tone_elem.text.strip()

        # 统计SECTION数量
        sections = root.findall(".//SECTION")
        metadata["slide_count"] = len(sections)

    except Exception as e:
        logger.error(f"提取元数据失败: {str(e)}")

    return metadata
