#!/usr/bin/env python3
"""
FastAPI 서버 - 토지 분석 웹 애플리케이션
"""

import logging
import time
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import uvicorn
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import os
import json
from weasyprint import HTML
from fastapi.middleware.cors import CORSMiddleware

from main_orchestrator import run_land_analysis_inference, render_html_report
from logging_config import setup_logging

# --- Logging Setup ---
setup_logging()
logger = logging.getLogger(__name__)
# ---------------------


# Pydantic 모델 정의
class LandData(BaseModel):
    주소: str = Field(..., description="토지 주소")
    지목: str = Field(..., description="토지 지목")
    용도지역: str = Field(..., description="용도지역")
    용도지구: str = Field(default="지정되지않음", description="용도지구")
    토지이용상황: str = Field(..., description="토지이용상황")
    지형고저: str = Field(..., description="지형고저")
    형상: str = Field(..., description="토지 형상")
    도로접면: str = Field(..., description="도로접면")
    공시지가: int = Field(..., description="공시지가")

class AnalyzeData(BaseModel):
    totalScore: Optional[int] = Field(None, description="종합 점수")
    입지조건: Optional[int] = Field(None, description="입지조건 점수")
    인프라: Optional[int] = Field(None, description="인프라 점수")
    안정성: Optional[int] = Field(None, description="안정성 점수")

class AnalysisRequest(BaseModel):
    analyze_data: AnalyzeData = Field(..., description="분석 점수 데이터")
    land_data: LandData = Field(..., description="토지 데이터")

class AnalysisResponse(BaseModel):
    task_id: str = Field(..., description="분석 작업 ID")
    status: str = Field(..., description="작업 상태")
    message: str = Field(..., description="상태 메시지")

