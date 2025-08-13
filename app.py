from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载根目录下的 .env（如有）
BASE_DIR = Path(__file__).parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

# 路由层
from src.serve.api import api_router


def create_app() -> FastAPI:
    """创建 FastAPI 应用并注册中间件与路由。"""
    app = FastAPI(title="Deep Research Backend", version="0.1.0")

    # CORS（前后端联调友好；生产建议收窄 allow_origins）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册统一 /api 前缀路由
    app.include_router(api_router, prefix="/api")
    return app

g
app = create_app()


if __name__ == "__main__":
    # 本地启动：与前端默认 API_BASE_URL= http://localhost:8000/api 保持一致
    import uvicorn
    uvicorn.run("app:app", host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 8000)), reload=True)


