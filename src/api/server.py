"""
FastAPI 服务入口 - 启动 Web GUI 后端

开发模式：
    uvicorn src.api.server:app --reload --port 8000
    # 前端单独启动: cd frontend && npm run dev

生产模式：
    cd frontend && npm run build   # 构建前端到 src/api/static/
    python -m src.api.server        # FastAPI 同时 serve 前端和 API
    # 访问 http://localhost:8000
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.routes import router
from src.config import LLM_PROVIDER, CURRENT_LLM_MODEL


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    app = FastAPI(
        title="NIO Diagnosis Agent API",
        description="蔚来效能平台 AI 智能诊断系统 - Web API",
        version="0.1.0",
    )

    # CORS：允许 Vite dev server (localhost:5173) 跨域访问
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 挂载 API 路由
    app.include_router(router, prefix="/api")

    # 生产模式：serve 前端静态文件
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists() and (static_dir / "index.html").exists():
        app.mount(
            "/",
            StaticFiles(directory=str(static_dir), html=True),
            name="frontend",
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    print(f"\n  NIO Diagnosis Agent - Web GUI")
    print(f"  LLM 供应商: {LLM_PROVIDER} | 模型: {CURRENT_LLM_MODEL}")
    print(f"  启动中... http://localhost:8000\n")

    uvicorn.run(
        "src.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