# FastAPI 앱 초기화
app = FastAPI(
    title="토지 분석 AI 서비스 API",
    version="2.0.0",
    description="MSA 기반 토지 분석 서비스 - JSON API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Middleware for Logging ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log incoming requests, their processing time, and status.
    """
    start_time = time.time()
    
    logger.info(
        "Request started",
        extra={"method": request.method, "url": str(request.url)}
    )
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    
    logger.info(
        "Request finished",
        extra={
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "process_time_ms": f"{process_time:.2f}"
        }
    )
    return response
# --------------------------


# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 분석 작업 상태 저장소 (실제 운영에서는 Redis 등 사용)
analysis_tasks: Dict[str, Dict[str, Any]] = {}

@app.post("/api/analyze", response_model=AnalysisResponse)
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """토지 분석 시작 - JSON API"""
    
    try:
        # 고유 작업 ID 생성
        task_id = str(uuid.uuid4())
        logger.info("Creating new analysis task", extra={"task_id": task_id})
        
        # JSON 데이터를 문자열로 변환 (기존 orchestrator 호환성)
        land_data_dict = request.land_data.dict()
        analyze_data_dict = request.analyze_data.dict()
        land_data_str = ", ".join([f"'{k}': '{v}'" for k, v in land_data_dict.items()])
        
        # 작업 상태 초기화
        analysis_tasks[task_id] = {
            "status": "processing",
            "progress": 0,
            "message": "분석을 시작합니다...",
            "land_data": land_data_dict,
            "analyze_data": analyze_data_dict,
            "land_data_str": land_data_str,
            "created_at": datetime.now(),
            "result": None,
            "error": None
        }
        
        # 백그라운드에서 분석 실행
        background_tasks.add_task(run_analysis_task, task_id, land_data_str, analyze_data_dict)
        
        return AnalysisResponse(
            task_id=task_id,
            status="processing",
            message="분석이 시작되었습니다."
        )
        
    except Exception as e:
        logger.error("Error processing analysis request", extra={"error": str(e)})
        raise HTTPException(status_code=400, detail=f"분석 요청 처리 오류: {str(e)}")

@app.get("/loading/{task_id}", response_class=HTMLResponse)
async def loading_page(request: Request, task_id: str):
    """로딩 페이지 - MSA 프론트엔드용"""
    if task_id not in analysis_tasks:
        logger.warning("Loading page requested for non-existent task", extra={"task_id": task_id})
        return HTMLResponse(f'''
        <html>
        <head><title>오류</title></head>
        <body>
            <h1>❌ 분석 작업을 찾을 수 없습니다</h1>
            <p>Task ID: {task_id}</p>
            <p><a href="/browser_test.html">새 분석 시작</a></p>
        </body>
        </html>
        ''', status_code=404)
    
    task = analysis_tasks[task_id]
    
    try:
        return templates.TemplateResponse("loading.html", {
            "request": request,
            "task_id": task_id,
            "land_data": task["land_data"]
        })
    except Exception as e:
        logger.error("Error rendering loading template", extra={"task_id": task_id, "error": str(e)})
        # Fallback HTML
        return HTMLResponse(f"<h1>Template Error</h1><p>{e}</p>", status_code=500)


@app.get("/api/status/{task_id}")
async def get_analysis_status(task_id: str):
    """분석 상태 확인 API"""
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    
    task = analysis_tasks[task_id]
    return {
        "task_id": task_id,
        "status": task["status"],
        "progress": task["progress"],
        "message": task["message"],
        "error": task.get("error"),
        "created_at": task["created_at"].isoformat()
    }

@app.get("/api/result/{task_id}")
async def get_analysis_result_json(task_id: str):
    """분석 결과 JSON API"""
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    
    task = analysis_tasks[task_id]
    
    if task["status"] == "processing":
        raise HTTPException(status_code=202, detail="분석이 아직 진행 중입니다.")
    
    if task["status"] == "error":
        raise HTTPException(status_code=500, detail=f"분석 중 오류가 발생했습니다: {task['error']}")
    
    if task["status"] == "completed" and task["result"]:
        return {
            "task_id": task_id,
            "status": "completed",
            "land_data": task["land_data"],
            "result": task["result"],
            "created_at": task["created_at"].isoformat()
        }
    
    raise HTTPException(status_code=404, detail="결과를 찾을 수 없습니다.")

@app.get("/result/{task_id}", response_class=HTMLResponse)
async def get_analysis_result_html(task_id: str):
    """분석 결과 HTML 페이지"""
    if task_id not in analysis_tasks:
        return HTMLResponse("<h1>작업을 찾을 수 없습니다.</h1>", status_code=404)
    
    task = analysis_tasks[task_id]
    
    if task["status"] == "processing":
        return HTMLResponse("<h1>분석이 아직 진행 중입니다.</h1>", status_code=202)
    
    if task["status"] == "error":
        return HTMLResponse(f"<h1>분석 중 오류가 발생했습니다.</h1><p>{task['error']}</p>", status_code=500)
    
    if task["status"] == "completed" and task["result"]:
        # HTML 보고서 렌더링
        html_report = render_html_report(task["land_data_str"], task["result"], task_id, template_path="web_report_template.html")
        return HTMLResponse(html_report)
    
    return HTMLResponse("<h1>결과를 찾을 수 없습니다.</h1>", status_code=404)

@app.get("/api/result/{task_id}/pdf")
async def get_analysis_result_pdf(task_id: str):
    """분석 결과 PDF 다운로드"""
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")

    task = analysis_tasks[task_id]

    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="분석이 완료되지 않았습니다.")
    
    if not task["result"]:
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")

    # HTML 보고서 렌더링
    html_report = render_html_report(task["land_data_str"], task["result"], task_id, template_path="pdf_template.html")
    
    # PDF 생성
    pdf_bytes = HTML(string=html_report).write_pdf()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{task_id}.pdf"}
    )

async def run_analysis_task(task_id: str, land_data: str, analyze_data: Dict[str, Any]):
    """백그라운드 분석 작업"""
    try:
        logger.info("Starting background analysis task", extra={"task_id": task_id})
        
        analysis_tasks[task_id]["progress"] = 10
        analysis_tasks[task_id]["message"] = "토지 데이터를 파싱하는 중..."
        await asyncio.sleep(1)
        
        analysis_tasks[task_id]["progress"] = 30
        analysis_tasks[task_id]["message"] = "AI 토지 분석을 수행하는 중..."
        await asyncio.sleep(2)
        
        analysis_tasks[task_id]["progress"] = 60
        analysis_tasks[task_id]["message"] = "관련 정책을 검색하는 중..."
        await asyncio.sleep(1)
        
        analysis_tasks[task_id]["progress"] = 80
        analysis_tasks[task_id]["message"] = "분석 결과를 정리하는 중..."
        
        result = await asyncio.get_event_loop().run_in_executor(
            None, run_land_analysis_inference, land_data, analyze_data
        )
        
        analysis_tasks[task_id]["progress"] = 100
        analysis_tasks[task_id]["message"] = "분석이 완료되었습니다!"
        analysis_tasks[task_id]["status"] = "completed"
        analysis_tasks[task_id]["result"] = result
        logger.info("Background analysis task completed successfully", extra={"task_id": task_id})
        
    except Exception as e:
        logger.error("Error in background analysis task", extra={"task_id": task_id, "error": str(e)})
        analysis_tasks[task_id]["status"] = "error"
        analysis_tasks[task_id]["error"] = str(e)
        analysis_tasks[task_id]["message"] = f"분석 중 오류가 발생했습니다: {str(e)}"

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy", 
        "timestamp": datetime.now(),
        "service": "토지 분석 AI 서비스",
        "version": "2.0.0",
        "active_tasks": len(analysis_tasks)
    }

@app.get("/api/test/error")
async def test_error():
    """테스트용 에러 발생 API"""
    logger.error("This is a test error log message.")
    raise HTTPException(status_code=500, detail="This is a test error.")

@app.get("/actuator/health")
async def actuator_health_check():
    """Actuator 헬스 체크"""
    return {"status": "UP"}

@app.get("/api/tasks")
async def list_active_tasks():
    """활성 작업 목록 조회"""
    tasks_summary = []
    for task_id, task in analysis_tasks.items():
        tasks_summary.append({
            "task_id": task_id,
            "status": task["status"],
            "progress": task["progress"],
            "created_at": task["created_at"].isoformat(),
            "land_address": task["land_data"].get("주소", "N/A") if isinstance(task["land_data"], dict) else "N/A"
        })
    
    return {
        "total_tasks": len(tasks_summary),
        "tasks": tasks_summary
    }

def create_directories():
    """필요한 디렉토리 생성"""
    os.makedirs("static/css", exist_ok=True)
    os.makedirs("static/js", exist_ok=True)
    os.makedirs("templates", exist_ok=True)

@app.get("/browser_test.html", response_class=HTMLResponse)
async def browser_test_page():
    """브라우저 테스트 페이지"""
    try:
        with open("browser_test.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>브라우저 테스트 페이지를 찾을 수 없습니다.</h1>", status_code=404)

@app.get("/")
async def api_info():
    """API 정보 및 사용법"""
    return {
        "service": "토지 분석 AI 서비스 API",
        "version": "2.0.0",
        "description": "MSA 기반 토지 분석 서비스",
        "browser_test": "/browser_test.html (브라우저 테스트 페이지)",
        "endpoints": {
            "POST /api/analyze": "토지 분석 시작",
            "GET /api/status/{task_id}": "분석 상태 확인",
            "GET /api/result/{task_id}": "분석 결과 JSON",
            "GET /result/{task_id}": "분석 결과 HTML",
            "GET /loading/{task_id}": "로딩 페이지",
            "GET /api/tasks": "활성 작업 목록",
            "GET /health": "헬스 체크"
        },
        "sample_request": {
            "analyze_data": {
                "totalScore": 71,
                "입지조건": 86,
                "인프라": 78,
                "안정성": 48
            },
            "land_data": {
                "주소": "대구광역시 중구 동인동1가 2-1",
                "지목": "대",
                "용도지역": "중심상업지역",
                "용도지구": "지정되지않음",
                "토지이용상황": "업무용",
                "지형고저": "평지",
                "형상": "세로장방",
                "도로접면": "광대소각",
                "공시지가": 3735000
            }
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    create_directories()
    logger.info("🚀 토지 분석 AI 서비스 API 시작")
    logger.info("📍 API 문서: http://localhost:8000/docs")
    logger.info("📍 API 정보: http://localhost:8000")
    logger.info("🔧 MSA 기반 JSON API 서비스")
    
    uvicorn.run(
        "fastapi_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )