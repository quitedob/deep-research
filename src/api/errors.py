# -*- coding: utf-8 -*-
"""
统一错误处理模块
提供标准化的错误响应格式和错误处理机制
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """统一错误响应模型"""
    error: bool = True
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class ErrorCodes:
    """错误代码常量"""
    # 通用错误
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    RATE_LIMITED = "RATE_LIMITED"

    # 数据库相关错误
    DATABASE_ERROR = "DATABASE_ERROR"
    CONNECTION_ERROR = "CONNECTION_ERROR"

    # 文件处理错误
    FILE_UPLOAD_ERROR = "FILE_UPLOAD_ERROR"
    FILE_PROCESSING_ERROR = "FILE_PROCESSING_ERROR"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"

    # RAG相关错误
    SEARCH_ERROR = "SEARCH_ERROR"
    VECTOR_STORE_ERROR = "VECTOR_STORE_ERROR"

    # 认证相关错误
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"

    # 业务逻辑错误
    BUSINESS_LOGIC_ERROR = "BUSINESS_LOGIC_ERROR"
    RESOURCE_NOT_READY = "RESOURCE_NOT_READY"


def create_error_response(
    code: str,
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> JSONResponse:
    """创建标准化的错误响应"""
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            code=code,
            message=message,
            details=details,
            request_id=request_id
        ).dict()
    )


def handle_database_error(error: Exception, operation: str = "database_operation") -> JSONResponse:
    """处理数据库相关错误"""
    from src.config.logging.logging import get_logger
    logger = get_logger("errors")

    logger.error(f"数据库操作失败: {operation} - {str(error)}")

    return create_error_response(
        code=ErrorCodes.DATABASE_ERROR,
        message="数据库操作失败，请稍后重试",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={"operation": operation, "error_type": type(error).__name__}
    )


def handle_validation_error(error: Exception, field: Optional[str] = None) -> JSONResponse:
    """处理验证错误"""
    from src.config.logging.logging import get_logger
    logger = get_logger("errors")

    logger.warning(f"验证失败: {field or 'unknown'} - {str(error)}")

    return create_error_response(
        code=ErrorCodes.VALIDATION_ERROR,
        message="输入数据验证失败",
        status_code=status.HTTP_400_BAD_REQUEST,
        details={"field": field, "error": str(error)}
    )


def handle_file_error(error: Exception, filename: str = "", operation: str = "file_operation") -> JSONResponse:
    """处理文件相关错误"""
    from src.config.logging.logging import get_logger
    logger = get_logger("errors")

    logger.error(f"文件操作失败: {operation} - {filename} - {str(error)}")

    return create_error_response(
        code=ErrorCodes.FILE_PROCESSING_ERROR,
        message="文件处理失败",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={"filename": filename, "operation": operation}
    )


def handle_auth_error(error: Exception, operation: str = "authentication") -> JSONResponse:
    """处理认证相关错误"""
    from src.config.logging.logging import get_logger
    logger = get_logger("errors")

    logger.warning(f"认证失败: {operation} - {str(error)}")

    return create_error_response(
        code=ErrorCodes.UNAUTHORIZED,
        message="认证失败",
        status_code=status.HTTP_401_UNAUTHORIZED,
        details={"operation": operation}
    )


def handle_not_found_error(resource: str, resource_id: Optional[str] = None) -> JSONResponse:
    """处理资源未找到错误"""
    from src.config.logging.logging import get_logger
    logger = get_logger("errors")

    logger.info(f"资源未找到: {resource} - {resource_id or 'unknown'}")

    return create_error_response(
        code=ErrorCodes.NOT_FOUND,
        message=f"{resource}不存在",
        status_code=status.HTTP_404_NOT_FOUND,
        details={"resource": resource, "resource_id": resource_id}
    )


def handle_rate_limit_error() -> JSONResponse:
    """处理速率限制错误"""
    from src.config.logging.logging import get_logger
    logger = get_logger("errors")

    logger.warning("触发速率限制")

    return create_error_response(
        code=ErrorCodes.RATE_LIMITED,
        message="请求过于频繁，请稍后再试",
        status_code=status.HTTP_429_TOO_MANY_REQUESTS
    )


class APIException(HTTPException):
    """自定义API异常类，提供更丰富的错误信息"""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.code = code
        self.details = details or {}
        self.details["error_code"] = code

        super().__init__(
            status_code=status_code,
            detail=message,
            headers=headers
        )


def create_success_response(
    data: Any,
    message: str = "操作成功",
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """创建标准化的成功响应"""
    response = {
        "error": False,
        "message": message,
        "data": data
    }

    if request_id:
        response["request_id"] = request_id

    return response


