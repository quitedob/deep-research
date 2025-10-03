# -*- coding: utf-8 -*-
"""
文件转换模块：将各种文档格式转换为PDF，以便后续的OCR处理
"""

import os
import subprocess
from pathlib import Path
from src.config.logging import get_logger

logger = get_logger("file_converter")

def convert_to_pdf(input_path: Path, output_dir: Path) -> Path:
    """
    将输入的文档文件转换为PDF格式。
    目前支持 .docx, .doc, .pptx, .ppt 文件。
    使用 unoconv (依赖LibreOffice)进行转换，因为它稳定且支持格式广泛。

    :param input_path: 输入文件的路径。
    :param output_dir: PDF输出目录的路径。
    :return: 转换后的PDF文件路径。
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_path = output_dir / f"{input_path.stem}.pdf"
    
    logger.info(f"开始将 {input_path} 转换为 PDF...")

    try:
        # 使用 unoconv 进行转换。这是一个强大的工具，但需要在系统中安装。
        # 'unoconv', '-f', 'pdf', '-o', str(pdf_path), str(input_path)
        # 为确保在不同环境下的可用性，我们优先使用subprocess调用soffice
        command = [
            "soffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_dir),
            str(input_path),
        ]
        
        # 在独立的进程中运行转换命令
        process = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        # soffice 会自动命名文件，我们需要找到它
        expected_output_filename = f"{input_path.stem}.pdf"
        generated_pdf_path = output_dir / expected_output_filename

        if not generated_pdf_path.exists():
            # 有时soffice的输出文件名可能与预期不完全一致，做一次检查
            found = False
            for f in output_dir.glob("*.pdf"):
                if f.stem == input_path.stem:
                    generated_pdf_path = f
                    found = True
                    break
            if not found:
                 raise FileNotFoundError(f"转换后的PDF文件未在输出目录中找到: {expected_output_filename}")

        logger.info(f"成功将文件转换为PDF: {generated_pdf_path}")
        return generated_pdf_path

    except FileNotFoundError:
        logger.error("错误: 'soffice' 命令未找到。请确保LibreOffice已安装并配置在系统的PATH中。")
        raise RuntimeError("文档转换工具 (LibreOffice) 不可用。")
    except subprocess.CalledProcessError as e:
        error_message = f"使用soffice转换文件 '{input_path}' 时失败。\n" \
                        f"返回码: {e.returncode}\n" \
                        f"输出: {e.stdout}\n" \
                        f"错误: {e.stderr}"
        logger.error(error_message)
        raise RuntimeError(f"文档转换失败: {e.stderr}")
    except Exception as e:
        logger.error(f"转换文件到PDF时发生未知错误: {e}")
        raise