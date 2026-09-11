"""Document extraction for the upload dialog."""

import asyncio
import base64
from io import BytesIO
from pathlib import PurePosixPath
from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from backend.repositories.interaction_dao import InteractionDAO

TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".py", ".js", ".json", ".yaml", ".yml"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}


def document_response(document):
    return {
        "success": True, "status": "completed", "job_id": document["id"],
        "document_id": document["id"], "file_id": document["id"],
        "filename": document["filename"], "file_type": document["file_type"],
        "content_preview": document["content"][:500],
        "processed_content": document["content"], "created_at": document["created_at"],
    }


async def describe_image(content):
    def verify():
        with Image.open(BytesIO(content)) as image:
            image.verify()
    try:
        await asyncio.to_thread(verify)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise HTTPException(status_code=422, detail="图片内容无效") from exc
    from backend.config.llm_config import get_config
    from backend.core.llm.factory import LLMFactory
    config = get_config().get_provider_config("deepseek")
    # Normalize supported uploads to PNG, including BMP, before the multimodal request.
    def encode_png():
        with Image.open(BytesIO(content)) as image:
            output = BytesIO()
            image.convert("RGB").save(output, format="PNG")
        return base64.b64encode(output.getvalue()).decode("ascii")
    encoded = await asyncio.to_thread(encode_png)
    llm = LLMFactory.create_llm("deepseek")
    try:
        result = await llm.chat_completion(
            model=config.default_model,
            messages=[{"role": "user", "content": [
                {"type": "text", "text": "请描述这张图片并提取可见文字。"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded}"}},
            ]}],
        )
    finally:
        await llm.close()
    description = result.get("choices", [{}])[0].get("message", {}).get("content")
    if not isinstance(description, str) or not description.strip():
        raise ValueError("Image provider returned no description")
    return description


async def upload_document(file: UploadFile, user_id: str, dao=None):
    dao = dao or InteractionDAO()
    filename = PurePosixPath((file.filename or "").replace("\\", "/")).name
    extension = PurePosixPath(filename).suffix.lower()
    if extension not in TEXT_EXTENSIONS | IMAGE_EXTENSIONS:
        raise HTTPException(status_code=415, detail="不支持此文件类型")
    limit = (10 if extension in IMAGE_EXTENSIONS else 50) * 1024 * 1024
    try:
        content = await file.read(limit + 1)
    finally:
        await file.close()
    if len(content) > limit:
        raise HTTPException(status_code=413, detail="文件超过大小限制")
    if not content:
        raise HTTPException(status_code=422, detail="文件为空")
    if extension in TEXT_EXTENSIONS:
        try:
            processed = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=422, detail="文本文件必须使用 UTF-8 编码") from exc
        if "\x00" in processed:
            raise HTTPException(status_code=422, detail="文件包含无效文本")
        file_type = "text"
    else:
        try:
            processed = await describe_image(content)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=502, detail="图片分析失败，请检查视觉模型后重试") from exc
        file_type = "image"
    result = await dao.save_document(user_id, filename, file_type, processed, content)
    return document_response(result)
