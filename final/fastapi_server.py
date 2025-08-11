#!/usr/bin/env python3
"""
FastAPI 서버 - 토지 분석 웹 애플리케이션
"""

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
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

from main_orchestrator import run_land_analysis_inference, render_html_report

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

class AnalysisRequest(BaseModel):
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
        
        # JSON 데이터를 문자열로 변환 (기존 orchestrator 호환성)
        land_data_dict = request.land_data.dict()
        land_data_str = ", ".join([f"'{k}': '{v}'" for k, v in land_data_dict.items()])
        
        # 작업 상태 초기화
        analysis_tasks[task_id] = {
            "status": "processing",
            "progress": 0,
            "message": "분석을 시작합니다...",
            "land_data": land_data_dict,
            "land_data_str": land_data_str,
            "created_at": datetime.now(),
            "result": None,
            "error": None
        }
        
        # 백그라운드에서 분석 실행
        background_tasks.add_task(run_analysis_task, task_id, land_data_str)
        
        return AnalysisResponse(
            task_id=task_id,
            status="processing",
            message="분석이 시작되었습니다."
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"분석 요청 처리 오류: {str(e)}")

@app.get("/loading/{task_id}", response_class=HTMLResponse)
async def loading_page(request: Request, task_id: str):
    """로딩 페이지 - MSA 프론트엔드용"""
    if task_id not in analysis_tasks:
        return HTMLResponse(f"""
        <html>
        <head><title>오류</title></head>
        <body>
            <h1>❌ 분석 작업을 찾을 수 없습니다</h1>
            <p>Task ID: {task_id}</p>
            <p><a href="/demo/start">새 분석 시작</a></p>
        </body>
        </html>
        """, status_code=404)
    
    task = analysis_tasks[task_id]
    
    try:
        return templates.TemplateResponse("loading.html", {
            "request": request,
            "task_id": task_id,
            "land_data": task["land_data"]
        })
    except Exception as e:
        # 템플릿 오류 시 결과 페이지와 동일한 테마의 HTML 반환
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>토지 분석 진행 중...</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');

                body {{
                    font-family: 'Noto Sans KR', sans-serif;
                    background-color: #f8f9fa;
                    margin: 0;
                    padding: 24px;
                    color: #333;
                }}

                .report-container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                    overflow: hidden;
                }}

                .report-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 20px 24px;
                    border-bottom: 1px solid #e0e0e0;
                }}

                .report-header .title-group {{
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }}

                .report-header .icon {{
                    font-size: 24px;
                    color: #007bff;
                }}

                .report-header h1 {{
                    font-size: 20px;
                    font-weight: 700;
                    margin: 0;
                }}

                .report-header .timestamp {{
                    font-size: 14px;
                    color: #888;
                    margin: 0;
                }}

                .report-body {{
                    padding: 24px;
                }}

                .card {{
                    background-color: #ffffff;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    padding: 24px;
                    margin-bottom: 24px;
                }}

                .card-title {{
                    font-size: 18px;
                    font-weight: 700;
                    margin-bottom: 20px;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 16px;
                }}

                .loading-content {{
                    text-align: center;
                    padding: 40px 20px;
                }}

                .spinner {{
                    width: 60px;
                    height: 60px;
                    border: 4px solid #e9ecef;
                    border-top: 4px solid #007bff;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 20px auto;
                }}

                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}

                .progress-container {{
                    margin: 30px 0;
                }}

                .progress-bar {{
                    height: 12px;
                    background-color: #e9ecef;
                    border-radius: 6px;
                    overflow: hidden;
                    margin-bottom: 12px;
                }}

                .progress-fill {{
                    height: 100%;
                    background-color: #007bff;
                    border-radius: 6px;
                    transition: width 0.3s ease;
                    width: 0%;
                }}

                .progress-text {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 14px;
                    color: #6c757d;
                }}

                .progress-percent {{
                    font-weight: 700;
                    color: #007bff;
                }}

                .steps-container {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 16px;
                    margin: 30px 0;
                }}

                .step {{
                    text-align: center;
                    padding: 16px;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    transition: all 0.3s ease;
                }}

                .step.active {{
                    border-color: #007bff;
                    background-color: #f8f9ff;
                }}

                .step.completed {{
                    border-color: #28a745;
                    background-color: #f8fff9;
                }}

                .step-icon {{
                    font-size: 24px;
                    margin-bottom: 8px;
                }}

                .step-text {{
                    font-size: 14px;
                    font-weight: 500;
                    color: #495057;
                }}

                .land-info {{
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    padding: 20px;
                    margin-top: 20px;
                }}

                .land-info h3 {{
                    margin: 0 0 12px 0;
                    font-size: 16px;
                    font-weight: 700;
                    color: #495057;
                }}

                .land-info p {{
                    margin: 0;
                    font-size: 14px;
                    color: #6c757d;
                    line-height: 1.5;
                }}
            </style>
        </head>
        <body>
            <div class="report-container">
                <header class="report-header">
                    <div class="title-group">
                        <span class="icon">🔍</span>
                        <div>
                            <h1>토지 분석 진행 중</h1>
                            <p class="timestamp">AI가 토지 데이터를 분석하고 있습니다</p>
                        </div>
                    </div>
                </header>

                <main class="report-body">
                    <div class="card">
                        <h2 class="card-title">분석 진행 상황</h2>
                        <div class="loading-content">
                            <div class="spinner"></div>
                            
                            <div class="progress-container">
                                <div class="progress-bar">
                                    <div class="progress-fill" id="progressFill"></div>
                                </div>
                                <div class="progress-text">
                                    <span id="progressMessage">분석을 시작합니다...</span>
                                    <span class="progress-percent" id="progressPercent">0%</span>
                                </div>
                            </div>

                            <div class="steps-container">
                                <div class="step" id="step1">
                                    <div class="step-icon">📊</div>
                                    <div class="step-text">데이터 파싱</div>
                                </div>
                                <div class="step" id="step2">
                                    <div class="step-icon">🤖</div>
                                    <div class="step-text">AI 분석</div>
                                </div>
                                <div class="step" id="step3">
                                    <div class="step-icon">🏛️</div>
                                    <div class="step-text">정책 검색</div>
                                </div>
                                <div class="step" id="step4">
                                    <div class="step-icon">📋</div>
                                    <div class="step-text">보고서 생성</div>
                                </div>
                            </div>

                            <div class="land-info">
                                <h3>📍 분석 대상 토지</h3>
                                <p><strong>주소:</strong> {task["land_data"].get("주소", "N/A")}</p>
                                <p><strong>지목:</strong> {task["land_data"].get("지목", "N/A")} | <strong>용도지역:</strong> {task["land_data"].get("용도지역", "N/A")}</p>
                                <p><strong>Task ID:</strong> {task_id}</p>
                            </div>
                        </div>
                    </div>
                </main>
            </div>

            <script>
                const taskId = "{task_id}";
                
                async function checkStatus() {{
                    try {{
                        const response = await fetch(`/api/status/${{taskId}}`);
                        const data = await response.json();
                        
                        // 진행률 업데이트
                        updateProgress(data.progress, data.message);
                        
                        // 단계 표시 업데이트
                        updateSteps(data.progress);
                        
                        if (data.status === 'completed') {{
                            window.location.href = `/result/${{taskId}}`;
                        }} else if (data.status === 'error') {{
                            showError(data.error || '알 수 없는 오류가 발생했습니다.');
                        }} else {{
                            setTimeout(checkStatus, 2000);
                        }}
                    }} catch (error) {{
                        console.error('상태 확인 오류:', error);
                        setTimeout(checkStatus, 5000);
                    }}
                }}
                
                function updateProgress(progress, message) {{
                    const progressFill = document.getElementById('progressFill');
                    const progressPercent = document.getElementById('progressPercent');
                    const progressMessage = document.getElementById('progressMessage');
                    
                    progressFill.style.width = `${{progress}}%`;
                    progressPercent.textContent = `${{progress}}%`;
                    progressMessage.textContent = message;
                }}
                
                function updateSteps(progress) {{
                    const steps = document.querySelectorAll('.step');
                    
                    steps.forEach((step, index) => {{
                        const threshold = (index + 1) * 25;
                        step.classList.remove('active', 'completed');
                        
                        if (progress >= threshold) {{
                            step.classList.add('completed');
                        }} else if (progress >= threshold - 25) {{
                            step.classList.add('active');
                        }}
                    }});
                }}
                
                function showError(error) {{
                    const loadingContent = document.querySelector('.loading-content');
                    loadingContent.innerHTML = `
                        <div style="text-align: center; padding: 40px;">
                            <div style="font-size: 48px; margin-bottom: 20px;">❌</div>
                            <h2 style="color: #dc3545; margin-bottom: 16px;">분석 중 오류가 발생했습니다</h2>
                            <p style="color: #6c757d; margin-bottom: 24px;">${{error}}</p>
                            <button onclick="window.location.href='/demo/start'" 
                                    style="background: #007bff; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 14px;">
                                다시 시도
                            </button>
                        </div>
                    `;
                }}
                
                // 페이지 로드 시 상태 확인 시작
                setTimeout(checkStatus, 1000);
            </script>
        </body>
        </html>
        """, status_code=200)

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
    """분석 결과 HTML 페이지 - MSA 프론트엔드용"""
    if task_id not in analysis_tasks:
        return HTMLResponse("<h1>작업을 찾을 수 없습니다.</h1>", status_code=404)
    
    task = analysis_tasks[task_id]
    
    if task["status"] == "processing":
        return HTMLResponse("<h1>분석이 아직 진행 중입니다.</h1>", status_code=202)
    
    if task["status"] == "error":
        return HTMLResponse(f"<h1>분석 중 오류가 발생했습니다.</h1><p>{task['error']}</p>", status_code=500)
    
    if task["status"] == "completed" and task["result"]:
        # HTML 보고서 렌더링
        html_report = render_html_report(task["land_data_str"], task["result"])
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
    return {
        "status": "healthy", 
        "timestamp": datetime.now(),
        "service": "토지 분석 AI 서비스",
        "version": "2.0.0",
        "active_tasks": len(analysis_tasks)
    }

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

# 정적 파일 및 템플릿 디렉토리 생성
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

@app.get("/demo/start")
async def start_demo_analysis(background_tasks: BackgroundTasks):
    """데모 분석 시작 - 브라우저 테스트용"""
    demo_data = {
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
    
    try:
        # 고유 작업 ID 생성
        task_id = str(uuid.uuid4())
        
        # JSON 데이터를 문자열로 변환
        land_data_str = ", ".join([f"'{k}': '{v}'" for k, v in demo_data.items()])
        
        # 작업 상태 초기화
        analysis_tasks[task_id] = {
            "status": "processing",
            "progress": 0,
            "message": "데모 분석을 시작합니다...",
            "land_data": demo_data,
            "land_data_str": land_data_str,
            "created_at": datetime.now(),
            "result": None,
            "error": None
        }
        
        # 백그라운드에서 분석 실행
        background_tasks.add_task(run_analysis_task, task_id, land_data_str)
        
        return {
            "task_id": task_id,
            "status": "processing",
            "message": "데모 분석이 시작되었습니다.",
            "loading_url": f"http://localhost:8000/loading/{task_id}",
            "status_url": f"http://localhost:8000/api/status/{task_id}",
            "result_url": f"http://localhost:8000/result/{task_id}",
            "debug_info": {
                "total_tasks": len(analysis_tasks),
                "demo_data": demo_data
            }
        }
    except Exception as e:
        return {
            "error": f"데모 시작 오류: {str(e)}",
            "task_id": None
        }

@app.get("/")
async def api_info():
    """API 정보 및 사용법"""
    return {
        "service": "토지 분석 AI 서비스 API",
        "version": "2.0.0",
        "description": "MSA 기반 토지 분석 서비스",
        "browser_test": "/browser_test.html (브라우저 테스트 페이지)",
        "demo_start": "/demo/start (데모 분석 시작)",
        "endpoints": {
            "POST /api/analyze": "토지 분석 시작",
            "GET /api/status/{task_id}": "분석 상태 확인",
            "GET /api/result/{task_id}": "분석 결과 JSON",
            "GET /result/{task_id}": "분석 결과 HTML",
            "GET /loading/{task_id}": "로딩 페이지",
            "GET /api/tasks": "활성 작업 목록",
            "GET /health": "헬스 체크",
            "GET /demo/start": "데모 분석 시작"
        },
        "sample_request": {
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
    print("🚀 토지 분석 AI 서비스 API 시작")
    print("📍 API 문서: http://localhost:8000/docs")
    print("📍 API 정보: http://localhost:8000")
    print("🔧 MSA 기반 JSON API 서비스")
    
    uvicorn.run(
        "fastapi_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )