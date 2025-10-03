# -*- coding: utf-8 -*-
"""
文件处理模块：处理各种格式的文件并转换为文本
支持PDF OCR、Office文档转换、图片识别等功能
"""

import asyncio
import locale
import os
import re
import subprocess
import time
from pathlib import Path
import ollama
import ocrmypdf
from aiohttp import web

from src.config.logging import get_logger
from .config import ALLOWED_EXTENSIONS, KB_ROOT_PATH, OCR_LANGUAGE
from .file_converter import convert_to_pdf

logger = get_logger("file_processor")


class FileProcessor:

    @staticmethod
    def _process_image_with_ollama_sync(image_path: Path, txt_path: Path):
        """
        [同步执行] 使用 Ollama 的 gemma3:12b 模型识别图片内容并保存为文本。
        这个函数是阻塞的，应当在 asyncio 的线程池中执行。
        
        :param image_path: 输入的图片文件路径。
        :param txt_path: 输出的文本文件路径。
        """
        logger.info(f"开始使用 Ollama 识别图片: {image_path}")
        try:
            # 准备向 Ollama 发送的消息
            messages = [
                {
                    'role': 'user',
                    'content': '请详细描述这张图片中的所有内容，包括场景、物体、人物、动作、氛围以及任何可辨识的文字。输出应为一段连贯的中文描述性文本,开头为该文件描述了',
                    'images': [str(image_path)] # 直接传递文件路径
                }
            ]

            # 调用 Ollama 服务 (这是一个同步阻塞调用)
            response = ollama.chat(
                model='gemma3:12b', # 使用您指定的高级模型
                messages=messages
            )

            # 提取并保存识别出的文本
            description = response['message']['content']
            if not description:
                raise ValueError("Ollama 模型返回了空描述。")

            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(description)
            
            logger.info(f"图片识别成功，描述已保存到: {txt_path}")

        except FileNotFoundError:
            logger.error(f"Ollama 识别失败：图片文件未找到 at {image_path}")
            raise
        except Exception as e:
            logger.error(f"调用 Ollama 服务时发生错误: {e}", exc_info=True)
            # 向上抛出异常，让上层调用者知道处理失败
            raise RuntimeError(f"Ollama 图片识别失败: {e}") from e

    @staticmethod
    async def save_and_process_file(file_bytes: bytes, original_filename: str, kb_name: str) -> Path:
        """
        异步入口：保存上传文件并调用同步处理；返回最终 TXT 路径
        - 修复：HTTP 错误 reason 必须单行
        """
        file_ext = Path(original_filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise web.HTTPBadRequest(reason=f"不支持的文件类型: {file_ext}。只支持 {', '.join(ALLOWED_EXTENSIONS)}")

        kb_path = KB_ROOT_PATH / kb_name
        kb_path.mkdir(exist_ok=True)
        save_path = kb_path / original_filename

        try:
            with open(save_path, 'wb') as f:
                f.write(file_bytes)
            logger.info(f"文件 '{original_filename}' 已成功保存到 '{save_path}'")
        except IOError as e:
            logger.error(f"保存文件时出错 '{save_path}': {e}")
            raise web.HTTPInternalServerError(reason="保存上传文件失败。")

        loop = asyncio.get_event_loop()
        try:
            txt_path = await loop.run_in_executor(
                None,
                FileProcessor._process_file_sync,
                save_path,
                kb_path,
                file_ext
            )
            return txt_path
        except Exception as e:
            logger.error(f"处理文件 '{original_filename}' 时发生严重错误: {e}", exc_info=True)
            # aiohttp 的 reason 不允许换行，做单行清洗
            single_line_reason = re.sub(r"[\r\n]+", " ", f"{e}")
            # 如需保留原始文件用于排查，可注释掉以下删除
            if save_path.exists():
                save_path.unlink()
            raise web.HTTPInternalServerError(reason=f"处理文件 '{original_filename}' 失败: {single_line_reason}")

    @staticmethod
    def _process_file_sync(file_path: Path, kb_path: Path, file_ext: str) -> Path:
        """
        同步处理主流程（在线程池中执行）：
        - PDF：调用升级版OCR流程
        - Office：先转 PDF 再 OCR
        - 图片：调用 Ollama 视觉模型进行描述
        - 纯文本：直接重命名或使用
        """
        txt_path = kb_path / f"{file_path.stem}.txt"

        office_formats = [".docx", ".doc", ".pptx", ".ppt"]
        text_formats = [".txt", ".md"]
        image_formats = [".png", ".jpg", ".jpeg"]

        if file_ext == ".pdf":
            FileProcessor.process_pdf_upgraded(file_path, txt_path)
            # 处理完后删除原始PDF文件
            if file_path.exists():
                file_path.unlink()
        elif file_ext in office_formats:
            pdf_path = None
            try:
                pdf_path = convert_to_pdf(file_path, kb_path)
                FileProcessor.process_pdf_upgraded(pdf_path, txt_path)
            finally:
                # 清理原始office文件和转换过程中的PDF
                if file_path.exists():
                    file_path.unlink()
                if pdf_path and pdf_path.exists():
                    pdf_path.unlink()
        
        elif file_ext in image_formats:
            try:
                # 调用同步的Ollama处理函数
                FileProcessor._process_image_with_ollama_sync(file_path, txt_path)
            finally:
                # 无论成功失败，都删除临时的原始图片文件
                if file_path.exists():
                    file_path.unlink()

        elif file_ext in text_formats:
            FileProcessor.process_text(file_path, txt_path)
            
        return txt_path

    @staticmethod
    def process_text(text_file_path: Path, txt_path: Path):
        """
        优化后的文本处理
        如果文件是.md，直接重命名为.txt；如果是.txt，则什么都不做，避免IO。
        """
        logger.info(f"正在处理文本文件: {text_file_path}...")
        try:
            # 如果源文件是 .md 且目标 .txt 文件不存在，直接重命名
            if text_file_path.suffix.lower() == ".md":
                if text_file_path.exists():
                    os.rename(text_file_path, txt_path)
                    logger.info(f"已将 {text_file_path} 重命名为 {txt_path}")
            # 如果已经是 .txt 文件，并且源和目标是同一个文件，则无需任何操作
            elif text_file_path == txt_path:
                logger.info(f"文件已经是 .txt 格式且路径相同，无需处理: {text_file_path}")
            else:
                # 兼容其他文本格式（虽然目前只有.txt和.md）或路径不同的情况，进行内容复制
                with open(text_file_path, 'r', encoding='utf-8', errors='replace') as f_in:
                    content = f_in.read()
                with open(txt_path, 'w', encoding='utf-8') as f_out:
                    f_out.write(content)
                
                # 复制完成后删除原始文件
                if text_file_path.exists():
                    text_file_path.unlink()
        except Exception as e:
            logger.error(f"处理文本文件 {text_file_path} 时出错: {e}")
            raise

    @staticmethod
    def process_pdf_upgraded(pdf_path: Path, txt_path: Path):
        """
        使用两阶段 OCR 策略和原子写入，对PDF文件进行健壮的处理。
        """
        logger.info(f"正在使用升级版 OCR 参数处理 PDF: {pdf_path}...")
        
        tmp_txt_path = txt_path.with_suffix(".txt.tmp")
        
        # 策略一：尝试 --redo-ocr
        cmd_redo = [
            "ocrmypdf", "-l", OCR_LANGUAGE, "--redo-ocr",
            "--rotate-pages", "--optimize", "1", "--oversample", "300",
            "--tesseract-timeout", "300", "--skip-big", "300",
            "--sidecar", str(tmp_txt_path), str(pdf_path), "-",
        ]

        # 策略二：回退方案
        cmd_force = [
            "ocrmypdf", "-l", OCR_LANGUAGE, "--force-ocr",
            "--rotate-pages", "--deskew", "--optimize", "1",
            "--oversample", "300", "--tesseract-timeout", "300", "--skip-big", "300",
            "--sidecar", str(tmp_txt_path), str(pdf_path), "-",
        ]
        
        success = False
        last_error = ""
        encoding = locale.getpreferredencoding(False)

        # 首先尝试策略一
        try:
            logger.info("OCR 尝试 #1: 使用 --redo-ocr 策略...")
            proc = subprocess.run(cmd_redo, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
            if proc.stderr:
                logger.info(f"OCRmyPDF (--redo-ocr) 日志:\n{proc.stderr.decode(encoding, errors='ignore')}")
            success = True
        except subprocess.CalledProcessError as e:
            last_error = e.stderr.decode(encoding, errors='ignore')
            logger.warning(f"--redo-ocr 策略失败，将尝试 --force-ocr。错误: {last_error}")
        except FileNotFoundError:
            logger.error("命令 'ocrmypdf' 未找到。")
            raise RuntimeError("OCR 工具 (ocrmypdf) 不可用。")

        # 检查是否需要兜底
        need_fallback = False
        if not success:
            need_fallback = True
        elif tmp_txt_path.exists():
            try:
                if tmp_txt_path.stat().st_size < 200: # 检查文件大小
                     logger.warning(f"策略一提取的文本量过少，将尝试兜底策略")
                     need_fallback = True
            except Exception as e:
                logger.warning(f"读取临时文本文件大小失败: {e}")
                need_fallback = True
        
        # 如果需要，尝试策略二
        if need_fallback:
            try:
                logger.info("OCR 尝试 #2: 使用 --force-ocr + --deskew 策略...")
                proc = subprocess.run(cmd_force, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
                if proc.stderr:
                    logger.info(f"OCRmyPDF (--force-ocr) 日志:\n{proc.stderr.decode(encoding, errors='ignore')}")
                success = True
            except subprocess.CalledProcessError as e:
                last_error = e.stderr.decode(encoding, errors='ignore')
                logger.error(f"--force-ocr 策略也失败了。错误: {last_error}")
                success = False # 明确设置失败
            except FileNotFoundError:
                 logger.error("命令 'ocrmypdf' 未找到。")
                 raise RuntimeError("OCR 工具 (ocrmypdf) 不可用。")

        if not success:
            clean_error = last_error.replace('\\n', ' ').replace('\\r', '')
            raise RuntimeError(f"所有 OCR 策略均失败: {clean_error}")

        if tmp_txt_path.exists():
            os.replace(tmp_txt_path, txt_path)
            logger.info(f"成功将 PDF-OCR 文本原子化写入到: {txt_path}")
        else:
            txt_path.touch()
            logger.warning(f"OCR 过程没有生成文本文件，可能PDF为空。已创建空的标记文件: {txt_path}")

    @staticmethod
    async def cleanup_kb_files(kb_name: str):
        """
        删除与指定知识库相关的所有文件
        """
        kb_path = KB_ROOT_PATH / kb_name
        if not kb_path.is_dir():
            return

        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, FileProcessor._delete_directory, kb_path)
            logger.info(f"已成功删除知识库目录: {kb_path}")
        except Exception as e:
            logger.error(f"删除知识库目录 '{kb_path}' 时出错: {e}")
            raise

    @staticmethod
    def _delete_directory(path: Path):
        import shutil
        shutil.rmtree(path)