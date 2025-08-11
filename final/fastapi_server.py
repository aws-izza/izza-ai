#!/usr/bin/env python3
"""
FastAPI 서버 - 토지 분석 웹 애플리케이션
"""

from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any
import os
import json

from main_orchestrator import run_land_analysis_inference, render_html_report

# FastAPI 앱 초기화
app = FastAPI(title="토지 분석 AI 서비스", version="1.0.0")

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 분석 작업 상태 저장소 (실제 운영에서는 Redis 등 사용)
analysis_tasks: Dict[str, Dict[str, Any]] = {}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """메인 페이지"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze")
async def start_analysis(
    background_tasks: BackgroundTasks,
    land_data: str = Form(..., description="토지 데이터")
):
    """토지 분석 시작"""
    
    # 고유 작업 ID 생성
    task_id = str(uuid.uuid4())
    
    # 작업 상태 초기화
    analysis_tasks[task_id] = {
        "status": "processing",
        "progress": 0,
        "message": "분석을 시작합니다...",
        "land_data": land_data,
        "created_at": datetime.now(),
        "result": None,
        "error": None
    }
    
    # 백그라운드에서 분석 실행
    background_tasks.add_task(run_analysis_task, task_id, land_data)
    
    # 로딩 페이지로 리다이렉트
    return RedirectResponse(url=f"/loading/{task_id}", status_code=302)

@app.get("/loading/{task_id}", response_class=HTMLResponse)
async def loading_page(request: Request, task_id: str):
    """로딩 페이지"""
    if task_id not in analysis_tasks:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "분석 작업을 찾을 수 없습니다."
        })
    
    task = analysis_tasks[task_id]
    return templates.TemplateResponse("loading.html", {
        "request": request,
        "task_id": task_id,
        "land_data": task["land_data"]
    })

@app.get("/status/{task_id}")
async def get_analysis_status(task_id: str):
    """분석 상태 확인 API"""
    if task_id not in analysis_tasks:
        return {"error": "작업을 찾을 수 없습니다."}
    
    task = analysis_tasks[task_id]
    return {
        "status": task["status"],
        "progress": task["progress"],
        "message": task["message"],
        "error": task.get("error")
    }

@app.get("/result/{task_id}", response_class=HTMLResponse)
async def get_analysis_result(task_id: str):
    """분석 결과 페이지"""
    if task_id not in analysis_tasks:
        return HTMLResponse("<h1>작업을 찾을 수 없습니다.</h1>", status_code=404)
    
    task = analysis_tasks[task_id]
    
    if task["status"] == "processing":
        return HTMLResponse("<h1>분석이 아직 진행 중입니다.</h1>", status_code=202)
    
    if task["status"] == "error":
        return HTMLResponse(f"<h1>분석 중 오류가 발생했습니다.</h1><p>{task['error']}</p>", status_code=500)
    
    if task["status"] == "completed" and task["result"]:
        # HTML 보고서 렌더링
        html_report = render_html_report(task["land_data"], task["result"])
        return HTMLResponse(html_report)
    
    return HTMLResponse("<h1>결과를 찾을 수 없습니다.</h1>", status_code=404)

async def run_analysis_task(task_id: str, land_data: str):
    """백그라운드 분석 작업"""
    try:
        # 작업 상태 업데이트
        analysis_tasks[task_id]["progress"] = 10
        analysis_tasks[task_id]["message"] = "토지 데이터를 파싱하는 중..."
        await asyncio.sleep(1)  # UI 업데이트를 위한 지연
        
        # 지식 분석 시작
        analysis_tasks[task_id]["progress"] = 30
        analysis_tasks[task_id]["message"] = "AI 토지 분석을 수행하는 중..."
        await asyncio.sleep(2)
        
        # 정책 분석 시작
        analysis_tasks[task_id]["progress"] = 60
        analysis_tasks[task_id]["message"] = "관련 정책을 검색하는 중..."
        await asyncio.sleep(1)
        
        # 실제 분석 실행 (동기 함수를 비동기로 실행)
        analysis_tasks[task_id]["progress"] = 80
        analysis_tasks[task_id]["message"] = "분석 결과를 정리하는 중..."
        
        # 메인 오케스트레이터 실행
        result = await asyncio.get_event_loop().run_in_executor(
            None, run_land_analysis_inference, land_data
        )
        
        # 완료 처리
        analysis_tasks[task_id]["progress"] = 100
        analysis_tasks[task_id]["message"] = "분석이 완료되었습니다!"
        analysis_tasks[task_id]["status"] = "completed"
        analysis_tasks[task_id]["result"] = result
        
    except Exception as e:
        # 오류 처리
        analysis_tasks[task_id]["status"] = "error"
        analysis_tasks[task_id]["error"] = str(e)
        analysis_tasks[task_id]["message"] = f"분석 중 오류가 발생했습니다: {str(e)}"

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "timestamp": datetime.now()}

# 정적 파일 및 템플릿 디렉토리 생성
def create_directories():
    """필요한 디렉토리 생성"""
    os.makedirs("static/css", exist_ok=True)
    os.makedirs("static/js", exist_ok=True)
    os.makedirs("templates", exist_ok=True)

if __name__ == "__main__":
    create_directories()
    print("🚀 토지 분석 AI 서비스 시작")
    print("📍 http://localhost:8000 에서 접속 가능합니다.")
    
    uvicorn.run(
        "fastapi_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )