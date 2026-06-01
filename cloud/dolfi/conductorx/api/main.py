"""
ConductorX FastAPI — main API entry point.

Endpoints:
  POST /api/chat          — send message to ConductorX (3SP-aware)
  GET  /api/device/info   — Flipper device info
  POST /api/device/flash  — Flash firmware (Speed 3 confirmation bypass)
  POST /api/files/upload  — Upload file to SD card
  GET  /api/files/list    — List SD card contents
  GET  /api/logs/stream   — SSE stream of serial logs
  POST /api/speed         — Set 3SP speed mode
  GET  /api/audit         — Query audit ledger
  GET  /health            — Health check
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..agents.receptionist import ReceptionistAgent
from ..agents.conductor import ConductorAgent
from ..agents.code_agent import CodeAgent
from ..agents.debug_agent import DebugAgent
from ..agents.recovery import RecoveryAgent
from ..agents.sql_agent import SQLAgent
from ..agents.crypto_agent import CryptoAgent
from ..agents.tutorial import TutorialAgent
from ..ledger.chain import AuditLedger
from ..speed.mode_controller import ModeController, Speed
from ..infra.containers import InfraManager


# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------

_infra = InfraManager()
_ledger = AuditLedger()
_mode = ModeController()

_receptionist = ReceptionistAgent()
_conductor = ConductorAgent(stub_mode=os.getenv("DOLFI_ENV", "ci") != "prod")
_code = CodeAgent()
_debug = DebugAgent()
_recovery = RecoveryAgent()
_sql = SQLAgent()
_crypto = CryptoAgent()
_tutorial = TutorialAgent()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    cfg = _infra.config()
    app.state.infra = cfg
    yield
    _infra.teardown()


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    app = FastAPI(
        title="Dolfi.AI — ConductorX API",
        description="Cloud qFlipper with AI orchestration",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(_router)
    return app


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8192)
    speed: int = Field(default=1, ge=1, le=3)
    domain: str | None = None


class ChatResponse(BaseModel):
    reply: str
    agent: str
    speed: int
    rag_context_used: bool = False


class SpeedRequest(BaseModel):
    speed: int = Field(..., ge=1, le=3)


class FlashRequest(BaseModel):
    firmware_version: str
    confirmed: bool = False


class UploadRequest(BaseModel):
    remote_path: str
    content_b64: str


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

from fastapi import APIRouter
_router = APIRouter()


@_router.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}


@_router.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    _mode.set_speed(req.speed)
    decision = _receptionist.route(req.message)
    _ledger.append("receptionist", "route", {"target": decision.target, "confidence": decision.confidence})

    # Speed 2: auto-detect from message content
    if req.speed == 2:
        _mode.auto_detect(req.message)

    reply = f"[ConductorX Speed {req.speed} → {decision.target}] Routing: {decision.reason}"
    return ChatResponse(
        reply=reply,
        agent=decision.target,
        speed=req.speed,
        rag_context_used=False,
    )


@_router.get("/api/device/info")
async def device_info() -> dict:
    result = await _conductor.device_info()
    _ledger.append("conductor", "device_info", {"success": result.success})
    if not result.success:
        raise HTTPException(status_code=503, detail=result.error)
    return {"output": result.output, "success": result.success}


@_router.post("/api/device/flash")
async def flash_firmware(req: FlashRequest) -> dict:
    if not req.confirmed and not _mode.is_autonomous():
        raise HTTPException(
            status_code=400,
            detail="Flash requires explicit confirmation. Set confirmed=true or use Speed 3.",
        )
    _ledger.append("conductor", "flash", {"firmware_version": req.firmware_version})
    # In production: trigger firmware download + flash pipeline
    return {"status": "queued", "firmware_version": req.firmware_version}


@_router.get("/api/files/list")
async def list_files() -> dict:
    result = await _conductor.list_storage()
    _ledger.append("conductor", "list_storage", {"success": result.success})
    return {"output": result.output, "success": result.success}


@_router.get("/api/logs/stream")
async def stream_logs() -> StreamingResponse:
    async def generator():
        async for line in _conductor.stream_log():
            yield f"data: {line}\n\n"
    return StreamingResponse(generator(), media_type="text/event-stream")


@_router.post("/api/speed")
async def set_speed(req: SpeedRequest) -> dict:
    speed = _mode.set_speed(req.speed)
    _ledger.append("system", "set_speed", {"speed": speed.value})
    return {"speed": speed.value, "name": speed.name}


@_router.get("/api/audit")
async def get_audit() -> dict:
    chain_valid = _ledger.verify_chain()
    return {
        "chain_valid": chain_valid,
        "entries": _ledger.to_list()[-50:],
    }


@_router.post("/api/code/proof")
async def proof_code(body: dict) -> dict:
    code = body.get("code", "")
    language = body.get("language", "python")
    result = _code.proof_python(code) if language == "python" else _code.proof_c(code)
    return {
        "is_safe": result.is_safe,
        "issues": result.issues,
        "suggestions": result.suggestions,
        "rewritten": result.rewritten,
    }


@_router.post("/api/debug/analyze")
async def analyze_error(body: dict) -> dict:
    error_text = body.get("error", "")
    analysis = _debug.analyze(error_text)
    return {
        "error_type": analysis.error_type,
        "message": analysis.message,
        "file": analysis.file,
        "line": analysis.line,
        "suggestions": analysis.suggestions,
        "auto_fixable": analysis.auto_fixable,
        "report": _debug.format_report(analysis),
    }


# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------

app = create_app()
