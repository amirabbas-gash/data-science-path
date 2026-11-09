from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="1.0.0", docs_url="/api/docs")
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_url], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.middleware("http")
async def enforce_trusted_origin(request: Request, call_next):
    """Reject cross-origin browser mutations before cookie authentication runs."""
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = request.headers.get("origin")
        if origin and origin.rstrip("/") != settings.frontend_url.rstrip("/"):
            return JSONResponse(status_code=403, content={"detail": "Untrusted request origin"})
    return await call_next(request)


@app.get("/health")
async def health(): return {"status": "ok"}
