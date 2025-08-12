# -*- coding: utf-8 -*-
"""
输出文本清洗工具：过滤推理可见内容（如 <think>...</think> 等）  # 模块说明
"""
import re  # 正则表达式库


_THINK_TAG_RE = re.compile(r"<\s*think\s*>[\s\S]*?<\s*/\s*think\s*>", re.IGNORECASE)  # 匹配<think>标签
_REASONING_TAG_RE = re.compile(r"<\s*reasoning\s*>[\s\S]*?<\s*/\s*reasoning\s*>", re.IGNORECASE)  # 匹配<reasoning>
_BRACKET_LINE_RE = re.compile(r"^[\s\t]*[【\[]?(思考|推理|推断|思路)[】\]]?\s*[:：].*$", re.MULTILINE)  # 匹配以“思考:”等开头的整行


def strip_reasoning(text: str) -> str:
    """移除文本中的推理/思考可见内容

    - 去除 <think>...</think>、<reasoning>...</reasoning>
    - 去除整行以“思考: / 推理: / 推断: / 思路:”开头的内容
    """
    if not text:  # 空文本直接返回
        return text
    cleaned = _THINK_TAG_RE.sub("", text)  # 去掉<think>块
    cleaned = _REASONING_TAG_RE.sub("", cleaned)  # 去掉<reasoning>块
    cleaned = _BRACKET_LINE_RE.sub("", cleaned)  # 去掉“思考:”整行
    # 再次清理多余的空行（可选）
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)  # 连续空行压缩为2行
    return cleaned.strip()  # 去首尾空白


class IncrementalReasoningFilter:
    """增量过滤器：用于SSE分片场景，避免<think>/<reasoning>内容在流中外泄

    用法：
      f = IncrementalReasoningFilter()
      safe = f.process(piece)  # 传入每个分片，返回安全的可输出文本
    """

    def __init__(self) -> None:
        self._inside: dict[str, bool] = {"think": False, "reasoning": False}  # 当前是否在某标签内
        self._buf: str = ""  # 处理缓冲，承载跨分片标签匹配

    def _find_case_insensitive(self, haystack: str, needle: str) -> int:
        return haystack.lower().find(needle.lower())

    def _consume_tag_start(self, tag: str) -> None:
        """进入标签态：删除起始标签（含'>'）前所有内容"""
        s = self._buf
        idx = self._find_case_insensitive(s, f"<{tag}")
        if idx < 0:
            return
        # 定位到下一个 '>' 作为起始标签结束
        gt = s.find('>', idx)
        if gt >= 0:
            # 丢弃到'>'为止内容（起始标签不输出）
            self._buf = s[gt + 1:]
            self._inside[tag] = True
        else:
            # 起始标签跨分片：仅保留从 idx 起的尾部以待下个分片补全
            self._buf = s[idx:]

    def _consume_tag_end_if_inside(self, tag: str) -> bool:
        """若在标签态，尝试消费结束标签并退出；返回是否完成退出"""
        if not self._inside[tag]:
            return True
        s = self._buf
        end_token = f"</{tag}>"
        idx = self._find_case_insensitive(s, end_token)
        if idx >= 0:
            # 丢弃结束标签之前的内容（即推理块），并丢弃结束标签本身
            self._buf = s[idx + len(end_token):]
            self._inside[tag] = False
            return True
        # 未发现结束标签：将缓冲限制在最大尾长，防止内存增长
        self._buf = s[-2048:]
        return False

    def process(self, piece: str) -> str:
        """处理单个内容分片，返回已过滤且可安全输出的文本"""
        if not piece:
            return ""
        self._buf += piece
        out_parts: list[str] = []

        while True:
            # 如果处于任意标签内，先尝试找到最近的结束标签
            progressed = False
            for tag in ("think", "reasoning"):
                if self._inside[tag]:
                    if not self._consume_tag_end_if_inside(tag):
                        # 仍在标签内，无法输出任何内容
                        return ""
                    progressed = True
            if progressed:
                # 可能已经跳出标签，继续下一轮处理
                continue

            # 不在任何标签内：查找下一个起始标签位置
            s = self._buf
            # 计算最近的起始标签位置与对应tag
            candidates: list[tuple[int, str]] = []
            for tag in ("think", "reasoning"):
                pos = self._find_case_insensitive(s, f"<{tag}")
                if pos >= 0:
                    candidates.append((pos, tag))
            if not candidates:
                # 无新起始标签，整段输出（但去掉“思考:”类行）
                out_parts.append(_BRACKET_LINE_RE.sub("", s))
                self._buf = ""
                break

            # 取最靠前的起始标签
            start_pos, tag = min(candidates, key=lambda x: x[0])
            # 输出起始标签前的安全文本（去掉“思考:”类行）
            safe_prefix = s[:start_pos]
            if safe_prefix:
                out_parts.append(_BRACKET_LINE_RE.sub("", safe_prefix))
            # 截断缓冲到起始标签位置以便进入标签态
            self._buf = s[start_pos:]
            # 进入标签态（并删除标签本体）
            self._consume_tag_start(tag)

        # 合并输出并做一次尾部清洗（压缩多空行）
        out_text = "".join(out_parts)
        out_text = re.sub(r"\n{3,}", "\n\n", out_text)
        return out_text



