#!/usr/bin/env python3
"""
Beautiful Web Interface for FAL.AI Video Generator
FastAPI-based modern web application with drag-and-drop, preview, and progress tracking
"""

import asyncio
import os
import json
import uuid
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import uvicorn

# Import our existing modules
from main import Config, VideoGenerator
from security import security_manager
from performance import (
    performance_optimizer, cache_manager, async_file_manager,
    performance_monitor_decorator, optimized_api_call
)

# ========================================================================
#                              Web Application                            
# ========================================================================

app = FastAPI(
    title="FAL.AI Video Generator",
    description="Professional Video Generation Interface",
    version="2.0.0",
    docs_url=None if os.getenv("PRODUCTION", "false").lower() == "true" else "/docs",
    redoc_url=None if os.getenv("PRODUCTION", "false").lower() == "true" else "/redoc"
)

# Rate limiting configuration
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Production CORS configuration
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000,http://localhost:8001,http://127.0.0.1:8001").split(",")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=ALLOWED_HOSTS
)

app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Only allow necessary methods
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # Content Security Policy
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
        "font-src 'self' https://cdnjs.cloudflare.com; "
        "img-src 'self' data: blob:; "
        "media-src 'self' blob:; "
        "connect-src 'self' wss: ws:; "
        "frame-ancestors 'none'; "
        "base-uri 'self';"
    )
    response.headers["Content-Security-Policy"] = csp
    
    # HTTPS enforcement in production
    if os.getenv("PRODUCTION", "false").lower() == "true":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# Static files and templates
app.mount("/static", StaticFiles(directory="web/static"), name="static")
templates = Jinja2Templates(directory="web/templates")

# Global application state
config = Config()
generator = VideoGenerator(config)

# WebSocket connection manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.job_status: Dict[str, Dict] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast_job_update(self, job_id: str, status: dict):
        self.job_status[job_id] = status
        message = {"job_id": job_id, "status": status}
        
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                dead_connections.append(connection)
        
        # Clean up dead connections
        for connection in dead_connections:
            self.active_connections.remove(connection)

manager = ConnectionManager()

# ========================================================================
#                                Routes                                   
# ========================================================================

@app.get("/", response_class=HTMLResponse)
@limiter.limit("30/minute")
async def home(request: Request):
    """Main application page"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "FAL.AI Video Generator",
        "models": config.get("models", {})
    })

@app.get("/api/models")
@limiter.limit("60/minute")
async def get_models(request: Request):
    """Get available models with detailed cost information"""
    models = config.get("models", {})
    
    # Filter out non-dict entries and add cost calculations
    enhanced_models = {}
    
    for key, model_data in models.items():
        if isinstance(model_data, dict) and "endpoint" in model_data and "cost_5s" in model_data:
            enhanced_models[key] = {
                **model_data,
                "cost_breakdown": {
                    "5_seconds": f"${model_data['cost_5s']:.2f}",
                    "10_seconds": f"${model_data['cost_10s']:.2f}",
                    "per_second": f"${model_data['cost_per_second']:.3f}/s"
                },
                "duration_options": [5, 10] if model_data['max_duration'] >= 10 else [5],
                "recommended": key in ["kling_21_pro", "kling_21_standard"]  # Highlight recommended models
            }
    
    # Calculate cost ranges if we have models
    cost_calculator = {}
    if enhanced_models:
        cost_calculator = {
            "5s_range": {
                "min": min(m["cost_5s"] for m in enhanced_models.values()),
                "max": max(m["cost_5s"] for m in enhanced_models.values())
            },
            "10s_range": {
                "min": min(m["cost_10s"] for m in enhanced_models.values()),
                "max": max(m["cost_10s"] for m in enhanced_models.values())
            }
        }
    
    return {
        "models": enhanced_models,
        "default_model": "kling_21_pro" if "kling_21_pro" in enhanced_models else (list(enhanced_models.keys())[0] if enhanced_models else None),
        "cost_calculator": cost_calculator
    }

@app.post("/api/upload")
@limiter.limit("10/minute")
@performance_monitor_decorator("file_upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    """Upload and validate image file"""
    try:
        # Enhanced file validation
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Only image files are allowed")
        
        # File size limit (10MB)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB")
        
        # Reset file pointer after reading
        await file.seek(0)
        
        # Save uploaded file temporarily
        upload_dir = Path("./temp/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        temp_path = upload_dir / f"{file_id}{file_extension}"
        
        # File already read above for size validation
        await async_file_manager.write_file(str(temp_path), content)
        
        # Validate with security manager
        validated_path = security_manager.validator.sanitize_file_path(str(temp_path))
        if not validated_path:
            os.unlink(temp_path)
            raise HTTPException(status_code=400, detail="Invalid or unsafe file")
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "size": len(content),
            "path": str(temp_path),
            "preview_url": f"/api/preview/{file_id}{file_extension}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/preview/{file_path}")
@limiter.limit("100/minute")
async def get_file_preview(request: Request, file_path: str):
    """Get file preview (serve uploaded images)"""
    full_path = Path("./temp/uploads") / file_path
    
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    from fastapi.responses import FileResponse
    return FileResponse(full_path)

@app.post("/api/generate")
@limiter.limit("5/minute")
async def generate_video(
    request: Request,
    model: str = Form(...),
    prompt: str = Form(...),
    file_id: str = Form(...),
    duration: int = Form(5),
    aspect_ratio: str = Form("16:9"),
    negative_prompt: Optional[str] = Form(None),
    cfg_scale: Optional[float] = Form(None),
    tail_file_id: Optional[str] = Form(None)
):
    """Generate video with security validation"""
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Find uploaded file
        upload_dir = Path("./temp/uploads")
        image_files = list(upload_dir.glob(f"{file_id}*"))
        if not image_files:
            raise HTTPException(status_code=404, detail="Uploaded file not found")
        
        image_path = str(image_files[0])
        
        # Prepare generation parameters
        kwargs = {
            "image_path": image_path,
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio
        }
        
        if negative_prompt:
            kwargs["negative_prompt"] = negative_prompt
        if cfg_scale is not None:
            kwargs["cfg_scale"] = cfg_scale
        if tail_file_id:
            tail_files = list(upload_dir.glob(f"{tail_file_id}*"))
            if tail_files:
                kwargs["tail_image_path"] = str(tail_files[0])
        
        # Enhanced input validation
        if len(prompt) > 2000:  # Reasonable prompt length
            raise HTTPException(status_code=400, detail="Prompt too long")
        
        # Validate inputs with security manager
        validated_inputs = security_manager.validate_and_sanitize_inputs(**kwargs)
        
        # Start generation in background
        asyncio.create_task(
            background_generation(job_id, model, validated_inputs)
        )
        
        # Return job ID for tracking
        return {
            "job_id": job_id,
            "status": "started",
            "message": "Video generation started"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

async def background_generation(job_id: str, model: str, validated_inputs: Dict[str, Any]):
    """Background task for video generation with progress updates"""
    try:
        # Update status: Starting
        await manager.broadcast_job_update(job_id, {
            "status": "starting",
            "progress": 0,
            "message": "Initializing generation...",
            "timestamp": datetime.now().isoformat()
        })
        
        # Update status: Uploading
        await manager.broadcast_job_update(job_id, {
            "status": "uploading",
            "progress": 20,
            "message": "Uploading image to FAL.AI...",
            "timestamp": datetime.now().isoformat()
        })
        
        # Update status: Processing
        await manager.broadcast_job_update(job_id, {
            "status": "processing",
            "progress": 40,
            "message": "Generating video...",
            "timestamp": datetime.now().isoformat()
        })
        
        # Get model configuration
        models = config.get("models", {})
        if model not in models:
            raise ValueError(f"Unknown model: {model}")
        
        model_config = models[model]
        if isinstance(model_config, dict):
            endpoint = model_config["endpoint"]
        else:
            endpoint = model_config  # Legacy string format
        
        # Generate video using the specified endpoint
        try:
            result = await generator.generate_video(endpoint, **validated_inputs)
        except Exception as e:
            # Try legacy method mapping for backward compatibility
            if model == "kling_21_standard":
                result = await generator.generate_kling_21_standard(**validated_inputs)
            elif model == "kling_21_pro":
                result = await generator.generate_kling_21_pro(**validated_inputs)
            elif model == "kling_21_master":
                result = await generator.generate_kling_21_master(**validated_inputs)
            elif model == "kling_16_pro":
                result = await generator.generate_kling_v16(**validated_inputs)
            elif model == "workflow":
                result = await generator.run_workflow(arguments=validated_inputs)
            else:
                raise ValueError(f"Model {model} not supported: {str(e)}")
        
        # Update status: Completed
        await manager.broadcast_job_update(job_id, {
            "status": "completed",
            "progress": 100,
            "message": "Video generation completed!",
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        # Update status: Failed
        await manager.broadcast_job_update(job_id, {
            "status": "failed",
            "progress": 0,
            "message": f"Generation failed: {str(e)}",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

@app.get("/api/job/{job_id}")
@limiter.limit("60/minute")
async def get_job_status(request: Request, job_id: str):
    """Get job status"""
    if job_id not in manager.job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return manager.job_status[job_id]

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo received data (for connection testing)
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/history")
@limiter.limit("30/minute")
async def get_generation_history(request: Request):
    """Get generation history"""
    # Simple in-memory history (could be replaced with database)
    return {
        "history": [
            {
                "id": job_id,
                "timestamp": status.get("timestamp"),
                "status": status.get("status"),
                "result": status.get("result")
            }
            for job_id, status in manager.job_status.items()
            if status.get("status") == "completed"
        ]
    }

@app.get("/api/performance")
@limiter.limit("10/minute")
async def get_performance_metrics(request: Request):
    """Get application performance metrics"""
    return performance_optimizer.get_performance_report()

@app.get("/metrics")
async def get_prometheus_metrics():
    """Prometheus metrics endpoint"""
    # This would be implemented with prometheus_client in a real application
    return {"message": "Prometheus metrics endpoint - implement with prometheus_client library"}

# ========================================================================
#                           Error Handlers                               
# ========================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    # Log the actual error but don't expose it
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.exception_handler(413)
async def payload_too_large_handler(request: Request, exc):
    return JSONResponse(
        status_code=413,
        content={"detail": "Request payload too large"}
    )

@app.exception_handler(422)
async def validation_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error"}
    )

# ========================================================================
#                              Startup                                   
# ========================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    # Create necessary directories
    directories = ["./temp/uploads", "./web/static", "./web/templates"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Initialize performance optimizations
    await performance_optimizer.initialize()
    
    # Validate API key
    try:
        config.set_api_key()
        print("✅ Web application initialized successfully")
    except Exception as e:
        print(f"⚠️ Warning: API key not configured - {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    # Cleanup performance optimizations
    await performance_optimizer.cleanup()
    
    # Clean up temporary files
    temp_dir = Path("./temp/uploads")
    if temp_dir.exists():
        for file in temp_dir.glob("*"):
            try:
                file.unlink()
            except:
                pass

# ========================================================================
#                              Main                                      
# ========================================================================

def main():
    """Run the web application"""
    import argparse
    
    parser = argparse.ArgumentParser(description="FAL.AI Video Generator Web Interface")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    print(f"""
🚀 FAL.AI Video Generator Web Interface
📡 Server: http://{args.host}:{args.port}
📱 Modern UI with drag-and-drop, real-time progress, and file previews
    """)
    
    uvicorn.run(
        "web_app:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )

if __name__ == "__main__":
    main()